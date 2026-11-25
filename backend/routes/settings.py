import ast
import csv
import io
import json
import math
import platform
import shutil
import sqlite3
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import unquote

from fastapi import APIRouter, HTTPException, Query, Request
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


DEFAULT_SALES_CHANNELS = [
    {"id": "balcao", "name": "Balcão / Pix", "fee_pct": 0.0, "fixed_fee": 0.0},
    {"id": "debito", "name": "Cartão Débito", "fee_pct": 1.9, "fixed_fee": 0.0},
    {"id": "credito", "name": "Cartão Crédito", "fee_pct": 4.5, "fixed_fee": 0.0},
    {"id": "ifood", "name": "iFood", "fee_pct": 23.0, "fixed_fee": 0.0},
]


def _load_sales_channels() -> List[Dict[str, Any]]:
    raw = get_setting("sales_channels_json", "")
    if not raw:
        return [dict(c) for c in DEFAULT_SALES_CHANNELS]
    try:
        parsed = json.loads(raw)
        if not isinstance(parsed, list):
            return [dict(c) for c in DEFAULT_SALES_CHANNELS]
        cleaned: List[Dict[str, Any]] = []
        for idx, item in enumerate(parsed):
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()
            if not name:
                continue
            fee_pct = max(0.0, min(98.9, float(item.get("fee_pct") or 0.0)))
            fixed_fee = max(0.0, float(item.get("fixed_fee") or 0.0))
            cid = str(item.get("id") or f"ch_{idx + 1}").strip() or f"ch_{idx + 1}"
            cleaned.append({
                "id": cid,
                "name": name,
                "fee_pct": round(fee_pct, 2),
                "fixed_fee": round(fixed_fee, 2),
            })
        return cleaned if cleaned else [dict(c) for c in DEFAULT_SALES_CHANNELS]
    except Exception:
        return [dict(c) for c in DEFAULT_SALES_CHANNELS]


@router.get("/api/status")
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

    import sys

    health = get_database_health(db_file)

    return {
        "connected": connected,
        "db_name": db_file.name,
        "db_path": str(db_file),
        "db_health": {
            "health_status": health["health_status"],
            "health_label": health["health_label"],
            "size_fmt": health["size_fmt"],
            "health_reasons": health["health_reasons"],
        },
        "theme": theme,
        "company_name": company_name,
        "units": list(UNITS),
        "mat_hidden_cols": mat_hidden_cols,
        "rec_hidden_cols": rec_hidden_cols,
        "prod_hidden_cols": prod_hidden_cols,
        "ai_enabled": get_setting("ai_enabled", "0") in ("1", "true", "True"),
        "language": get_setting("language", "pt-BR"),
        "currency": get_setting("currency", "BRL"),
        "date_format": get_setting("date_format", "DD/MM/YYYY"),
        "time_format": get_setting("time_format", "24h"),
        "is_packaged": bool(getattr(sys, "frozen", False)),
        "version": "v2.1.3",
    }


# ---------- Settings Models & Endpoints (Etapa 3) ----------

class CompanyPayload(BaseModel):
    name: str
    logo: Optional[str] = ""
    brand_theme_enabled: Optional[bool] = False
    brand_color: Optional[str] = "#F28C28"
    apply_brand_to_sidebar: Optional[bool] = True
    apply_brand_to_buttons: Optional[bool] = True
    show_company_name: Optional[bool] = True
    logo_shape: Optional[str] = "round" 

class OperationalCostItemPayload(BaseModel):
    id: Optional[int] = None
    name: str
    percentage: Optional[Any] = 0.0
    cost_type: Optional[str] = "PERCENT"
    fixed_value: Optional[Any] = 0.0

class OperationalCostsPayload(BaseModel):
    costs: List[OperationalCostItemPayload]

class KitchenSettingsPayload(BaseModel):
    kitchen_days_month: Optional[Any] = "26"
    kitchen_hours_day: Optional[Any] = "8"
    gas_supply_type: Optional[str] = "cylinder_13"
    gas_price: Optional[Any] = "125.00"
    electricity_bill_monthly: Optional[Any] = "350.00"
    water_bill_monthly: Optional[Any] = "80.00" 


