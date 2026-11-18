"""Módulo de Visão Computacional e Extração por IA para o Nexo (Etapa 5).

Suporta Google Gemini, OpenAI ChatGPT, OpenRouter e provedores compatíveis OpenAI,
com controle de limite diário (ai_usage_logs) e retorno estruturado para pré-visualização.
"""
from __future__ import annotations

import base64
import json
import re
import ssl
import time
import urllib.error
import urllib.request
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

from . import normalize_text
from .database import db, get_setting

_OPENROUTER_FREE_CACHE: Dict[str, Any] = {
    "ts": 0.0,
    "vision": [],
    "text": [],
}
_OPENROUTER_AUTO_FREE_SENTINELS = {"", "auto", "free", "auto-free", "openrouter/free"}
_OPENROUTER_FALLBACK_VISION_FREE = [
    "openrouter/free",
    "google/gemma-3-27b-it:free",
    "qwen/qwen2.5-vl-72b-instruct:free",
    "meta-llama/llama-3.2-11b-vision-instruct:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
]
_OPENROUTER_FALLBACK_TEXT_FREE = [
    "openrouter/free",
    "google/gemma-3-27b-it:free",
    "qwen/qwen3-32b:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
]


def _get_ai_config() -> Dict[str, Any]:
    enabled = get_setting("ai_enabled", "0") in ("1", "true", "True")
    provider = get_setting("ai_provider", "Google Gemini").strip()
    api_key = get_setting("ai_api_key", "").strip().strip('"').strip("'")
    base_url = get_setting("ai_base_url", "").strip().rstrip("/")
    model = get_setting("ai_model", "").strip()
    try:
        daily_limit = max(1, int(get_setting("ai_daily_limit", "50") or 50))
    except Exception:
        daily_limit = 50
    return {
        "enabled": enabled,
        "provider": provider,
        "api_key": api_key,
        "base_url": base_url,
        "model": model,
        "daily_limit": daily_limit,
    }


def check_and_consume_daily_quota(daily_limit: int) -> int:
    today = date.today().isoformat()
    with db() as c:
        row = c.execute("SELECT request_count FROM ai_usage_logs WHERE date_str = ?", (today,)).fetchone()
        used = int(row["request_count"]) if row else 0
        if used >= daily_limit:
            raise RuntimeError(
                f"Limite diário de segurança atingido ({used}/{daily_limit} leituras hoje). "
                "Ajuste o limite em Configurações → Sincronismo de IA se necessário."
            )
        if row:
            c.execute("UPDATE ai_usage_logs SET request_count = request_count + 1 WHERE date_str = ?", (today,))
        else:
            c.execute("INSERT INTO ai_usage_logs(date_str, request_count) VALUES(?, 1)", (today,))
        c.commit()
        return used + 1


def _extract_json_object(raw_text: str) -> Dict[str, Any]:
    cleaned = raw_text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", cleaned, re.I)
    if fence:
        cleaned = fence.group(1).strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        cleaned = cleaned[start : end + 1]
    return json.loads(cleaned)


def _is_free_openrouter_model(model_obj: Dict[str, Any]) -> bool:
    mid = str(model_obj.get("id") or "")
    if not mid or mid == "openrouter/auto":
        return False
    if mid == "openrouter/free" or mid.endswith(":free"):
        return True
    pricing = model_obj.get("pricing") or {}
    try:
        return float(pricing.get("prompt", 1)) == 0.0 and float(pricing.get("completion", 1)) == 0.0
    except Exception:
        return False


def _score_free_model(mid: str) -> Tuple[int, str]:
    low = mid.lower()
    if low == "openrouter/free":
        return (0, low)
    preferred_prefixes = ("google/", "qwen/", "meta-llama/", "mistralai/", "deepseek/", "nvidia/")
    for idx, pref in enumerate(preferred_prefixes, start=1):
        if low.startswith(pref):
            return (idx, low)
    return (99, low)


