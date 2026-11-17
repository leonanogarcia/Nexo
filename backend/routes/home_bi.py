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


def _period_cutoff_date(period: str) -> Optional[str]:
    from datetime import timedelta
    days_map = {
        "30d": 30,
        "3m": 90,
        "6m": 180,
        "12m": 365,
    }
    days = days_map.get(period)
    if not days:
        return None
    return (date.today() - timedelta(days=days)).isoformat()


def _get_bi_preferences() -> Dict[str, Any]:
    return {
        "default_period": get_setting("bi_default_period", "12m"),
        "chart_style": get_setting("bi_chart_style", "auto"),
        "cost_variation_alert_pct": float(get_setting("bi_cost_variation_alert_pct", "10") or 10),
        "target_margin_pct": float(get_setting("bi_target_margin_pct", "30") or 30),
        "include_inactive": get_setting("bi_include_inactive", "0") in ("1", "true", "True"),
        "color_palette": get_setting("bi_color_palette", "nexo"),
        "custom_primary_color": get_setting("bi_custom_primary_color", "#F28C28"),
        "custom_secondary_color": get_setting("bi_custom_secondary_color", "#18223A"),
        "brand_color": get_setting("brand_color", "#F28C28"),
    }


@router.get("/api/dashboard")
def get_dashboard(period: Optional[str] = Query(None, description="30d | 3m | 6m | 12m | all")):
    init_db()
    bi_prefs = _get_bi_preferences()
    active_period = period if period in ("30d", "3m", "6m", "12m", "all") else bi_prefs["default_period"]
    cutoff = _period_cutoff_date(active_period)
    include_inactive = bi_prefs["include_inactive"]
    alert_threshold = bi_prefs["cost_variation_alert_pct"]

    active_filter_m = "" if include_inactive else "AND COALESCE(m.active,1)=1 AND COALESCE(m.archived,0)=0"
    active_filter_p = "" if include_inactive else "WHERE COALESCE(active,1)=1 AND COALESCE(archived,0)=0"
    active_filter_r = "" if include_inactive else "WHERE COALESCE(active,1)=1 AND COALESCE(archived,0)=0"

    with db() as c:
        ins_count = int(c.execute("SELECT COUNT(*) FROM materials WHERE COALESCE(active,1)=1 AND COALESCE(archived,0)=0").fetchone()[0])
        rec_count = int(c.execute("SELECT COUNT(*) FROM base_recipes WHERE COALESCE(active,1)=1 AND COALESCE(archived,0)=0").fetchone()[0])
        prod_count = int(c.execute("SELECT COUNT(*) FROM products WHERE COALESCE(active,1)=1 AND COALESCE(archived,0)=0").fetchone()[0])

        prod_rows = c.execute(f"SELECT id, name, sale_price FROM products {active_filter_p} ORDER BY name COLLATE NOCASE").fetchall()
        rec_rows = c.execute(f"SELECT id, name FROM base_recipes {active_filter_r} ORDER BY name COLLATE NOCASE").fetchall()

        prod_costs: List[float] = []
        margins: List[float] = []
        cost_slices_raw: List[Dict[str, Any]] = []
        target_margin = bi_prefs["target_margin_pct"]
        below_target_margin: List[Dict[str, Any]] = []
        profit_candidates: List[Dict[str, Any]] = []
        cost_candidates: List[Dict[str, Any]] = []
        no_price_count = 0

        for pr in prod_rows:
            try:
                uc = float(product_unit_cost(pr["id"]) or 0.0)
                sp = float(pr["sale_price"] or 0.0)
                if uc > 0:
                    prod_costs.append(uc)
                    cost_slices_raw.append({"name": f"Prod: {pr['name']}", "value": round(uc, 2)})
                cost_candidates.append({
                    "id": pr["id"],
                    "name": pr["name"],
                    "unit_cost": round(uc, 2),
                    "unit_cost_fmt": fmt(uc),
                    "sale_price_fmt": fmt(sp) if sp > 0 else "Sem preço",
                })
                if sp > 0 and uc >= 0:
                    profit_val = sp - uc
                    margin_pct = (profit_val / sp) * 100.0
                    margins.append(margin_pct)
                    profit_candidates.append({
                        "id": pr["id"],
                        "name": pr["name"],
                        "profit": round(profit_val, 2),
                        "profit_fmt": fmt(profit_val),
                        "margin_pct": round(margin_pct, 1),
                    })
                    if margin_pct < target_margin:
                        below_target_margin.append({
                            "id": pr["id"],
                            "name": pr["name"],
                            "unit_cost_fmt": fmt(uc),
                            "sale_price_fmt": fmt(sp),
                            "margin_pct": round(margin_pct, 1),
                        })
                else:
                    no_price_count += 1
            except Exception:
                pass

        below_target_margin.sort(key=lambda x: x["margin_pct"])
        profit_ranking = sorted(profit_candidates, key=lambda x: x["profit"], reverse=True)[:3]
        highest_cost_products = sorted(cost_candidates, key=lambda x: x["unit_cost"], reverse=True)[:3]

        unused_mat_count = int(c.execute("""
            SELECT COUNT(*) FROM materials m
            WHERE COALESCE(m.active,1)=1 AND COALESCE(m.archived,0)=0
              AND NOT EXISTS (SELECT 1 FROM base_recipe_items bri WHERE bri.material_id = m.id)
              AND NOT EXISTS (SELECT 1 FROM product_items pi WHERE pi.item_type = 'material' AND pi.ref_id = m.id)
        """).fetchone()[0])

        unused_rec_count = int(c.execute("""
            SELECT COUNT(*) FROM base_recipes r
            WHERE COALESCE(r.active,1)=1 AND COALESCE(r.archived,0)=0
              AND NOT EXISTS (SELECT 1 FROM product_items pi WHERE pi.item_type = 'recipe' AND pi.ref_id = r.id)
        """).fetchone()[0])

        pending_items: List[Dict[str, Any]] = []
        if no_price_count > 0:
            pending_items.append({
                "key": "no_price",
                "label": f"{no_price_count} produto(s) sem preço de venda definido",
                "count": no_price_count,
                "target_tab": "Produtos",
            })
        if unused_mat_count > 0:
            pending_items.append({
                "key": "unused_materials",
                "label": f"{unused_mat_count} insumo(s) ativo(s) sem uso em receitas ou produtos",
                "count": unused_mat_count,
                "target_tab": "Cadastro",
            })
        if unused_rec_count > 0:
            pending_items.append({
                "key": "unused_recipes",
                "label": f"{unused_rec_count} receita(s) ativa(s) ainda não vinculada(s) a nenhum produto",
                "count": unused_rec_count,
                "target_tab": "Receitas",
            })

        for rr in rec_rows:
            try:
                rc = float(recipe_cost(rr["id"]) or 0.0)
                if rc > 0:
                    cost_slices_raw.append({"name": f"Rec: {rr['name']}", "value": round(rc, 2)})
            except Exception:
                pass

        avg_cost = (sum(prod_costs) / len(prod_costs)) if prod_costs else 0.0
        avg_margin = (sum(margins) / len(margins)) if margins else None

        # Purchases by category
        if cutoff:
            cat_rows = c.execute(
                f"""
                SELECT COALESCE(NULLIF(TRIM(m.category), ''), 'Outros') AS category, SUM(pu.value) AS total
                FROM purchases pu
                JOIN materials m ON m.id = pu.material_id
                WHERE date(pu.purchase_date) >= date(?) {active_filter_m}
                GROUP BY category
                ORDER BY total DESC
                """,
                (cutoff,),
            ).fetchall()
        else:
            cat_rows = c.execute(
                f"""
                SELECT COALESCE(NULLIF(TRIM(m.category), ''), 'Outros') AS category, SUM(pu.value) AS total
                FROM purchases pu
                JOIN materials m ON m.id = pu.material_id
                WHERE 1=1 {active_filter_m}
                GROUP BY category
                ORDER BY total DESC
                """
            ).fetchall()

        cat_total = sum(float(r["total"] or 0.0) for r in cat_rows) or 1.0
        purchases_by_category = [
            {
                "category": r["category"],
                "total": round(float(r["total"] or 0.0), 2),
                "total_fmt": fmt(float(r["total"] or 0.0)),
                "pct": round((float(r["total"] or 0.0) / cat_total) * 100.0, 1),
            }
            for r in cat_rows[:4]
        ]

        # Price variations per material
        date_clause = "AND date(pu.purchase_date) >= date(?)" if cutoff else ""
        var_params = (cutoff,) if cutoff else ()
        var_rows = c.execute(
            f"""
            SELECT m.name, MIN(pu.value) AS mn, MAX(pu.value) AS mx
            FROM purchases pu
            JOIN materials m ON m.id = pu.material_id
            WHERE 1=1 {date_clause} {active_filter_m}
            GROUP BY m.id
            HAVING COUNT(pu.id) > 1
            ORDER BY CASE WHEN MIN(pu.value) > 0 THEN (MAX(pu.value) - MIN(pu.value)) / MIN(pu.value) ELSE 0 END DESC
            LIMIT 6
            """,
            var_params,
        ).fetchall()

        price_variations = []
        for r in var_rows:
            mn = float(r["mn"] or 0.0)
            mx = float(r["mx"] or 0.0)
            pct = ((mx - mn) / mn * 100.0) if mn > 0 else 0.0
            price_variations.append({
                "name": r["name"],
                "min_fmt": fmt(mn),
                "max_fmt": fmt(mx),
                "pct": round(pct, 1),
                "is_alert": abs(pct) >= alert_threshold,
            })

        # Recent purchases
        recent_rows = c.execute(
            f"""
            SELECT pu.id, pu.purchase_date, m.name AS material_name, COALESCE(pu.brand, '') AS brand, pu.value
            FROM purchases pu
            JOIN materials m ON m.id = pu.material_id
            WHERE 1=1 {active_filter_m}
            ORDER BY pu.purchase_date DESC, pu.id DESC
            LIMIT 5
            """
        ).fetchall()
        recent_purchases = [
            {
                "id": r["id"],
                "date": str(r["purchase_date"]),
                "description": r["material_name"] + (f" - {r['brand']}" if r["brand"] else ""),
                "type": "Compra",
                "value": float(r["value"] or 0.0),
                "value_fmt": fmt(float(r["value"] or 0.0)),
            }
            for r in recent_rows
        ]

        # Purchase pie slices (distribution by material)
        pie_rows = c.execute(
            f"""
            SELECT m.name, SUM(pu.value) AS total
            FROM purchases pu
            JOIN materials m ON m.id = pu.material_id
            WHERE 1=1 {date_clause} {active_filter_m}
            GROUP BY m.id
            ORDER BY total DESC
            """,
            var_params,
        ).fetchall()
        purchase_slices_raw = [
            {"name": r["name"], "value": round(float(r["total"] or 0.0), 2)}
            for r in pie_rows
            if float(r["total"] or 0.0) > 0
        ]

        # Cost evolution series
        ch_date_clause = "WHERE date(recorded_at) >= date(?)" if cutoff else ""
        ch_params = (cutoff,) if cutoff else ()
        hist_rows = c.execute(
            f"""
            SELECT substr(recorded_at, 1, 7) AS mes, AVG(cost) AS avg_cost
            FROM cost_history
            {ch_date_clause}
            GROUP BY mes
            ORDER BY mes ASC
            """,
            ch_params,
        ).fetchall()

        if hist_rows:
            cost_series = [{"month": r["mes"], "avg_cost": round(float(r["avg_cost"] or 0.0), 2)} for r in hist_rows[-12:]]
        else:
            all_curr = [x["value"] for x in cost_slices_raw]
            cost_series = (
                [{"month": date.today().strftime("%Y-%m"), "avg_cost": round(sum(all_curr) / len(all_curr), 2)}]
                if all_curr
                else []
            )

    def _top_4_with_others(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        sorted_items = sorted(items, key=lambda x: x["value"], reverse=True)
        top = sorted_items[:4]
        rest = sum(x["value"] for x in sorted_items[4:])
        if rest > 0:
            top.append({"name": "Outros", "value": round(rest, 2)})
        total_v = sum(x["value"] for x in top) or 1.0
        for x in top:
            x["value_fmt"] = fmt(x["value"])
            x["pct"] = round((x["value"] / total_v) * 100.0, 1)
        return top

    return {
        "period": active_period,
        "bi_preferences": bi_prefs,
        "kpis": {
            "products": prod_count,
            "recipes": rec_count,
            "materials": ins_count,
        },
        "avg_product_cost": round(avg_cost, 2),
        "avg_product_cost_fmt": fmt(avg_cost),
        "avg_margin_pct": round(avg_margin, 1) if avg_margin is not None else None,
        "purchases_by_category": purchases_by_category,
        "price_variations": price_variations,
        "recent_purchases": recent_purchases,
        "purchase_pie_slices": _top_4_with_others(purchase_slices_raw),
        "cost_pie_slices": _top_4_with_others(cost_slices_raw),
        "cost_evolution_series": cost_series,
        "below_target_margin": below_target_margin,
        "profit_ranking": profit_ranking,
        "highest_cost_products": highest_cost_products,
        "pending_items": pending_items,
    }


@router.get("/api/bi/details")
def get_bi_details(
    period: Optional[str] = Query(None, description="30d | 3m | 6m | 12m | all"),
):
    init_db()
    bi_prefs = _get_bi_preferences()
    active_period = period if period in ("30d", "3m", "6m", "12m", "all") else bi_prefs["default_period"]
    cutoff = _period_cutoff_date(active_period)
    include_inactive = bi_prefs["include_inactive"]
    active_filter_m = "" if include_inactive else "AND COALESCE(m.active,1)=1 AND COALESCE(m.archived,0)=0"

    date_clause = "AND date(pu.purchase_date) >= date(?)" if cutoff else ""
    params = (cutoff,) if cutoff else ()

    with db() as c:
        r_ins = c.execute(
            f"""
            SELECT m.id AS mat_id, m.name, substr(pu.purchase_date, 1, 7) AS mes,
                   MIN(pu.value) AS mn, MAX(pu.value) AS mx, AVG(pu.value) AS av
            FROM purchases pu
            JOIN materials m ON m.id = pu.material_id
            WHERE 1=1 {date_clause} {active_filter_m}
            GROUP BY m.id, mes
            ORDER BY mes DESC, m.name COLLATE NOCASE ASC
            """,
            params,
        ).fetchall()

        rows_insumo = []
        for idx, r in enumerate(r_ins):
            mn = float(r["mn"] or 0.0)
            mx = float(r["mx"] or 0.0)
            av = float(r["av"] or 0.0)
            var_pct = ((mx - mn) / mn * 100.0) if mn > 0 else 0.0
            rows_insumo.append({
                "id": f"ins_{r['mat_id']}_{r['mes']}_{idx}",
                "item": r["name"],
                "mes": r["mes"],
                "min": round(mn, 2),
                "min_fmt": fmt(mn),
                "max": round(mx, 2),
                "max_fmt": fmt(mx),
                "media": round(av, 2),
                "media_fmt": fmt(av),
                "variacao_pct": round(var_pct, 1),
            })

        r_br = c.execute(
            f"""
            SELECT m.id AS mat_id, m.name, COALESCE(NULLIF(TRIM(pu.brand), ''), '—') AS brand_label,
                   substr(pu.purchase_date, 1, 7) AS mes,
                   MIN(pu.value) AS mn, MAX(pu.value) AS mx, AVG(pu.value) AS av
            FROM purchases pu
            JOIN materials m ON m.id = pu.material_id
            WHERE 1=1 {date_clause} {active_filter_m}
            GROUP BY m.id, brand_label, mes
            ORDER BY mes DESC, m.name COLLATE NOCASE ASC, brand_label COLLATE NOCASE ASC
            """,
            params,
        ).fetchall()

        rows_marca = [
            {
                "id": f"br_{r['mat_id']}_{idx}",
                "item": r["name"],
                "marca": r["brand_label"],
                "mes": r["mes"],
                "min": round(float(r["mn"] or 0.0), 2),
                "min_fmt": fmt(float(r["mn"] or 0.0)),
                "max": round(float(r["mx"] or 0.0), 2),
                "max_fmt": fmt(float(r["mx"] or 0.0)),
                "media": round(float(r["av"] or 0.0), 2),
                "media_fmt": fmt(float(r["av"] or 0.0)),
            }
            for idx, r in enumerate(r_br)
        ]

        ch_date_clause = "WHERE date(ch.recorded_at) >= date(?)" if cutoff else ""
        r_ch = c.execute(
            f"""
            SELECT ch.id, ch.entity_type, ch.entity_id, ch.cost, substr(ch.recorded_at, 1, 7) AS mes
            FROM cost_history ch
            {ch_date_clause}
            ORDER BY ch.recorded_at DESC, ch.id DESC
            """,
            params,
        ).fetchall()

        rows_custos = []
        for r in r_ch:
            tbl = "base_recipes" if r["entity_type"] == "RECIPE_BASE" else "products"
            nm = c.execute(f"SELECT name FROM {tbl} WHERE id = ?", (r["entity_id"],)).fetchone()
            cost_val = float(r["cost"] or 0.0)
            rows_custos.append({
                "id": f"ch_{r['id']}",
                "tipo": "Receita" if r["entity_type"] == "RECIPE_BASE" else "Produto",
                "item": nm["name"] if nm else f"ID {r['entity_id']}",
                "mes": r["mes"],
                "custo": round(cost_val, 2),
                "custo_fmt": fmt(cost_val),
            })

        if not rows_custos:
            mes_now = date.today().strftime("%Y-%m")
            rec_sql = "SELECT id, name FROM base_recipes" if include_inactive else "SELECT id, name FROM base_recipes WHERE COALESCE(active,1)=1 AND COALESCE(archived,0)=0"
            prod_sql = "SELECT id, name FROM products" if include_inactive else "SELECT id, name FROM products WHERE COALESCE(active,1)=1 AND COALESCE(archived,0)=0"
            for r in c.execute(rec_sql).fetchall():
                try:
                    rc = float(recipe_cost(r["id"]) or 0.0)
                    rows_custos.append({"id": f"rec_{r['id']}", "tipo": "Receita", "item": r["name"], "mes": mes_now, "custo": round(rc, 2), "custo_fmt": fmt(rc)})
                except Exception:
                    pass
            for r in c.execute(prod_sql).fetchall():
                try:
                    pc = float(product_unit_cost(r["id"]) or 0.0)
                    rows_custos.append({"id": f"prod_{r['id']}", "tipo": "Produto", "item": r["name"], "mes": mes_now, "custo": round(pc, 2), "custo_fmt": fmt(pc)})
                except Exception:
                    pass

    months = sorted(
        {r["mes"] for r in rows_insumo if r.get("mes")}
        | {r["mes"] for r in rows_marca if r.get("mes")}
        | {r["mes"] for r in rows_custos if r.get("mes")},
        reverse=True,
    )

    return {
        "period": active_period,
        "bi_preferences": bi_prefs,
        "months": months,
        "insumo": rows_insumo,
        "marca": rows_marca,
        "custos": rows_custos,
    }
