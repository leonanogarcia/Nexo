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


@router.get("/api/recipes")
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

        mats = {
            m["id"]: m
            for m in c.execute(
                "SELECT id, name, brand, purchase_unit, COALESCE(active, 1) as active, COALESCE(archived, 0) as archived FROM materials"
            ).fetchall()
        }
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
                is_broken = (mat is None) or (int(mat["active"] or 0) == 0) or (int(mat["archived"] or 0) == 1)
                
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
                    "broken": is_broken,
                })

            is_active = bool(r["active"] if r["active"] is not None else 1)
            created = r["created_at"] or ""
            c_date = created[:10] if created else ""
            if len(c_date) == 10 and "-" in c_date:
                y, m, d = c_date.split("-")
                c_date = f"{d}/{m}/{y}"

            c_app = r["cooking_appliance"] if "cooking_appliance" in r.keys() and r["cooking_appliance"] else "none"
            c_time = float(r["cooking_time_minutes"] or 0.0) if "cooking_time_minutes" in r.keys() else 0.0

            result.append({
                "id": rid,
                "code": r["code"] or "",
                "name": r["name"],
                "yield_qty": y_qty,
                "yield_qty_fmt": fmt_num(y_qty) if y_qty > 0 else "",
                "yield_unit": y_unit,
                "cooking_appliance": c_app,
                "cooking_time_minutes": c_time,
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
                "has_broken_items": any(x["broken"] for x in formatted_items),
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


@router.get("/api/recipes/{recipe_id}")
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

    c_app = r["cooking_appliance"] if "cooking_appliance" in r.keys() and r["cooking_appliance"] else "none"
    c_time = float(r["cooking_time_minutes"] or 0.0) if "cooking_time_minutes" in r.keys() else 0.0
    mat_cost = sum(it["cost"] for it in formatted_items)
    op_breakdown = calculate_product_operational_breakdown(mat_cost, c_app, c_time, batch_yield_units=1.0)
    op_cost = op_breakdown["total_cost"] if op_breakdown.get("is_precise") else 0.0

    return {
        "id": r["id"],
        "code": r["code"] or "",
        "name": r["name"],
        "yield_qty": y_qty,
        "yield_qty_fmt": fmt_num(y_qty) if y_qty > 0 else "",
        "yield_unit": r["yield_unit"] or "",
        "cooking_appliance": c_app,
        "cooking_time_minutes": c_time,
        "notes": r["notes"] or "",
        "active": bool(r["active"] if r["active"] is not None else 1),
        "materials_cost": float(mat_cost),
        "materials_cost_fmt": fmt(mat_cost),
        "operational_cost": float(op_cost),
        "operational_cost_fmt": fmt(op_cost),
        "operational_breakdown": op_breakdown,
        "total_cost": float(tot_cost),
        "total_cost_fmt": fmt(tot_cost),
        "portion_cost": float(portion_cost),
        "portion_cost_fmt": fmt(portion_cost),
        "items": formatted_items,
    }


def _validate_recipe_items(c, items: List[RecipeItemPayload]) -> None:
    if not items:
        raise HTTPException(status_code=400, detail="Adicione ao menos um ingrediente válido à receita.")
    for it in items:
        mid = int(getattr(it, "material_id", 0) or 0)
        if mid <= 0:
            raise HTTPException(
                status_code=400,
                detail="Há ingrediente(s) sem vínculo válido. Vincule, crie ou remova os itens pendentes antes de salvar.",
            )
        row = c.execute(
            "SELECT id FROM materials WHERE id=? AND COALESCE(active, 1)=1 AND COALESCE(archived, 0)=0",
            (mid,),
        ).fetchone()
        if not row:
            raise HTTPException(
                status_code=400,
                detail=f"Insumo ID {mid} não encontrado, inativo ou arquivado. Substitua por um insumo ativo antes de salvar.",
            )


@router.post("/api/recipes")
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

        _validate_recipe_items(c, payload.items)

        code = next_code("base_recipes", "RB")
        c_app = str(payload.cooking_appliance or "none").strip()
        try:
            c_time = float(str(payload.cooking_time_minutes or 0.0).replace(",", "."))
        except Exception:
            c_time = 0.0

        cur = c.execute(
            """
            INSERT INTO base_recipes(code, name, yield_qty, yield_unit, notes, cooking_appliance, cooking_time_minutes, created_at, updated_at, active, archived)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 0)
            """,
            (code, name, yield_qty, yield_unit, notes, c_app, c_time, now_val, now_val),
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


@router.put("/api/recipes/{recipe_id}")
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

        _validate_recipe_items(c, payload.items)

        c_app = str(payload.cooking_appliance or "none").strip()
        try:
            c_time = float(str(payload.cooking_time_minutes or 0.0).replace(",", "."))
        except Exception:
            c_time = 0.0

        c.execute(
            """
            UPDATE base_recipes
            SET name=?, yield_qty=?, yield_unit=?, notes=?, cooking_appliance=?, cooking_time_minutes=?, updated_at=?
            WHERE id=?
            """,
            (name, yield_qty, yield_unit, notes, c_app, c_time, now_val, recipe_id),
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


@router.patch("/api/recipes/{recipe_id}/active")
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


@router.post("/api/recipes/delete-check")
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


@router.post("/api/recipes/delete-execute")
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


@router.post("/api/recipes/{recipe_id}/duplicate")
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


@router.get("/api/recipes/{recipe_id}/history")
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
    cooking_appliance: Optional[str] = "none"
    cooking_time_minutes: Optional[Any] = 0.0
    items: List[RecipeItemPayload] = []


@router.post("/api/recipes/preview-cost")
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

    c_app = payload.cooking_appliance or "none"
    c_time = float(payload.cooking_time_minutes or 0.0)
    op_breakdown = calculate_product_operational_breakdown(total, c_app, c_time, batch_yield_units=1.0)
    op_cost = op_breakdown["total_cost"] if op_breakdown.get("is_precise") else 0.0
    final_total = total + op_cost
    portion = (final_total / y_qty) if y_qty > 0 else 0.0

    return {
        "materials_cost": float(total),
        "materials_cost_fmt": fmt(total),
        "operational_cost": float(op_cost),
        "operational_cost_fmt": fmt(op_cost),
        "operational_breakdown": op_breakdown,
        "total_cost": float(final_total),
        "total_cost_fmt": fmt(final_total),
        "portion_cost": float(portion),
        "portion_cost_fmt": fmt(portion),
        "items": items_out,
    }