def _get_openrouter_free_models(needs_vision: bool) -> List[str]:
    now = time.time()
    cache_key = "vision" if needs_vision else "text"
    if (now - float(_OPENROUTER_FREE_CACHE.get("ts") or 0.0)) < 600 and _OPENROUTER_FREE_CACHE.get(cache_key):
        return list(_OPENROUTER_FREE_CACHE[cache_key])

    vision_list: List[str] = []
    text_list: List[str] = []
    try:
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/models",
            headers={"User-Agent": "Nexo/1.9.3"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        for m in payload.get("data") or []:
            if not isinstance(m, dict) or not _is_free_openrouter_model(m):
                continue
            mid = str(m.get("id") or "").strip()
            if not mid:
                continue
            arch = m.get("architecture") or {}
            modalities = [str(x).lower() for x in (arch.get("input_modalities") or [])]
            if "image" in modalities:
                vision_list.append(mid)
            text_list.append(mid)
    except Exception:
        pass

    vision_sorted = sorted(set(vision_list), key=_score_free_model)
    text_sorted = sorted(set(text_list), key=_score_free_model)

    if not vision_sorted:
        vision_sorted = list(_OPENROUTER_FALLBACK_VISION_FREE)
    elif "openrouter/free" not in vision_sorted:
        vision_sorted.insert(0, "openrouter/free")

    if not text_sorted:
        text_sorted = list(_OPENROUTER_FALLBACK_TEXT_FREE)
    elif "openrouter/free" not in text_sorted:
        text_sorted.insert(0, "openrouter/free")

    _OPENROUTER_FREE_CACHE["ts"] = now
    _OPENROUTER_FREE_CACHE["vision"] = vision_sorted[:8]
    _OPENROUTER_FREE_CACHE["text"] = text_sorted[:8]
    return list(_OPENROUTER_FREE_CACHE[cache_key])


def _call_openai_compatible(
    url: str,
    model: str,
    headers: Dict[str, str],
    content_blocks: List[Dict[str, Any]],
    provider: str,
) -> str:
    body = {
        "model": model,
        "temperature": 0.1,
        "messages": [{"role": "user", "content": content_blocks}],
    }
    req_headers = {
        "Accept": "application/json",
        "Connection": "close",
        **headers,
    }
    ssl_ctx = ssl.create_default_context()
    data_bytes = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data_bytes, headers=req_headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60, context=ssl_ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError(f"O provedor {provider} não retornou resposta.")
        msg = choices[0].get("message", {}).get("content", "")
        if isinstance(msg, list):
            return "\n".join(str(x.get("text", "")) for x in msg if isinstance(x, dict))
        return str(msg)
    except urllib.error.HTTPError as e:
        err_raw = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Erro em {provider} ({model} • HTTP {e.code}): {err_raw[:280]}")
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise RuntimeError(f"Falha de conexão em {provider} ({model}): {str(e)[:220]}")


def _call_ai_vision(
    prompt: str,
    image_bytes: Optional[bytes] = None,
    mime_type: str = "image/jpeg",
    extra_text: str = "",
) -> str:
    cfg = _get_ai_config()
    if not cfg["enabled"]:
        raise RuntimeError("A IA está desativada. Ative em Configurações → Sincronismo de IA.")
    if not cfg["api_key"] and cfg["provider"] != "Outro (Compatível OpenAI)":
        raise RuntimeError("Chave API não configurada em Configurações → Sincronismo de IA.")

    check_and_consume_daily_quota(cfg["daily_limit"])

    provider = cfg["provider"]
    api_key = cfg["api_key"]
    full_prompt = prompt if not extra_text else f"{prompt}\n\nConteúdo do documento:\n{extra_text[:12000]}"

    if provider == "Google Gemini":
        model = cfg["model"] or "gemini-2.0-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        parts: List[Dict[str, Any]] = [{"text": full_prompt}]
        if image_bytes:
            parts.append({
                "inline_data": {
                    "mime_type": mime_type,
                    "data": base64.b64encode(image_bytes).decode("ascii"),
                }
            })
        body = {
            "contents": [{"parts": parts}],
            "generationConfig": {"temperature": 0.1},
        }
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Nexo/1.9.3",
        }
        req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            candidates = data.get("candidates") or []
            if not candidates:
                raise RuntimeError("O Google Gemini não retornou resposta.")
            text_parts = [p.get("text", "") for p in candidates[0].get("content", {}).get("parts", [])]
            return "\n".join(text_parts)
        except urllib.error.HTTPError as e:
            err_raw = e.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Erro no Google Gemini (HTTP {e.code}): {err_raw[:240]}")

    # OpenAI / OpenRouter / Outro (Compatível OpenAI)
    if provider == "OpenAI ChatGPT":
        url = "https://api.openai.com/v1/chat/completions"
        model = cfg["model"] or "gpt-4o-mini"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "Nexo/1.9.3",
        }
    elif provider == "OpenRouter":
        url = "https://openrouter.ai/api/v1/chat/completions"
        model = cfg["model"] or "openrouter/free"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://nexo.local",
            "X-Title": "Nexo",
            "User-Agent": "Nexo/1.9.3",
        }
    else:
        if not cfg["base_url"]:
            raise RuntimeError("URL Base da API não configurada para o provedor personalizado.")
        url = f"{cfg['base_url']}/chat/completions"
        model = cfg["model"] or "gpt-4o-mini"
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Nexo/1.9.3",
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

    content_blocks: List[Dict[str, Any]] = [{"type": "text", "text": full_prompt}]
    if image_bytes:
        b64 = base64.b64encode(image_bytes).decode("ascii")
        content_blocks.append({
            "type": "image_url",
            "image_url": {"url": f"data:{mime_type};base64,{b64}"},
        })

    if provider == "OpenRouter" and cfg["model"].strip().lower() in _OPENROUTER_AUTO_FREE_SENTINELS:
        candidates = _get_openrouter_free_models(needs_vision=bool(image_bytes))
        last_err = ""
        for cand in candidates[:6]:
            try:
                out = _call_openai_compatible(url, cand, headers, content_blocks, provider)
                if out and out.strip():
                    return out
            except RuntimeError as exc:
                last_err = str(exc)
                continue
        raise RuntimeError(
            "Nenhum modelo gratuito do OpenRouter respondeu no momento. "
            f"Último detalhe: {last_err[:220]}"
        )

    return _call_openai_compatible(url, model, headers, content_blocks, provider)