@router.get("/api/settings")
def get_all_settings():
    init_db()
    db_file = paths.get_db_path()
    theme = get_setting("theme", "light")
    company_name = get_setting("company_name", "Nexo")
    company_logo = get_setting("company_logo", "")
    brand_theme_enabled = get_setting("brand_theme_enabled", "0") in ("1", "true", "True")
    brand_color = get_setting("brand_color", "#F28C28")
    apply_brand_to_sidebar = get_setting("apply_brand_to_sidebar", "1") in ("1", "true", "True")
    apply_brand_to_buttons = get_setting("apply_brand_to_buttons", "1") in ("1", "true", "True")
    show_company_name = get_setting("show_company_name", "1") in ("1", "true", "True")
    logo_shape = get_setting("logo_shape", "round")
    
    cost_detailed = get_cost_settings_detailed()
    cost_list = [
        {
            "id": r["id"],
            "name": r["name"],
            "cost_type": r["cost_type"],
            "percentage": float(r["percentage"] or 0.0),
            "fixed_value": float(r["fixed_value"] or 0.0),
            "rate_label": (f"R$ {float(r['fixed_value'] or 0.0):.2f}".replace(".", ",") if r["cost_type"] == "FIXED" else f"{float(r['percentage'] or 0.0):.1f}%".replace(".", ",")),
        }
        for r in cost_detailed
    ]
    total_pct = sum(r["percentage"] for r in cost_list if r["cost_type"] == "PERCENT")
    total_fixed = sum(r["fixed_value"] for r in cost_list if r["cost_type"] == "FIXED")

    # DB Size & Health
    health = get_database_health(db_file)

    return {
        "theme": theme,
        "company_name": company_name,
        "company_logo": company_logo,
        "brand_theme_enabled": brand_theme_enabled,
        "brand_color": brand_color,
        "apply_brand_to_sidebar": apply_brand_to_sidebar,
        "apply_brand_to_buttons": apply_brand_to_buttons,
        "show_company_name": show_company_name,
        "logo_shape": logo_shape,
        "regional": {
            "language": get_setting("language", "pt-BR"),
            "currency": get_setting("currency", "BRL"),
            "date_format": get_setting("date_format", "DD/MM/YYYY"),
            "time_format": get_setting("time_format", "24h"),
        },
        "cost_settings": cost_list,
        "total_operational_percentage": round(total_pct, 1),
        "total_operational_fixed": round(total_fixed, 2),
        "total_operational_fixed_fmt": f"R$ {total_fixed:.2f}".replace(".", ","),
        "kitchen": {
            "days_month": get_setting("kitchen_days_month", "26"),
            "hours_day": get_setting("kitchen_hours_day", "8"),
            "gas_supply_type": get_setting("gas_supply_type", "cylinder_13"),
            "gas_price": float(get_setting("gas_price", "125.00") or 125.0),
            "electricity_bill_monthly": float(get_setting("electricity_bill_monthly", "350.00") or 350.0),
            "water_bill_monthly": float(get_setting("water_bill_monthly", "80.00") or 80.0),
            "rates": get_kitchen_rates(),
            "presets": list(EQUIPMENT_PRESETS.values()),
        },
        "units": {
            "mass": ["mg", "g", "kg", "t"],
            "volume": ["ml", "L", "kL"],
            "count": ["un"],
        },
        "database": {
            "name": db_file.name,
            "path": str(db_file),
            "connected": True,
            **health,
        },
        "bi": {
            "default_period": get_setting("bi_default_period", "12m"),
            "chart_style": get_setting("bi_chart_style", "auto"),
            "cost_variation_alert_pct": float(get_setting("bi_cost_variation_alert_pct", "10") or 10),
            "target_margin_pct": float(get_setting("bi_target_margin_pct", "30") or 30),
            "include_inactive": get_setting("bi_include_inactive", "0") in ("1", "true", "True"),
            "color_palette": get_setting("bi_color_palette", "nexo"),
            "custom_primary_color": get_setting("bi_custom_primary_color", "#F28C28"),
            "custom_secondary_color": get_setting("bi_custom_secondary_color", "#18223A"),
        },
        "ai": (
            {
                "enabled": True,
                "provider": get_setting("ai_provider", "Google Gemini"),
                "api_key": get_setting("ai_api_key", ""),
                "daily_limit": get_setting("ai_daily_limit", "50"),
                "base_url": get_setting("ai_base_url", ""),
                "model": get_setting("ai_model", ""),
            }
            if get_setting("ai_enabled", "0") in ("1", "true", "True")
            else {
                "enabled": False,
                "provider": "Google Gemini",
                "api_key": "",
                "daily_limit": "50",
                "base_url": "",
                "model": "",
            }
        ),
        "sales_channels": {
            "enabled": get_setting("sales_channels_enabled", "0") in ("1", "true", "True"),
            "channels": _load_sales_channels(),
        },
        "about": {
            "app_name": "Nexo",
            "version": "2.1.3",
            "release_date": "21/11/2026",
            "edition": "Local (SQLite)",
            "os_info": f"{platform.system()} {platform.release()}",
            "python_version": platform.python_version(),
            "highlights": [
                "Aba Início (Dashboard + BI): 3 KPIs clicáveis, gráfico de Custo dos Produtos, Compras por categoria e Variação de preços.",
                "Inteligência de Precificação: Produtos abaixo da meta de margem, Ranking de Lucro & Custo e Pendências do Cadastro.",
                "Modal de BI Detalhado (Insumo, Marca e Custos) com filtro de mês, exportação CSV e Padrão Único de Tabelas.",
                "Indicador de saúde do banco (Verde/Amarelo/Vermelho) no rodapé global e suporte universal a IA (Gemini, OpenAI, OpenRouter e Compatível OpenAI).",
                "Padrão Único de Tabelas, Relatórios completos (PDF/Excel/CSV/XML) e Aba Sobre.",
            ],
        },
    }


