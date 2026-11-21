"""Tradução de mensagens da API do Nexo conforme o idioma ativo (pt-BR, en, es).

Dados cadastrados pelo usuário nunca são traduzidos; apenas mensagens de erro,
status de saúde do banco e avisos retornados pelo backend.
"""

from typing import Any, Dict, Optional

from .database import get_setting

VALID_LANGUAGES = ("pt-BR", "en", "es")

_EXACT_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "Saudável": {"en": "Healthy", "es": "Saludable"},
    "Atenção": {"en": "Warning", "es": "Atención"},
    "Crítico": {"en": "Critical", "es": "Crítico"},
    "Sem espaço suficiente em disco ou teto do banco atingido.": {
        "en": "Insufficient disk space or database size limit reached.",
        "es": "Espacio en disco insuficiente o límite de base de datos alcanzado.",
    },
    "Insumo não encontrado.": {"en": "Material not found.", "es": "Insumo no encontrado."},
    "Receita não encontrada.": {"en": "Recipe not found.", "es": "Receta no encontrada."},
    "Produto não encontrado.": {"en": "Product not found.", "es": "Producto no encontrado."},
    "Unidade não encontrada.": {"en": "Unit not found.", "es": "Unidad no encontrada."},
    "Anexo não encontrado.": {"en": "Attachment not found.", "es": "Adjunto no encontrado."},
    "Nome do insumo é obrigatório.": {
        "en": "Material name is required.",
        "es": "El nombre del insumo es obligatorio.",
    },
    "Nome da receita é obrigatório.": {
        "en": "Recipe name is required.",
        "es": "El nombre de la receta es obligatorio.",
    },
    "Nome do produto é obrigatório.": {
        "en": "Product name is required.",
        "es": "El nombre del producto es obligatorio.",
    },
    "Configurações e chave de IA zeradas com sucesso.": {
        "en": "AI settings and key reset successfully.",
        "es": "Configuración y clave de IA restablecidas con éxito.",
    },
    "Arquivo de backup inválido.": {
        "en": "Invalid backup file.",
        "es": "Archivo de copia de seguridad no válido.",
    },
    "Backup restaurado com sucesso.": {
        "en": "Backup restored successfully.",
        "es": "Copia de seguridad restaurada con éxito.",
    },
    "Compra": {"en": "Purchase", "es": "Compra"},
}

_PREFIX_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "Banco fragmentado": {
        "en": "Fragmented database — run Compact (VACUUM) in Settings.",
        "es": "Base de datos fragmentada — ejecuta Compactar (VACUUM) en Configuración.",
    },
    "Teto do banco": {
        "en": "Database size limit reached. Increase the limit or clean old records in Settings.",
        "es": "Límite de tamaño de base de datos alcanzado. Aumenta el límite o limpia registros antiguos.",
    },
    "Pouco espaço livre em disco": {
        "en": "Low free disk space on this computer.",
        "es": "Poco espacio libre en disco en este equipo.",
    },
}


def get_active_language() -> str:
    try:
        lang = str(get_setting("language", "pt-BR") or "pt-BR").strip()
        return lang if lang in VALID_LANGUAGES else "pt-BR"
    except Exception:
        return "pt-BR"


def translate_api_message(text: Any, lang: Optional[str] = None) -> Any:
    """Traduz strings de erro/status do backend mantendo valores não-textuais intactos."""
    if not isinstance(text, str) or not text:
        return text
    target = lang or get_active_language()
    if target == "pt-BR":
        return text

    exact = _EXACT_TRANSLATIONS.get(text)
    if exact and target in exact:
        return exact[target]

    for prefix, mapping in _PREFIX_TRANSLATIONS.items():
        if text.startswith(prefix) and target in mapping:
            return mapping[target]

    return text