def _match_material(name: str, materials: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    norm = normalize_text(name).strip().lower()
    if not norm:
        return None
    for m in materials:
        if normalize_text(m["name"]).strip().lower() == norm:
            return m
    for m in materials:
        mn = normalize_text(m["name"]).strip().lower()
        if mn and (mn in norm or norm in mn):
            return m
    return None


def parse_receipt_with_ai(image_bytes: bytes, mime_type: str) -> Dict[str, Any]:
    prompt = (
        "Você é um assistente de compras e estoque de confeitaria/produção de alimentos. "
        "Analise esta foto de cupom fiscal / notinha de supermercado e extraia TODOS os itens comprados. "
        "Responda SOMENTE com um JSON válido neste formato exato:\n"
        "{\n"
        '  "purchase_date": "YYYY-MM-DD",\n'
        '  "items": [\n'
        "    {\n"
        '      "name": "Nome limpo do insumo (ex: Farinha de Trigo)",\n'
        '      "brand": "Marca se visível ou string vazia",\n'
        '      "qty": 1,\n'
        '      "unit": "un | g | kg | ml | L",\n'
        '      "value": 12.50,\n'
        '      "category": "Comestível | Não comestível",\n'
        '      "barcode": ""\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "Use unidades padrão (mg, g, kg, t, ml, L, kL, un). Se não tiver certeza da data, use a data de hoje."
    )
    raw = _call_ai_vision(prompt, image_bytes=image_bytes, mime_type=mime_type)
    parsed = _extract_json_object(raw)

    with db() as c:
        mats = [
            dict(r)
            for r in c.execute(
                "SELECT id, name, brand, purchase_qty, purchase_unit, purchase_value, category FROM materials WHERE COALESCE(archived,0)=0"
            ).fetchall()
        ]

    from .units import dimension_of_unit, to_base

    items_out: List[Dict[str, Any]] = []
    for idx, it in enumerate(parsed.get("items") or []):
        name = str(it.get("name") or "").strip()
        if not name:
            continue
        unit = str(it.get("unit") or "un").strip()
        if unit not in ("mg", "g", "kg", "t", "ml", "L", "kL", "un"):
            unit = "un"
        qty_val = float(it.get("qty") or 1)
        brand_val = str(it.get("brand") or "").strip()

        matched = _match_material(name, mats)
        # Só sugere "update" automaticamente se a embalagem na unidade base também bater (ex.: 1 kg == 1000 g; 500 g != 1 kg)
        can_auto_update = False
        if matched:
            try:
                it_dim = dimension_of_unit(unit) or unit
                m_dim = dimension_of_unit(matched["purchase_unit"]) or matched["purchase_unit"]
                if it_dim == m_dim:
                    it_base = float(to_base(qty_val, unit))
                    m_base = float(to_base(float(matched["purchase_qty"] or 0), matched["purchase_unit"]))
                    if abs(it_base - m_base) <= max(0.01, m_base * 0.001):
                        can_auto_update = True
            except Exception:
                can_auto_update = False

        items_out.append({
            "temp_id": idx + 1,
            "selected": True,
            "name": name,
            "brand": brand_val,
            "no_brand": False,
            "qty": qty_val,
            "unit": unit,
            "value": round(float(it.get("value") or 0), 2),
            "category": str(it.get("category") or (matched["category"] if can_auto_update and matched else "Comestível") or "Comestível"),
            "barcode": str(it.get("barcode") or "").strip(),
            "action": "update" if can_auto_update else "create",
            "matched_material_id": matched["id"] if can_auto_update and matched else None,
            "matched_material_name": matched["name"] if can_auto_update and matched else "",
            "reason": "Compra via Notinha (IA)",
        })

    return {
        "purchase_date": str(parsed.get("purchase_date") or date.today().isoformat())[:10],
        "items": items_out,
    }


def parse_recipe_or_product_with_ai(
    target_kind: str,
    image_bytes: Optional[bytes] = None,
    mime_type: str = "image/jpeg",
    extra_text: str = "",
) -> Dict[str, Any]:
    kind_label = "receita base" if target_kind == "recipe" else "produto final / ficha de montagem"
    prompt = (
        f"Você é um assistente de ficha técnica de confeitaria e produção. "
        f"Extraia os dados desta {kind_label}. "
        "Responda SOMENTE com um JSON válido neste formato exato:\n"
        "{\n"
        '  "name": "Nome da receita ou produto",\n'
        '  "yield_qty": 1,\n'
        '  "yield_unit": "un | g | kg | ml | L",\n'
        '  "notes": "Modo de preparo resumido se houver",\n'
        '  "ingredients": [\n'
        "    {\n"
        '      "name": "Nome do ingrediente/insumo",\n'
        '      "qty": 100,\n'
        '      "unit": "g | kg | ml | L | un"\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "Converta frações para decimais (ex: 0.5). Prefira unidades padrão (mg, g, kg, t, ml, L, kL, un)."
    )
    raw = _call_ai_vision(prompt, image_bytes=image_bytes, mime_type=mime_type, extra_text=extra_text)
    parsed = _extract_json_object(raw)

    with db() as c:
        mats = [dict(r) for r in c.execute("SELECT id, name, purchase_unit FROM materials WHERE COALESCE(active,1)=1 AND COALESCE(archived,0)=0").fetchall()]
        recs = [dict(r) for r in c.execute("SELECT id, name, yield_unit FROM base_recipes WHERE COALESCE(active,1)=1 AND COALESCE(archived,0)=0").fetchall()]

    ingredients_out: List[Dict[str, Any]] = []
    for idx, ing in enumerate(parsed.get("ingredients") or []):
        name = str(ing.get("name") or "").strip()
        if not name:
            continue
        matched_mat = _match_material(name, mats)
        matched_rec = None if matched_mat or target_kind != "product" else _match_material(name, recs)
        item_type = "RECIPE_BASE" if matched_rec else "MATERIAL"
        matched_obj = matched_rec or matched_mat
        ingredients_out.append({
            "temp_id": idx + 1,
            "selected": True,
            "name": name,
            "qty": float(ing.get("qty") or 1),
            "unit": str(ing.get("unit") or "g").strip(),
            "item_type": item_type,
            "matched_id": matched_obj["id"] if matched_obj else None,
            "matched_name": matched_obj["name"] if matched_obj else "",
        })

    return {
        "name": str(parsed.get("name") or "").strip(),
        "yield_qty": float(parsed.get("yield_qty") or 1),
        "yield_unit": str(parsed.get("yield_unit") or "un").strip(),
        "notes": str(parsed.get("notes") or "").strip(),
        "ingredients": ingredients_out,
    }


def transcribe_image_to_text(image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
    """Transcreve texto legível de uma foto de receita/ficha usando IA (quando ativa)."""
    cfg = _get_ai_config()
    if not cfg["enabled"] or not image_bytes:
        return ""
    prompt = (
        "Transcreva fielmente todo o texto visível desta imagem de receita ou ficha técnica em português, "
        "mantendo título, lista de ingredientes com quantidades e modo de preparo bem organizados em texto puro. "
        "Não adicione comentários extras."
    )
    try:
        return (_call_ai_vision(prompt, image_bytes=image_bytes, mime_type=mime_type) or "").strip()
    except Exception:
        return ""