class RegionalSettingsPayload(BaseModel):
    language: Optional[str] = "pt-BR"
    currency: Optional[str] = "BRL"
    date_format: Optional[str] = "DD/MM/YYYY"
    time_format: Optional[str] = "24h"


@router.post("/api/settings/regional")
def save_regional_settings(payload: RegionalSettingsPayload):
    valid_langs = {"pt-BR", "en", "es"}
    valid_currencies = {"BRL", "USD", "EUR", "GBP"}
    valid_dates = {"DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD"}
    valid_times = {"24h", "12h"}

    lang = payload.language if payload.language in valid_langs else "pt-BR"
    curr = payload.currency if payload.currency in valid_currencies else "BRL"
    dfmt = payload.date_format if payload.date_format in valid_dates else "DD/MM/YYYY"
    tfmt = payload.time_format if payload.time_format in valid_times else "24h"

    set_setting("language", lang)
    set_setting("currency", curr)
    set_setting("date_format", dfmt)
    set_setting("time_format", tfmt)

    return {
        "ok": True,
        "regional": {
            "language": lang,
            "currency": curr,
            "date_format": dfmt,
            "time_format": tfmt,
        },
    }


class AiTestPayload(BaseModel):
    provider: str
    api_key: str = ""
    base_url: str = ""
    model: str = ""


@router.post("/api/settings/ai/reset")
def reset_ai_settings():
    set_setting("ai_enabled", "0")
    set_setting("ai_provider", "Google Gemini")
    set_setting("ai_api_key", "")
    set_setting("ai_daily_limit", "50")
    set_setting("ai_base_url", "")
    set_setting("ai_model", "")
    return {"ok": True, "message": "Configurações e chave de IA zeradas com sucesso."}


@router.post("/api/settings/ai/test")
def test_ai_connection(payload: AiTestPayload):
    import urllib.error
    import urllib.request

    provider = payload.provider.strip()
    api_key = payload.api_key.strip().strip('"').strip("'")
    base_url = payload.base_url.strip().rstrip("/")
    base_headers = {"User-Agent": "Nexo/2.1.3"}

    if provider == "Google Gemini":
        if not api_key:
            raise HTTPException(status_code=400, detail="Informe a Chave API do Google Gemini.")
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        headers = {**base_headers}
    elif provider == "OpenAI ChatGPT":
        if not api_key:
            raise HTTPException(status_code=400, detail="Informe a Chave API da OpenAI.")
        url = "https://api.openai.com/v1/models"
        headers = {**base_headers, "Authorization": f"Bearer {api_key}"}
    elif provider == "OpenRouter":
        if not api_key:
            raise HTTPException(status_code=400, detail="Informe o Token/Chave API do OpenRouter.")
        url = "https://openrouter.ai/api/v1/auth/key"
        headers = {
            **base_headers,
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://nexo.local",
            "X-Title": "Nexo",
        }
    else:
        if not base_url:
            raise HTTPException(status_code=400, detail="Informe a URL Base da API (ex.: https://api.groq.com/openai/v1).")
        url = f"{base_url}/models"
        headers = {**base_headers, "Authorization": f"Bearer {api_key}"} if api_key else {**base_headers}

    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("utf-8", errors="ignore")
            data = json.loads(raw) if raw else {}
            if provider == "OpenRouter" and isinstance(data, dict) and "data" in data:
                label = data["data"].get("label") or "Chave ativa"
                return {"ok": True, "message": f"OpenRouter conectado com sucesso! ({label})"}
            return {"ok": True, "message": f"Conexão com {provider} validada com sucesso!"}
    except urllib.error.HTTPError as e:
        err_msg = ""
        try:
            err_body = e.read().decode("utf-8", errors="ignore")
            err_json = json.loads(err_body) if err_body else {}
            if isinstance(err_json, dict):
                err_msg = err_json.get("error", {}).get("message") if isinstance(err_json.get("error"), dict) else str(err_json.get("error") or err_json.get("detail") or "")
        except Exception:
            pass
        if e.code in (401, 403):
            extra = f" ({err_msg})" if err_msg else ""
            raise HTTPException(status_code=400, detail=f"Chave API recusada pelo provedor {provider} (HTTP {e.code}){extra}.")
        raise HTTPException(status_code=400, detail=f"O provedor {provider} respondeu com erro HTTP {e.code}{': ' + err_msg if err_msg else ''}.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Não foi possível conectar em {provider}: {str(e)}")


