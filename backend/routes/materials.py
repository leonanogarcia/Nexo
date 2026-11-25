import ast
import csv
import io
import json
import math
import platform
import shutil
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from pydantic import BaseModel

from ..reports import (
    build_csv_or_zip_report,
    build_pdf_report,
    build_xlsx_report,
    build_xml_report,
    collect_report_sections,
)
from .. import (
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
    item_direct_cost,
    item_operational_cost,
    calculate_product_operational_breakdown,
    get_kitchen_rates,
    EQUIPMENT_PRESETS,
    get_cost_settings_detailed,
    product_unit_cost,
    product_direct_cost,
    product_operational_cost,
    recipe_operational_breakdown,
    product_operational_breakdown,
    convert_generic,
    record_edit,
    set_setting,
    snapshot_costs,
    to_float,
)


from .common import *

router = APIRouter()


@router.get("/api/materials")
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


@router.get("/api/materials/options")
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


@router.get("/api/materials/{material_id}")
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

@router.post("/api/materials")
def create_material(payload: MaterialCreatePayload):
    try:
        name = _validate_quality_text(payload.name, "Nome")
        raw_brand = (payload.brand or "").strip()
        is_no_brand = _canonical_key(raw_brand) in ("", "sem marca", "granel")
        brand = "Sem marca" if is_no_brand else _validate_quality_text(raw_brand, "Marca", is_brand=True, no_brand=False)
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
            _check_material_duplicate_or_typo(
                c, name, brand, qty, unit, confirm_similar=bool(payload.confirm_similar)
            )
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
    except SimilarMaterialWarning as e:
        raise HTTPException(
            status_code=409,
            detail={"code": "SIMILAR_MATERIAL_EXISTS", "message": str(e), "existing": e.existing},
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Não foi possível salvar o item: {e}")


@router.put("/api/materials/{material_id}")
def update_material(material_id: int, payload: MaterialUpdatePayload):
    try:
        with db() as c:
            row = c.execute("SELECT * FROM materials WHERE id=?", (material_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Insumo não encontrado.")
        before = dict(row)

        name = _validate_quality_text(payload.name, "Nome")
        raw_brand = (payload.brand or "").strip()
        is_no_brand = _canonical_key(raw_brand) in ("", "sem marca", "granel")
        brand = "Sem marca" if is_no_brand else _validate_quality_text(raw_brand, "Marca", is_brand=True, no_brand=False)
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

        with db() as chk_c:
            _check_material_duplicate_or_typo(
                chk_c,
                name,
                brand,
                qty,
                unit,
                exclude_id=material_id,
                confirm_similar=bool(payload.confirm_similar),
            )

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
    except SimilarMaterialWarning as e:
        raise HTTPException(
            status_code=409,
            detail={"code": "SIMILAR_MATERIAL_EXISTS", "message": str(e), "existing": e.existing},
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Não foi possível atualizar o item: {e}")


@router.patch("/api/materials/{material_id}/active")
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


@router.post("/api/materials/delete-check")
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


@router.post("/api/materials/delete-execute")
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

@router.get("/api/materials/{material_id}/history")
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


@router.get("/api/materials/{material_id}/history/export")
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

@router.get("/api/materials/{material_id}/conversions")
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


@router.post("/api/conversions")
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


@router.get("/api/conversions")
def list_all_conversions(search: Optional[str] = None):
    init_db()
    with db() as c:
        query = """
            SELECT cu.id, cu.material_id, m.name as material_name, m.purchase_unit as material_unit,
                   m.brand as material_brand, m.category as material_category, m.code as material_code,
                   m.barcode as material_barcode,
                   cu.name as unit_name, cu.base_unit, cu.factor_to_base
            FROM custom_units cu
            JOIN materials m ON m.id = cu.material_id
            WHERE COALESCE(m.archived, 0) = 0
        """
        params = []
        if search and search.strip():
            s = f"%{search.strip().lower()}%"
            query += " AND (LOWER(m.name) LIKE ? OR LOWER(cu.name) LIKE ?)"
            params.extend([s, s])

        query += " ORDER BY m.name COLLATE NOCASE ASC, cu.name COLLATE NOCASE ASC"
        rows = c.execute(query, params).fetchall()

        items = []
        for r in rows:
            factor = float(r["factor_to_base"])
            items.append({
                "id": r["id"],
                "material_id": r["material_id"],
                "material_name": r["material_name"],
                "material_unit": r["material_unit"],
                "material_brand": r["material_brand"] or "",
                "material_category": r["material_category"] or "",
                "material_code": r["material_code"] or "",
                "material_barcode": r["material_barcode"] or "",
                "unit_name": r["unit_name"],
                "base_unit": r["base_unit"],
                "factor_to_base": factor,
                "factor_fmt": fmt_num(factor),
                "equivalence_fmt": f"1 {r['unit_name']} = {fmt_num(factor)} {r['base_unit']}",
            })
        return {"items": items, "total": len(items)}


@router.put("/api/conversions/{conversion_id}")
def update_conversion(conversion_id: int, payload: UpdateConversionPayload):
    with db() as c:
        row = c.execute("SELECT * FROM custom_units WHERE id=?", (conversion_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Unidade configurável não encontrada.")

        name = normalize_text(payload.name.strip()) if payload.name is not None and payload.name.strip() else row["name"]
        base_unit = payload.base_unit.strip() if payload.base_unit is not None and payload.base_unit.strip() else row["base_unit"]
        factor = to_float(payload.factor_to_base, "Quantidade") if payload.factor_to_base is not None else float(row["factor_to_base"])

        if factor <= 0:
            raise HTTPException(status_code=400, detail="A quantidade deve ser maior que zero.")

        c.execute(
            "UPDATE custom_units SET name=?, base_unit=?, factor_to_base=? WHERE id=?",
            (name, base_unit, factor, conversion_id),
        )
        c.commit()
    return {"ok": True, "message": "Unidade atualizada com sucesso!"}


@router.delete("/api/conversions/{conversion_id}")
def delete_conversion(conversion_id: int):
    with db() as c:
        c.execute("DELETE FROM custom_units WHERE id=?", (conversion_id,))
        c.commit()
    return {"ok": True, "message": "Unidade excluída com sucesso!"}


@router.post("/api/conversions/batch-delete")
def batch_delete_conversions(payload: BatchDeleteConversionsPayload):
    if not payload.ids:
        return {"ok": True, "deleted_count": 0}
    with db() as c:
        placeholders = ",".join("?" for _ in payload.ids)
        c.execute(f"DELETE FROM custom_units WHERE id IN ({placeholders})", payload.ids)
        c.commit()
    return {"ok": True, "deleted_count": len(payload.ids)}
