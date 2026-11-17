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
    cooking_appliance: Optional[str] = "none"
    cooking_time_minutes: Optional[Any] = 0.0
    batch_yield_units: Optional[Any] = 1.0
    notes: Optional[str] = ""
    items: List[ProductItemPayload] = []

class ProductPreviewPayload(BaseModel):
    items: List[ProductItemPayload] = []
    sale_price: Optional[Any] = "0"
    cooking_appliance: Optional[str] = "none"
    cooking_time_minutes: Optional[Any] = 0.0
    batch_yield_units: Optional[Any] = 1.0


@router.get("/api/products/composition-options")
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


@router.get("/api/products")
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
        mat_cache = {
            m["id"]: m
            for m in c.execute(
                "SELECT id, name, brand, purchase_unit, COALESCE(active, 1) as active, COALESCE(archived, 0) as archived FROM materials"
            ).fetchall()
        }
        rec_cache = {
            r["id"]: r
            for r in c.execute(
                "SELECT id, name, yield_unit, COALESCE(active, 1) as active, COALESCE(archived, 0) as archived FROM base_recipes"
            ).fetchall()
        }
        prod_cache = {
            p["id"]: p
            for p in c.execute(
                "SELECT id, name, weight_unit, COALESCE(active, 1) as active, COALESCE(archived, 0) as archived FROM products"
            ).fetchall()
        }

        result = []
        for p in rows:
            pid = p["id"]
            try:
                direct_cost = product_direct_cost(pid)
            except Exception:
                direct_cost = 0.0
            
            try:
                op_cost = product_operational_cost(pid)
            except Exception:
                op_cost = 0.0

            tot_cost = direct_cost + op_cost
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
                ref_obj = None
                if itype == "MATERIAL":
                    ref_obj = mat_cache.get(ref_id)
                    ref_name = ref_obj["name"] if ref_obj else f"Insumo #{ref_id}"
                elif itype == "RECIPE_BASE":
                    ref_obj = rec_cache.get(ref_id)
                    ref_name = ref_obj["name"] if ref_obj else f"Receita #{ref_id}"
                elif itype == "PRODUCT":
                    ref_obj = prod_cache.get(ref_id)
                    ref_name = ref_obj["name"] if ref_obj else f"Produto #{ref_id}"

                is_broken = (ref_obj is None) or (int(ref_obj["active"] or 0) == 0) or (int(ref_obj["archived"] or 0) == 1)
                
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
                    "broken": is_broken,
                })

            w_qty = float(p["weight_qty"] or 1.0)
            w_unit = p["weight_unit"] or "un"
            c_app = p["cooking_appliance"] if "cooking_appliance" in p.keys() and p["cooking_appliance"] else "none"
            c_time = float(p["cooking_time_minutes"] or 0.0) if "cooking_time_minutes" in p.keys() else 0.0
            b_yield = float(p["batch_yield_units"] or 1.0) if "batch_yield_units" in p.keys() else 1.0

            result.append({
                "id": pid,
                "code": p["code"] or f"PROD_{pid:04d}",
                "name": p["name"],
                "weight_qty": w_qty,
                "weight_qty_fmt": fmt_num(w_qty),
                "weight_unit": w_unit,
                "cooking_appliance": c_app,
                "cooking_time_minutes": c_time,
                "batch_yield_units": b_yield,
                "direct_cost": float(direct_cost),
                "direct_cost_fmt": fmt(direct_cost),
                "operational_cost": float(op_cost),
                "operational_cost_fmt": fmt(op_cost),
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
                "has_broken_items": any(x["broken"] for x in comp_list),
                "items": comp_list,
            })

    if search:
        s = search.strip().lower()
        result = [r for r in result if s in r["name"].lower() or s in (r["code"] or "").lower()]

    return {"items": result, "total": len(result)}