@router.post("/api/settings/company")
def update_company_settings(payload: CompanyPayload):
    c_name = payload.name.strip()
    if not c_name:
        raise HTTPException(status_code=400, detail="O nome da empresa não pode ficar em branco.")
    set_setting("company_name", c_name)
    if payload.logo is not None:
        set_setting("company_logo", payload.logo)
    set_setting("brand_theme_enabled", "1" if payload.brand_theme_enabled else "0")
    if payload.brand_color:
        set_setting("brand_color", payload.brand_color)
    set_setting("apply_brand_to_sidebar", "1" if payload.apply_brand_to_sidebar else "0")
    set_setting("apply_brand_to_buttons", "1" if payload.apply_brand_to_buttons else "0")
    set_setting("show_company_name", "1" if payload.show_company_name is not False else "0")
    if payload.logo_shape:
        set_setting("logo_shape", payload.logo_shape)
    return {
        "ok": True,
        "company_name": c_name,
        "company_logo": payload.logo,
        "brand_theme_enabled": bool(payload.brand_theme_enabled),
        "brand_color": payload.brand_color or "#F28C28",
        "apply_brand_to_sidebar": bool(payload.apply_brand_to_sidebar),
        "apply_brand_to_buttons": bool(payload.apply_brand_to_buttons),
        "show_company_name": payload.show_company_name is not False,
        "logo_shape": payload.logo_shape or "round",
    }


@router.post("/api/settings/company/reset")
def reset_company_settings():
    set_setting("company_name", "Nexo")
    set_setting("company_logo", "")
    set_setting("brand_theme_enabled", "0")
    set_setting("brand_color", "#F28C28")
    set_setting("apply_brand_to_sidebar", "1")
    set_setting("apply_brand_to_buttons", "1")
    set_setting("show_company_name", "1")
    set_setting("logo_shape", "round")
    return {
        "ok": True,
        "company_name": "Nexo",
        "company_logo": "",
        "brand_theme_enabled": False,
        "brand_color": "#F28C28",
        "apply_brand_to_sidebar": True,
        "apply_brand_to_buttons": True,
        "show_company_name": True,
        "logo_shape": "round",
        "message": "Padrão oficial Nexo restaurado com sucesso.",
    }


@router.post("/api/settings/kitchen-costs")
def update_kitchen_costs(payload: KitchenSettingsPayload):
    set_setting("kitchen_days_month", str(payload.kitchen_days_month or "26").replace(",", "."))
    set_setting("kitchen_hours_day", str(payload.kitchen_hours_day or "8").replace(",", "."))
    set_setting("gas_supply_type", str(payload.gas_supply_type or "cylinder_13"))
    set_setting("gas_price", str(payload.gas_price or "125.00").replace(",", "."))
    set_setting("electricity_bill_monthly", str(payload.electricity_bill_monthly or "350.00").replace(",", "."))
    set_setting("water_bill_monthly", str(payload.water_bill_monthly or "80.00").replace(",", "."))
    try:
        snapshot_costs()
    except Exception:
        pass
    return {"ok": True, "message": "Parâmetros da jornada da cozinha salvos com sucesso.", "rates": get_kitchen_rates()}


@router.post("/api/settings/operational-costs")
def update_operational_costs(payload: OperationalCostsPayload):
    with db() as c:
        for it in payload.costs:
            try:
                p_val = float(str(it.percentage or 0.0).replace(",", "."))
            except Exception:
                p_val = 0.0
            try:
                f_val = float(str(it.fixed_value or 0.0).replace(",", "."))
            except Exception:
                f_val = 0.0
            c_type = "FIXED" if str(it.cost_type or "").upper() == "FIXED" else "PERCENT"
            
            if it.id:
                c.execute("UPDATE cost_settings SET percentage=?, cost_type=?, fixed_value=? WHERE id=?", (p_val, c_type, f_val, it.id))
            else:
                c.execute("UPDATE cost_settings SET percentage=?, cost_type=?, fixed_value=? WHERE name=?", (p_val, c_type, f_val, it.name))
        c.commit()
    try:
        snapshot_costs()
    except Exception:
        pass
    return {"ok": True, "message": "Custos operacionais atualizados com sucesso."}


@router.post("/api/settings/database/backup")
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


def _backup_dirs(db_file: Path) -> List[Path]:
    dirs = [db_file.parent / "backups"]
    if hasattr(paths, "BACKUPS_DIR") and paths.BACKUPS_DIR not in dirs:
        dirs.append(paths.BACKUPS_DIR)
    return dirs


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.2f} MB"


