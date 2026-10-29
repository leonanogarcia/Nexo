import json
import os
import shutil
import sys
from datetime import date
from pathlib import Path

# Pasta onde os recursos de leitura (ícones, ui_assets) estão localizados.
# Funciona tanto rodando via "python main.py" quanto empacotado em .exe (PyInstaller).
if getattr(sys, 'frozen', False):
    RESOURCE_DIR = Path(getattr(sys, '_MEIPASS', Path(sys.executable).resolve().parent))
    APP_DIR = Path(sys.executable).resolve().parent
else:
    RESOURCE_DIR = Path(__file__).resolve().parent.parent
    APP_DIR = RESOURCE_DIR

BASE_DIR = APP_DIR


def _is_dir_writable(directory: Path) -> bool:
    """Verifica se o usuário atual (mesmo sem Admin) tem permissão de escrita na pasta."""
    try:
        directory.mkdir(parents=True, exist_ok=True)
        probe = directory / '.nexo_write_probe'
        probe.write_text('ok', encoding='utf-8')
        probe.unlink(missing_ok=True)
        return True
    except Exception:
        return False


def get_user_data_dir() -> Path:
    """
    Retorna a pasta oficial de dados do usuário no Windows (%LOCALAPPDATA%\\Nexo).
    Qualquer conta de usuário (mesmo sem acesso Administrador) possui permissão total aqui.
    """
    local_appdata = os.environ.get('LOCALAPPDATA')
    if local_appdata:
        user_dir = Path(local_appdata) / 'Nexo'
    else:
        user_dir = Path.home() / 'AppData' / 'Local' / 'Nexo'
    try:
        user_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return user_dir


USER_DATA_DIR = get_user_data_dir()
BACKUPS_DIR = USER_DATA_DIR / 'backups'
try:
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass

# Se estiver rodando instalado (.exe) ou em uma pasta protegida (ex: C:\Program Files\Nexo sem Admin),
# usa automaticamente %LOCALAPPDATA%\Nexo para criar o banco limpo do zero, configurações e documentos.
# Em modo de desenvolvimento (python main.py), mantém separado na pasta do projeto.
if getattr(sys, 'frozen', False) or not _is_dir_writable(BASE_DIR):
    DATA_DIR = USER_DATA_DIR
else:
    DATA_DIR = BASE_DIR

CONFIG_PATH = DATA_DIR / 'nexo_config.json'
DEFAULT_DB_PATH = DATA_DIR / 'nexo.db'


def load_file_config() -> Path:
    try:
        if CONFIG_PATH.exists():
            data = json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
            path = data.get('sqlite_path')
            if path:
                candidate = Path(path)
                if _is_dir_writable(candidate.parent):
                    return candidate
    except Exception:
        pass
    return DEFAULT_DB_PATH


DB_PATH = load_file_config()
DOCS_DIR = DATA_DIR / 'documentos'
ICON_PNG = RESOURCE_DIR / 'nexo_icon.png'
LOGO_PNG = RESOURCE_DIR / 'nexo_logo.png'
ICON_ICO = RESOURCE_DIR / 'nexo_icon.ico'
UI_ASSETS = RESOURCE_DIR / 'ui_assets'


def get_db_path() -> Path:
    return DB_PATH


def set_db_path(new_path) -> Path:
    global DB_PATH
    DB_PATH = Path(new_path)
    return DB_PATH


def save_file_config():
    payload = json.dumps({'sqlite_path': str(DB_PATH)}, ensure_ascii=False, indent=2)
    try:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(payload, encoding='utf-8')
    except Exception:
        pass


def ensure_daily_backup():
    """Cria uma cópia automática diária do banco em %LOCALAPPDATA%\\Nexo\\backups."""
    try:
        if DB_PATH.exists() and BACKUPS_DIR.exists():
            prefix = 'nexo_backup' if DATA_DIR == USER_DATA_DIR else 'nexo_dev_backup'
            today_backup = BACKUPS_DIR / f'{prefix}_{date.today().isoformat()}.db'
            if not today_backup.exists():
                shutil.copy2(DB_PATH, today_backup)
    except Exception:
        pass