@router.get("/api/products/{product_id}")
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
            op_cost = product_operational_cost(product_id)
        except Exception:
            op_cost = 0.0

        tot_cost = direct_cost + op_cost
        sp = float(p["sale_price"] or 0.0)
        profit_val = sp - tot_cost
        margin_pct = (profit_val / sp * 100.0) if sp > 0 else 0.0
        try:
            op_breakdown = product_operational_breakdown(product_id)
        except Exception:
            op_breakdown = {
                "items": [],
                "total_cost": float(op_cost),
                "total_cost_fmt": fmt(op_cost),
            }

        return {
            "id": p["id"],
            "code": p["code"],
            "name": p["name"],
            "weight_qty": p["weight_qty"],
            "weight_unit": p["weight_unit"],
            "cooking_appliance": p["cooking_appliance"] if "cooking_appliance" in p.keys() and p["cooking_appliance"] else "none",
            "cooking_time_minutes": float(p["cooking_time_minutes"] or 0.0) if "cooking_time_minutes" in p.keys() else 0.0,
            "batch_yield_units": float(p["batch_yield_units"] or 1.0) if "batch_yield_units" in p.keys() else 1.0,
            "sale_price": sp,
            "sale_price_fmt": fmt(sp),
            "direct_cost": float(direct_cost),
            "direct_cost_fmt": fmt(direct_cost),
            "operational_cost": float(op_cost),
            "operational_cost_fmt": fmt(op_cost),
            "operational_breakdown": op_breakdown,
            "production_cost": float(tot_cost),
            "production_cost_fmt": fmt(tot_cost),
            "profit_val": float(profit_val),
            "profit_val_fmt": fmt(profit_val),
            "profit_margin_pct": round(margin_pct, 1),
            "notes": p["notes"] or "",
            "active": bool(p["active"]),
            "items": items_out,
        }


def _validate_product_items(c, items: List[ProductItemPayload]) -> None:
    if not items:
        raise HTTPException(status_code=400, detail="Adicione ao menos um componente válido ao produto.")
    table_map = {
        "MATERIAL": "materials",
        "RECIPE_BASE": "base_recipes",
        "PRODUCT": "products",
    }
    for it in items:
        rid = int(getattr(it, "ref_id", 0) or 0)
        itype = it.item_type if it.item_type in table_map else "MATERIAL"
        if rid <= 0:
            raise HTTPException(
                status_code=400,
                detail="Há componente(s) sem vínculo válido. Vincule, crie ou remova os itens pendentes antes de salvar.",
            )
        tbl = table_map[itype]
        row = c.execute(
            f"SELECT id FROM {tbl} WHERE id=? AND COALESCE(active, 1)=1 AND COALESCE(archived, 0)=0",
            (rid,),
        ).fetchone()
        if not row:
            raise HTTPException(
                status_code=400,
                detail=f"Componente ID {rid} ({itype}) não encontrado, inativo ou arquivado. Substitua por um item ativo antes de salvar.",
            )