@router.get("/api/settings/database/backups")
def list_database_backups():
    db_file = paths.get_db_path()
    seen: set[str] = set()
    items: List[Dict[str, Any]] = []
    for folder in _backup_dirs(db_file):
        if not folder.exists() or not folder.is_dir():
            continue
        for p in folder.glob("*.db"):
            if not p.is_file() or p.name in seen:
                continue
            seen.add(p.name)
            st = p.stat()
            items.append({
                "name": p.name,
                "size_bytes": st.st_size,
                "size_fmt": _format_size(st.st_size),
                "modified_ts": st.st_mtime,
                "modified_at": datetime.fromtimestamp(st.st_mtime).strftime("%d/%m/%Y às %H:%M:%S"),
            })
    items.sort(key=lambda x: x["modified_ts"], reverse=True)
    for item in items:
        item.pop("modified_ts", None)
    return {"ok": True, "backups": items}


class DatabaseRestorePayload(BaseModel):
    filename: str


_MAX_RESTORE_BYTES = 500 * 1024 * 1024
_REQUIRED_NEXO_TABLES = {"materials", "base_recipes", "products", "system_settings"}


def _validate_and_restore_db_file(source_file: Path, display_name: str) -> Dict[str, Any]:
    if not source_file.exists() or not source_file.is_file():
        raise HTTPException(status_code=404, detail="Arquivo de backup não encontrado.")

    size_bytes = source_file.stat().st_size
    if size_bytes <= 16 or size_bytes > _MAX_RESTORE_BYTES:
        raise HTTPException(status_code=400, detail="Tamanho de arquivo inválido para restauração (máx. 500 MB).")

    with source_file.open("rb") as fh:
        header = fh.read(16)
    if header != b"SQLite format 3\x00":
        raise HTTPException(status_code=400, detail="O arquivo selecionado não é um banco SQLite válido.")

    try:
        conn = sqlite3.connect(str(source_file))
        try:
            row = conn.execute("PRAGMA integrity_check").fetchone()
            if not row or str(row[0]).lower() != "ok":
                raise HTTPException(status_code=400, detail="O arquivo de backup falhou na verificação de integridade SQLite.")
            tables = {
                str(r[0])
                for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            }
            missing = _REQUIRED_NEXO_TABLES - tables
            if missing:
                raise HTTPException(
                    status_code=400,
                    detail="Este arquivo SQLite não pertence ao Nexo (estrutura de tabelas incompatível).",
                )
        finally:
            conn.close()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Arquivo de backup inválido ou corrompido: {exc}")

    db_file = paths.get_db_path()
    backup_dir = db_file.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pre_restore_file = backup_dir / f"nexo_pre_restore_{timestamp}.db"
    if db_file.exists():
        shutil.copy2(db_file, pre_restore_file)

    for suffix in ("-wal", "-shm"):
        sidecar = Path(f"{db_file}{suffix}")
        if sidecar.exists():
            try:
                sidecar.unlink()
            except OSError:
                pass

    shutil.copy2(source_file, db_file)
    init_db()

    return {
        "ok": True,
        "restored_from": display_name,
        "pre_restore_backup": pre_restore_file.name if pre_restore_file.exists() else None,
        "message": f"Backup '{display_name}' restaurado com sucesso! Cópia de segurança salva em '{pre_restore_file.name}'.",
    }


@router.post("/api/settings/database/restore")
def restore_database_backup(payload: DatabaseRestorePayload):
    safe_name = Path(payload.filename or "").name
    if not safe_name or safe_name != (payload.filename or "") or not safe_name.lower().endswith(".db"):
        raise HTTPException(status_code=400, detail="Nome de arquivo de backup inválido.")

    db_file = paths.get_db_path()
    backup_file: Optional[Path] = None
    for folder in _backup_dirs(db_file):
        candidate = (folder / safe_name).resolve()
        try:
            candidate.relative_to(folder.resolve())
        except ValueError:
            continue
        if candidate.exists() and candidate.is_file():
            backup_file = candidate
            break

    if backup_file is None:
        raise HTTPException(status_code=404, detail="Arquivo de backup não encontrado.")

    return _validate_and_restore_db_file(backup_file, backup_file.name)


@router.post("/api/settings/database/restore-upload")
async def restore_database_backup_upload(request: Request):
    raw_name = unquote(request.headers.get("X-Backup-Filename") or "backup_externo.db")
    safe_name = Path(raw_name).name
    if not safe_name or not safe_name.lower().endswith(".db"):
        raise HTTPException(status_code=400, detail="Envie um arquivo de backup válido com extensão .db.")

    tmp_path: Optional[Path] = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            tmp_path = Path(tmp.name)
            total = 0
            async for chunk in request.stream():
                if not chunk:
                    continue
                total += len(chunk)
                if total > _MAX_RESTORE_BYTES:
                    raise HTTPException(status_code=400, detail="O arquivo excede o limite máximo permitido (500 MB).")
                tmp.write(chunk)
        return _validate_and_restore_db_file(tmp_path, safe_name)
    finally:
        if tmp_path and tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass


