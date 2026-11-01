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
    record_edit,
    set_setting,
    snapshot_costs,
    to_float,
)

app = FastAPI(title="Nexo API", version="1.3.0")

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

    return {
        "connected": connected,
        "db_name": db_file.name,
        "db_path": str(db_file),
        "theme": theme,
        "company_name": company_name,
        "units": list(UNITS),
        "mat_hidden_cols": mat_hidden_cols,
        "rec_hidden_cols": rec_hidden_cols,
        "version": "v1.3.0",
    }


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


# ---------- Frontend v2 Static Serving ----------

FRONTEND_DIST = paths.RESOURCE_DIR / "frontend_v2" / "dist"

if FRONTEND_DIST.exists():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="frontend_assets")

    @app.get("/")
    def serve_frontend_index():
        return FileResponse(str(FRONTEND_DIST / "index.html"))