@router.post("/api/products")
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

        _validate_product_items(c, payload.items)

        code = next_code("products", "PROD")
        c_app = str(payload.cooking_appliance or "none").strip()
        try:
            c_time = float(str(payload.cooking_time_minutes or 0.0).replace(",", "."))
        except Exception:
            c_time = 0.0
        try:
            b_yield = max(1.0, float(str(payload.batch_yield_units or 1.0).replace(",", ".")))
        except Exception:
            b_yield = 1.0

        cur = c.execute(
            """
            INSERT INTO products(code, name, weight_qty, weight_unit, sale_price, notes, cooking_appliance, cooking_time_minutes, batch_yield_units, created_at, updated_at, active, archived)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 0)
            """,
            (code, name, weight_qty, weight_unit, sale_price, notes, c_app, c_time, b_yield, now_val, now_val),
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


@router.put("/api/products/{product_id}")
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

        _validate_product_items(c, payload.items)

        c_app = str(payload.cooking_appliance or "none").strip()
        try:
            c_time = float(str(payload.cooking_time_minutes or 0.0).replace(",", "."))
        except Exception:
            c_time = 0.0
        try:
            b_yield = max(1.0, float(str(payload.batch_yield_units or 1.0).replace(",", ".")))
        except Exception:
            b_yield = 1.0

        c.execute(
            """
            UPDATE products
            SET name=?, weight_qty=?, weight_unit=?, sale_price=?, notes=?, cooking_appliance=?, cooking_time_minutes=?, batch_yield_units=?, updated_at=?
            WHERE id=?
            """,
            (name, weight_qty, weight_unit, sale_price, notes, c_app, c_time, b_yield, now_val, product_id),
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


@router.post("/api/products/{product_id}/toggle-status")
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


@router.post("/api/products/{product_id}/duplicate")
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


@router.post("/api/products/check-delete")
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


@router.post("/api/products/batch-delete")
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


@router.post("/api/products/preview-cost")
def preview_product_cost(payload: ProductPreviewPayload):
    direct_total = 0.0
    op_total = 0.0
    tot_gas = 0.0
    tot_energy = 0.0
    tot_water = 0.0
    items_out = []

    for it in payload.items:
        itype = it.item_type if it.item_type in ("MATERIAL", "RECIPE_BASE", "PRODUCT") else "MATERIAL"
        ref_id = it.ref_id
        try:
            q = to_float(it.qty_per_unit, "Quantidade")
        except Exception:
            q = 0.0

        d_cost = 0.0
        o_cost = 0.0
        if ref_id > 0 and q > 0 and it.unit:
            try:
                d_cost = item_direct_cost(itype, ref_id, q, it.unit)
                o_cost = item_operational_cost(itype, ref_id, q, it.unit)
            except Exception:
                try:
                    d_cost = item_cost(itype, ref_id, q, it.unit)
                except Exception:
                    d_cost = 0.0
                o_cost = 0.0

            if itype == "RECIPE_BASE":
                try:
                    with db() as c:
                        rec = c.execute("SELECT yield_qty, yield_unit FROM base_recipes WHERE id=?", (ref_id,)).fetchone()
                    if rec and rec["yield_qty"] and rec["yield_qty"] > 0:
                        conv_q = convert_generic(q, it.unit, rec["yield_unit"])
                        factor = conv_q / rec["yield_qty"]
                        rb = recipe_operational_breakdown(ref_id)
                        tot_gas += rb["gas"] * factor
                        tot_energy += rb["energy"] * factor
                        tot_water += rb["water"] * factor
                except Exception:
                    pass

        c_val = d_cost + o_cost
        direct_total += d_cost
        op_total += o_cost
        items_out.append({
            "item_type": itype,
            "ref_id": ref_id,
            "qty": q,
            "unit": it.unit,
            "cost": float(c_val),
            "cost_fmt": fmt(c_val),
            "direct_cost": float(d_cost),
            "operational_cost": float(o_cost),
        })

    tot_cost = direct_total + op_total

    op_items = [
        {
            "id": 1,
            "name": "Gás",
            "cost": round(tot_gas, 4),
            "cost_fmt": fmt(tot_gas),
            "rate_label": "Herdado das receitas" if tot_gas > 0.0001 else "Sem cocção a gás",
        },
        {
            "id": 2,
            "name": "Energia",
            "cost": round(tot_energy, 4),
            "cost_fmt": fmt(tot_energy),
            "rate_label": "Equipamentos / Ativação" if tot_energy > 0.0001 else "Sem cocção elétrica",
        },
        {
            "id": 3,
            "name": "Água",
            "cost": round(tot_water, 4),
            "cost_fmt": fmt(tot_water),
            "rate_label": "Rateio da cozinha" if tot_water > 0.0001 else "Rateio cozinha",
        },
    ]

    op_breakdown = {
        "items": op_items,
        "total_cost": round(op_total, 4),
        "total_cost_fmt": fmt(op_total),
    }

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
        "operational_cost": float(op_total),
        "operational_cost_fmt": fmt(op_total),
        "operational_breakdown": op_breakdown,
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


@router.get("/api/products/{product_id}/history")
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