class DatabaseLimitPayload(BaseModel):
    max_size_kb: Optional[int] = None
    max_size_mb: Optional[int] = None


@router.post("/api/settings/database/limit")
def update_database_limit(payload: DatabaseLimitPayload):
    if payload.max_size_kb is not None:
        kb = int(payload.max_size_kb)
    elif payload.max_size_mb is not None:
        kb = int(payload.max_size_mb) * 1024
    else:
        raise HTTPException(status_code=400, detail="Informe o limite desejado para o banco.")

    if kb < 50:
        raise HTTPException(status_code=400, detail="O teto mínimo do banco é 50 KB.")
    health = get_database_health()
    if kb * 1024 < health["size_bytes"]:
        raise HTTPException(
            status_code=400,
            detail=f"O limite escolhido ({_format_limit_kb(kb)}) é menor que o tamanho atual do banco ({health['size_fmt']}). Compacte o banco (VACUUM) ou limpe registros antigos antes de reduzir o teto.",
        )
    max_disk_kb = health.get("max_disk_supported_kb")
    if max_disk_kb is not None and kb > max_disk_kb:
        raise HTTPException(
            status_code=400,
            detail=f"O disco atual não comporta um teto de {_format_limit_kb(kb)} com segurança (espaço livre: {health['disk_free_fmt']}). Máximo recomendado neste disco: {_format_limit_kb(max_disk_kb)}.",
        )
    set_setting("db_max_size_kb", str(kb))
    return {"ok": True, "max_size_kb": kb, "max_size_label": _format_limit_kb(kb)}


@router.post("/api/settings/database/vacuum")
def vacuum_database():
    health = get_database_health()
    if not health["can_vacuum"]:
        raise HTTPException(
            status_code=507,
            detail=f"Espaço livre em disco insuficiente ({health['disk_free_fmt']}) para compactar o banco com segurança. É necessário pelo menos o dobro do tamanho atual ({health['size_fmt']}).",
        )
    with db() as c:
        c.execute("VACUUM")
    return {"ok": True, "message": "Banco de dados compactado e otimizado com sucesso."}


class BiSettingsPayload(BaseModel):
    default_period: str = "12m"
    chart_style: str = "auto"
    cost_variation_alert_pct: float = 10.0
    target_margin_pct: float = 30.0
    include_inactive: bool = False
    color_palette: str = "nexo"
    custom_primary_color: str = "#F28C28"
    custom_secondary_color: str = "#18223A"


@router.post("/api/settings/bi")
def update_bi_settings(payload: BiSettingsPayload):
    valid_periods = {"30d", "3m", "6m", "12m", "all"}
    valid_styles = {"auto", "bar", "line"}
    valid_palettes = {"nexo", "brand", "contrast", "corporate", "custom"}
    if payload.default_period not in valid_periods:
        raise HTTPException(status_code=400, detail="Período padrão de BI inválido.")
    if payload.chart_style not in valid_styles:
        raise HTTPException(status_code=400, detail="Estilo de gráfico inválido.")
    if payload.color_palette not in valid_palettes:
        raise HTTPException(status_code=400, detail="Paleta de cores do BI inválida.")
    if payload.cost_variation_alert_pct < 0 or payload.cost_variation_alert_pct > 500:
        raise HTTPException(status_code=400, detail="O alerta de variação de custo deve ficar entre 0% e 500%.")
    if payload.target_margin_pct < 0 or payload.target_margin_pct > 500:
        raise HTTPException(status_code=400, detail="A meta de margem de lucro deve ficar entre 0% e 500%.")

    set_setting("bi_default_period", payload.default_period)
    set_setting("bi_chart_style", payload.chart_style)
    set_setting("bi_cost_variation_alert_pct", str(round(float(payload.cost_variation_alert_pct), 1)))
    set_setting("bi_target_margin_pct", str(round(float(payload.target_margin_pct), 1)))
    set_setting("bi_include_inactive", "1" if payload.include_inactive else "0")
    set_setting("bi_color_palette", payload.color_palette)
    if payload.custom_primary_color.startswith("#") and len(payload.custom_primary_color) == 7:
        set_setting("bi_custom_primary_color", payload.custom_primary_color)
    if payload.custom_secondary_color.startswith("#") and len(payload.custom_secondary_color) == 7:
        set_setting("bi_custom_secondary_color", payload.custom_secondary_color)
    return {"ok": True, "message": "Preferências de BI salvas com sucesso!"}


