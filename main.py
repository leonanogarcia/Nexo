"""
Nexo — Gestão de Custos e Precificação (v1.0.0)
Ponto de entrada principal da aplicação.
"""
try:
    import ctypes
    # DPI_AWARENESS_CONTEXT_UNAWARE_GDISCALED (-5):
    # Escala automaticamente a janela para o tamanho proporcional correto em qualquer escala (ex: 4K a 300%),
    # preservando nitidez de texto e componentes GDI.
    ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-5))
except Exception:
    pass

from backend import (
    paths,
    BASE_DIR, RESOURCE_DIR, USER_DATA_DIR, DATA_DIR, BACKUPS_DIR,
    CONFIG_PATH, DEFAULT_DB_PATH, DB_PATH, DOCS_DIR,
    ICON_PNG, LOGO_PNG, ICON_ICO, UI_ASSETS,
    load_file_config, save_file_config, get_db_path, set_db_path,
    get_user_data_dir, ensure_daily_backup,
    db, now_iso, init_db, next_code, get_setting, set_setting,
    get_cost_settings, record_edit, list_names,
    UNITS_MASS, UNITS_VOLUME, UNITS_COUNT, UNITS, BASE_UNITS_DEFAULT,
    to_float, optional_float, money_to_float, fmt, fmt_num, normalize_text,
    dimension_of_unit, base_unit, unit_factor_to_default_base,
    configured_base_unit, unit_factor_to_internal,
    custom_units_for_material, conversion_to_base, convert_generic, conversion_between,
    material_cost, recipe_cost, item_cost, operational_cost,
    product_unit_cost, product_direct_cost, snapshot_costs,
    save_uploaded_document, latest_document,
    extract_docx_text, extract_pdf_text, parse_recipe_lines,
)
from frontend import (
    _field_palette, rounded_entry, numeric_entry, masked_money_entry,
    safe_error, bind_text_capitalization, FlatEmojiButton,
    Modal, RoundedPanel, PillScrollbar, VerticalPillScrollbar,
    RoundedActionButton, RoundedEntry, SidebarIcon, NavItem,
    ReferenceSidebar, RoundedDropdown, CustomHistoryModal, ListDialog,
    get_work_area, App,
)


if __name__ == '__main__':
    init_db()
    App().mainloop()
