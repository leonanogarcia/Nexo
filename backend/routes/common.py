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

from fastapi import HTTPException
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


def _format_bytes_label(num_bytes: int) -> str:
    if num_bytes < 1024:
        return f"{num_bytes} B"
    if num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} KB"
    if num_bytes < 1024 * 1024 * 1024:
        return f"{num_bytes / (1024 * 1024):.2f} MB"
    return f"{num_bytes / (1024 * 1024 * 1024):.2f} GB"


def _format_limit_kb(kb: int) -> str:
    if kb == 250 * 1024:
        return "250 MB (Padrão)"
    if kb < 1024:
        return f"{kb} KB"
    mb = kb / 1024.0
    if mb >= 1000:
        gb = mb / 1000.0
        return f"{gb:g} GB".replace(".", ",")
    return f"{mb:g} MB".replace(".", ",")


def _next_limit_step_kb(kb: int) -> int:
    if kb < 950:
        return kb + 50
    if kb < 1024:
        return 1024
    if kb < 50 * 1024:
        step_5mb = 5 * 1024
        return ((kb // step_5mb) + 1) * step_5mb
    step_50mb = 50 * 1024
    return ((kb // step_50mb) + 1) * step_50mb


def get_database_health(db_file: Optional[Path] = None) -> Dict[str, Any]:
    target = db_file or paths.get_db_path()
    default_kb = 250 * 1024
    max_size_kb = default_kb
    try:
        raw_kb = get_setting("db_max_size_kb", "")
        if raw_kb:
            max_size_kb = int(float(raw_kb))
        else:
            raw_mb = get_setting("db_max_size_mb", "250")
            max_size_kb = int(float(raw_mb or 250)) * 1024
    except Exception:
        max_size_kb = default_kb
    max_size_kb = max(50, max_size_kb)
    max_size_bytes = max_size_kb * 1024

    size_bytes = 0
    try:
        if target.exists():
            size_bytes = target.stat().st_size
    except Exception:
        pass

    page_count = 0
    page_size = 4096
    freelist_count = 0
    try:
        with db() as c:
            page_count = int(c.execute("PRAGMA page_count").fetchone()[0] or 0)
            page_size = int(c.execute("PRAGMA page_size").fetchone()[0] or 4096)
            freelist_count = int(c.execute("PRAGMA freelist_count").fetchone()[0] or 0)
    except Exception:
        pass

    wasted_bytes = freelist_count * page_size
    wasted_pct = round((freelist_count / page_count) * 100, 1) if page_count > 0 else 0.0
    usage_pct = round((size_bytes / max_size_bytes) * 100, 1) if max_size_bytes > 0 else 0.0

    disk_free_bytes = 0
    disk_total_bytes = 0
    try:
        usage = shutil.disk_usage(target.parent)
        disk_free_bytes = int(usage.free)
        disk_total_bytes = int(usage.total)
    except Exception:
        pass

    reasons: List[str] = []
    status = "green"
    can_write = True

    # 1. Disco do computador (PCs modestos)
    if disk_free_bytes > 0:
        if disk_free_bytes < 50 * 1024 * 1024:
            status = "red"
            can_write = False
            reasons.append(f"Espaço livre em disco crítico ({_format_bytes_label(disk_free_bytes)}). Gravações bloqueadas para evitar corrupção.")
        elif disk_free_bytes < 200 * 1024 * 1024:
            status = "red"
            reasons.append(f"Espaço livre em disco muito baixo ({_format_bytes_label(disk_free_bytes)}).")
        elif disk_free_bytes < 500 * 1024 * 1024:
            if status == "green":
                status = "yellow"
            reasons.append(f"Pouco espaço livre em disco ({_format_bytes_label(disk_free_bytes)}).")

    # 2. Teto fixo configurado do Nexo
    if usage_pct >= 100.0:
        status = "red"
        can_write = False
        reasons.append(f"Banco atingiu o teto configurado ({_format_limit_kb(max_size_kb)}). Compacte ou ajuste o limite para continuar criando registros.")
    elif usage_pct >= 90.0:
        status = "red"
        reasons.append(f"Banco em {usage_pct:.1f}% do teto configurado ({_format_limit_kb(max_size_kb)}).")
    elif usage_pct >= 70.0:
        if status == "green":
            status = "yellow"
        reasons.append(f"Banco em {usage_pct:.1f}% do teto configurado ({_format_limit_kb(max_size_kb)}).")

    # 3. Fragmentação interna ("lixo" de exclusões)
    if wasted_pct >= 40.0 and wasted_bytes >= 10 * 1024 * 1024:
        status = "red"
        reasons.append(f"Alto acúmulo de espaço morto ({_format_bytes_label(wasted_bytes)} / {wasted_pct:.1f}%). Recomenda-se Compactar (VACUUM).")
    elif wasted_pct >= 20.0 and wasted_bytes >= 2 * 1024 * 1024:
        if status == "green":
            status = "yellow"
        reasons.append(f"Banco fragmentado ({_format_bytes_label(wasted_bytes)} recuperáveis). Clique em Compactar (VACUUM).")

    from ..i18n import get_active_language, translate_api_message
    _lang = get_active_language()
    health_label = translate_api_message(
        {
            "green": "Saudável",
            "yellow": "Atenção",
            "red": "Crítico",
        }[status],
        _lang,
    )
    reasons = [translate_api_message(r, _lang) for r in reasons]

    can_vacuum = disk_free_bytes == 0 or disk_free_bytes > max(size_bytes * 2, 10 * 1024 * 1024)

    # Janela deslizante inteligente: 9 opções progressivas (KB -> MB -> GB) acima do tamanho atual + 250 MB (Padrão)
    size_kb = int(math.ceil(size_bytes / 1024)) if size_bytes > 0 else 50
    if size_kb < 950:
        first_kb = max(50, ((size_kb + 49) // 50) * 50)
    elif size_kb < 1024:
        first_kb = 1024
    elif size_kb < 50 * 1024:
        step_5mb = 5 * 1024
        first_kb = ((size_kb + step_5mb - 1) // step_5mb) * step_5mb
    else:
        step_50mb = 50 * 1024
        first_kb = ((size_kb + step_50mb - 1) // step_50mb) * step_50mb

    if disk_free_bytes > 0:
        safe_total_bytes = max(size_bytes, size_bytes + max(0, disk_free_bytes - 100 * 1024 * 1024))
        max_disk_supported_kb = max(first_kb, int(safe_total_bytes // 1024))
    else:
        max_disk_supported_kb = None

    option_kbs: List[int] = []
    curr = first_kb
    for _ in range(9):
        if max_disk_supported_kb is not None and curr > max_disk_supported_kb:
            break
        option_kbs.append(curr)
        curr = _next_limit_step_kb(curr)

    if default_kb >= first_kb and (max_disk_supported_kb is None or default_kb <= max_disk_supported_kb):
        if default_kb not in option_kbs:
            option_kbs.append(default_kb)

    if max_size_kb >= first_kb and (max_disk_supported_kb is None or max_size_kb <= max_disk_supported_kb):
        if max_size_kb not in option_kbs:
            option_kbs.append(max_size_kb)

    option_kbs = sorted(set(option_kbs))
    if not option_kbs:
        option_kbs = [first_kb]

    limit_options = [{"kb": kb, "label": _format_limit_kb(kb)} for kb in option_kbs]

    limit_advisory = ""
    if max_size_kb > 500 * 1024:
        limit_advisory = (
            f"Teto elevado ({_format_limit_kb(max_size_kb)}): em computadores mais antigos ou com menos memória RAM, processador mais simples e pouco espaço em disco (HD/SSD), "
            "bancos muito grandes podem deixar buscas, relatórios e backups mais lentos ou travar o sistema. Prefira usar Compactar (VACUUM) ou reduzir os meses de retenção."
        )
    elif max_size_kb > default_kb and wasted_bytes >= 1024 * 1024:
        limit_advisory = (
            f"Há {_format_bytes_label(wasted_bytes)} de espaço morto recuperável no banco. "
            "Considere compactar (VACUUM) antes de subir ainda mais o limite."
        )

    return {
        "size_bytes": size_bytes,
        "size_fmt": _format_bytes_label(size_bytes),
        "max_size_kb": max_size_kb,
        "max_size_mb": round(max_size_kb / 1024, 2),
        "max_size_label": _format_limit_kb(max_size_kb),
        "max_disk_supported_kb": max_disk_supported_kb,
        "limit_options": limit_options,
        "limit_advisory": limit_advisory,
        "usage_pct": usage_pct,
        "wasted_bytes": wasted_bytes,
        "wasted_fmt": _format_bytes_label(wasted_bytes),
        "wasted_pct": wasted_pct,
        "disk_free_bytes": disk_free_bytes,
        "disk_free_fmt": _format_bytes_label(disk_free_bytes) if disk_free_bytes > 0 else "-",
        "disk_total_bytes": disk_total_bytes,
        "health_status": status,
        "health_label": health_label,
        "health_reasons": reasons,
        "can_write": can_write,
        "can_vacuum": can_vacuum,
    }

class MaterialCreatePayload(BaseModel):
    name: str
    brand: Optional[str] = ""
    qty: Any
    unit: str
    value: Any
    category: str = "Comestível"
    barcode: Optional[str] = ""
    purchase_date: Optional[str] = None
    confirm_similar: bool = False


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
    confirm_similar: bool = False


class BulkDeleteCheckPayload(BaseModel):
    ids: List[int]


class ToggleActivePayload(BaseModel):
    active: bool


class ConversionPayload(BaseModel):
    material_id: int
    name: str
    base_unit: str
    factor_to_base: Any


class UpdateConversionPayload(BaseModel):
    name: Optional[str] = None
    base_unit: Optional[str] = None
    factor_to_base: Any = None


class BatchDeleteConversionsPayload(BaseModel):
    ids: list[int]


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
    cooking_appliance: Optional[str] = "none"
    cooking_time_minutes: Optional[Any] = 0.0
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

def _canonical_key(text: str) -> str:
    import re
    import unicodedata
    raw = unicodedata.normalize("NFKD", str(text or ""))
    no_acc = "".join(ch for ch in raw if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", no_acc.strip().lower())


_PLACEHOLDER_WORDS = {"teste", "test", "asdf", "qwe", "qwerty", "nada", "na", "n/a", "nenhum", "nenhuma", "generico", "sem", "qualquer", "abc", "xyz"}


def _validate_quality_text(value: str, field_label: str, is_brand: bool = False, no_brand: bool = False) -> str:
    import re
    val = str(value or "").strip()
    if is_brand and no_brand:
        return "Sem marca"
    if not val:
        if is_brand:
            raise ValueError('O campo "Marca" é obrigatório (ou marque a opção "Sem marca").')
        raise ValueError(f'O campo "{field_label}" é obrigatório.')
    letters = re.findall(r"[a-zA-ZÀ-ÿ]", val)
    if len(letters) < 2:
        raise ValueError(f'"{field_label}" inválido ("{val}"). Informe um nome real com pelo menos 2 letras.')
    compact = re.sub(r"\s+", "", val.lower())
    if len(set(compact)) <= 1:
        raise ValueError(f'"{field_label}" inválido ("{val}"). Não use caracteres repetidos.')
    canon = _canonical_key(val)
    if canon in _PLACEHOLDER_WORDS or (is_brand and canon == "sem marca" and not no_brand):
        if is_brand:
            raise ValueError('Não use texto genérico em "Marca". Informe a marca real ou marque "Sem marca".')
        raise ValueError(f'Não use texto genérico em "{field_label}".')
    return normalize_text(val)


def _base_packaging(qty: float, unit: str) -> tuple[str, float]:
    from ..units import dimension_of_unit, to_base
    dim = dimension_of_unit(unit) or f"unit:{unit}"
    try:
        base_q = float(to_base(float(qty), unit))
    except Exception:
        base_q = float(qty)
    return (dim, round(base_q, 4))


class SimilarMaterialWarning(ValueError):
    """Raised when a similar (non-identical) material already exists and requires user confirmation."""
    def __init__(self, message: str, existing: dict):
        super().__init__(message)
        self.existing = existing


def _check_material_duplicate_or_typo(
    c,
    name: str,
    brand: str,
    qty: float,
    unit: str,
    exclude_id: Optional[int] = None,
    confirm_similar: bool = False,
) -> None:
    import difflib
    c_name = _canonical_key(name)
    c_brand = _canonical_key(brand or "Sem marca")
    dim, b_qty = _base_packaging(qty, unit)

    rows = c.execute(
        "SELECT id, code, name, brand, purchase_qty, purchase_unit, purchase_value, category, COALESCE(barcode, '') AS barcode FROM materials WHERE COALESCE(archived, 0)=0"
    ).fetchall()
    for r in rows:
        if exclude_id and r["id"] == exclude_id:
            continue
        r_name = _canonical_key(r["name"])
        r_brand = _canonical_key(r["brand"] or "Sem marca")
        r_dim, r_bqty = _base_packaging(float(r["purchase_qty"] or 0), r["purchase_unit"] or "un")
        same_pack = (r_dim == dim) and (abs(r_bqty - b_qty) <= max(0.01, b_qty * 0.001))
        if not same_pack:
            continue
        if r_name == c_name and r_brand == c_brand:
            raise ValueError(
                f'Já existe um insumo idêntico cadastrado: "{r["name"]}" ({r["brand"] or "Sem marca"} • {fmt_num(r["purchase_qty"])} {r["purchase_unit"]}). Atualize o existente em vez de duplicar.'
            )
        if r_brand == c_brand and not confirm_similar:
            ratio = difflib.SequenceMatcher(None, c_name, r_name).ratio()
            if ratio >= 0.85:
                raise SimilarMaterialWarning(
                    f'Já existe um insumo parecido: "{r["name"]}" ({r["brand"] or "Sem marca"} • {fmt_num(r["purchase_qty"])} {r["purchase_unit"]}).',
                    existing={
                        "id": r["id"],
                        "code": r["code"] or "",
                        "name": r["name"],
                        "brand": r["brand"] or "Sem marca",
                        "qty": float(r["purchase_qty"] or 0),
                        "qty_fmt": fmt_num(r["purchase_qty"]),
                        "unit": r["purchase_unit"] or "un",
                        "value": float(r["purchase_value"] or 0),
                        "value_fmt": fmt(r["purchase_value"]),
                        "category": r["category"] or "Comestível",
                        "barcode": r["barcode"] or "",
                    },
                )

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

__all__ = ['_format_bytes_label', '_format_limit_kb', '_next_limit_step_kb', 'get_database_health', 'MaterialCreatePayload', 'MaterialUpdatePayload', 'BulkDeleteCheckPayload', 'ToggleActivePayload', 'ConversionPayload', 'UpdateConversionPayload', 'BatchDeleteConversionsPayload', 'SettingPayload', 'RecipeItemPayload', 'RecipePayload', '_normalize_purchase_datetime', '_load_hidden_cols', '_canonical_key', '_validate_quality_text', '_base_packaging', 'SimilarMaterialWarning', '_check_material_duplicate_or_typo', '_format_history_date']