class SalesChannelItemPayload(BaseModel):
    id: Optional[str] = None
    name: str
    fee_pct: float = 0.0
    fixed_fee: float = 0.0


class SalesChannelsPayload(BaseModel):
    enabled: bool = False
    channels: List[SalesChannelItemPayload] = []


@router.post("/api/settings/sales-channels")
def update_sales_channels(payload: SalesChannelsPayload):
    cleaned: List[Dict[str, Any]] = []
    for idx, ch in enumerate(payload.channels or []):
        name = str(ch.name or "").strip()
        if not name:
            raise HTTPException(status_code=400, detail="Todo canal de venda precisa ter um nome.")
        fee_pct = float(ch.fee_pct or 0.0)
        fixed_fee = float(ch.fixed_fee or 0.0)
        if fee_pct < 0 or fee_pct >= 99:
            raise HTTPException(status_code=400, detail=f"A taxa (%) do canal '{name}' deve ficar entre 0% e 98,9%.")
        if fixed_fee < 0:
            raise HTTPException(status_code=400, detail=f"A taxa fixa do canal '{name}' não pode ser negativa.")
        cid = str(ch.id or f"ch_{idx + 1}").strip() or f"ch_{idx + 1}"
        cleaned.append({
            "id": cid,
            "name": name,
            "fee_pct": round(fee_pct, 2),
            "fixed_fee": round(fixed_fee, 2),
        })

    if not cleaned:
        cleaned = [dict(c) for c in DEFAULT_SALES_CHANNELS]

    set_setting("sales_channels_enabled", "1" if payload.enabled else "0")
    set_setting("sales_channels_json", json.dumps(cleaned, ensure_ascii=False))
    return {
        "ok": True,
        "enabled": payload.enabled,
        "channels": cleaned,
        "message": (
            "Canais de Venda & Taxas ativados e salvos com sucesso!"
            if payload.enabled
            else "Canais de Venda & Taxas desativados."
        ),
    }


@router.get("/api/reports/export")
def export_database_report(
    scope: str = Query("all", description="all | materials | recipes | products | custom_units | audit"),
    fmt_type: str = Query("pdf", alias="fmt", description="pdf | xlsx | csv | xml"),
):
    valid_scopes = {"all", "materials", "recipes", "products", "custom_units", "audit"}
    valid_formats = {"pdf", "xlsx", "csv", "xml"}
    if scope not in valid_scopes:
        raise HTTPException(status_code=400, detail="Escopo de relatório inválido.")
    if fmt_type not in valid_formats:
        raise HTTPException(status_code=400, detail="Formato de exportação inválido.")

    init_db()
    health = get_database_health()
    sections = collect_report_sections(scope, health)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"nexo_relatorio_{scope}_{stamp}"

    if fmt_type == "pdf":
        data = build_pdf_report(sections, scope)
        media_type = "application/pdf"
        ext = "pdf"
    elif fmt_type == "xlsx":
        data = build_xlsx_report(sections)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ext = "xlsx"
    elif fmt_type == "csv":
        data, media_type, ext = build_csv_or_zip_report(sections)
    else:
        data = build_xml_report(sections, scope)
        media_type = "application/xml; charset=utf-8"
        ext = "xml"

    return Response(
        content=data,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{base_name}.{ext}"'},
    )


@router.post("/api/settings/{key}")
def update_setting(key: str, payload: SettingPayload):
    val = payload.value
    if isinstance(val, (list, dict)):
        set_setting(key, repr(val))
    else:
        set_setting(key, str(val))
    return {"ok": True, "key": key, "value": val}


# =====================================================================
# Atualizações em Rede Local (NexoHub)
# =====================================================================

def _get_current_app_version() -> str:
    try:
        pkg = paths.BASE_DIR / "frontend" / "package.json"
        if pkg.exists():
            data = json.loads(pkg.read_text(encoding="utf-8"))
            v = str(data.get("version") or "").strip()
            if v:
                return v
    except Exception:
        pass
    return "2.1.3"


def _normalize_update_url(raw: str) -> str:
    url = (raw or "").strip().rstrip("/")
    if not url:
        return ""
    low = url.lower()
    if low.startswith("http://"):
        return "http://" + url[7:]
    if low.startswith("https://"):
        return "https://" + url[8:]
    return f"http://{url}"


