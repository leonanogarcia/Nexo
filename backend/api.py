import ast
import csv
import io
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import (
    UI_ASSETS,
    ICON_PNG,
    LOGO_PNG,
    UNITS,
    custom_units_for_material,
    db,
    fmt,
    fmt_num,
    get_db_path,
    get_setting,
    init_db,
    material_cost,
    money_to_float,
    next_code,
    normalize_text,
    now_iso,
    paths,
    recipe_cost,
    item_cost,
    operational_cost,
    product_unit_cost,
    product_direct_cost,
    record_edit,
    set_setting,
    snapshot_costs,
    to_float,
)

app = FastAPI(title="Nexo API", version="1.4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount ui_assets so the React frontend can load official Nexo icons and illustrations
if UI_ASSETS.exists():
    app.mount("/ui_assets", StaticFiles(directory=str(UI_ASSETS)), name="ui_assets")


# ---------- Models ----------

class MaterialCreatePayload(BaseModel):
    name: str
    brand: Optional[str] = ""
    qty: Any
    unit: str
    value: Any
    category: str = "Comestível"
    barcode: Optional[str] = ""
    purchase_date: Optional[str] = None


class MaterialUpdatePayload(BaseModel):
    name: str
    brand: Optional[str] = ""
    qty: Any
    unit: str
    value: Any
    category: str = "Comestível"
    barcode: Optional[str] = ""
    purchase_date: Optional[str] = None
    edit_mode: str = "correction"  # "correction" | "update"
    edit_reason: Optional[str] = ""


class BulkDeleteCheckPayload(BaseModel):
    ids: List[int]


class ToggleActivePayload(BaseModel):
    active: bool


class ConversionPayload(BaseModel):
    material_id: int
    name: str
    base_unit: str
    factor_to_base: Any


class SettingPayload(BaseModel):
    value: Any


class RecipeItemPayload(BaseModel):
    material_id: int
    qty: Any
    unit: str


class RecipePayload(BaseModel):
    name: str
    yield_qty: Any
    yield_unit: str
    notes: Optional[str] = ""
    items: List[RecipeItemPayload] = []


# ---------- Helpers ----------

def _normalize_purchase_datetime(date_str: Optional[str]) -> str:
    clean = (date_str or "").strip()
    now = datetime.now()
    if not clean:
        return now.strftime("%Y-%m-%dT%H:%M:%S")
    clean = clean.replace(" ", "T")
    if "T" in clean:
        return clean
    now_time = now.strftime("%H:%M:%S")
    return f"{clean}T{now_time}"

def _load_hidden_cols(key: str, default: Optional[List[str]] = None) -> List[str]:
    if default is None:
        default = ["code"]
    val = get_setting(key)
    if isinstance(val, str) and val.strip():
        try:
            parsed = ast.literal_eval(val)
            if isinstance(parsed, list):
                return [str(x) for x in parsed]
            if isinstance(parsed, str):
                return [parsed]
        except Exception:
            try:
                parsed = json.loads(val)
                if isinstance(parsed, list):
                    return [str(x) for x in parsed]
            except Exception:
                pass
    elif isinstance(val, list):
        return [str(x) for x in val]
    return default


# ---------- System & Shell Endpoints ----------

@app.get("/api/status")
def get_system_status():
    init_db()
    connected = False
    db_file = paths.get_db_path()
    try:
        with db() as c:
            c.execute("SELECT 1").fetchone()
        connected = True
    except Exception:
        connected = False

    theme = get_setting("theme", "light")
    company_name = get_setting("company_name", "Nexo")
    mat_hidden_cols = _load_hidden_cols("mat_hidden_cols", ["code"])
    rec_hidden_cols = _load_hidden_cols("rec_hidden_cols", ["code"])
    prod_hidden_cols = _load_hidden_cols("prod_hidden_cols", ["code"])

    return {
        "connected": connected,
        "db_name": db_file.name,
        "db_path": str(db_file),
        "theme": theme,
        "company_name": company_name,
        "units": list(UNITS),
        "mat_hidden_cols": mat_hidden_cols,
        "rec_hidden_cols": rec_hidden_cols,
        "prod_hidden_cols": prod_hidden_cols,
        "version": "v1.4.0",
    }


# ---------- Settings Models & Endpoints (Etapa 3) ----------

class CompanyPayload(BaseModel):
    name: str
    logo: Optional[str] = ""

class OperationalCostItemPayload(BaseModel):
    id: Optional[int] = None
    name: str
    percentage: Any

class OperationalCostsPayload(BaseModel):
    costs: List[OperationalCostItemPayload]


@app.get("/api/settings")
def get_all_settings():
    init_db()
    db_file = paths.get_db_path()
    theme = get_setting("theme", "light")
    company_name = get_setting("company_name", "Nexo")
    company_logo = get_setting("company_logo", "")
    
    with db() as c:
        cost_rows = c.execute("SELECT id, name, percentage FROM cost_settings ORDER BY id ASC").fetchall()
        cost_list = [{"id": r["id"], "name": r["name"], "percentage": float(r["percentage"] or 0.0)} for r in cost_rows]
    
    total_pct = sum(r["percentage"] for r in cost_list)

    # DB Size
    size_bytes = 0
    size_fmt = "0 KB"
    try:
        if db_file.exists():
            size_bytes = db_file.stat().st_size
            if size_bytes < 1024 * 1024:
                size_fmt = f"{size_bytes / 1024:.1f} KB"
            else:
                size_fmt = f"{size_bytes / (1024 * 1024):.2f} MB"
    except Exception:
        pass

    return {
        "theme": theme,
        "company_name": company_name,
        "company_logo": company_logo,
        "cost_settings": cost_list,
        "total_operational_percentage": round(total_pct, 1),
        "units": {
            "mass": ["mg", "g", "kg", "t"],
            "volume": ["ml", "L", "kL"],
            "count": ["un"],
        },
        "database": {
            "name": db_file.name,
            "path": str(db_file),
            "size_bytes": size_bytes,
            "size_fmt": size_fmt,
            "connected": True,
        },
    }


@app.post("/api/settings/company")
def update_company_settings(payload: CompanyPayload):
    c_name = payload.name.strip()
    if not c_name:
        raise HTTPException(status_code=400, detail="O nome da empresa não pode ficar em branco.")
    set_setting("company_name", c_name)
    if payload.logo is not None:
        set_setting("company_logo", payload.logo)
    return {"ok": True, "company_name": c_name, "company_logo": payload.logo}


@app.post("/api/settings/operational-costs")
def update_operational_costs(payload: OperationalCostsPayload):
    with db() as c:
        for it in payload.costs:
            try:
                p_val = float(str(it.percentage).replace(",", "."))
            except Exception:
                p_val = 0.0
            if it.id:
                c.execute("UPDATE cost_settings SET percentage=? WHERE id=?", (p_val, it.id))
            else:
                c.execute("UPDATE cost_settings SET percentage=? WHERE name=?", (p_val, it.name))
        c.commit()
    try:
        snapshot_costs()
    except Exception:
        pass
    return {"ok": True, "message": "Custos operacionais atualizados com sucesso."}


@app.post("/api/settings/database/backup")
def create_database_backup():
    db_file = paths.get_db_path()
    if not db_file.exists():
        raise HTTPException(status_code=404, detail="Arquivo de banco de dados não encontrado.")
    
    backup_dir = db_file.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    from datetime import datetime
    import shutil
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"nexo_backup_{timestamp}.db"
    
    shutil.copy2(db_file, backup_file)
    
    size_bytes = backup_file.stat().st_size
    size_fmt = f"{size_bytes / 1024:.1f} KB" if size_bytes < 1024*1024 else f"{size_bytes / (1024*1024):.2f} MB"
    
    return {
        "ok": True,
        "backup_name": backup_file.name,
        "backup_path": str(backup_file),
        "size_fmt": size_fmt,
        "created_at": datetime.now().strftime("%d/%m/%Y às %H:%M:%S"),
        "message": f"Backup criado com sucesso: {backup_file.name}",
    }


@app.post("/api/settings/database/vacuum")
def vacuum_database():
    with db() as c:
        c.execute("VACUUM")
    return {"ok": True, "message": "Banco de dados otimizado e compactado com sucesso."}


@app.post("/api/settings/{key}")
def update_setting(key: str, payload: SettingPayload):
    val = payload.value
    if isinstance(val, (list, dict)):
        set_setting(key, repr(val))
    else:
        set_setting(key, str(val))
    return {"ok": True, "key": key, "value": val}


# ---------- Materials (Insumos) Endpoints ----------

@app.get("/api/materials")
def list_materials(
    search: str = Query("", description="Filtro de busca por nome, marca ou código"),
    status: str = Query("Ativos", description="Ativos | Inativos | Todos"),
    order_by: str = Query("name", description="Coluna de ordenação"),
    order_dir: str = Query("ASC", description="ASC | DESC"),
):
    init_db()
    query_like = f"%{search.strip()}%"
    if status == "Ativos":
        status_cond = "COALESCE(active,1)=1 AND COALESCE(archived,0)=0"
    elif status == "Inativos":
        status_cond = "COALESCE(active,1)=0 AND COALESCE(archived,0)=0"
    else:
        status_cond = "COALESCE(archived,0)=0"

    valid_cols = {
        "code": "code",
        "barcode": "barcode",
        "name": "name",
        "brand": "brand",
        "qty": "purchase_qty",
        "unit": "purchase_unit",
        "value": "purchase_value",
        "category": "category",
        "date": "created_at",
        "mod_date": "COALESCE(updated_at,created_at)",
        "status": "COALESCE(active,1)",
    }
    sql_order = valid_cols.get(order_by, "name")
    sql_dir = "DESC" if str(order_dir).upper() == "DESC" else "ASC"

    with db() as c:
        rows = c.execute(
            f"""
            SELECT
                id,
                code,
                COALESCE(barcode, '') AS barcode,
                name,
                COALESCE(brand, '') AS brand,
                purchase_qty,
                purchase_unit,
                purchase_value,
                category,
                substr(created_at, 1, 10) AS created_date,
                substr(COALESCE(updated_at, created_at), 1, 10) AS updated_date,
                COALESCE(active, 1) AS active
            FROM materials
            WHERE {status_cond}
              AND (name LIKE ? OR COALESCE(brand, '') LIKE ? OR code LIKE ? OR COALESCE(barcode, '') LIKE ?)
            ORDER BY {sql_order} COLLATE NOCASE {sql_dir}
            """,
            (query_like, query_like, query_like, query_like),
        ).fetchall()

    items = []
    for r in rows:
        items.append(
            {
                "id": r["id"],
                "code": r["code"] or "",
                "barcode": r["barcode"] or "",
                "name": r["name"],
                "brand": r["brand"] or "",
                "qty": float(r["purchase_qty"]),
                "qty_fmt": fmt_num(r["purchase_qty"]),
                "unit": r["purchase_unit"],
                "value": float(r["purchase_value"]),
                "value_fmt": fmt(r["purchase_value"]),
                "category": r["category"] or "Comestível",
                "date": r["created_date"] or "",
                "mod_date": r["updated_date"] or "",
                "active": bool(r["active"]),
                "status": "Ativo" if r["active"] else "Inativo",
            }
        )
    return {"items": items, "total": len(items)}


@app.get("/api/materials/options")
def list_material_options():
    """Retorna todos os insumos (id, code, name) ordenados por nome para o seletor de Conversões."""
    init_db()
    with db() as c:
        rows = c.execute(
            "SELECT id, code, name, purchase_unit FROM materials WHERE COALESCE(archived,0)=0 ORDER BY name COLLATE NOCASE"
        ).fetchall()
    return {
        "items": [
            {
                "id": r["id"],
                "code": r["code"] or "",
                "name": r["name"],
                "purchase_unit": r["purchase_unit"],
                "label": f"{r['id']} - {r['name']} ({r['code']})",
            }
            for r in rows
        ]
    }


@app.get("/api/materials/{material_id}")
def get_material(material_id: int):
    with db() as c:
        r = c.execute("SELECT * FROM materials WHERE id=?", (material_id,)).fetchone()
    if not r:
        raise HTTPException(status_code=404, detail="Insumo não encontrado.")
    return {
        "id": r["id"],
        "code": r["code"] or "",
        "barcode": r["barcode"] or "",
        "name": r["name"],
        "brand": r["brand"] or "",
        "qty": float(r["purchase_qty"]),
        "qty_fmt": fmt_num(r["purchase_qty"]),
        "unit": r["purchase_unit"],
        "value": float(r["purchase_value"]),
        "value_fmt": fmt(r["purchase_value"]),
        "category": r["category"] or "Comestível",
        "date": date.today().isoformat(),
        "created_at": r["created_at"],
        "updated_at": r["updated_at"],
        "active": bool(r["active"] if r["active"] is not None else 1),
    }


@app.post("/api/materials")
def create_material(payload: MaterialCreatePayload):
    try:
        name = normalize_text(payload.name.strip())
        brand = normalize_text((payload.brand or "").strip())
        unit = payload.unit.strip()
        category = payload.category.strip()
        barcode = (payload.barcode or "").strip()
        purchase_date = _normalize_purchase_datetime(payload.purchase_date)

        if not name:
            raise ValueError('O campo "Nome" é obrigatório.')
        if not unit:
            raise ValueError('O campo "Unidade" é obrigatório.')
        if not category:
            raise ValueError('O campo "Categoria" é obrigatório.')

        qty = to_float(payload.qty, "Quantidade")
        value = money_to_float(payload.value, "Valor da compra")

        if qty <= 0:
            raise ValueError("A Quantidade deve ser maior que zero.")
        if value < 0:
            raise ValueError("O Valor da compra não pode ser negativo.")
        if value == 0 and category != "Doação":
            raise ValueError("Valor zero só é permitido para itens da categoria Doação.")
        if not purchase_date:
            raise ValueError('O campo "Data" é obrigatório.')

        code = next_code("materials", "INS")
        now_val = now_iso()

        with db() as c:
            cur = c.execute(
                """
                INSERT INTO materials(code, name, purchase_qty, purchase_unit, purchase_value, brand, category, barcode, updated_at)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (code, name, qty, unit, value, brand, category, barcode, now_val),
            )
            mid = cur.lastrowid
            c.execute(
                """
                INSERT INTO purchases(material_id, qty, unit, value, brand, purchase_date)
                VALUES(?, ?, ?, ?, ?, ?)
                """,
                (mid, qty, unit, value, brand, purchase_date),
            )
            c.commit()

        snapshot_costs()
        return {"ok": True, "id": mid, "code": code, "message": "Insumo salvo com sucesso."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Não foi possível salvar o item: {e}")


@app.put("/api/materials/{material_id}")
def update_material(material_id: int, payload: MaterialUpdatePayload):
    try:
        with db() as c:
            row = c.execute("SELECT * FROM materials WHERE id=?", (material_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Insumo não encontrado.")
        before = dict(row)

        name = normalize_text(payload.name.strip())
        brand = normalize_text((payload.brand or "").strip())
        unit = payload.unit.strip()
        category = payload.category.strip()
        barcode = (payload.barcode or "").strip()
        purchase_date = _normalize_purchase_datetime(payload.purchase_date)

        if not name:
            raise ValueError('O campo "Nome" é obrigatório.')
        if not unit:
            raise ValueError('O campo "Unidade" é obrigatório.')
        if not category:
            raise ValueError('O campo "Categoria" é obrigatório.')

        qty = to_float(payload.qty, "Quantidade")
        value = money_to_float(payload.value, "Valor da compra")

        if qty <= 0:
            raise ValueError("A Quantidade deve ser maior que zero.")
        if value < 0:
            raise ValueError("O Valor da compra não pode ser negativo.")
        if value == 0 and category != "Doação":
            raise ValueError("Valor zero só é permitido para itens da categoria Doação.")
        if not purchase_date:
            raise ValueError('O campo "Data" é obrigatório.')

        after = {
            "name": name,
            "purchase_qty": qty,
            "purchase_unit": unit,
            "purchase_value": value,
            "brand": brand,
            "category": category,
            "barcode": barcode,
        }

        if payload.edit_mode == "update":
            reason = (payload.edit_reason or "").strip()
            if not reason:
                raise ValueError("A justificativa da atualização não pode ficar vazia.")
            record_edit("INSUMO", material_id, reason, {"antes": before, "depois": after})

        now_val = now_iso()
        with db() as c:
            c.execute(
                """
                UPDATE materials
                SET name=?, purchase_qty=?, purchase_unit=?, purchase_value=?, brand=?, category=?, barcode=?, updated_at=?
                WHERE id=?
                """,
                (name, qty, unit, value, brand, category, barcode, now_val, material_id),
            )
            if payload.edit_mode == "update":
                c.execute(
                    """
                    INSERT INTO purchases(material_id, qty, unit, value, brand, purchase_date)
                    VALUES(?, ?, ?, ?, ?, ?)
                    """,
                    (material_id, qty, unit, value, brand, purchase_date),
                )
            c.commit()

        snapshot_costs()
        return {"ok": True, "id": material_id, "message": "Insumo salvo com sucesso."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Não foi possível atualizar o item: {e}")


@app.patch("/api/materials/{material_id}/active")
def toggle_material_active(material_id: int, payload: ToggleActivePayload):
    with db() as c:
        row = c.execute("SELECT id, name FROM materials WHERE id=?", (material_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Insumo não encontrado.")
        new_val = 1 if payload.active else 0
        c.execute("UPDATE materials SET active=?, updated_at=? WHERE id=?", (new_val, now_iso(), material_id))
        c.commit()
    return {
        "ok": True,
        "message": f"Item {'ativado' if payload.active else 'desativado'} com sucesso.",
    }


@app.post("/api/materials/delete-check")
def check_materials_delete(payload: BulkDeleteCheckPayload):
    """Analisa vínculos em receitas e produtos para exibir o Modal de Exclusão Inteligente."""
    if not payload.ids:
        return {"linked": [], "unlinked": []}

    linked = []
    unlinked = []
    with db() as c:
        for mid in payload.ids:
            r = c.execute(
                "SELECT id, code, name, COALESCE(active, 1) AS active FROM materials WHERE id=?",
                (mid,),
            ).fetchone()
            if not r:
                continue
            refs = c.execute("SELECT COUNT(*) n FROM base_recipe_items WHERE material_id=?", (mid,)).fetchone()["n"]
            refs += c.execute(
                "SELECT COUNT(*) n FROM product_items WHERE item_type='MATERIAL' AND ref_id=?",
                (mid,),
            ).fetchone()["n"]
            item_info = {
                "id": r["id"],
                "code": r["code"] or "",
                "name": r["name"],
                "active": bool(r["active"]),
                "refs": int(refs),
            }
            if refs > 0:
                linked.append(item_info)
            else:
                unlinked.append(item_info)

    return {"linked": linked, "unlinked": unlinked, "total": len(linked) + len(unlinked)}


@app.post("/api/materials/delete-execute")
def execute_materials_delete(payload: BulkDeleteCheckPayload):
    """Executa a operação atômica de exclusão permanente (livres) e inativação/arquivamento (vinculados)."""
    check = check_materials_delete(payload)
    linked = check["linked"]
    unlinked = check["unlinked"]
    if not linked and not unlinked:
        return {"ok": True, "message": "Nenhum item para alterar."}

    now_val = now_iso()
    with db() as c:
        for r in unlinked:
            mid = r["id"]
            c.execute("DELETE FROM purchases WHERE material_id=?", (mid,))
            c.execute("DELETE FROM cost_history WHERE entity_type='MATERIAL' AND entity_id=?", (mid,))
            c.execute("DELETE FROM custom_units WHERE material_id=?", (mid,))
            c.execute("DELETE FROM materials WHERE id=?", (mid,))

        for r in linked:
            mid = r["id"]
            if r["active"]:
                c.execute("UPDATE materials SET active=0, updated_at=? WHERE id=?", (now_val, mid))
            else:
                c.execute("UPDATE materials SET archived=1, updated_at=? WHERE id=?", (now_val, mid))
        c.commit()

    total = len(linked) + len(unlinked)
    if total == 1:
        single_name = (unlinked[0] if unlinked else linked[0])["name"]
        msg = f"Item '{single_name}' alterado com sucesso."
    else:
        msg = f"{len(unlinked)} excluídos, {len(linked)} inativados/ocultados."

    return {
        "ok": True,
        "deleted_count": len(unlinked),
        "archived_count": len(linked),
        "message": msg,
    }


# ---------- Material History Endpoints ----------

def _format_history_date(val_str: str) -> str:
    if not val_str:
        return "-"
    is_hoje = "(Hoje)" in val_str
    clean = val_str.replace(" (Hoje)", "").strip().replace(" ", "T")
    formatted = clean
    try:
        if "T" in clean:
            dt, tm = clean.split("T")
            y, m, d = dt.split("-")
            formatted = f"{d}/{m}/{y} {tm[:5]}"
        elif "-" in clean and len(clean) >= 10:
            y, m, d = clean[:10].split("-")
            formatted = f"{d}/{m}/{y}"
    except Exception:
        formatted = clean
    if is_hoje:
        formatted += " (Hoje)"
    return formatted


@app.get("/api/materials/{material_id}/history")
def get_material_history(material_id: int):
    with db() as c:
        mat = c.execute(
            "SELECT id, code, name, purchase_qty, purchase_unit, purchase_value, COALESCE(brand, '') AS brand FROM materials WHERE id=?",
            (material_id,),
        ).fetchone()
        if not mat:
            raise HTTPException(status_code=404, detail="Insumo não encontrado.")
        rows = c.execute(
            "SELECT id, purchase_date, qty, unit, value, COALESCE(brand, '') AS brand FROM purchases WHERE material_id=? ORDER BY id DESC",
            (material_id,),
        ).fetchall()

    now_raw = datetime.now().strftime("%Y-%m-%dT%H:%M:%S") + " (Hoje)"
    entries = [
        {
            "id": "today",
            "raw_date": now_raw,
            "date_fmt": _format_history_date(now_raw),
            "qty": float(mat["purchase_qty"]),
            "qty_fmt": fmt_num(mat["purchase_qty"]),
            "unit": mat["purchase_unit"],
            "value": float(mat["purchase_value"]),
            "value_fmt": fmt(mat["purchase_value"]),
            "brand": mat["brand"] or "-",
            "is_today": True,
        }
    ]
    for r in rows:
        entries.append(
            {
                "id": r["id"],
                "raw_date": r["purchase_date"],
                "date_fmt": _format_history_date(r["purchase_date"]),
                "qty": float(r["qty"]),
                "qty_fmt": fmt_num(r["qty"]),
                "unit": r["unit"],
                "value": float(r["value"]),
                "value_fmt": fmt(r["value"]),
                "brand": r["brand"] or "-",
                "is_today": False,
            }
        )

    return {
        "material": {
            "id": mat["id"],
            "code": mat["code"] or "",
            "name": mat["name"],
        },
        "rows": entries,
    }


@app.get("/api/materials/{material_id}/history/export")
def export_material_history_csv(material_id: int):
    data = get_material_history(material_id)
    mat_name = data["material"]["name"]
    rows = data["rows"]

    output = io.StringIO()
    output.write("\ufeff")  # UTF-8 BOM for Excel on Windows
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["Data/Hora", "Qtd.", "Un.", "Custo", "Marca"])
    for r in rows:
        writer.writerow([r["date_fmt"], r["qty_fmt"], r["unit"], r["value_fmt"], r["brand"]])

    safe_name = "".join(ch if ch.isalnum() or ch in ("_", "-") else "_" for ch in mat_name)
    headers = {
        "Content-Disposition": f'attachment; filename="historico_{safe_name}.csv"'
    }
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers=headers,
    )


# ---------- Custom Conversions Endpoints ----------

@app.get("/api/materials/{material_id}/conversions")
def list_material_conversions(material_id: int):
    rows = custom_units_for_material(material_id)
    return {
        "items": [
            {
                "id": r["id"],
                "name": r["name"],
                "base_unit": r["base_unit"],
                "factor_to_base": float(r["factor_to_base"]),
                "factor_fmt": fmt_num(r["factor_to_base"]),
            }
            for r in rows
        ]
    }


@app.post("/api/conversions")
def save_material_conversion(payload: ConversionPayload):
    try:
        if not payload.material_id:
            raise ValueError("Selecione um insumo primeiro.")
        name = normalize_text(payload.name.strip())
        base_unit = payload.base_unit.strip()
        factor = to_float(payload.factor_to_base, "Quantidade")

        if not name:
            raise ValueError("O nome da unidade configurável é obrigatório.")
        if not base_unit:
            raise ValueError("A unidade interna é obrigatória.")
        if factor <= 0:
            raise ValueError("A quantidade deve ser maior que zero.")

        with db() as c:
            exist = c.execute(
                "SELECT id FROM custom_units WHERE material_id=? AND name=?",
                (payload.material_id, name),
            ).fetchone()
            if exist:
                c.execute(
                    "UPDATE custom_units SET base_unit=?, factor_to_base=? WHERE id=?",
                    (base_unit, factor, exist["id"]),
                )
            else:
                c.execute(
                    "INSERT INTO custom_units(material_id, name, base_unit, factor_to_base) VALUES(?, ?, ?, ?)",
                    (payload.material_id, name, base_unit, factor),
                )
            c.commit()

        return {"ok": True, "message": "Conversão salva com sucesso!"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Não foi possível salvar a conversão: {e}")


# ---------- Base Recipes (Receitas Base) Endpoints ----------

@app.get("/api/recipes")
def list_recipes(search: Optional[str] = None, status: Optional[str] = None):
    init_db()
    with db() as c:
        query = "SELECT * FROM base_recipes WHERE COALESCE(archived, 0)=0"
        params = []
        if status == "active":
            query += " AND COALESCE(active, 1)=1"
        elif status == "inactive":
            query += " AND COALESCE(active, 1)=0"
        query += " ORDER BY id DESC"
        rows = c.execute(query, params).fetchall()

        mats = {m["id"]: m for m in c.execute("SELECT id, name, brand, purchase_unit FROM materials").fetchall()}
        all_items = c.execute("SELECT * FROM base_recipe_items ORDER BY id ASC").fetchall()
        items_by_recipe = {}
        for it in all_items:
            items_by_recipe.setdefault(it["recipe_id"], []).append(it)

        result = []
        for r in rows:
            rid = r["id"]
            y_qty = float(r["yield_qty"] or 0)
            y_unit = r["yield_unit"] or ""
            
            try:
                tot_cost = recipe_cost(rid)
            except Exception:
                tot_cost = 0.0

            portion_cost = (tot_cost / y_qty) if y_qty > 0 else 0.0
            
            rec_items = items_by_recipe.get(rid, [])
            formatted_items = []
            for it in rec_items:
                mid = it["material_id"]
                mat = mats.get(mid)
                m_name = mat["name"] if mat else f"Insumo #{mid}"
                m_brand = (mat["brand"] or "") if mat else ""
                m_unit = mat["purchase_unit"] if mat else ""
                
                try:
                    i_cost = material_cost(mid, it["qty"], it["unit"])
                except Exception:
                    i_cost = 0.0

                formatted_items.append({
                    "id": it["id"],
                    "material_id": mid,
                    "material_name": m_name,
                    "material_brand": m_brand,
                    "material_unit": m_unit,
                    "qty": float(it["qty"]),
                    "qty_fmt": fmt_num(it["qty"]),
                    "unit": it["unit"],
                    "cost": float(i_cost),
                    "cost_fmt": fmt(i_cost),
                })

            is_active = bool(r["active"] if r["active"] is not None else 1)
            created = r["created_at"] or ""
            c_date = created[:10] if created else ""
            if len(c_date) == 10 and "-" in c_date:
                y, m, d = c_date.split("-")
                c_date = f"{d}/{m}/{y}"

            result.append({
                "id": rid,
                "code": r["code"] or "",
                "name": r["name"],
                "yield_qty": y_qty,
                "yield_qty_fmt": fmt_num(y_qty) if y_qty > 0 else "",
                "yield_unit": y_unit,
                "notes": r["notes"] or "",
                "created_at": c_date,
                "updated_at": r["updated_at"] or "",
                "active": is_active,
                "status": "Ativo" if is_active else "Inativo",
                "total_cost": float(tot_cost),
                "total_cost_fmt": fmt(tot_cost),
                "portion_cost": float(portion_cost),
                "portion_cost_fmt": fmt(portion_cost),
                "items_count": len(rec_items),
                "items": formatted_items,
            })

    if search and search.strip():
        s = search.strip().lower()
        result = [
            r for r in result
            if s in r["name"].lower()
            or s in r["code"].lower()
            or any(s in it["material_name"].lower() for it in r["items"])
        ]

    return result


@app.get("/api/recipes/{recipe_id}")
def get_recipe_detail(recipe_id: int):
    with db() as c:
        r = c.execute("SELECT * FROM base_recipes WHERE id=?", (recipe_id,)).fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="Receita não encontrada.")
        
        items = c.execute(
            """
            SELECT bri.*, m.name AS material_name, m.brand AS material_brand, m.purchase_unit AS material_unit
            FROM base_recipe_items bri
            JOIN materials m ON m.id = bri.material_id
            WHERE bri.recipe_id = ?
            ORDER BY bri.id ASC
            """,
            (recipe_id,),
        ).fetchall()

        try:
            tot_cost = recipe_cost(recipe_id)
        except Exception:
            tot_cost = 0.0

        y_qty = float(r["yield_qty"] or 0)
        portion_cost = (tot_cost / y_qty) if y_qty > 0 else 0.0

        formatted_items = []
        for it in items:
            mid = it["material_id"]
            try:
                i_cost = material_cost(mid, it["qty"], it["unit"])
            except Exception:
                i_cost = 0.0

            formatted_items.append({
                "id": it["id"],
                "material_id": mid,
                "material_name": it["material_name"],
                "material_brand": it["material_brand"] or "",
                "material_unit": it["material_unit"],
                "qty": float(it["qty"]),
                "qty_fmt": fmt_num(it["qty"]),
                "unit": it["unit"],
                "cost": float(i_cost),
                "cost_fmt": fmt(i_cost),
            })

    return {
        "id": r["id"],
        "code": r["code"] or "",
        "name": r["name"],
        "yield_qty": y_qty,
        "yield_qty_fmt": fmt_num(y_qty) if y_qty > 0 else "",
        "yield_unit": r["yield_unit"] or "",
        "notes": r["notes"] or "",
        "active": bool(r["active"] if r["active"] is not None else 1),
        "total_cost": float(tot_cost),
        "total_cost_fmt": fmt(tot_cost),
        "portion_cost": float(portion_cost),
        "portion_cost_fmt": fmt(portion_cost),
        "items": formatted_items,
    }


@app.post("/api/recipes")
def create_recipe(payload: RecipePayload):
    name = normalize_text(payload.name.strip())
    if not name:
        raise HTTPException(status_code=400, detail="O nome da receita é obrigatório.")
    
    yield_qty = to_float(payload.yield_qty, "Rendimento")
    if yield_qty <= 0:
        raise HTTPException(status_code=400, detail="O rendimento deve ser maior que zero.")
    
    yield_unit = payload.yield_unit.strip()
    if not yield_unit:
        raise HTTPException(status_code=400, detail="A unidade de rendimento é obrigatória.")
    
    notes = (payload.notes or "").strip()
    now_val = now_iso()

    with db() as c:
        exists = c.execute("SELECT id FROM base_recipes WHERE LOWER(name)=LOWER(?)", (name,)).fetchone()
        if exists:
            raise HTTPException(status_code=400, detail=f"Já existe uma receita com o nome '{name}'.")

        code = next_code("base_recipes", "RB")
        cur = c.execute(
            """
            INSERT INTO base_recipes(code, name, yield_qty, yield_unit, notes, created_at, updated_at, active, archived)
            VALUES(?, ?, ?, ?, ?, ?, ?, 1, 0)
            """,
            (code, name, yield_qty, yield_unit, notes, now_val, now_val),
        )
        recipe_id = cur.lastrowid

        for it in payload.items:
            m_qty = to_float(it.qty, "Quantidade do ingrediente")
            if m_qty <= 0:
                continue
            c.execute(
                """
                INSERT INTO base_recipe_items(recipe_id, material_id, qty, unit)
                VALUES(?, ?, ?, ?)
                """,
                (recipe_id, it.material_id, m_qty, it.unit.strip()),
            )
        c.commit()

    snapshot_costs()
    return {"ok": True, "id": recipe_id, "code": code, "message": "Receita salva com sucesso."}


@app.put("/api/recipes/{recipe_id}")
def update_recipe(recipe_id: int, payload: RecipePayload):
    name = normalize_text(payload.name.strip())
    if not name:
        raise HTTPException(status_code=400, detail="O nome da receita é obrigatório.")
    
    yield_qty = to_float(payload.yield_qty, "Rendimento")
    if yield_qty <= 0:
        raise HTTPException(status_code=400, detail="O rendimento deve ser maior que zero.")
    
    yield_unit = payload.yield_unit.strip()
    if not yield_unit:
        raise HTTPException(status_code=400, detail="A unidade de rendimento é obrigatória.")
    
    notes = (payload.notes or "").strip()
    now_val = now_iso()

    with db() as c:
        existing = c.execute("SELECT id FROM base_recipes WHERE id=?", (recipe_id,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Receita não encontrada.")

        dup = c.execute("SELECT id FROM base_recipes WHERE LOWER(name)=LOWER(?) AND id!=?", (name, recipe_id)).fetchone()
        if dup:
            raise HTTPException(status_code=400, detail=f"Já existe outra receita com o nome '{name}'.")

        c.execute(
            """
            UPDATE base_recipes
            SET name=?, yield_qty=?, yield_unit=?, notes=?, updated_at=?
            WHERE id=?
            """,
            (name, yield_qty, yield_unit, notes, now_val, recipe_id),
        )

        c.execute("DELETE FROM base_recipe_items WHERE recipe_id=?", (recipe_id,))
        for it in payload.items:
            m_qty = to_float(it.qty, "Quantidade do ingrediente")
            if m_qty <= 0:
                continue
            c.execute(
                """
                INSERT INTO base_recipe_items(recipe_id, material_id, qty, unit)
                VALUES(?, ?, ?, ?)
                """,
                (recipe_id, it.material_id, m_qty, it.unit.strip()),
            )
        c.commit()

    snapshot_costs()
    return {"ok": True, "id": recipe_id, "message": "Receita atualizada com sucesso."}


@app.patch("/api/recipes/{recipe_id}/active")
def toggle_recipe_active(recipe_id: int, payload: ToggleActivePayload):
    with db() as c:
        row = c.execute("SELECT id, name FROM base_recipes WHERE id=?", (recipe_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Receita não encontrada.")
        c.execute(
            "UPDATE base_recipes SET active=?, updated_at=? WHERE id=?",
            (1 if payload.active else 0, now_iso(), recipe_id),
        )
        c.commit()
    state_str = "ativada" if payload.active else "desativada"
    return {"ok": True, "id": recipe_id, "active": payload.active, "message": f"Receita {state_str} com sucesso."}


@app.post("/api/recipes/delete-check")
def check_recipes_delete(payload: BulkDeleteCheckPayload):
    if not payload.ids:
        return {"linked": [], "unlinked": [], "total": 0}
    
    linked = []
    unlinked = []
    with db() as c:
        for rid in payload.ids:
            r = c.execute(
                "SELECT id, code, name, COALESCE(active, 1) AS active FROM base_recipes WHERE id=?",
                (rid,),
            ).fetchone()
            if not r:
                continue
            refs = c.execute(
                "SELECT COUNT(*) AS n FROM product_items WHERE item_type='RECIPE_BASE' AND ref_id=?",
                (rid,),
            ).fetchone()["n"]
            item_info = {
                "id": r["id"],
                "code": r["code"] or "",
                "name": r["name"],
                "active": bool(r["active"]),
                "refs": int(refs),
            }
            if refs > 0:
                linked.append(item_info)
            else:
                unlinked.append(item_info)

    return {"linked": linked, "unlinked": unlinked, "total": len(linked) + len(unlinked)}


@app.post("/api/recipes/delete-execute")
def execute_recipes_delete(payload: BulkDeleteCheckPayload):
    check = check_recipes_delete(payload)
    linked = check["linked"]
    unlinked = check["unlinked"]
    if not linked and not unlinked:
        return {"ok": True, "message": "Nenhuma receita para alterar."}
    
    now_val = now_iso()
    with db() as c:
        for r in unlinked:
            rid = r["id"]
            c.execute("DELETE FROM base_recipe_items WHERE recipe_id=?", (rid,))
            c.execute("DELETE FROM cost_history WHERE entity_type='RECIPE_BASE' AND entity_id=?", (rid,))
            c.execute("DELETE FROM base_recipes WHERE id=?", (rid,))
        
        for r in linked:
            rid = r["id"]
            if r["active"]:
                c.execute("UPDATE base_recipes SET active=0, updated_at=? WHERE id=?", (now_val, rid))
            else:
                c.execute("UPDATE base_recipes SET archived=1, updated_at=? WHERE id=?", (now_val, rid))
        c.commit()

    snapshot_costs()
    return {
        "ok": True,
        "deleted": len(unlinked),
        "inactivated": len(linked),
        "message": "Exclusão executada com sucesso.",
    }


@app.post("/api/recipes/{recipe_id}/duplicate")
def duplicate_recipe(recipe_id: int):
    with db() as c:
        r = c.execute("SELECT * FROM base_recipes WHERE id=?", (recipe_id,)).fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="Receita original não encontrada.")
        
        base_name = r["name"]
        new_name = f"{base_name} (Cópia)"
        counter = 2
        while c.execute("SELECT id FROM base_recipes WHERE LOWER(name)=LOWER(?)", (new_name,)).fetchone():
            new_name = f"{base_name} (Cópia {counter})"
            counter += 1

        code = next_code("base_recipes", "RB")
        now_val = now_iso()
        cur = c.execute(
            """
            INSERT INTO base_recipes(code, name, yield_qty, yield_unit, notes, created_at, updated_at, active, archived)
            VALUES(?, ?, ?, ?, ?, ?, ?, 1, 0)
            """,
            (code, new_name, r["yield_qty"], r["yield_unit"], r["notes"] or "", now_val, now_val),
        )
        new_id = cur.lastrowid

        items = c.execute("SELECT * FROM base_recipe_items WHERE recipe_id=?", (recipe_id,)).fetchall()
        for it in items:
            c.execute(
                """
                INSERT INTO base_recipe_items(recipe_id, material_id, qty, unit)
                VALUES(?, ?, ?, ?)
                """,
                (new_id, it["material_id"], it["qty"], it["unit"]),
            )
        c.commit()

    snapshot_costs()
    return {"ok": True, "id": new_id, "code": code, "name": new_name, "message": "Receita duplicada com sucesso."}


@app.get("/api/recipes/{recipe_id}/history")
def get_recipe_history(recipe_id: int):
    with db() as c:
        rec = c.execute("SELECT id, code, name, yield_qty, yield_unit FROM base_recipes WHERE id=?", (recipe_id,)).fetchone()
        if not rec:
            raise HTTPException(status_code=404, detail="Receita não encontrada.")
        
        try:
            curr_cost = recipe_cost(recipe_id)
        except Exception:
            curr_cost = 0.0

        rows = c.execute(
            """
            SELECT id, cost, recorded_at
            FROM cost_history
            WHERE entity_type='RECIPE_BASE' AND entity_id=?
            ORDER BY id DESC
            """,
            (recipe_id,),
        ).fetchall()

    now_raw = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    entries = [
        {
            "id": "current",
            "date": now_raw,
            "date_fmt": _format_history_date(now_raw),
            "cost": float(curr_cost),
            "cost_fmt": fmt(curr_cost),
            "is_today": True,
        }
    ]
    for r in rows:
        entries.append({
            "id": r["id"],
            "date": r["recorded_at"],
            "date_fmt": _format_history_date(r["recorded_at"]),
            "cost": float(r["cost"]),
            "cost_fmt": fmt(r["cost"]),
            "is_today": False,
        })

    return {
        "recipe": {
            "id": rec["id"],
            "code": rec["code"] or "",
            "name": rec["name"],
            "yield_qty": rec["yield_qty"],
            "yield_unit": rec["yield_unit"],
        },
        "rows": entries,
    }


class RecipePreviewPayload(BaseModel):
    yield_qty: Optional[Any] = 1
    yield_unit: Optional[str] = "un"
    items: List[RecipeItemPayload] = []


@app.post("/api/recipes/preview-cost")
def preview_recipe_cost(payload: RecipePreviewPayload):
    total = 0.0
    items_out = []
    for it in payload.items:
        mid = it.material_id
        try:
            q = to_float(it.qty, "Quantidade")
        except Exception:
            q = 0.0
        
        c_val = 0.0
        if mid > 0 and q > 0 and it.unit:
            try:
                c_val = material_cost(mid, q, it.unit)
            except Exception:
                c_val = 0.0
        
        total += c_val
        items_out.append({
            "material_id": mid,
            "qty": q,
            "unit": it.unit,
            "cost": float(c_val),
            "cost_fmt": fmt(c_val),
        })

    try:
        y_qty = to_float(payload.yield_qty, "Rendimento")
    except Exception:
        y_qty = 1.0
    
    portion = (total / y_qty) if y_qty > 0 else 0.0
    return {
        "total_cost": float(total),
        "total_cost_fmt": fmt(total),
        "portion_cost": float(portion),
        "portion_cost_fmt": fmt(portion),
        "items": items_out,
    }


# ---------- Products (Etapa 2.2: Aba Produtos) ----------

class ProductItemPayload(BaseModel):
    item_type: str  # 'MATERIAL' | 'RECIPE_BASE' | 'PRODUCT'
    ref_id: int
    qty_per_unit: Any
    unit: str

class ProductPayload(BaseModel):
    name: str
    weight_qty: Optional[Any] = "1"
    weight_unit: Optional[str] = "un"
    sale_price: Optional[Any] = "0"
    notes: Optional[str] = ""
    items: List[ProductItemPayload] = []

class ProductPreviewPayload(BaseModel):
    items: List[ProductItemPayload] = []
    sale_price: Optional[Any] = "0"


@app.get("/api/products/composition-options")
def get_product_composition_options():
    init_db()
    with db() as c:
        materials = c.execute(
            """
            SELECT id, code, name, brand, purchase_unit, category, purchase_value
            FROM materials
            WHERE COALESCE(active, 1)=1 AND COALESCE(archived, 0)=0
            ORDER BY name ASC
            """
        ).fetchall()
        recipes = c.execute(
            """
            SELECT id, code, name, yield_qty, yield_unit
            FROM base_recipes
            WHERE COALESCE(active, 1)=1 AND COALESCE(archived, 0)=0
            ORDER BY name ASC
            """
        ).fetchall()
        products = c.execute(
            """
            SELECT id, code, name, weight_qty, weight_unit, sale_price
            FROM products
            WHERE COALESCE(active, 1)=1 AND COALESCE(archived, 0)=0
            ORDER BY name ASC
            """
        ).fetchall()

    return {
        "materials": [
            {
                "id": m["id"],
                "code": m["code"],
                "name": m["name"],
                "brand": m["brand"] or "",
                "unit": m["purchase_unit"],
                "category": m["category"] or "Insumo",
                "label": f"{m['name']}{' (' + m['brand'] + ')' if m['brand'] else ''}",
            }
            for m in materials
        ],
        "recipes": [
            {
                "id": r["id"],
                "code": r["code"],
                "name": r["name"],
                "yield_qty": r["yield_qty"],
                "yield_unit": r["yield_unit"],
                "label": f"{r['name']} ({r['yield_qty']} {r['yield_unit']})",
            }
            for r in recipes
        ],
        "products": [
            {
                "id": p["id"],
                "code": p["code"],
                "name": p["name"],
                "unit": p["weight_unit"] or "un",
                "label": p["name"],
            }
            for p in products
        ],
    }


@app.get("/api/products")
def list_products(search: Optional[str] = None, status: Optional[str] = None):
    init_db()
    with db() as c:
        query = "SELECT * FROM products WHERE COALESCE(archived, 0)=0"
        params = []
        if status == "active":
            query += " AND COALESCE(active, 1)=1"
        elif status == "inactive":
            query += " AND COALESCE(active, 1)=0"
        query += " ORDER BY id DESC"
        rows = c.execute(query, params).fetchall()

        all_items = c.execute("SELECT * FROM product_items ORDER BY id ASC").fetchall()
        items_by_prod = {}
        for it in all_items:
            items_by_prod.setdefault(it["product_id"], []).append(it)

        # Lookup caches
        mat_cache = {m["id"]: m for m in c.execute("SELECT id, name, brand, purchase_unit FROM materials").fetchall()}
        rec_cache = {r["id"]: r for r in c.execute("SELECT id, name, yield_unit FROM base_recipes").fetchall()}
        prod_cache = {p["id"]: p for p in c.execute("SELECT id, name, weight_unit FROM products").fetchall()}

        result = []
        for p in rows:
            pid = p["id"]
            try:
                direct_cost = product_direct_cost(pid)
            except Exception:
                direct_cost = 0.0
            
            try:
                tot_cost = product_unit_cost(pid)
            except Exception:
                tot_cost = direct_cost + operational_cost(direct_cost)

            sp = float(p["sale_price"] or 0.0)
            profit_val = sp - tot_cost
            margin_pct = (profit_val / sp * 100.0) if sp > 0 else 0.0
            markup = (sp / tot_cost) if tot_cost > 0 else 0.0

            # Composition items for table expansion / preview
            comp_list = []
            for it in items_by_prod.get(pid, []):
                itype = it["item_type"]
                ref_id = it["ref_id"]
                ref_name = "Item"
                if itype == "MATERIAL":
                    ref_name = mat_cache[ref_id]["name"] if ref_id in mat_cache else f"Insumo #{ref_id}"
                elif itype == "RECIPE_BASE":
                    ref_name = rec_cache[ref_id]["name"] if ref_id in rec_cache else f"Receita #{ref_id}"
                elif itype == "PRODUCT":
                    ref_name = prod_cache[ref_id]["name"] if ref_id in prod_cache else f"Produto #{ref_id}"
                
                try:
                    c_cost = item_cost(itype, ref_id, it["qty_per_unit"], it["unit"])
                except Exception:
                    c_cost = 0.0

                comp_list.append({
                    "id": it["id"],
                    "item_type": itype,
                    "ref_id": ref_id,
                    "name": ref_name,
                    "qty": it["qty_per_unit"],
                    "qty_fmt": fmt_num(it["qty_per_unit"]),
                    "unit": it["unit"],
                    "cost": float(c_cost),
                    "cost_fmt": fmt(c_cost),
                })

            w_qty = float(p["weight_qty"] or 1.0)
            w_unit = p["weight_unit"] or "un"

            result.append({
                "id": pid,
                "code": p["code"] or f"PROD_{pid:04d}",
                "name": p["name"],
                "weight_qty": w_qty,
                "weight_qty_fmt": fmt_num(w_qty),
                "weight_unit": w_unit,
                "direct_cost": float(direct_cost),
                "direct_cost_fmt": fmt(direct_cost),
                "production_cost": float(tot_cost),
                "production_cost_fmt": fmt(tot_cost),
                "sale_price": sp,
                "sale_price_fmt": fmt(sp),
                "profit_val": float(profit_val),
                "profit_val_fmt": fmt(profit_val),
                "profit_margin_pct": round(margin_pct, 1),
                "profit_margin_fmt": f"{margin_pct:.1f}%",
                "markup": round(markup, 2),
                "notes": p["notes"] or "",
                "active": bool(p["active"]),
                "created_at": p["created_at"],
                "updated_at": p["updated_at"],
                "items_count": len(comp_list),
                "items": comp_list,
            })

    if search:
        s = search.strip().lower()
        result = [r for r in result if s in r["name"].lower() or s in (r["code"] or "").lower()]

    return {"items": result, "total": len(result)}


@app.get("/api/products/{product_id}")
def get_product_detail(product_id: int):
    with db() as c:
        p = c.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
        if not p:
            raise HTTPException(status_code=404, detail="Produto não encontrado.")
        
        items = c.execute("SELECT * FROM product_items WHERE product_id=? ORDER BY id ASC", (product_id,)).fetchall()
        mat_cache = {m["id"]: m for m in c.execute("SELECT id, name, brand, purchase_unit FROM materials").fetchall()}
        rec_cache = {r["id"]: r for r in c.execute("SELECT id, name, yield_unit FROM base_recipes").fetchall()}
        prod_cache = {p["id"]: p for p in c.execute("SELECT id, name, weight_unit FROM products").fetchall()}

        items_out = []
        for it in items:
            itype = it["item_type"]
            ref_id = it["ref_id"]
            ref_name = "Item"
            if itype == "MATERIAL":
                ref_name = mat_cache[ref_id]["name"] if ref_id in mat_cache else f"Insumo #{ref_id}"
            elif itype == "RECIPE_BASE":
                ref_name = rec_cache[ref_id]["name"] if ref_id in rec_cache else f"Receita #{ref_id}"
            elif itype == "PRODUCT":
                ref_name = prod_cache[ref_id]["name"] if ref_id in prod_cache else f"Produto #{ref_id}"

            try:
                c_cost = item_cost(itype, ref_id, it["qty_per_unit"], it["unit"])
            except Exception:
                c_cost = 0.0

            items_out.append({
                "id": it["id"],
                "item_type": itype,
                "ref_id": ref_id,
                "name": ref_name,
                "qty": it["qty_per_unit"],
                "unit": it["unit"],
                "cost": float(c_cost),
                "cost_fmt": fmt(c_cost),
            })

        try:
            direct_cost = product_direct_cost(product_id)
        except Exception:
            direct_cost = 0.0
        
        try:
            tot_cost = product_unit_cost(product_id)
        except Exception:
            tot_cost = direct_cost + operational_cost(direct_cost)

        sp = float(p["sale_price"] or 0.0)
        profit_val = sp - tot_cost
        margin_pct = (profit_val / sp * 100.0) if sp > 0 else 0.0

        return {
            "id": p["id"],
            "code": p["code"],
            "name": p["name"],
            "weight_qty": p["weight_qty"],
            "weight_unit": p["weight_unit"],
            "sale_price": sp,
            "sale_price_fmt": fmt(sp),
            "direct_cost": float(direct_cost),
            "direct_cost_fmt": fmt(direct_cost),
            "production_cost": float(tot_cost),
            "production_cost_fmt": fmt(tot_cost),
            "profit_val": float(profit_val),
            "profit_val_fmt": fmt(profit_val),
            "profit_margin_pct": round(margin_pct, 1),
            "notes": p["notes"] or "",
            "active": bool(p["active"]),
            "items": items_out,
        }


@app.post("/api/products")
def create_product(payload: ProductPayload):
    name = normalize_text(payload.name.strip())
    if not name:
        raise HTTPException(status_code=400, detail="O nome do produto é obrigatório.")

    try:
        weight_qty = to_float(payload.weight_qty, "Peso / Rendimento")
    except Exception:
        weight_qty = 1.0
    
    weight_unit = (payload.weight_unit or "un").strip()
    
    try:
        sale_price = money_to_float(payload.sale_price, "Preço de Venda") if isinstance(payload.sale_price, str) else float(payload.sale_price or 0.0)
    except Exception:
        sale_price = 0.0

    notes = (payload.notes or "").strip()
    now_val = now_iso()

    with db() as c:
        exists = c.execute("SELECT id FROM products WHERE LOWER(name)=LOWER(?)", (name,)).fetchone()
        if exists:
            raise HTTPException(status_code=400, detail=f"Já existe um produto com o nome '{name}'.")

        code = next_code("products", "PROD")
        cur = c.execute(
            """
            INSERT INTO products(code, name, weight_qty, weight_unit, sale_price, notes, created_at, updated_at, active, archived)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, 1, 0)
            """,
            (code, name, weight_qty, weight_unit, sale_price, notes, now_val, now_val),
        )
        pid = cur.lastrowid

        for it in payload.items:
            try:
                q = to_float(it.qty_per_unit, "Quantidade")
            except Exception:
                q = 0.0
            if it.ref_id > 0 and q > 0 and it.unit:
                itype = it.item_type if it.item_type in ("MATERIAL", "RECIPE_BASE", "PRODUCT") else "MATERIAL"
                c.execute(
                    """
                    INSERT INTO product_items(product_id, item_type, ref_id, qty_per_unit, unit)
                    VALUES(?, ?, ?, ?, ?)
                    """,
                    (pid, itype, it.ref_id, q, it.unit.strip()),
                )

        c.commit()

    # Snapshot cost history
    try:
        c_cost = product_unit_cost(pid)
        with db() as c:
            c.execute(
                "INSERT INTO cost_history(entity_type, entity_id, cost, recorded_at) VALUES('PRODUCT', ?, ?, ?)",
                (pid, c_cost, now_val),
            )
            c.commit()
    except Exception:
        pass

    return {"ok": True, "id": pid, "code": code, "name": name}


@app.put("/api/products/{product_id}")
def update_product(product_id: int, payload: ProductPayload):
    name = normalize_text(payload.name.strip())
    if not name:
        raise HTTPException(status_code=400, detail="O nome do produto é obrigatório.")

    try:
        weight_qty = to_float(payload.weight_qty, "Peso / Rendimento")
    except Exception:
        weight_qty = 1.0
    
    weight_unit = (payload.weight_unit or "un").strip()
    
    try:
        sale_price = money_to_float(payload.sale_price, "Preço de Venda") if isinstance(payload.sale_price, str) else float(payload.sale_price or 0.0)
    except Exception:
        sale_price = 0.0

    notes = (payload.notes or "").strip()
    now_val = now_iso()

    with db() as c:
        exists = c.execute("SELECT id FROM products WHERE LOWER(name)=LOWER(?) AND id!=?", (name, product_id)).fetchone()
        if exists:
            raise HTTPException(status_code=400, detail=f"Já existe outro produto com o nome '{name}'.")

        c.execute(
            """
            UPDATE products
            SET name=?, weight_qty=?, weight_unit=?, sale_price=?, notes=?, updated_at=?
            WHERE id=?
            """,
            (name, weight_qty, weight_unit, sale_price, notes, now_val, product_id),
        )

        c.execute("DELETE FROM product_items WHERE product_id=?", (product_id,))
        for it in payload.items:
            try:
                q = to_float(it.qty_per_unit, "Quantidade")
            except Exception:
                q = 0.0
            if it.ref_id > 0 and q > 0 and it.unit:
                itype = it.item_type if it.item_type in ("MATERIAL", "RECIPE_BASE", "PRODUCT") else "MATERIAL"
                c.execute(
                    """
                    INSERT INTO product_items(product_id, item_type, ref_id, qty_per_unit, unit)
                    VALUES(?, ?, ?, ?, ?)
                    """,
                    (product_id, itype, it.ref_id, q, it.unit.strip()),
                )
        c.commit()

    try:
        c_cost = product_unit_cost(product_id)
        with db() as c:
            c.execute(
                "INSERT INTO cost_history(entity_type, entity_id, cost, recorded_at) VALUES('PRODUCT', ?, ?, ?)",
                (product_id, c_cost, now_val),
            )
            c.commit()
    except Exception:
        pass

    return {"ok": True, "id": product_id, "name": name}


@app.post("/api/products/{product_id}/toggle-status")
def toggle_product_status(product_id: int):
    now_val = now_iso()
    with db() as c:
        p = c.execute("SELECT active, name FROM products WHERE id=?", (product_id,)).fetchone()
        if not p:
            raise HTTPException(status_code=404, detail="Produto não encontrado.")
        new_active = 0 if p["active"] else 1
        c.execute("UPDATE products SET active=?, updated_at=? WHERE id=?", (new_active, now_val, product_id))
        c.commit()
    return {"ok": True, "active": bool(new_active)}


@app.post("/api/products/{product_id}/duplicate")
def duplicate_product(product_id: int):
    with db() as c:
        p = c.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
        if not p:
            raise HTTPException(status_code=404, detail="Produto original não encontrado.")
        
        base_name = p["name"]
        new_name = f"{base_name} (Cópia)"
        counter = 2
        while c.execute("SELECT id FROM products WHERE LOWER(name)=LOWER(?)", (new_name,)).fetchone():
            new_name = f"{base_name} (Cópia {counter})"
            counter += 1

        code = next_code("products", "PROD")
        now_val = now_iso()
        cur = c.execute(
            """
            INSERT INTO products(code, name, weight_qty, weight_unit, sale_price, notes, created_at, updated_at, active, archived)
            VALUES(?, ?, ?, ?, ?, ?, ?, 1, 0)
            """,
            (code, new_name, p["weight_qty"], p["weight_unit"], p["sale_price"], p["notes"], now_val, now_val),
        )
        new_pid = cur.lastrowid

        items = c.execute("SELECT * FROM product_items WHERE product_id=?", (product_id,)).fetchall()
        for it in items:
            c.execute(
                """
                INSERT INTO product_items(product_id, item_type, ref_id, qty_per_unit, unit)
                VALUES(?, ?, ?, ?, ?)
                """,
                (new_pid, it["item_type"], it["ref_id"], it["qty_per_unit"], it["unit"]),
            )
        c.commit()

    try:
        c_cost = product_unit_cost(new_pid)
        with db() as c:
            c.execute(
                "INSERT INTO cost_history(entity_type, entity_id, cost, recorded_at) VALUES('PRODUCT', ?, ?, ?)",
                (new_pid, c_cost, now_val),
            )
            c.commit()
    except Exception:
        pass

    return {"ok": True, "id": new_pid, "code": code, "name": new_name}


@app.post("/api/products/check-delete")
def check_products_delete(payload: BulkDeleteCheckPayload):
    with db() as c:
        linked = []
        unlinked = []
        for pid in payload.ids:
            p = c.execute("SELECT id, name, code, active FROM products WHERE id=?", (pid,)).fetchone()
            if not p:
                continue
            # Check if this product is used in another product
            usage = c.execute(
                """
                SELECT p.name
                FROM product_items pi
                JOIN products p ON p.id = pi.product_id
                WHERE pi.item_type='PRODUCT' AND pi.ref_id=? AND p.id!=?
                """,
                (pid, pid),
            ).fetchall()
            if usage:
                linked.append({
                    "id": p["id"],
                    "name": p["name"],
                    "code": p["code"],
                    "active": bool(p["active"]),
                    "used_by": [u["name"] for u in usage],
                })
            else:
                unlinked.append({
                    "id": p["id"],
                    "name": p["name"],
                    "code": p["code"],
                    "active": bool(p["active"]),
                })
        return {
            "total": len(linked) + len(unlinked),
            "linked": linked,
            "unlinked": unlinked,
        }


@app.post("/api/products/batch-delete")
def execute_products_delete(payload: BulkDeleteCheckPayload):
    check = check_products_delete(payload)
    linked = check["linked"]
    unlinked = check["unlinked"]
    if not linked and not unlinked:
        return {"ok": True, "message": "Nenhum produto para alterar."}

    now_val = now_iso()
    with db() as c:
        for p in unlinked:
            pid = p["id"]
            c.execute("DELETE FROM product_items WHERE product_id=?", (pid,))
            c.execute("DELETE FROM cost_history WHERE entity_type='PRODUCT' AND entity_id=?", (pid,))
            c.execute("DELETE FROM products WHERE id=?", (pid,))

        for p in linked:
            pid = p["id"]
            if p["active"]:
                c.execute("UPDATE products SET active=0, updated_at=? WHERE id=?", (now_val, pid))
            else:
                c.execute("UPDATE products SET archived=1, updated_at=? WHERE id=?", (now_val, pid))
        c.commit()

    return {
        "ok": True,
        "deleted_count": len(unlinked),
        "inactivated_count": len(linked),
        "message": f"{len(unlinked)} produtos excluídos e {len(linked)} inativados/arquivados com sucesso.",
    }


@app.post("/api/products/preview-cost")
def preview_product_cost(payload: ProductPreviewPayload):
    direct_total = 0.0
    items_out = []
    for it in payload.items:
        itype = it.item_type if it.item_type in ("MATERIAL", "RECIPE_BASE", "PRODUCT") else "MATERIAL"
        ref_id = it.ref_id
        try:
            q = to_float(it.qty_per_unit, "Quantidade")
        except Exception:
            q = 0.0

        c_val = 0.0
        if ref_id > 0 and q > 0 and it.unit:
            try:
                c_val = item_cost(itype, ref_id, q, it.unit)
            except Exception:
                c_val = 0.0

        direct_total += c_val
        items_out.append({
            "item_type": itype,
            "ref_id": ref_id,
            "qty": q,
            "unit": it.unit,
            "cost": float(c_val),
            "cost_fmt": fmt(c_val),
        })

    op_cost = operational_cost(direct_total)
    tot_cost = direct_total + op_cost

    try:
        sp = money_to_float(payload.sale_price, "Preço de Venda") if isinstance(payload.sale_price, str) else float(payload.sale_price or 0.0)
    except Exception:
        sp = 0.0

    profit_val = sp - tot_cost
    margin_pct = (profit_val / sp * 100.0) if sp > 0 else 0.0
    markup = (sp / tot_cost) if tot_cost > 0 else 0.0

    return {
        "direct_cost": float(direct_total),
        "direct_cost_fmt": fmt(direct_total),
        "operational_cost": float(op_cost),
        "operational_cost_fmt": fmt(op_cost),
        "production_cost": float(tot_cost),
        "production_cost_fmt": fmt(tot_cost),
        "sale_price": float(sp),
        "sale_price_fmt": fmt(sp),
        "profit_val": float(profit_val),
        "profit_val_fmt": fmt(profit_val),
        "profit_margin_pct": round(margin_pct, 1),
        "profit_margin_fmt": f"{margin_pct:.1f}%",
        "markup": round(markup, 2),
        "items": items_out,
    }


@app.get("/api/products/{product_id}/history")
def get_product_history(product_id: int):
    with db() as c:
        p = c.execute("SELECT id, code, name, sale_price FROM products WHERE id=?", (product_id,)).fetchone()
        if not p:
            raise HTTPException(status_code=404, detail="Produto não encontrado.")
        
        try:
            curr_cost = product_unit_cost(product_id)
        except Exception:
            curr_cost = 0.0

        rows = c.execute(
            """
            SELECT id, cost, recorded_at
            FROM cost_history
            WHERE entity_type='PRODUCT' AND entity_id=?
            ORDER BY id DESC
            """,
            (product_id,),
        ).fetchall()

        today_iso = date.today().isoformat()
        res_rows = []
        for r in rows:
            rec_date = r["recorded_at"][:10] if r["recorded_at"] else ""
            is_today = rec_date == today_iso
            cost_val = float(r["cost"] or 0.0)

            try:
                dt = datetime.fromisoformat(r["recorded_at"])
                d_fmt = dt.strftime("%d/%m/%Y às %H:%M")
            except Exception:
                d_fmt = r["recorded_at"] or ""

            res_rows.append({
                "id": r["id"],
                "cost": cost_val,
                "cost_fmt": fmt(cost_val),
                "raw_date": r["recorded_at"],
                "date_fmt": f"{d_fmt} (Hoje)" if is_today else d_fmt,
                "is_today": is_today,
            })

        if not res_rows:
            now_str = datetime.now().strftime("%d/%m/%Y às %H:%M")
            res_rows.append({
                "id": 0,
                "cost": curr_cost,
                "cost_fmt": fmt(curr_cost),
                "raw_date": now_iso(),
                "date_fmt": f"{now_str} (Hoje)",
                "is_today": True,
            })

        return {
            "product_id": p["id"],
            "code": p["code"],
            "name": p["name"],
            "current_cost": curr_cost,
            "current_cost_fmt": fmt(curr_cost),
            "rows": res_rows,
        }


# ---------- Frontend v2 Static Serving ----------

FRONTEND_DIST = paths.RESOURCE_DIR / "frontend_v2" / "dist"

if FRONTEND_DIST.exists():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="frontend_assets")

    @app.get("/")
    def serve_frontend_index():
        return FileResponse(str(FRONTEND_DIST / "index.html"))