def _parse_ver_tuple(v: str) -> tuple:
    clean = str(v or "").strip().lstrip("vV")
    parts = []
    for p in clean.split("."):
        try:
            parts.append(int("".join(ch for ch in p if ch.isdigit()) or "0"))
        except Exception:
            parts.append(0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


class UpdateConfigPayload(BaseModel):
    server_url: str = ""
    auto_check: bool = True


class UpdateInstallPayload(BaseModel):
    server_url: Optional[str] = None


@router.get("/api/updates/config")
def get_update_config():
    return {
        "ok": True,
        "server_url": get_setting("update_server_url", "") or "",
        "auto_check": get_setting("update_auto_check", "0") in ("1", "true", "True"),
        "current_version": _get_current_app_version(),
    }


@router.post("/api/updates/config")
def save_update_config(payload: UpdateConfigPayload):
    norm_url = _normalize_update_url(payload.server_url)
    set_setting("update_server_url", norm_url)
    set_setting("update_auto_check", "1" if payload.auto_check else "0")
    return {
        "ok": True,
        "server_url": norm_url,
        "auto_check": payload.auto_check,
        "message": "Configurações de atualização salvas com sucesso.",
    }


@router.get("/api/updates/check")
def check_for_updates(url: Optional[str] = Query(None)):
    import urllib.request

    current_version = _get_current_app_version()
    target_url = _normalize_update_url(url if url is not None else (get_setting("update_server_url", "") or ""))
    if not target_url:
        return {
            "ok": True,
            "configured": False,
            "reachable": False,
            "has_update": False,
            "current_version": current_version,
            "message": "Servidor de atualização não configurado.",
        }

    manifest_url = f"{target_url}/manifest.json"
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        req = urllib.request.Request(manifest_url, headers={"Accept": "application/json"})
        with opener.open(req, timeout=2.5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        latest_version = str(data.get("version") or "").strip()
        filename = str(data.get("file") or "").strip()
        sha256 = str(data.get("sha256") or "").strip()
        size = int(data.get("size") or 0)
        has_update = bool(latest_version and filename and _parse_ver_tuple(latest_version) > _parse_ver_tuple(current_version))
        return {
            "ok": True,
            "configured": True,
            "reachable": True,
            "has_update": has_update,
            "current_version": current_version,
            "latest_version": latest_version,
            "file": filename,
            "sha256": sha256,
            "size": size,
            "message": (
                f"Nova versão {latest_version} disponível!"
                if has_update
                else f"O Nexo já está na versão mais recente ({current_version})."
            ),
        }
    except Exception:
        return {
            "ok": True,
            "configured": True,
            "reachable": False,
            "has_update": False,
            "current_version": current_version,
            "message": "Servidor local offline ou inacessível no momento.",
        }


@router.post("/api/updates/install")
def install_update(payload: Optional[UpdateInstallPayload] = None):
    import hashlib
    import subprocess
    import tempfile
    import threading
    import urllib.request

    raw_url = (payload.server_url if payload and payload.server_url else None) or get_setting("update_server_url", "") or ""
    target_url = _normalize_update_url(raw_url)
    if not target_url:
        raise HTTPException(status_code=400, detail="URL do servidor de atualização não configurada.")

    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(f"{target_url}/manifest.json", timeout=3.0) as resp:
            manifest = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Não foi possível conectar ao servidor de atualização: {e}")

    filename = str(manifest.get("file") or "").strip()
    expected_sha = str(manifest.get("sha256") or "").strip().lower()
    if not filename or "/" in filename or "\\" in filename or ".." in filename or not filename.lower().endswith(".exe"):
        raise HTTPException(status_code=400, detail="Manifesto de atualização inválido.")

    temp_dir = Path(tempfile.gettempdir()) / "NexoUpdate"
    temp_dir.mkdir(parents=True, exist_ok=True)
    dest_exe = temp_dir / filename

    try:
        h = hashlib.sha256()
        with opener.open(f"{target_url}/releases/{filename}", timeout=30.0) as resp, dest_exe.open("wb") as out:
            while True:
                chunk = resp.read(1024 * 512)
                if not chunk:
                    break
                h.update(chunk)
                out.write(chunk)
        actual_sha = h.hexdigest().lower()
    except Exception as e:
        if dest_exe.exists():
            try:
                dest_exe.unlink()
            except Exception:
                pass
        raise HTTPException(status_code=502, detail=f"Falha ao baixar o instalador: {e}")

    if expected_sha and actual_sha != expected_sha:
        try:
            dest_exe.unlink()
        except Exception:
            pass
        raise HTTPException(status_code=400, detail="Falha na verificação de integridade (SHA-256) do instalador.")

    try:
        flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        subprocess.Popen([str(dest_exe), "/AUTOUPDATE"], creationflags=flags, close_fds=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Não foi possível iniciar o instalador: {e}")

    def _delayed_exit():
        import time
        time.sleep(0.6)
        os._exit(0)

    threading.Thread(target=_delayed_exit, daemon=True).start()
    return {"ok": True, "message": "Instalador iniciado. O Nexo será atualizado e reaberto em instantes."}
