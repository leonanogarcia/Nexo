import json
import re
import shutil
import sqlite3
from pathlib import Path
from datetime import date, datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / 'nexo_config.json'
DEFAULT_DB_PATH = BASE_DIR / 'nexo.db'

def load_file_config():
    try:
        data=json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
        path=data.get('sqlite_path')
        if path:
            return Path(path)
    except Exception:
        pass
    return DEFAULT_DB_PATH

DB_PATH = load_file_config()
DOCS_DIR = BASE_DIR / 'documentos'
ICON_PNG = BASE_DIR / 'nexo_icon.png'
LOGO_PNG = BASE_DIR / 'nexo_logo.png'
ICON_ICO = BASE_DIR / 'nexo_icon.ico'
UI_ASSETS = BASE_DIR / 'ui_assets'

UNITS_MASS = ('mg', 'g', 'kg', 't')
UNITS_VOLUME = ('ml', 'L', 'kL')
UNITS_COUNT = ('un',)
UNITS = UNITS_MASS + UNITS_VOLUME + UNITS_COUNT
BASE_UNITS_DEFAULT = {'mass': 'mg', 'volume': 'ml', 'count': 'un'}


def db():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON')
    return c


def now_iso():
    return datetime.now().isoformat(timespec='seconds')


def to_float(value, field_name='valor'):
    text = str(value).strip()
    if not text:
        raise ValueError(f'O campo "{field_name}" é obrigatório.')
    try:
        # Aceita 1,5 e 1.5. Quando há os dois separadores, considera o último
        # como separador decimal (ex.: 1.234,56).
        if ',' in text and '.' in text:
            if text.rfind(',') > text.rfind('.'):
                text = text.replace('.', '').replace(',', '.')
            else:
                text = text.replace(',', '')
        elif ',' in text:
            text = text.replace(',', '.')
        elif text.count('.') > 1:
            text = text.replace('.', '')
        return float(text)
    except ValueError:
        raise ValueError(f'O campo "{field_name}" deve conter um número válido.')


def _field_palette(parent):
    try:
        app=parent.winfo_toplevel()
        colors=getattr(app,'colors',{})
        return colors.get('field','#FFFFFF'), colors.get('line','#DDE5F2'), colors.get('panel','#FFFFFF')
    except Exception:
        return '#FFFFFF','#DDE5F2',parent.cget('bg')


def rounded_entry(parent, variable, **kwargs):
    field, line, panel = _field_palette(parent)
    wrap=RoundedPanel(parent, fill=field, border='', radius=18, bg=panel)
    # O próprio campo ocupa o corpo da cápsula; não usamos um ttk.Entry quadrado
    # dentro dela, pois isso cria a falsa sensação de que só a borda é arredondada.
    entry_kwargs=dict(bg=field, fg=getattr(parent.winfo_toplevel(),'colors',{}).get('text','#1F2A44'),
                      insertbackground=getattr(parent.winfo_toplevel(),'colors',{}).get('text','#1F2A44'),
                      relief='flat', bd=0, highlightthickness=0, font=('Segoe UI',10), **kwargs)
    entry=tk.Entry(wrap, textvariable=variable, **entry_kwargs)
    entry.pack(fill='both', expand=True, padx=12, pady=8)
    return wrap, entry


def numeric_entry(parent, variable, **kwargs):
    """Campo numérico arredondado; bloqueia qualquer entrada não numérica."""
    wrap, entry = rounded_entry(parent, variable, **kwargs)
    vcmd=(entry.register(lambda proposed: bool(re.fullmatch(r'[0-9]*([.,][0-9]*)?',proposed))),'%P')
    entry.configure(validate='key',validatecommand=vcmd)
    return wrap


def optional_float(value, field_name='valor'):
    text = str(value).strip()
    if not text:
        return None
    return to_float(text, field_name)


def money_to_float(value, field_name='Valor'):
    text = str(value).strip().replace('R$', '').replace(' ', '')
    if not text:
        raise ValueError(f'O campo "{field_name}" é obrigatório.')
    return to_float(text, field_name)


def masked_money_entry(parent, variable, **kwargs):
    """Campo monetário: aceita somente dígitos; separadores digitados são ignorados."""
    wrap, entry = rounded_entry(parent, variable, **kwargs)
    state = {'digits': ''}

    def format_digits(digits):
        digits = ''.join(ch for ch in str(digits) if ch.isdigit()) or '0'
        digits = digits.lstrip('0') or '0'
        state['digits'] = digits
        variable.set(fmt(int(digits) / 100.0))
        entry.icursor(tk.END)

    def sync_from_display():
        digits = ''.join(ch for ch in variable.get() if ch.isdigit())
        # O display sempre tem R$ e duas casas. Não deixamos o campo vazio.
        format_digits(digits[-18:] if digits else '0')

    def keypress(event):
        if event.char and event.char.isdigit():
            format_digits(state['digits'] + event.char)
            return 'break'
        if event.char in (',', '.'):
            # Separadores são apenas ignorados. A máscara já fornece a vírgula.
            entry.icursor(tk.END)
            return 'break'
        if event.keysym in ('BackSpace', 'Delete'):
            digits = state['digits'][:-1] if state['digits'] else '0'
            format_digits(digits)
            return 'break'
        if event.keysym in ('Tab','Return','Escape','Left','Right','Home','End','Shift_L','Shift_R','Control_L','Control_R'):
            return
        return 'break'

    entry.bind('<KeyPress>', keypress)
    entry.bind('<FocusIn>', lambda e: sync_from_display())
    if not variable.get():
        variable.set('R$ 0,00')
    else:
        sync_from_display()
    return wrap

def fmt(v):
    if v is None:
        return '-'
    return f'R$ {v:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def fmt_num(v):
    if v is None:
        return '-'
    s = f'{float(v):,.3f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    return s.rstrip('0').rstrip(',')


def safe_error(parent, title, exc):
    message = str(exc)
    if 'obrigat' in message.lower():
        action = 'finalizar' if any(word in title.lower() for word in ('finalizar','concluir')) else 'salvar'
        message = f'Não foi possível {action}. Existem campos obrigatórios que precisam ser preenchidos.'
    messagebox.showerror(title, message, parent=parent)

def normalize_text(value):
    """Normaliza textos digitados manualmente: primeira letra em maiúscula."""
    text = str(value)
    for i, ch in enumerate(text):
        if ch.isalpha():
            return text[:i] + ch.upper() + text[i+1:]
    return text


def bind_text_capitalization(widget):
    if isinstance(widget, (ttk.Entry, ttk.Combobox)):
        def normalize(_event=None, w=widget):
            try:
                if str(w.cget('state')) == 'disabled':
                    return
                value = w.get()
                normalized = normalize_text(value)
                if normalized != value:
                    w.delete(0, tk.END)
                    w.insert(0, normalized)
            except Exception:
                pass
        widget.bind('<FocusOut>', normalize, add='+')
        widget.bind('<Return>', normalize, add='+')
        widget.bind('<KeyRelease>', normalize, add='+')
    for child in widget.winfo_children():
        bind_text_capitalization(child)



def dimension_of_unit(unit):
    if unit in UNITS_MASS:
        return 'mass'
    if unit in UNITS_VOLUME:
        return 'volume'
    if unit in UNITS_COUNT:
        return 'count'
    return None


def base_unit(unit):
    d = dimension_of_unit(unit)
    return BASE_UNITS_DEFAULT.get(d)


def unit_factor_to_default_base(unit):
    factors = {
        'mg': 1.0,
        'g': 1000.0,
        'kg': 1_000_000.0,
        't': 1_000_000_000.0,
        'ml': 1.0,
        'L': 1000.0,
        'kL': 1_000_000.0,
        'un': 1.0,
    }
    return factors.get(unit)


def configured_base_unit(dimension):
    return get_setting({'mass':'mass_base_unit','volume':'volume_base_unit','count':'count_base_unit'}.get(dimension), BASE_UNITS_DEFAULT[dimension])


def unit_factor_to_internal(unit):
    factor = unit_factor_to_default_base(unit)
    if factor is None:
        return None, None
    dim = dimension_of_unit(unit)
    internal = configured_base_unit(dim)
    base_factor = unit_factor_to_default_base(internal)
    return factor / base_factor, internal


def init_db():
    DOCS_DIR.mkdir(exist_ok=True)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with db() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS materials(
          id INTEGER PRIMARY KEY,
          code TEXT UNIQUE,
          name TEXT NOT NULL,
          purchase_qty REAL NOT NULL DEFAULT 0,
          purchase_unit TEXT NOT NULL DEFAULT 'g',
          purchase_value REAL NOT NULL DEFAULT 0,
          brand TEXT,
          category TEXT NOT NULL DEFAULT 'Comestível',
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS purchases(
          id INTEGER PRIMARY KEY,
          material_id INTEGER NOT NULL,
          qty REAL NOT NULL,
          unit TEXT NOT NULL,
          value REAL NOT NULL,
          brand TEXT,
          purchase_date TEXT NOT NULL,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY(material_id) REFERENCES materials(id)
        );
        CREATE TABLE IF NOT EXISTS base_recipes(
          id INTEGER PRIMARY KEY,
          code TEXT UNIQUE,
          name TEXT UNIQUE NOT NULL,
          yield_qty REAL,
          yield_unit TEXT,
          notes TEXT,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS base_recipe_items(
          id INTEGER PRIMARY KEY,
          recipe_id INTEGER NOT NULL,
          material_id INTEGER NOT NULL,
          qty REAL NOT NULL,
          unit TEXT NOT NULL,
          FOREIGN KEY(recipe_id) REFERENCES base_recipes(id) ON DELETE CASCADE,
          FOREIGN KEY(material_id) REFERENCES materials(id)
        );
        CREATE TABLE IF NOT EXISTS products(
          id INTEGER PRIMARY KEY,
          code TEXT UNIQUE,
          name TEXT UNIQUE NOT NULL,
          weight_qty REAL,
          weight_unit TEXT,
          sale_price REAL,
          notes TEXT,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS product_items(
          id INTEGER PRIMARY KEY,
          product_id INTEGER NOT NULL,
          item_type TEXT NOT NULL,
          ref_id INTEGER NOT NULL,
          qty_per_unit REAL NOT NULL,
          unit TEXT NOT NULL,
          FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS cost_settings(
          id INTEGER PRIMARY KEY,
          name TEXT UNIQUE NOT NULL,
          percentage REAL NOT NULL DEFAULT 20
        );
        CREATE TABLE IF NOT EXISTS system_settings(
          key TEXT PRIMARY KEY,
          value TEXT
        );
        CREATE TABLE IF NOT EXISTS custom_units(
          id INTEGER PRIMARY KEY,
          material_id INTEGER NOT NULL,
          name TEXT NOT NULL,
          base_unit TEXT NOT NULL,
          factor_to_base REAL NOT NULL,
          UNIQUE(material_id, name),
          FOREIGN KEY(material_id) REFERENCES materials(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS edit_history(
          id INTEGER PRIMARY KEY,
          entity_type TEXT NOT NULL,
          entity_id INTEGER NOT NULL,
          reason TEXT NOT NULL,
          changes_json TEXT,
          edited_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS audit_log(
          id INTEGER PRIMARY KEY,
          action TEXT NOT NULL,
          table_name TEXT NOT NULL,
          record_id INTEGER,
          before_json TEXT,
          after_json TEXT,
          changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS document_links(
          id INTEGER PRIMARY KEY,
          entity_type TEXT NOT NULL,
          entity_id INTEGER NOT NULL,
          original_name TEXT NOT NULL,
          stored_path TEXT NOT NULL,
          uploaded_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS cost_history(
          id INTEGER PRIMARY KEY,
          entity_type TEXT NOT NULL,
          entity_id INTEGER NOT NULL,
          cost REAL NOT NULL,
          recorded_at TEXT NOT NULL
        );
        ''')
        # Backward-compatible columns for databases from the early prototype.
        def add_col(table, col, definition):
            cols = {r['name'] for r in c.execute(f'PRAGMA table_info({table})').fetchall()}
            if col not in cols:
                c.execute(f'ALTER TABLE {table} ADD COLUMN {col} {definition}')
        add_col('materials', 'code', 'TEXT')
        add_col('materials', 'updated_at', 'TEXT')
        add_col('products', 'active', 'INTEGER NOT NULL DEFAULT 1')
        add_col('materials', 'active', 'INTEGER NOT NULL DEFAULT 1')
        add_col('base_recipes', 'active', 'INTEGER NOT NULL DEFAULT 1')
        add_col('base_recipes', 'code', 'TEXT')
        add_col('base_recipes', 'updated_at', 'TEXT')
        add_col('products', 'code', 'TEXT')
        add_col('products', 'weight_qty', 'REAL')
        add_col('products', 'weight_unit', 'TEXT')
        add_col('products', 'notes', 'TEXT')
        add_col('products', 'created_at', 'TEXT')
        add_col('products', 'updated_at', 'TEXT')
        add_col('cost_settings', 'percentage', 'REAL NOT NULL DEFAULT 20')
        for name in ('Gás', 'Energia', 'Água'):
            c.execute('INSERT OR IGNORE INTO cost_settings(name, percentage) VALUES(?,20)', (name,))
        c.execute('INSERT OR IGNORE INTO system_settings(key,value) VALUES(?,?)', ('theme', 'light'))
        c.execute('INSERT OR IGNORE INTO system_settings(key,value) VALUES(?,?)', ('company_name', 'Nexo'))
        c.execute('INSERT OR IGNORE INTO system_settings(key,value) VALUES(?,?)', ('company_logo', ''))
        c.execute('INSERT OR IGNORE INTO system_settings(key,value) VALUES(?,?)', ('mass_base_unit', 'mg'))
        c.execute('INSERT OR IGNORE INTO system_settings(key,value) VALUES(?,?)', ('volume_base_unit', 'ml'))
        c.execute('INSERT OR IGNORE INTO system_settings(key,value) VALUES(?,?)', ('count_base_unit', 'un'))
        _ensure_codes(c)
        _ensure_audit_triggers(c)


def _ensure_audit_triggers(c):
    specs = {
        'materials': (
            "json_object('id',OLD.id,'code',OLD.code,'name',OLD.name,'brand',OLD.brand,'qty',OLD.purchase_qty,'unit',OLD.purchase_unit,'value',OLD.purchase_value,'category',OLD.category)",
            "json_object('id',NEW.id,'code',NEW.code,'name',NEW.name,'brand',NEW.brand,'qty',NEW.purchase_qty,'unit',NEW.purchase_unit,'value',NEW.purchase_value,'category',NEW.category)"),
        'base_recipes': (
            "json_object('id',OLD.id,'code',OLD.code,'name',OLD.name,'yield_qty',OLD.yield_qty,'yield_unit',OLD.yield_unit,'notes',OLD.notes)",
            "json_object('id',NEW.id,'code',NEW.code,'name',NEW.name,'yield_qty',NEW.yield_qty,'yield_unit',NEW.yield_unit,'notes',NEW.notes)"),
        'products': (
            "json_object('id',OLD.id,'code',OLD.code,'name',OLD.name,'weight_qty',OLD.weight_qty,'weight_unit',OLD.weight_unit,'sale_price',OLD.sale_price,'notes',OLD.notes)",
            "json_object('id',NEW.id,'code',NEW.code,'name',NEW.name,'weight_qty',NEW.weight_qty,'weight_unit',NEW.weight_unit,'sale_price',NEW.sale_price,'notes',NEW.notes)"),
    }
    for table,(before,after) in specs.items():
        c.execute(f'''CREATE TRIGGER IF NOT EXISTS audit_{table}_insert AFTER INSERT ON {table} BEGIN
          INSERT INTO audit_log(action,table_name,record_id,after_json,changed_at) VALUES('INSERT','{table}',NEW.id,{after.replace('OLD.','NEW.')},datetime('now','localtime'));
        END''')
        c.execute(f'''CREATE TRIGGER IF NOT EXISTS audit_{table}_update AFTER UPDATE ON {table} BEGIN
          INSERT INTO audit_log(action,table_name,record_id,before_json,after_json,changed_at) VALUES('UPDATE','{table}',NEW.id,{before},{after},datetime('now','localtime'));
        END''')
        c.execute(f'''CREATE TRIGGER IF NOT EXISTS audit_{table}_delete AFTER DELETE ON {table} BEGIN
          INSERT INTO audit_log(action,table_name,record_id,before_json,changed_at) VALUES('DELETE','{table}',OLD.id,{before},datetime('now','localtime'));
        END''')


def _ensure_codes(c):
    for table, prefix in (('materials', 'INS'), ('base_recipes', 'RB'), ('products', 'PROD')):
        rows = c.execute(f'SELECT id FROM {table} WHERE code IS NULL OR code="" ORDER BY id').fetchall()
        used = {r['code'] for r in c.execute(f'SELECT code FROM {table} WHERE code IS NOT NULL').fetchall()}
        max_num = 0
        for code in used:
            m = re.fullmatch(re.escape(prefix) + r'_(\d+)', str(code))
            if m:
                max_num = max(max_num, int(m.group(1)))
        for r in rows:
            while True:
                max_num += 1
                code = f'{prefix}_{max_num:04d}'
                if code not in used:
                    break
            c.execute(f'UPDATE {table} SET code=? WHERE id=?', (code, r['id']))
            used.add(code)


def next_code(table, prefix):
    with db() as c:
        rows = c.execute(f'SELECT code FROM {table} WHERE code LIKE ?', (f'{prefix}_%',)).fetchall()
        highest = 0
        for r in rows:
            m = re.fullmatch(re.escape(prefix) + r'_(\d+)', str(r['code'] or ''))
            if m:
                highest = max(highest, int(m.group(1)))
        return f'{prefix}_{highest + 1:04d}'


def get_setting(key, default=''):
    with db() as c:
        r = c.execute('SELECT value FROM system_settings WHERE key=?', (key,)).fetchone()
    return r['value'] if r else default


def save_file_config():
    try:
        CONFIG_PATH.write_text(json.dumps({'sqlite_path': str(DB_PATH)}, ensure_ascii=False, indent=2), encoding='utf-8')
    except Exception:
        pass


def set_setting(key, value):
    with db() as c:
        c.execute('INSERT INTO system_settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value', (key, str(value)))


def get_cost_settings():
    with db() as c:
        rows = c.execute('SELECT name, percentage FROM cost_settings ORDER BY id').fetchall()
    return {r['name']: float(r['percentage']) for r in rows}


def record_edit(entity_type, entity_id, reason, changes):
    with db() as c:
        c.execute('INSERT INTO edit_history(entity_type,entity_id,reason,changes_json,edited_at) VALUES(?,?,?,?,?)',
                  (entity_type, entity_id, reason, json.dumps(changes, ensure_ascii=False), now_iso()))


def list_names(table):
    with db() as c:
        if table == 'products':
            return c.execute('SELECT id,name,code FROM products WHERE COALESCE(active,1)=1 ORDER BY name').fetchall()
        return c.execute(f'SELECT id,name,code FROM {table} WHERE COALESCE(active,1)=1 ORDER BY name').fetchall()


def custom_units_for_material(material_id):
    with db() as c:
        return c.execute('SELECT id,name,base_unit,factor_to_base FROM custom_units WHERE material_id=? ORDER BY name', (material_id,)).fetchall()


def conversion_to_base(material_id, unit, qty):
    factor, base = unit_factor_to_internal(unit)
    if factor is not None:
        return qty * factor, base
    with db() as c:
        row = c.execute('SELECT base_unit,factor_to_base FROM custom_units WHERE material_id=? AND name=?', (material_id, unit)).fetchone()
    if row:
        current_base = configured_base_unit(dimension_of_unit(row['base_unit']))
        if row['base_unit'] != current_base:
            raise ValueError(f'A conversão configurável "{unit}" precisa ser atualizada para a unidade interna atual ({current_base}).')
        return qty * row['factor_to_base'], current_base
    raise ValueError(f'Não existe conversão configurada para "{unit}" neste insumo.')


def convert_generic(qty, from_unit, to_unit):
    f_from, b_from = unit_factor_to_internal(from_unit)
    f_to, b_to = unit_factor_to_internal(to_unit)
    if f_from is None or f_to is None or b_from != b_to:
        raise ValueError(f'Unidades incompatíveis: {from_unit} → {to_unit}.')
    return qty * f_from / f_to


def conversion_between(material_id, qty, from_unit, to_unit):
    q_base, base_a = conversion_to_base(material_id, from_unit, qty)
    q2_base, base_b = conversion_to_base(material_id, to_unit, 1.0)
    if base_a != base_b:
        raise ValueError(f'Unidades incompatíveis: {from_unit} → {to_unit}.')
    return q_base / q2_base


def material_cost(material_id, qty, unit):
    with db() as c:
        m = c.execute('SELECT purchase_qty,purchase_unit,purchase_value FROM materials WHERE id=?', (material_id,)).fetchone()
    if not m:
        raise ValueError('Insumo não encontrado no Cadastro.')
    used_base, base = conversion_to_base(material_id, unit, qty)
    purchase_base, purchase_base_unit = conversion_to_base(material_id, m['purchase_unit'], m['purchase_qty'])
    if base != purchase_base_unit:
        raise ValueError(f'Unidades incompatíveis para o insumo: {unit} e {m["purchase_unit"]}.')
    if purchase_base <= 0:
        return 0.0
    return used_base * (m['purchase_value'] / purchase_base)


def recipe_cost(recipe_id, stack=None):
    stack = set() if stack is None else stack
    if recipe_id in stack:
        raise ValueError('Ciclo detectado na Receita.')
    with db() as c:
        rows = c.execute('SELECT * FROM base_recipe_items WHERE recipe_id=?', (recipe_id,)).fetchall()
    if not rows:
        return 0.0
    total = 0.0
    stack.add(recipe_id)
    for r in rows:
        total += material_cost(r['material_id'], r['qty'], r['unit'])
    stack.remove(recipe_id)
    return total



def item_cost(item_type, ref_id, qty, unit, stack=None):
    if item_type == 'MATERIAL':
        return material_cost(ref_id, qty, unit)
    if item_type == 'RECIPE_BASE':
        with db() as c:
            r = c.execute('SELECT yield_qty,yield_unit FROM base_recipes WHERE id=?', (ref_id,)).fetchone()
        if not r or not r['yield_qty'] or r['yield_qty'] <= 0:
            raise ValueError('A Receita precisa ter rendimento definido antes de ser usada em um Produto.')
        q = convert_generic(qty, unit, r['yield_unit'])
        return q * recipe_cost(ref_id) / r['yield_qty']
    if item_type == 'PRODUCT':
        return qty * product_unit_cost(ref_id, stack)
    raise ValueError('Tipo de componente inválido.')


def operational_cost(direct_cost):
    settings = get_cost_settings()
    total_pct = settings.get('Gás', 0) + settings.get('Energia', 0) + settings.get('Água', 0)
    return direct_cost * total_pct / 100.0


def product_unit_cost(product_id, stack=None):
    stack = set() if stack is None else stack
    if product_id in stack:
        raise ValueError('Ciclo detectado na composição de Produtos.')
    with db() as c:
        rows = c.execute('SELECT * FROM product_items WHERE product_id=?', (product_id,)).fetchall()
    direct = 0.0
    stack.add(product_id)
    for r in rows:
        direct += item_cost(r['item_type'], r['ref_id'], r['qty_per_unit'], r['unit'], stack)
    stack.remove(product_id)
    return direct + operational_cost(direct)


def product_direct_cost(product_id, stack=None):
    stack = set() if stack is None else stack
    if product_id in stack:
        raise ValueError('Ciclo detectado na composição de Produtos.')
    with db() as c:
        rows = c.execute('SELECT * FROM product_items WHERE product_id=?', (product_id,)).fetchall()
    total = 0.0
    stack.add(product_id)
    for r in rows:
        total += item_cost(r['item_type'], r['ref_id'], r['qty_per_unit'], r['unit'], stack)
    stack.remove(product_id)
    return total


def snapshot_costs():
    recorded = now_iso()
    with db() as c:
        recipes = c.execute('SELECT id FROM base_recipes').fetchall()
        products = c.execute('SELECT id FROM products').fetchall()
    with db() as c:
        for r in recipes:
            try:
                cost = recipe_cost(r['id'])
                c.execute('INSERT INTO cost_history(entity_type,entity_id,cost,recorded_at) VALUES(?,?,?,?)', ('RECIPE_BASE', r['id'], cost, recorded))
            except Exception:
                pass
        for p in products:
            try:
                cost = product_unit_cost(p['id'])
                c.execute('INSERT INTO cost_history(entity_type,entity_id,cost,recorded_at) VALUES(?,?,?,?)', ('PRODUCT', p['id'], cost, recorded))
            except Exception:
                pass


def save_uploaded_document(entity_type, entity_id, source_path):
    src = Path(source_path)
    target = DOCS_DIR / f'{entity_type.lower()}_{entity_id}_{src.name}'
    shutil.copy2(src, target)
    with db() as c:
        c.execute('INSERT INTO document_links(entity_type,entity_id,original_name,stored_path,uploaded_at) VALUES(?,?,?,?,?)',
                  (entity_type, entity_id, src.name, str(target), now_iso()))
    return target


def latest_document(entity_type, entity_id):
    with db() as c:
        r = c.execute('SELECT * FROM document_links WHERE entity_type=? AND entity_id=? ORDER BY id DESC LIMIT 1', (entity_type, entity_id)).fetchone()
    return r


def extract_docx_text(path):
    try:
        from docx import Document
    except ImportError:
        raise RuntimeError('Para importar Word, instale a dependência "python-docx". O núcleo do Nexo não depende dela.')
    doc = Document(path)
    return '\n'.join(p.text for p in doc.paragraphs if p.text.strip())


def extract_pdf_text(path):
    try:
        from pypdf import PdfReader
    except ImportError:
        raise RuntimeError('Para importar PDF, instale a dependência "pypdf". O núcleo do Nexo não depende dela.')
    reader = PdfReader(path)
    return '\n'.join((p.extract_text() or '') for p in reader.pages)


def parse_recipe_lines(text):
    results = []
    patterns = [
        re.compile(r'^\s*(\d+(?:[\.,]\d+)?)\s+(.+?)\s+(mg|g|kg|t|ml|L|kL|un|xícara(?:s)?|xicara(?:s)?|colher(?:es)? de sopa|colher(?:es)? de chá)\s*$', re.I),
        re.compile(r'^\s*(.+?)\s*[-:]\s*(\d+(?:[\.,]\d+)?)\s*(mg|g|kg|t|ml|L|kL|un|xícara(?:s)?|xicara(?:s)?)\s*$', re.I),
    ]
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        match = None
        for p in patterns:
            m = p.match(line)
            if m:
                match = m
                break
        if match:
            g = match.groups()
            if g[0].replace(',', '.', 1).replace('.', '', 1).isdigit():
                qty, name, unit = g
            else:
                name, qty, unit = g
            results.append((name.strip(), float(qty.replace(',', '.')), unit.lower()))
    return results


class Modal(tk.Toplevel):
    def __init__(self, master, title, geometry='760x560'):
        super().__init__(master)
        self.title(title)
        self.transient(master)
        self.resizable(True, True)
        self.minsize(520, 320)
        self._place_over_master(geometry)
        self.action_host=tk.Frame(self,bg=self.cget('bg'),height=58)
        self.action_host.pack(side='bottom',fill='x',padx=12,pady=(4,10))
        self.action_host.pack_propagate(False)
        self.grab_set()
        self.lift()
        self.focus_force()
        self.protocol('WM_DELETE_WINDOW', self.destroy)
        self.bind('<Map>', lambda e: (self.lift(), self.focus_force()))
        self.after(50, lambda: (self.lift(), self.focus_force(), bind_text_capitalization(self)))

    def _work_area(self, x, y):
        # No Windows, usa a área útil do monitor onde a janela principal está.
        try:
            import ctypes
            from ctypes import wintypes
            class RECT(ctypes.Structure):
                _fields_=[('left',wintypes.LONG),('top',wintypes.LONG),('right',wintypes.LONG),('bottom',wintypes.LONG)]
            class MONITORINFO(ctypes.Structure):
                _fields_=[('cbSize',wintypes.DWORD),('rcMonitor',RECT),('rcWork',RECT),('dwFlags',wintypes.DWORD)]
            MONITOR_DEFAULTTONEAREST=2
            hmon=ctypes.windll.user32.MonitorFromPoint(wintypes.POINT(x,y), MONITOR_DEFAULTTONEAREST)
            mi=MONITORINFO(); mi.cbSize=ctypes.sizeof(MONITORINFO)
            if hmon and ctypes.windll.user32.GetMonitorInfoW(hmon, ctypes.byref(mi)):
                r=mi.rcWork
                return r.left,r.top,r.right,r.bottom
        except Exception:
            pass
        return 0,0,self.winfo_screenwidth(),self.winfo_screenheight()

    def _place_over_master(self, geometry):
        m=re.match(r'^(\d+)x(\d+)', str(geometry))
        req_w,req_h=(int(m.group(1)),int(m.group(2))) if m else (760,560)
        self.update_idletasks()
        mx=self.master.winfo_rootx(); my=self.master.winfo_rooty()
        mw=max(self.master.winfo_width(),1); mh=max(self.master.winfo_height(),1)
        left,top,right,bottom=self._work_area(mx+mw//2,my+mh//2)
        max_w=max(520,right-left-24); max_h=max(320,bottom-top-24)
        w=min(req_w,max_w); h=min(req_h,max_h)
        x=mx+(mw-w)//2; y=my+(mh-h)//2
        x=max(left+12,min(x,right-w-12)); y=max(top+12,min(y,bottom-h-12))
        self.geometry(f'{w}x{h}+{x}+{y}')


class RoundedPanel(tk.Frame):
    """Painel visual com fundo arredondado, com suporte a cor sólida ou degradê vertical."""
    def __init__(self, parent, fill='#FFFFFF', border='#E8DED0', radius=22, padding=0, **kwargs):
        bg = kwargs.pop('bg', None)
        if bg is None:
            try: bg = parent.cget('bg')
            except Exception:
                try: bg = parent.cget('background')
                except Exception: bg = '#FFFFFF'
        super().__init__(parent, bg=bg, bd=0, highlightthickness=0, **kwargs)
        self._fill = fill
        self._border = border
        self._radius = radius
        self._canvas = tk.Canvas(self, bg=self.cget('bg'), highlightthickness=0, bd=0)
        self._canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._canvas.lower('all')
        self.bind('<Configure>', self._redraw)
        if padding:
            self.configure(padx=padding, pady=padding)

    def set_style(self, fill=None, border=None, bg=None):
        if fill is not None:
            self._fill = fill
        if border is not None:
            self._border = border
        if bg is not None:
            self.configure(bg=bg)
            self._canvas.configure(bg=bg)
        self._redraw()

    def _hex_to_rgb(self, color):
        color = str(color).strip()
        if color.startswith('#') and len(color) == 7:
            return tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
        return (255, 255, 255)

    def _rgb_to_hex(self, rgb):
        return '#%02x%02x%02x' % tuple(max(0, min(255, int(v))) for v in rgb)

    def _interpolate(self, c1, c2, t):
        a = self._hex_to_rgb(c1)
        b = self._hex_to_rgb(c2)
        return self._rgb_to_hex(tuple(a[i] + (b[i] - a[i]) * t for i in range(3)))

    def _draw_gradient(self, c, w, h, r):
        import math
        top, bottom = self._fill
        denom = max(h - 1, 1)
        for y in range(h):
            t = y / denom
            color = self._interpolate(top, bottom, t)
            if y < r:
                dy = r - y
                dx = r - math.sqrt(max(r*r - dy*dy, 0))
            elif y >= h - r:
                dy = y - (h - r - 1)
                dx = r - math.sqrt(max(r*r - dy*dy, 0))
            else:
                dx = 0
            x1 = dx
            x2 = w - dx
            c.create_line(x1, y, x2, y, fill=color)

    def _draw_solid(self, c, w, h, r, fill):
        c.create_rectangle(r,0,w-r,h,fill=fill,outline='')
        c.create_rectangle(0,r,w,h-r,fill=fill,outline='')
        c.create_arc(0,0,2*r,2*r,start=90,extent=90,fill=fill,outline=fill)
        c.create_arc(w-2*r,0,w,2*r,start=0,extent=90,fill=fill,outline=fill)
        c.create_arc(0,h-2*r,2*r,h,start=180,extent=90,fill=fill,outline=fill)
        c.create_arc(w-2*r,h-2*r,w,h,start=270,extent=90,fill=fill,outline=fill)

    def _redraw(self, _event=None):
        c=self._canvas; c.delete('all')
        w=max(self.winfo_width(),2); h=max(self.winfo_height(),2); r=min(self._radius, w//2, h//2)
        try:
            from PIL import Image, ImageDraw, ImageTk
            scale=4
            sw,sh=w*scale,h*scale
            im=Image.new('RGBA',(sw,sh),(0,0,0,0))
            d=ImageDraw.Draw(im)
            if isinstance(self._fill,(tuple,list)) and len(self._fill)>=2:
                top,bottom=self._fill
                def rgb(v):
                    v=str(v).lstrip('#'); return tuple(int(v[i:i+2],16) for i in (0,2,4))
                a,b=rgb(top),rgb(bottom)
                for yy in range(sh):
                    t=yy/max(sh-1,1)
                    col=tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))+(255,)
                    d.line((0,yy,sw,yy),fill=col)
                # Mask to rounded silhouette.
                mask=Image.new('L',(sw,sh),0); md=ImageDraw.Draw(mask)
                md.rounded_rectangle((0,0,sw-1,sh-1),radius=r*scale,fill=255)
                im.putalpha(mask)
            else:
                d.rounded_rectangle((0,0,sw-1,sh-1),radius=r*scale,fill=self._fill)
            if self._border:
                d.rounded_rectangle((scale,scale,sw-scale-1,sh-scale-1),radius=max(1,r*scale-scale),outline=self._border,width=scale)
            im=im.resize((w,h),Image.Resampling.LANCZOS)
            self._img_ref=ImageTk.PhotoImage(im)
            c.create_image(0,0,image=self._img_ref,anchor='nw')
        except Exception:
            if isinstance(self._fill,(tuple,list)):
                self._draw_solid(c,w,h,r,self._fill[0])
            else:
                self._draw_solid(c,w,h,r,self._fill)
            if self._border:
                c.create_rectangle(0,0,w-1,h-1,outline=self._border,width=1)


class PillScrollbar(tk.Canvas):
    def __init__(self, parent, tree, **kwargs):
        super().__init__(parent, height=8, bg=parent.cget('bg'), bd=0, highlightthickness=0, **kwargs)
        self.tree = tree
        self.tree.configure(xscrollcommand=self._on_scroll)
        self.bind('<Configure>', self._redraw)
        self.bind('<ButtonPress-1>', self._on_press)
        self.bind('<B1-Motion>', self._on_drag)
        self._pos = (0.0, 1.0)
        self._drag_data = {'x': 0, 'start_pos': 0.0}
        # Start hidden — do NOT pack yet

    def _on_scroll(self, first, last):
        first, last = float(first), float(last)
        self._pos = (first, last)
        if first <= 0.001 and last >= 0.999:
            if self.winfo_ismapped():
                self.pack_forget()
        else:
            if not self.winfo_ismapped():
                self.pack(side='bottom', fill='x', pady=(0, 4), padx=20)
            self.tk.call('raise', self._w)
        self._redraw()

    def _redraw(self, e=None):
        w, h = self.winfo_width(), self.winfo_height()
        if w < 10: return
        self.delete('all')
        first, last = self._pos
        if first <= 0.001 and last >= 0.999: return
        r = h / 2
        x1 = max(r, first * w)
        x2 = min(w - r, last * w)
        if x2 - x1 < 20:
            mid = (x1 + x2) / 2
            x1, x2 = mid - 10, mid + 10
            x1 = max(r, x1)
            x2 = min(w - r, max(x1+20, x2))
        self.create_line(x1, h / 2, x2, h / 2, fill='#A0ABB9', width=h, capstyle='round')

    def _on_press(self, e):
        w = self.winfo_width()
        first, last = self._pos
        x1 = first * w; x2 = last * w
        if x1 <= e.x <= x2:
            self._drag_data['x'] = e.x
            self._drag_data['start_pos'] = first
        else:
            new_first = max(0.0, min(1.0 - (last-first), (e.x / w) - (last-first)/2))
            self.tree.xview_moveto(new_first)

    def _on_drag(self, e):
        w = self.winfo_width(); dx = e.x - self._drag_data['x']; first, last = self._pos
        delta_pos = dx / w
        new_first = max(0.0, min(1.0 - (last-first), self._drag_data['start_pos'] + delta_pos))
        self.tree.xview_moveto(new_first)

    def _on_drag(self, e):
        w = self.winfo_width()
        dx = e.x - self._drag_data['x']
        first, last = self._pos
        delta_pos = dx / w
        new_first = max(0.0, min(1.0 - (last-first), self._drag_data['start_pos'] + delta_pos))
        self.tree.xview_moveto(new_first)

class RoundedActionButton(tk.Frame):
    """Botão cápsula com renderização antialias e ícones vetoriais leves."""
    def __init__(self,parent,text,command,width=150,height=42,fill='#2F67B1',hover='#255894',fg='#FFFFFF',font=('Segoe UI',10,'bold'),**kwargs):
        super().__init__(parent,bg=parent.cget('bg'),bd=0,highlightthickness=0,width=width,height=height,cursor='hand2',**kwargs)
        self.pack_propagate(False); self._fill=fill; self._hover=hover; self._fg=fg; self._text=text; self._command=command; self._font=font
        self._canvas=tk.Canvas(self,bg=self.cget('bg'),bd=0,highlightthickness=0); self._canvas.pack(fill='both',expand=True)
        self._img_ref=None; self._icon=self._detect_icon(text); self._label=self._clean_text(text)
        self.bind('<Configure>',lambda e:self._redraw())
        for w in (self,self._canvas):
            w.bind('<Enter>',self._on_enter); w.bind('<Leave>',self._on_leave); w.bind('<Button-1>',self._click)
        self.after_idle(self._redraw)

    def _detect_icon(self,text):
        if '+' in text: return 'plus'
        if '<clock>' in text: return 'clock'
        if '<convert>' in text: return 'convert'
        if '<delete>' in text: return 'delete'
        return None

    def _clean_text(self,text):
        for token in ('+', '<clock>', '<convert>', '<delete>'):
            text = text.replace(token, '')
        return ' '.join(text.split())

    def _make(self,fill):
        try:
            from PIL import Image,ImageDraw,ImageTk
            w=max(2,self.winfo_width()); h=max(2,self.winfo_height()); scale=4
            im=Image.new('RGBA',(w*scale,h*scale),(0,0,0,0)); d=ImageDraw.Draw(im)
            d.rounded_rectangle((scale,scale,w*scale-scale-1,h*scale-scale-1),radius=(h*scale)//2,fill=fill)
            im=im.resize((w,h),Image.Resampling.LANCZOS); return ImageTk.PhotoImage(im)
        except Exception:return None

    def _draw_icon(self,kind,cx,cy,col):
        w=1.8
        if kind=='plus':
            self._canvas.create_line(cx-7,cy,cx+7,cy,fill=col,width=w,capstyle='round')
            self._canvas.create_line(cx,cy-7,cx,cy+7,fill=col,width=w,capstyle='round')
        elif kind=='clock':
            self._canvas.create_oval(cx-7,cy-7,cx+7,cy+7,outline=col,width=w)
            self._canvas.create_line(cx,cy,cx,cy-4.5,fill=col,width=w,capstyle='round')
            self._canvas.create_line(cx,cy,cx+4,cy+2.5,fill=col,width=w,capstyle='round')
        elif kind=='convert':
            self._canvas.create_line(cx-8,cy-3,cx+6,cy-3,fill=col,width=w,capstyle='round')
            self._canvas.create_line(cx+3,cy-6,cx+6,cy-3,cx+3,cy,fill=col,width=w,capstyle='round',joinstyle='round')
            self._canvas.create_line(cx+8,cy+3,cx-6,cy+3,fill=col,width=w,capstyle='round')
            self._canvas.create_line(cx-3,cy,cx-6,cy+3,cx-3,cy+6,fill=col,width=w,capstyle='round',joinstyle='round')

    def _redraw(self):
        self._canvas.delete('all')
        img=self._make(self._fill); self._img_ref=img
        if img:self._canvas.create_image(0,0,image=img,anchor='nw')
        w=max(2,self.winfo_width()); h=max(2,self.winfo_height()); cy=h/2
        # Centraliza o conjunto ícone + texto como um único bloco.
        # Isso evita a sobreposição que ocorria especialmente em
        # "Conversões do item", mantendo o visual da referência.
        if self._icon:
            try:
                text_w=self._font.measure(self._label)
            except Exception:
                text_w=max(40,len(self._label)*7)
            icon_w=16
            gap=10
            group_w=icon_w+gap+text_w
            start=max(0,(w-group_w)/2)
            self._draw_icon(self._icon,start+icon_w/2,cy,self._fg)
            self._canvas.create_text(start+icon_w+gap,cy,text=self._label,fill=self._fg,font=self._font,anchor='w')
        else:
            self._canvas.create_text(w/2,cy,text=self._label,fill=self._fg,font=self._font,anchor='center')

    def _on_enter(self,e): self._fill0=self._fill; self._fill=self._hover; self._redraw()
    def _on_leave(self,e): self._fill=getattr(self,'_fill0',self._fill); self._redraw()
    def _click(self,e=None): self._command()


class RoundedEntry(tk.Frame):
    def __init__(self,parent,textvariable,width=280,height=40,placeholder='Pesquisar',**kwargs):
        super().__init__(parent,bg=parent.cget('bg'),bd=0,highlightthickness=0,width=width,height=height,**kwargs)
        self.pack_propagate(False); self.grid_propagate(False)
        self.config(width=width, height=height)
        self._bg='#FFFFFF'; self._line='#E2EAF5'; self._placeholder=placeholder
        self._canvas=tk.Canvas(self,bg=self.cget('bg'),bd=0,highlightthickness=0); self._canvas.place(relwidth=1,relheight=1)
        self.entry=tk.Entry(self,textvariable=textvariable,bg=self._bg,fg='#18223A',insertbackground='#18223A',relief='flat',bd=0,highlightthickness=0,font=('Segoe UI',10))
        self.entry.place(x=42,rely=.5,anchor='w',relwidth=1,width=-56,relheight=.56)
        self._var=textvariable
        self._var.trace_add('write',lambda *a:self._update_placeholder())
        self.entry.bind('<FocusIn>',lambda e:self._update_placeholder())
        self.entry.bind('<FocusOut>',lambda e:self._update_placeholder())
        self.bind('<Button-1>',lambda e:self.entry.focus_set())
        self._canvas.bind('<Button-1>',lambda e:self.entry.focus_set())
        self.bind('<Configure>',lambda e:self._redraw())
        self.after_idle(self._redraw)

    def _update_placeholder(self):
        if not hasattr(self,'_placeholder_label'): return
        show = (not self._var.get()) and (self.focus_get() != self.entry)
        self._placeholder_label.place_forget() if not show else self._placeholder_label.place(x=42,rely=.5,anchor='w')

    def _redraw(self):
        w=self.winfo_width(); h=self.winfo_height(); r=h/2
        if w < 10: return
        self._canvas.delete('all')
        try:
            from PIL import Image,ImageDraw,ImageTk
            scale=4; im=Image.new('RGBA',(w*scale,h*scale),(0,0,0,0)); d=ImageDraw.Draw(im)
            d.rounded_rectangle((scale,scale,w*scale-scale,h*scale-scale),radius=r*scale,fill=self._bg,outline=self._line,width=scale)
            im=im.resize((w,h),Image.Resampling.LANCZOS); self._img=ImageTk.PhotoImage(im); self._canvas.create_image(0,0,image=self._img,anchor='nw')
        except Exception:
            pass
        self._canvas.create_oval(14, 12, 24, 22, outline='#9AA9BF', width=2)
        self._canvas.create_line(22, 20, 27, 25, fill='#9AA9BF', width=2, capstyle='round')
        if not hasattr(self,'_placeholder_label'):
            self._placeholder_label=tk.Label(self,text=self._placeholder,bg=self._bg,fg='#9AA9BF',font=('Segoe UI',10))
            self._update_placeholder()


class SidebarIcon(tk.Canvas):
    """Ícones vetoriais desenhados para ficar mais próximos do layout de referência."""
    def __init__(self, parent, kind, color='#FFFFFF', bg='#17181C', size=42, **kwargs):
        super().__init__(parent, width=size, height=size, bg=bg, highlightthickness=0, bd=0, **kwargs)
        self.kind=kind; self.color=color; self.size=size
        self._draw()

    def set_style(self, color=None, bg=None):
        if color is not None:
            self.color=color
        if bg is not None:
            self.configure(bg=bg)
        self._draw()

    def _rounded_rect(self, x1, y1, x2, y2, r, outline, width=2.8):
        self.create_line(x1+r, y1, x2-r, y1, fill=outline, width=width, capstyle='round')
        self.create_line(x1+r, y2, x2-r, y2, fill=outline, width=width, capstyle='round')
        self.create_line(x1, y1+r, x1, y2-r, fill=outline, width=width, capstyle='round')
        self.create_line(x2, y1+r, x2, y2-r, fill=outline, width=width, capstyle='round')
        self.create_arc(x1, y1, x1+2*r, y1+2*r, start=90, extent=90, style='arc', outline=outline, width=width)
        self.create_arc(x2-2*r, y1, x2, y1+2*r, start=0, extent=90, style='arc', outline=outline, width=width)
        self.create_arc(x1, y2-2*r, x1+2*r, y2, start=180, extent=90, style='arc', outline=outline, width=width)
        self.create_arc(x2-2*r, y2-2*r, x2, y2, start=270, extent=90, style='arc', outline=outline, width=width)

    def _draw(self):
        import math
        c=self
        c.delete('all')
        col=self.color
        cx=self.size/2
        cy=self.size/2
        stroke=2.9
        line=dict(fill=col,width=stroke,capstyle='round',joinstyle='round')
        if self.kind=='home':
            c.create_line(cx-13, cy-2, cx, cy-14, cx+13, cy-2, **line)
            self._rounded_rect(cx-10, cy-3, cx+10, cy+13, 4, col, stroke)
            c.create_line(cx-3.5, cy+13, cx-3.5, cy+5, cx+3.5, cy+5, cx+3.5, cy+13, **line)
        elif self.kind=='cadastro':
            self._rounded_rect(cx-10, cy-13, cx+11, cy+13, 3.8, col, stroke)
            c.create_polygon(cx+4, cy-13, cx+11, cy-13, cx+11, cy-6, fill='', outline=col, width=stroke, joinstyle='round')
            c.create_line(cx-5, cy-6, cx+2, cy-6, **line)
            c.create_line(cx-5, cy, cx+2, cy, **line)
            c.create_line(cx-5, cy+6, cx+1, cy+6, **line)
            c.create_line(cx+4, cy+4, cx+7, cy+7, **line)
            c.create_line(cx+7, cy+7, cx+12, cy, **line)
        elif self.kind=='recipe':
            c.create_line(cx-10, cy-12, cx-10, cy-7, **line)
            c.create_line(cx, cy-12, cx, cy-7, **line)
            c.create_line(cx+10, cy-12, cx+10, cy-7, **line)
            c.create_line(cx-13, cy-7, cx+13, cy-7, **line)
            self._rounded_rect(cx-14, cy-7, cx+14, cy+9, 4, col, stroke)
            c.create_arc(cx-10, cy-3, cx-2, cy+5, start=180, extent=180, style='arc', outline=col, width=stroke)
            c.create_arc(cx-4, cy-3, cx+4, cy+5, start=180, extent=180, style='arc', outline=col, width=stroke)
            c.create_arc(cx+2, cy-3, cx+10, cy+5, start=180, extent=180, style='arc', outline=col, width=stroke)
        elif self.kind=='product':
            c.create_arc(cx-13, cy-10, cx+13, cy+6, start=180, extent=180, style='arc', outline=col, width=stroke)
            c.create_arc(cx-9, cy-14, cx+1, cy-2, start=180, extent=180, style='arc', outline=col, width=stroke)
            c.create_arc(cx-1, cy-14, cx+9, cy-2, start=180, extent=180, style='arc', outline=col, width=stroke)
            c.create_arc(cx+7, cy-11, cx+15, cy-1, start=180, extent=180, style='arc', outline=col, width=stroke)
            c.create_line(cx-12, cy-2, cx+12, cy-2, **line)
            c.create_polygon(cx-10, cy-1, cx+10, cy-1, cx+7, cy+12, cx-7, cy+12, fill='', outline=col, width=stroke, joinstyle='round')
            c.create_line(cx-4, cy+1, cx-1, cy+11, **line)
            c.create_line(cx+4, cy+1, cx+1, cy+11, **line)
        elif self.kind=='settings':
            pts=[]
            for i in range(16):
                ang=math.radians(i*22.5 - 90)
                radius=14 if i % 2 == 0 else 10.5
                pts.extend((cx + radius*math.cos(ang), cy + radius*math.sin(ang)))
            c.create_polygon(pts, fill='', outline=col, width=stroke, joinstyle='round')
            c.create_oval(cx-6, cy-6, cx+6, cy+6, outline=col, width=stroke)
            c.create_oval(cx-1.6, cy-1.6, cx+1.6, cy+1.6, fill=col, outline=col)


class NavItem(tk.Frame):
    """Item de navegação com botão grande, arredondado e sombreamento discreto."""
    def __init__(self, parent, icon_kind, text, command, icon_color, sidebar_bg='#17181C', **kwargs):
        super().__init__(parent, bg=sidebar_bg, bd=0, highlightthickness=0, cursor='hand2', **kwargs)
        self._sidebar_bg=sidebar_bg
        self._tile_normal=('#435CFA', '#5139E8')
        self._tile_hover=('#556BFF', '#5B41EF')
        self._tile_active=('#8B75FF', '#725CF7')
        self._border_normal='#5C66FF'
        self._border_hover='#7482FF'
        self._border_active='#9C8CFF'
        self._shadow_normal='#18255A'
        self._shadow_active='#1A1956'
        self._icon_color=icon_color
        self._text=text
        self._command=command
        self._tooltip=None
        self._active=False
        self.configure(width=88,height=96)
        self.pack_propagate(False)
        self.shadow=RoundedPanel(self, fill=self._shadow_normal, border='', radius=19, bg=sidebar_bg)
        self.shadow.place(relx=.5, rely=.5, anchor='center', x=3, y=4, width=72, height=72)
        self.tile=RoundedPanel(self, fill=self._tile_normal, border=self._border_normal, radius=19, bg=sidebar_bg)
        self.tile.place(relx=.5, rely=.5, anchor='center', width=72, height=72)
        self.icon=SidebarIcon(self.tile, icon_kind, color='#FFFFFF', bg='#4F48EF', size=44)
        self.icon.place(relx=.5, rely=.5, anchor='center')
        for w in (self, self.tile, self.tile._canvas, self.icon):
            w.bind('<Button-1>', self._click)
            w.bind('<Enter>', self._enter)
            w.bind('<Leave>', self._leave)

    def _click(self,_event=None):
        self._command()

    def _fill_center(self, fill):
        if isinstance(fill, (tuple, list)) and fill:
            return fill[0]
        return fill

    def _apply_state(self, fill, border, shadow):
        self.configure(bg=self._sidebar_bg)
        self.shadow.set_style(fill=shadow, bg=self._sidebar_bg)
        self.tile.set_style(fill=fill, border=border, bg=self._sidebar_bg)
        self.icon.set_style(color='#FFFFFF', bg=self._fill_center(fill))

    def _enter(self,_event=None):
        if not self._active:
            self._apply_state(self._tile_hover, self._border_hover, self._shadow_normal)
        self.after(180,self._show_tooltip)

    def _leave(self,_event=None):
        try:
            x,y=self.winfo_pointerxy(); target=self.winfo_containing(x,y)
            if target in (self, self.tile, self.tile._canvas, self.icon):
                return
        except Exception:
            pass
        self._hide_tooltip()
        if not self._active:
            self.set_active(False)

    def _show_tooltip(self):
        if not self.winfo_exists() or self._tooltip is not None:
            return
        try:
            x,y=self.winfo_pointerxy(); w=self.winfo_containing(x,y)
            if w not in (self, self.tile, self.tile._canvas, self.icon):
                return
        except Exception:
            pass
        tip = tk.Toplevel(self)
        tip.wm_overrideredirect(True)
        tip.attributes('-topmost', True)
        try: tip.attributes('-transparentcolor', '#FF00FF')
        except: pass
        tip.configure(bg='#FF00FF')
        
        tx = int(self.winfo_rootx() + self.winfo_width() + 2)
        ty = int(self.winfo_rooty() + max(0, (self.winfo_height() - 32) // 2))
        
        tip_w = len(self._text) * 8 + 24
        tip_h = 32
        tip.geometry(f'{tip_w}x{tip_h}+{tx}+{ty}')
        
        from PIL import Image, ImageDraw, ImageTk, ImageFont
        
        mask = Image.new('1', (tip_w, tip_h), 0)
        md = ImageDraw.Draw(mask)
        md.rounded_rectangle((0, 0, tip_w-1, tip_h-1), radius=14, fill=1)
        
        capsule = Image.new('RGBA', (tip_w, tip_h), '#101A33')
        cd = ImageDraw.Draw(capsule)
        
        try:
            fnt = ImageFont.truetype('segoeuib.ttf', 12)
        except Exception:
            try:
                fnt = ImageFont.truetype('arialbd.ttf', 12)
            except Exception:
                fnt = ImageFont.load_default()
                
        cd.text((tip_w/2, tip_h/2 - 1), self._text, fill='#FFFFFF', font=fnt, anchor='mm')
        
        im = Image.new('RGBA', (tip_w, tip_h), '#FF00FF')
        im.paste(capsule, (0, 0), mask)
        
        img_tk = ImageTk.PhotoImage(im)
        
        lbl = tk.Label(tip, image=img_tk, bg='#FF00FF', bd=0, highlightthickness=0)
        lbl.image = img_tk
        lbl.pack(fill='both', expand=True)
        self._tooltip = tip

    def _hide_tooltip(self, event=None):
        if getattr(self, '_tooltip', None):
            try:
                if isinstance(self._tooltip, tk.Toplevel):
                    self._tooltip.destroy()
                else:
                    self._tooltip.place_forget()
                    self._tooltip.destroy()
            except Exception: pass
            self._tooltip=None

    def set_active(self,active):
        self._active=active
        if active:
            self._apply_state(self._tile_active, self._border_active, self._shadow_active)
        else:
            self._apply_state(self._tile_normal, self._border_normal, self._shadow_normal)



class ReferenceSidebar(tk.Canvas):
    """Sidebar flutuante em formato de cápsula, reproduzindo a referência visual."""
    def __init__(self, parent, command, app_bg='#F4F7FC', dark_theme=False, **kwargs):
        super().__init__(parent, bg=app_bg, bd=0, highlightthickness=0, cursor='arrow', **kwargs)
        self._command=command; self._app_bg=app_bg; self._dark=dark_theme; self._active='Geral'; self._hover=None
        self._image_refs={}; self._button_items={}
        self._asset_slug={'Geral':'home','Cadastro':'cadastro','Receitas':'receitas','Produtos':'produtos','Configurações':'settings'}
        self._labels={'Geral':'Início','Cadastro':'Cadastro','Receitas':'Receitas','Produtos':'Produtos','Configurações':'Configurações'}
        self.bind('<Configure>', lambda e:self._redraw())
        self.bind('<Motion>', self._on_motion); self.bind('<Leave>', self._on_leave); self.bind('<Button-1>', self._on_click)
        self._load_assets()

    def _load_photo(self, filename):
        p=UI_ASSETS/filename
        try:
            from PIL import Image, ImageTk
            im=Image.open(p).convert('RGBA')
            if filename in ('home.png','cadastro.png','receitas.png','produtos.png','settings.png'):
                max_side=42
                scale=min(max_side/im.width,max_side/im.height,1.0)
                if scale < 1.0:
                    im=im.resize((max(1,int(im.width*scale)),max(1,int(im.height*scale))),Image.Resampling.LANCZOS)
            img=ImageTk.PhotoImage(im); self._image_refs[filename]=img; return img
        except Exception:
            try:
                img=tk.PhotoImage(file=str(p)); self._image_refs[filename]=img; return img
            except Exception:
                return None

    def _load_assets(self):
        self._buttons={k:self._load_photo(f'{slug}.png') for k,slug in self._asset_slug.items()}

    def _draw_pil_shape(self, x, y, w, h, radius, fill, outline='', line_width=1, tag='', blur=0):
        from PIL import Image, ImageDraw, ImageTk, ImageFilter
        scale = 4
        
        if blur > 0:
            pad = blur * 2
            sw, sh = int((w + pad*2) * scale), int((h + pad*2) * scale)
            def hex_to_rgba(h_str, alpha=0):
                h_str = h_str.lstrip('#')
                return tuple(int(h_str[i:i+2], 16) for i in (0, 2, 4)) + (alpha,)
            
            im = Image.new('RGBA', (sw, sh), hex_to_rgba(fill, 0))
            d = ImageDraw.Draw(im)
            r = int(radius * scale)
            d.rounded_rectangle((pad*scale, pad*scale, sw - pad*scale - 1, sh - pad*scale - 1), radius=r, fill=fill)
            im = im.filter(ImageFilter.GaussianBlur(blur * scale))
            im = im.resize((int(w + pad*2), int(h + pad*2)), Image.Resampling.LANCZOS)
            img_tk = ImageTk.PhotoImage(im)
            self._image_refs[f"shape_{tag}_{x}_{y}_{w}_{h}_{fill}"] = img_tk
            self.create_image(x - pad, y - pad, image=img_tk, anchor='nw', tags=tag)
        else:
            sw, sh = int(w * scale), int(h * scale)
            im = Image.new('RGBA', (sw, sh), (0,0,0,0))
            d = ImageDraw.Draw(im)
            r = int(radius * scale)
            if outline:
                lw = int(line_width * scale)
                d.rounded_rectangle((lw/2, lw/2, sw - lw/2 - 1, sh - lw/2 - 1), radius=r, fill=fill, outline=outline, width=lw)
            else:
                d.rounded_rectangle((0, 0, sw - 1, sh - 1), radius=r, fill=fill)
            
            im = im.resize((int(w), int(h)), Image.Resampling.LANCZOS)
            img_tk = ImageTk.PhotoImage(im)
            self._image_refs[f"shape_{tag}_{x}_{y}_{w}_{h}_{fill}"] = img_tk
            self.create_image(x, y, image=img_tk, anchor='nw', tags=tag)

    def _get_centers(self):
        W=max(self.winfo_width(),150); H=max(self.winfo_height(),650)
        y=188
        bottom = H - 32
        h=max(300,bottom-y)
        if h > 540:
            spacing = (h - 130) / 4
            return [y + 65 + i * spacing for i in range(5)]
        else:
            return [y+65, y+170, y+275, y+380, y+485]

    def _redraw(self):
        self.delete('all'); self._button_items.clear()
        self._image_refs = {}
        H=max(self.winfo_height(),650)
        
        # O espaçamento fixo na esquerda do Nexo é 150px
        available_w = 150
        side_w = 68
        x = (available_w - side_w) // 2
        y = 188
        bottom = H - 32
        h=max(300,bottom-y); r=side_w/2
        sidebar='#111C30' if not self._dark else '#F28C28'
        shadow='#D8E1EE' if not self._dark else '#0A0A0A'
        outline='#A9BFE0' if not self._dark else '#F6A24B'
        
        self._draw_pil_shape(x, y+4, side_w, h, r, shadow, tag='shadow', blur=6)
        self._draw_pil_shape(x, y, side_w, h, r, sidebar, outline=outline, line_width=1, tag='sidebar')
        
        centers = self._get_centers()
        for key,cy in zip(self._asset_slug.keys(),centers):
            if key==self._active:
                sel_w = side_w - 24
                sel_h = 60
                sel_r = 20
                sel_fill = '#304763' if not self._dark else '#F6A45A'
                self._draw_pil_shape(x+12, cy-sel_h/2, sel_w, sel_h, sel_r, sel_fill, tag='selection')
            img=self._buttons.get(key)
            if img:
                item=self.create_image(x+side_w/2,cy,image=img,anchor='center',tags=('nav',key))
                self._button_items[key]=item

    def _hit_key(self,x,y):
        W=max(self.winfo_width(),150); H=max(self.winfo_height(),650)
        side_w=min(68, max(64, int(W*0.055))); sx=29 if W>=600 else 8
        if not (sx <= x <= sx+side_w): return None
        centers = self._get_centers()
        for key,cy in zip(self._asset_slug.keys(), centers):
            if abs(y-cy)<=42: return key
        return None

    def _on_click(self,event):
        key=self._hit_key(event.x,event.y)
        if key: self._command(key)

    def _on_motion(self,event):
        key=self._hit_key(event.x,event.y)
        if key != self._hover:
            self._hover=key
            self.configure(cursor='hand2' if key else 'arrow')
            if key:
                self._show_tooltip(key, event)
            else:
                self._hide_tooltip()

    def _on_leave(self,event):
        self._hover=None; self.configure(cursor='arrow')
        self._hide_tooltip()

    def _show_tooltip(self, key, event):
        self._hide_tooltip()
        labels={'Geral':'Início','Cadastro':'Cadastro','Receitas':'Receitas','Produtos':'Produtos','Configurações':'Configurações'}
        text = labels.get(key, key)
        
        available_w = 150
        side_w = 68
        x = (available_w - side_w) // 2
        
        centers_map=dict(zip(self._asset_slug.keys(), self._get_centers()))
        cy = centers_map.get(key, event.y)

        tip = tk.Toplevel(self)
        tip.wm_overrideredirect(True)
        tip.attributes('-topmost', True)
        try: tip.attributes('-transparentcolor', '#FF00FF')
        except: pass
        tip.configure(bg='#FF00FF')
        
        tx = int(self.winfo_rootx() + x + side_w + 2)
        ty = int(self.winfo_rooty() + cy - 16)
        
        tip_w = len(text) * 8 + 24
        tip_h = 32
        tip.geometry(f'{tip_w}x{tip_h}+{tx}+{ty}')
        
        from PIL import Image, ImageDraw, ImageTk, ImageFont
        
        mask = Image.new('1', (tip_w, tip_h), 0)
        md = ImageDraw.Draw(mask)
        md.rounded_rectangle((0, 0, tip_w-1, tip_h-1), radius=14, fill=1)
        
        fill_c = '#101A33' if not self._dark else '#2A3B5C'
        capsule = Image.new('RGBA', (tip_w, tip_h), fill_c)
        cd = ImageDraw.Draw(capsule)
        
        try:
            fnt = ImageFont.truetype('segoeuib.ttf', 12)
        except Exception:
            try:
                fnt = ImageFont.truetype('arialbd.ttf', 12)
            except Exception:
                fnt = ImageFont.load_default()
                
        cd.text((tip_w/2, tip_h/2 - 1), text, fill='#FFFFFF', font=fnt, anchor='mm')
        
        im = Image.new('RGBA', (tip_w, tip_h), '#FF00FF')
        im.paste(capsule, (0, 0), mask)
        
        img_tk = ImageTk.PhotoImage(im)
        
        lbl = tk.Label(tip, image=img_tk, bg='#FF00FF', bd=0, highlightthickness=0)
        lbl.image = img_tk
        lbl.pack(fill='both', expand=True)
        self._tooltip_win = tip

    def _hide_tooltip(self):
        if getattr(self, '_tooltip_win', None):
            try:
                if isinstance(self._tooltip_win, tk.Toplevel):
                    self._tooltip_win.destroy()
                else:
                    self._tooltip_win.place_forget()
                    self._tooltip_win.destroy()
            except Exception: pass
            self._tooltip_win=None

    def set_active(self,key):
        self._active=key; self._redraw()

    def set_theme(self,dark,app_bg):
        self._dark=dark; self._app_bg=app_bg; self.configure(bg=app_bg); self._redraw()

    def set_brand(self,name):
        pass


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Nexo')
        self.geometry('1280x800')
        self.minsize(1080, 650)
        self._set_icon()
        self.style = ttk.Style(self)
        try:
            self.style.theme_use('clam')
        except Exception:
            pass
        self._build_styles()
        # O status do banco é usado pela página Configurações durante a
        # construção do shell; ele precisa existir antes dos builders das páginas.
        self.status = tk.StringVar(value='')
        self._build_shell()
        self._bind_combobox_full_click()
        self._apply_theme()
        self.refresh_all()

    def _set_icon(self):
        try:
            if ICON_ICO.exists():
                self.iconbitmap(str(ICON_ICO))
            if ICON_PNG.exists():
                self.icon_img = tk.PhotoImage(file=str(ICON_PNG))
                self.iconphoto(True, self.icon_img)
        except Exception:
            pass

    def _build_styles(self):
        # Estilos base; a paleta completa é aplicada em _build_shell/_apply_theme.
        self.style.configure('TButton', padding=(12, 8), font=('Segoe UI', 10, 'bold'))
        self.style.configure('Treeview', rowheight=32, font=('Segoe UI', 9))
        self.style.configure('TLabelframe', padding=10)
        self.style.configure('Header.TLabel', font=('Segoe UI', 19, 'bold'))
        self.style.configure('SubHeader.TLabel', font=('Segoe UI', 10))
        self.style.configure('Card.TLabelframe', padding=14)

    def _build_shell(self):
        theme = get_setting('theme','light')
        dark = theme == 'dark'
        if dark:
            self.colors = {
                'bg':'#081226', 'bg_alt':'#0B1730', 'panel':'#111F3B', 'panel_alt':'#142544',
                'text':'#F4F7FF', 'muted':'#93A4C6', 'accent':'#F28C28', 'accent_dark':'#D96F0B',
                'accent_soft':'#5A3518', 'line':'#24385E', 'field':'#0E1B35',
                'blue':'#2F72FF', 'cyan':'#18C39B', 'green':'#22C79A',
                'orange':'#F5A524', 'pink':'#9C5CFF', 'red':'#FF5E74',
                'sidebar':'#F28C28', 'sidebar_soft':'#C85A08', 'cream':'#FFF7EA'
            }
        else:
            self.colors = {
                'bg':'#F4F7FC', 'bg_alt':'#EEF3FA', 'panel':'#FFFFFF', 'panel_alt':'#F8FAFD',
                'text':'#18223A', 'muted':'#687796', 'accent':'#F28C28', 'accent_dark':'#D96F0B',
                'accent_soft':'#FFF0D8', 'line':'#DDE5F2', 'field':'#FFFFFF',
                'blue':'#2F72FF', 'cyan':'#18A98A', 'green':'#1FAE88',
                'orange':'#F5A524', 'pink':'#9C5CFF', 'red':'#D94B3D',
                'sidebar':'#17181C', 'sidebar_soft':'#101116', 'cream':'#FFF7EA'
            }
        bg=self.colors['bg']; panel=self.colors['panel']; fg=self.colors['text']; muted=self.colors['muted']
        self.configure(bg=bg)
        self.style.configure('TFrame', background=bg)
        self.style.configure('TLabel', background=bg, foreground=fg, font=('Segoe UI',10))
        self.style.configure('Title.TLabel', background=bg, foreground=fg, font=('Segoe UI',22,'bold'))
        self.style.configure('Sub.TLabel', background=bg, foreground=muted, font=('Segoe UI',10))
        btn_bg='#172746' if dark else '#EEF2F7'; btn_fg='#DDE6FF' if dark else '#25324A'; btn_active='#20375F' if dark else '#E2E8F0'
        self.style.configure('TButton', background=btn_bg, foreground=btn_fg, padding=(12,8), font=('Segoe UI',10,'bold'), relief='flat', borderwidth=0)
        self.style.map('TButton', background=[('active',btn_active),('pressed','#2A3F6A' if dark else '#D7DEE9')], foreground=[('disabled','#66789C'),('active','#FFFFFF' if dark else '#18223A')])
        self.style.configure('Primary.TButton', background=self.colors['accent'], foreground='#FFFFFF', padding=(15,9), font=('Segoe UI',10,'bold'), relief='flat', borderwidth=0)
        self.style.configure('Soft.TButton', background='#EFF4FB', foreground='#1D3557', padding=(13,9), font=('Segoe UI',10,'bold'), relief='flat', borderwidth=0)
        self.style.configure('Toolbar.TButton', background='#EFF4FB', foreground='#1D3557', padding=(13,9), font=('Segoe UI',10,'bold'), relief='flat', borderwidth=0)
        self.style.map('Primary.TButton', background=[('active',self.colors['accent_dark']),('pressed','#C75F08')], foreground=[('active','#FFFFFF')])
        self.style.configure('ActionEdit.TButton', background=btn_bg, foreground=self.colors['accent'], relief='flat', padding=(5,4), font=('Segoe UI Emoji',11,'bold'))
        self.style.configure('ActionDelete.TButton', background=btn_bg, foreground=self.colors['red'], relief='flat', padding=(5,4), font=('Segoe UI Emoji',11,'bold'))
        self.style.configure('Treeview', rowheight=38, font=('Segoe UI',10), background=self.colors['field'], fieldbackground=self.colors['field'], foreground=fg, borderwidth=0, relief='flat')
        self.style.layout('Treeview', [('Treeview.treearea', {'sticky': 'nswe'})])
        self.style.configure('Treeview.Heading', font=('Segoe UI',9,'bold'), background=(self.colors['bg_alt'] if not dark else '#142544'), foreground=(self.colors['text'] if not dark else '#AFC0E2'), relief='flat', borderwidth=0)
        self.style.map('Treeview', background=[('selected',self.colors['accent_soft'])], foreground=[('selected',fg)])
        self.style.configure('TEntry', padding=7, fieldbackground=self.colors['field'], foreground=fg, insertcolor=fg, borderwidth=0, relief='flat')
        self.style.configure('Field.TEntry', padding=4, fieldbackground=self.colors['field'], foreground=fg, insertcolor=fg, borderwidth=0, relief='flat')
        self.style.configure('TCombobox', padding=6, fieldbackground=self.colors['field'], foreground=fg, arrowcolor=('#8EA0BC' if dark else '#6A7892'))
        self.style.map('TCombobox', fieldbackground=[('readonly',self.colors['field'])], foreground=[('readonly',fg)], selectbackground=[('readonly',self.colors['field'])], selectforeground=[('readonly',fg)])
        self.style.configure('TLabelframe', background=panel, foreground=fg, borderwidth=1, relief='solid', padding=10)
        self.style.configure('TLabelframe.Label', background=panel, foreground=fg, font=('Segoe UI',10,'bold'))
        self.style.configure('TCheckbutton', background=bg, foreground=fg)
        self.style.configure('Vertical.TScrollbar', background=btn_bg, troughcolor=bg, bordercolor=bg, arrowcolor=('#91A5CC' if dark else '#7B879A'))

        root=tk.Frame(self, bg=bg); root.pack(fill='both', expand=True); self._root_frame=root

        # Sidebar reconstruída a partir da referência: marca fora da cápsula,
        # home superior sem tile e botões com ícones extraídos da própria referência.
        self.sidebar_nav = ReferenceSidebar(root, command=self.show_page, app_bg=bg, dark_theme=dark)
        self.sidebar_nav.place(x=0, y=0, relwidth=1.0, relheight=1.0)
        self._place_nexo_brand(root, dark)

        main=tk.Frame(root,bg=bg); main.place(x=150,y=0,relwidth=1.0,width=-150,relheight=1.0); self._content=main

        # Cabeçalho limpo, sem faixa laranja.
        head=tk.Frame(main,bg=bg); head.pack(fill='x',padx=18,pady=(58,14)); self._header=head
        self.header_accent=tk.Frame(head,bg=bg,height=1,width=1); self.header_accent.pack_forget()
        self.header_identity=tk.Frame(head,bg=bg); self.header_identity.pack(anchor='w')
        self.header_logo=tk.Label(self.header_identity,text='',bg=bg,bd=0)
        self.header_title=tk.Label(self.header_identity,text='Início',bg=bg,fg=fg,font=('Segoe UI',24,'bold'))
        self.header_title.pack(side='left')
        self.header_subtitle=tk.Label(head,text='Visão geral do seu negócio',bg=bg,fg=muted,font=('Segoe UI',10))
        self.header_subtitle.pack(anchor='w',pady=(2,0))
        self.company_label=tk.Label(head,text='',bg=bg,fg=muted,font=('Segoe UI',9))

        body=tk.Frame(main,bg=bg); body.pack(fill='both',expand=True); self._body=body
        self.toast_frame=tk.Frame(body,bg='#12372E',highlightthickness=0)
        self.toast_label=tk.Label(self.toast_frame,text='',bg='#12372E',fg='#61E3B9',font=('Segoe UI',9,'bold'),anchor='w',padx=12,pady=7); self.toast_label.pack(fill='x')
        self._checked_rows={}; self._action_buttons={}; self._pages={}
        pages=[('Geral',self.general),('Cadastro',self.cadastro),('Receitas',self.recipes_page),('Produtos',self.products_page),('Configurações',self.settings_page)]
        for name,builder in pages:
            f=tk.Frame(body,bg=bg); self._pages[name]=f; builder(f)
        self.show_page('Geral')

        footer=tk.Frame(main,bg=bg,height=26); footer.pack(fill='x',padx=24,pady=(0,7)); footer.pack_propagate(False)
        self.status_label=tk.Label(footer,textvariable=self.status,bg=bg,fg='#60769D',font=('Segoe UI',8),anchor='w'); self.status_label.pack(side='left',fill='y')
        self.footer_brand=tk.Label(footer,text='Nexo · Gestão de Custos e Precificação · v0.7.13',bg=bg,fg='#60769D',font=('Segoe UI',8),anchor='e'); self.footer_brand.pack(side='right',fill='y')
        self._update_db_status(); bind_text_capitalization(self)

    def _place_nexo_brand(self, root, dark):
        try:
            from PIL import Image, ImageTk
            source=UI_ASSETS / ('nexo_logo_dark_clean.png' if dark else 'nexo_logo_light_clean.png')
            img=Image.open(source).convert('RGBA')
            
            target_w,target_h=135,105
            scale=min(target_w/img.width,target_h/img.height)
            img=img.resize((max(1,int(img.width*scale)),max(1,int(img.height*scale))),Image.Resampling.LANCZOS)
            self._nexo_brand_img=ImageTk.PhotoImage(img)
            self.nexo_brand_label=tk.Label(root,image=self._nexo_brand_img,bg=self.colors['bg'],bd=0,highlightthickness=0)
            self.nexo_brand_label.place(x=10,y=54,width=135,height=105)
        except Exception:
            self.nexo_brand_label=None

    def _update_db_status(self):
        try:
            with db() as c:
                c.execute('SELECT 1').fetchone()
            self.status.set(f'Banco de dados: Conectado ✓  ·  {DB_PATH.name}')
        except Exception:
            self.status.set(f'Banco de dados: Desconectado ✕  ·  {DB_PATH.name}')

    def show_page(self,key):
        if getattr(self,'current_page',None) == key:
            return
        for f in self._pages.values(): f.pack_forget()
        self._pages[key].pack(fill='both',expand=True,padx=(0, 24),pady=(0,8))
        self.current_page=key
        titles={
            'Geral':('Início','Visão geral do seu negócio'),
            'Cadastro':('Cadastro','Gerencie insumos, compras e fornecedores'),
            'Receitas':('Receitas','Monte e acompanhe o custo das receitas base'),
            'Produtos':('Produtos','Custos, composição e precificação dos produtos'),
            'Configurações':('Configurações','Preferências, dados e parâmetros do Nexo'),
        }
        title,subtitle=titles[key]
        self.header_title.config(text=title)
        self.header_subtitle.config(text=subtitle)
        self.sidebar_nav.set_active(key)

    def refresh_all(self):
        self.refresh_general()
        self.refresh_materials()
        self.refresh_recipes()
        self.refresh_products()
        self.refresh_settings()

    def notify(self, message):
        self.toast_label.config(text=message)
        self.toast_frame.place(relx=0.5, y=30, anchor='n')
        self.toast_frame.lift()
        if hasattr(self, '_toast_after'):
            self.after_cancel(self._toast_after)
        self._toast_after = self.after(3000, self.toast_frame.place_forget)

    # ---------- Geral ----------
    def general(self, f):
        # Dashboard principal inspirado diretamente no layout de referência.
        bg=self.colors['bg']; panel=self.colors['panel']; panel_alt=self.colors['panel_alt']
        canvas=tk.Canvas(f, bg=bg, highlightthickness=0, bd=0)
        scrollbar=ttk.Scrollbar(f, orient='vertical', command=canvas.yview)
        body=tk.Frame(canvas, bg=bg)
        body.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        win=canvas.create_window((0,0), window=body, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side='left',fill='both',expand=True); scrollbar.pack(side='right',fill='y')
        canvas.bind('<Configure>', lambda e: canvas.itemconfigure(win,width=e.width))
        self.general_canvas=canvas
        canvas.bind_all('<MouseWheel>', self._general_mousewheel, add='+')
        canvas.bind_all('<Button-4>', self._general_mousewheel, add='+')
        canvas.bind_all('<Button-5>', self._general_mousewheel, add='+')

        cards=tk.Frame(body,bg=bg); cards.pack(fill='x',pady=(0,14))
        self.general_cards_widgets=[]
        card_defs=[
            ('Produtos','cube',self.colors['cyan'],'#103D3B','cadastrados'),
            ('Receitas base','doc',self.colors['pink'],'#30245F','cadastradas'),
            ('Insumos','cube',self.colors['blue'],'#17376A','cadastrados'),
            ('Embalagens','tag',self.colors['orange'],'#503A1C','cadastradas'),
        ]
        for i,(label,kind,accent,soft,suffix) in enumerate(card_defs):
            card=RoundedPanel(cards,fill=panel,border=self.colors['line'],radius=16,height=126,bg=bg)
            card.pack(side='left',fill='both',expand=True,padx=(0 if i==0 else 6,0 if i==3 else 6)); card.pack_propagate(False)
            ico=tk.Canvas(card,width=48,height=48,bg=panel,highlightthickness=0,bd=0)
            ico.place(x=16,y=14)
            ico.create_oval(2,2,46,46,fill=soft,outline='')
            # símbolos simples e vetoriais para manter o programa sem dependências externas.
            if kind=='doc':
                ico.create_rectangle(17,12,31,35,outline=accent,width=2)
                ico.create_line(20,20,28,20,fill=accent,width=2); ico.create_line(20,25,28,25,fill=accent,width=2)
            elif kind=='tag':
                ico.create_polygon(14,16,27,11,36,20,24,33,14,25,fill='',outline=accent,width=2)
                ico.create_oval(20,17,24,21,outline=accent,width=2)
            else:
                ico.create_polygon(15,18,24,13,33,18,24,23,fill='',outline=accent,width=2)
                ico.create_line(15,18,15,29,24,35,33,29,33,18,fill=accent,width=2)
                ico.create_line(24,23,24,35,fill=accent,width=2)
            tk.Label(card,text=label,bg=panel,fg='#DCE5FA',font=('Segoe UI',10,'bold'),anchor='w').place(x=16,y=69,relwidth=.78)
            value=tk.Label(card,text='0',bg=panel,fg='#FFFFFF',font=('Segoe UI',20,'bold'),anchor='w')
            value.place(x=16,y=91,width=74,height=28)
            tk.Label(card,text=suffix,bg=panel,fg=self.colors['muted'],font=('Segoe UI',9),anchor='w').place(x=80,y=98)
            tk.Label(card,text='›',bg=panel,fg='#7790BE',font=('Segoe UI',20),anchor='center').place(relx=.94,y=85,anchor='center')
            self.general_cards_widgets.append(value)

        row=tk.Frame(body,bg=bg); row.pack(fill='x',pady=(0,14))
        chart_box=RoundedPanel(row,fill=panel,border=self.colors['line'],radius=16,height=272,bg=bg)
        chart_box.pack(side='left',fill='both',expand=True,padx=(0,7)); chart_box.pack_propagate(False)
        chart_head=tk.Frame(chart_box,bg=panel); chart_head.pack(fill='x',padx=18,pady=(14,0))
        tk.Label(chart_head,text='Custo dos Produtos',bg=panel,fg=self.colors['text'],font=('Segoe UI',12,'bold')).pack(side='left')
        tk.Label(chart_head,text='Últimos 30 dias ⌄',bg=self.colors['field'],fg='#9EB1D4',font=('Segoe UI',8),padx=10,pady=6).pack(side='right')
        self.purchase_chart=tk.Canvas(chart_box,height=210,bg=panel,highlightthickness=0); self.purchase_chart.pack(fill='both',expand=True,padx=10,pady=(2,8))

        stat=RoundedPanel(row,fill=panel,border=self.colors['line'],radius=16,width=294,height=272,bg=bg)
        stat.pack(side='right',fill='y',padx=(7,0)); stat.pack_propagate(False)
        inner=RoundedPanel(stat,fill=self.colors['panel_alt'],border=self.colors['line'],radius=13,bg=panel)
        inner.pack(fill='both',expand=True,padx=18,pady=42)
        tk.Label(inner,text='◉  Custo médio dos produtos',bg=self.colors['panel_alt'],fg=self.colors['muted'],font=('Segoe UI',9,'bold'),anchor='w').pack(fill='x',padx=16,pady=(18,8))
        self.general_avg_cost=tk.Label(inner,text='R$ 0,00',bg=self.colors['panel_alt'],fg='#FFFFFF',font=('Segoe UI',24,'bold'),anchor='w')
        self.general_avg_cost.pack(fill='x',padx=16)
        self.general_status_pill=tk.Label(inner,text='↑  calculado agora',bg='#123B39',fg='#56D4B4',font=('Segoe UI',9,'bold'),padx=10,pady=5)
        self.general_status_pill.pack(anchor='w',padx=16,pady=(10,2))
        tk.Label(inner,text='com base nos custos cadastrados',bg=self.colors['panel_alt'],fg=self.colors['muted'],font=('Segoe UI',8),anchor='w').pack(fill='x',padx=16,pady=(1,14))

        lower=tk.Frame(body,bg=bg); lower.pack(fill='x',pady=(0,14))
        purchases=RoundedPanel(lower,fill=panel,border=self.colors['line'],radius=16,height=224,bg=bg)
        purchases.pack(side='left',fill='both',expand=True,padx=(0,7)); purchases.pack_propagate(False)
        tk.Label(purchases,text='▥  Compras',bg=panel,fg=self.colors['text'],font=('Segoe UI',11,'bold'),anchor='w').pack(fill='x',padx=18,pady=(14,0))
        tk.Label(purchases,text='últimos 30 dias',bg=panel,fg=self.colors['muted'],font=('Segoe UI',8),anchor='w').pack(fill='x',padx=18,pady=(1,7))
        self.general_purchase_lines=tk.Frame(purchases,bg=panel); self.general_purchase_lines.pack(fill='both',expand=True,padx=18,pady=(0,10))

        variation=RoundedPanel(lower,fill=panel,border=self.colors['line'],radius=16,height=224,bg=bg)
        variation.pack(side='right',fill='both',expand=True,padx=(7,0)); variation.pack_propagate(False)
        tk.Label(variation,text='↗  Variação de preços',bg=panel,fg=self.colors['text'],font=('Segoe UI',11,'bold'),anchor='w').pack(fill='x',padx=18,pady=(14,0))
        tk.Label(variation,text='histórico por insumo',bg=panel,fg=self.colors['muted'],font=('Segoe UI',8),anchor='w').pack(fill='x',padx=18,pady=(1,7))
        self.general_variation_lines=tk.Frame(variation,bg=panel); self.general_variation_lines.pack(fill='both',expand=True,padx=18,pady=(0,10))

        recent=RoundedPanel(body,fill=panel,border=self.colors['line'],radius=16,height=205,bg=bg)
        recent.pack(fill='x',pady=(0,14)); recent.pack_propagate(False)
        top=tk.Frame(recent,bg=panel); top.pack(fill='x',padx=18,pady=(13,4))
        tk.Label(top,text='◷  Últimas movimentações',bg=panel,fg=self.colors['text'],font=('Segoe UI',11,'bold'),anchor='w').pack(side='left')
        tk.Label(top,text='Ver todas  →',bg=panel,fg='#8A6CFF',font=('Segoe UI',9,'bold'),anchor='e').pack(side='right')
        header=tk.Frame(recent,bg=panel); header.pack(fill='x',padx=18,pady=(4,2))
        for txt,w in [('Data',22),('Descrição',52),('Tipo',16),('Valor',16)]:
            tk.Label(header,text=txt,bg=panel,fg=self.colors['muted'],font=('Segoe UI',8),anchor='w',width=w).pack(side='left',fill='x',expand=(txt=='Descrição'))
        self.general_recent=tk.Frame(recent,bg=panel); self.general_recent.pack(fill='both',expand=True,padx=18,pady=(0,10))

        # BI detalhado permanece acessível abaixo do dashboard, com o mesmo tema.
        bi=ttk.LabelFrame(body,text='Histórico mensal de compras',padding=10); bi.pack(fill='x',pady=(2,8))
        ttk.Label(bi,text='Variação do Insumo (todas as marcas)').pack(anchor='w')
        self.purchase_item_bi=ttk.Treeview(bi,columns=('item','mes','min','max','media'),show='headings',height=6)
        for k,t,w in [('item','Insumo',240),('mes','Mês',90),('min','Mínimo',105),('max','Máximo',105),('media','Média',105)]: self.purchase_item_bi.heading(k,text=t); self.purchase_item_bi.column(k,width=w)
        self.purchase_item_bi.pack(fill='x',pady=(3,8))
        ttk.Label(bi,text='Variação por marca').pack(anchor='w')
        self.purchase_brand_bi=ttk.Treeview(bi,columns=('item','marca','mes','min','max','media'),show='headings',height=6)
        for k,t,w in [('item','Insumo',210),('marca','Marca',150),('mes','Mês',90),('min','Mínimo',100),('max','Máximo',100),('media','Média',100)]: self.purchase_brand_bi.heading(k,text=t); self.purchase_brand_bi.column(k,width=w)
        self.purchase_brand_bi.pack(fill='x')
        hist=ttk.LabelFrame(body,text='Evolução de custos de Receitas e Produtos',padding=10); hist.pack(fill='x',pady=(8,20))
        self.cost_bi=ttk.Treeview(hist,columns=('tipo','item','mes','custo'),show='headings',height=8)
        for k,t,w in [('tipo','Tipo',120),('item','Item',300),('mes','Mês',100),('custo','Custo',130)]: self.cost_bi.heading(k,text=t); self.cost_bi.column(k,width=w)
        self.cost_bi.pack(fill='x')

    def _general_mousewheel(self, event):
        if getattr(self,'current_page',None) != 'Geral' or not hasattr(self,'general_canvas'):
            return
        delta = -int(event.delta/120) if getattr(event,'delta',0) else (-1 if getattr(event,'num',0)==4 else 1)
        self.general_canvas.yview_scroll(delta, 'units')
        return 'break'

    def _draw_bi_chart(self, canvas, title, series, value_label='R$'):
        canvas.delete('all')
        w=max(canvas.winfo_width(),620); h=max(int(canvas['height']),180)
        bg='#FFFFFF'; fg=self.colors['text']; muted=self.colors['muted']; grid=self.colors['line']; accent=self.colors['accent']
        canvas.configure(bg=bg)
        if not series:
            canvas.create_text(w/2,h/2,text='Ainda não há histórico suficiente para exibir este gráfico.',fill=muted,font=('Segoe UI',10))
            return
        data=series[-10:]; vals=[float(x[1] or 0) for x in data]
        mn=min(vals); mx=max(vals)
        if mx == mn:
            mx = mn + max(abs(mn)*0.2, 1)
            mn = max(0, mn - max(abs(mn)*0.2, 1))
        left,bottom,top,right=62,h-34,24,w-20
        # grade horizontal e rótulos de valor
        for i in range(5):
            y=top+(bottom-top)*i/4
            val=mx-(mx-mn)*i/4
            canvas.create_line(left,y,right,y,fill=grid,width=1)
            label=(f'R$ {val:,.2f}'.replace(',','X').replace('.',',').replace('X','.') if value_label=='R$' else f'{val:,.2f}')
            canvas.create_text(left-8,y,text=label,fill=muted,font=('Segoe UI',8),anchor='e')
        n=len(data)
        if n==1:
            xs=[(left+right)/2]
        else:
            xs=[left+i*(right-left)/(n-1) for i in range(n)]
        pts=[]
        for x,v in zip(xs,vals):
            y=bottom-(v-mn)/(mx-mn)*(bottom-top)
            pts.extend((x,y))
        # preenchimento suave sob a linha (cor sólida escura por limitação do Canvas Tk).
        if len(pts)>=4:
            poly=[left,bottom] + pts + [right,bottom]
            canvas.create_polygon(poly,fill=self.colors['accent_soft'],outline='')
            canvas.create_line(*pts,fill=accent,width=3,smooth=True,splinesteps=20)
        else:
            x,y=pts; canvas.create_line(left,y,right,y,fill=accent,width=3)
        for i,((label,v),x) in enumerate(zip(data,xs)):
            y=bottom-(v-mn)/(mx-mn)*(bottom-top)
            canvas.create_oval(x-4,y-4,x+4,y+4,fill=accent,outline='#8D85FF',width=1)
            if i==0 or i==len(data)-1 or len(data)<=6 or i%2==0:
                canvas.create_text(x,bottom+10,text=str(label),fill=muted,font=('Segoe UI',8),anchor='n')

    def refresh_general(self):
        if not hasattr(self, 'general_cards_widgets'):
            return
        panel=self.colors['panel']
        with db() as c:
            ins = c.execute('SELECT COUNT(*) n FROM materials').fetchone()['n']
            recipes = c.execute('SELECT COUNT(*) n FROM base_recipes').fetchone()['n']
            products = c.execute('SELECT COUNT(*) n FROM products').fetchone()['n']
            try:
                packaging = c.execute("SELECT COUNT(*) n FROM materials WHERE category='Não comestível'").fetchone()['n']
            except Exception:
                packaging = 0
        costs=[]; prices=[]
        for r in list_names('products'):
            try: costs.append(product_unit_cost(r['id']))
            except Exception: pass
            with db() as c:
                pr=c.execute('SELECT sale_price FROM products WHERE id=?',(r['id'],)).fetchone()
                if pr and pr['sale_price'] is not None: prices.append(pr['sale_price'])
        avg_cost = sum(costs)/len(costs) if costs else 0
        labels = [str(products), str(recipes), str(ins), str(packaging)]
        for w, value in zip(self.general_cards_widgets, labels):
            w.config(text=value)
        if hasattr(self,'general_avg_cost'): self.general_avg_cost.config(text=fmt(avg_cost))

        if hasattr(self,'general_purchase_lines'):
            for w in self.general_purchase_lines.winfo_children(): w.destroy()
            with db() as c:
                rows=c.execute('''SELECT COALESCE(m.category,'Outros') category, SUM(pu.value) total
                                  FROM purchases pu JOIN materials m ON m.id=pu.material_id
                                  WHERE date(pu.purchase_date) >= date('now','-30 day')
                                  GROUP BY m.category ORDER BY total DESC''').fetchall()
                if not rows:
                    rows=c.execute('''SELECT COALESCE(m.category,'Outros') category, SUM(pu.value) total
                                      FROM purchases pu JOIN materials m ON m.id=pu.material_id
                                      GROUP BY m.category ORDER BY total DESC LIMIT 4''').fetchall()
            total=sum(float(r['total'] or 0) for r in rows) or 1
            palette=[('#24C6A3','Ingredientes (alimentos)'),('#7B5CFF','Embalagens'),('#2F72FF','Insumos (não alimentícios)'),('#F5A524','Custos operacionais')]
            for idx,r in enumerate(rows[:4]):
                row=tk.Frame(self.general_purchase_lines,bg=panel); row.pack(fill='x',pady=2)
                dot,color_name=palette[idx%len(palette)]
                category=str(r['category'] or '')
                if category=='Comestível': name='Ingredientes (alimentos)'
                elif category=='Não comestível': name='Embalagens'
                else: name=category or color_name
                tk.Label(row,text='●',bg=panel,fg=dot,font=('Segoe UI',9)).pack(side='left')
                tk.Label(row,text=name,bg=panel,fg=self.colors['text'],font=('Segoe UI',8),anchor='w').pack(side='left',fill='x',expand=True,padx=(6,4))
                val=float(r['total'] or 0); pct=val/total*100
                tk.Label(row,text=fmt(val),bg=panel,fg='#DDE6F8',font=('Segoe UI',8),anchor='e').pack(side='left',padx=5)
                tk.Label(row,text=f'{pct:.0f}%',bg=panel,fg='#7D91B6',font=('Segoe UI',8),width=5,anchor='e').pack(side='right')
            if not rows:
                tk.Label(self.general_purchase_lines,text='Nenhuma compra registrada ainda.',bg=panel,fg=self.colors['muted'],font=('Segoe UI',8),anchor='w').pack(fill='x',pady=8)

        if hasattr(self,'general_variation_lines'):
            for w in self.general_variation_lines.winfo_children(): w.destroy()
            with db() as c:
                rows=c.execute('''SELECT m.name, MIN(pu.value) mn, MAX(pu.value) mx
                                  FROM purchases pu JOIN materials m ON m.id=pu.material_id
                                  GROUP BY m.id HAVING COUNT(pu.id) > 1
                                  ORDER BY CASE WHEN MIN(pu.value)>0 THEN (MAX(pu.value)-MIN(pu.value))/MIN(pu.value) ELSE 0 END DESC LIMIT 5''').fetchall()
            for r in rows:
                mn=float(r['mn'] or 0); mx=float(r['mx'] or 0)
                pct=((mx-mn)/mn*100) if mn>0 else 0
                row=tk.Frame(self.general_variation_lines,bg=panel); row.pack(fill='x',pady=4)
                tk.Label(row,text=r['name'],bg=panel,fg=self.colors['text'],font=('Segoe UI',8),anchor='w').pack(side='left',fill='x',expand=True)
                positive=pct>0.01
                txt=('↑ ' if positive else '↓ ') + f'{abs(pct):.1f}%'.replace('.',',')
                tk.Label(row,text=txt,bg=panel,fg=('#FF5E74' if positive else '#24C6A3'),font=('Segoe UI',9,'bold'),anchor='e').pack(side='right')
            if not rows:
                tk.Label(self.general_variation_lines,text='Ainda não há histórico suficiente.',bg=panel,fg=self.colors['muted'],font=('Segoe UI',8),anchor='w').pack(fill='x',pady=8)

        if hasattr(self,'general_recent'):
            for w in self.general_recent.winfo_children(): w.destroy()
            with db() as c:
                rows=c.execute('''SELECT pu.purchase_date date, m.name, COALESCE(pu.brand,'') brand, pu.value
                                  FROM purchases pu JOIN materials m ON m.id=pu.material_id
                                  ORDER BY pu.purchase_date DESC, pu.id DESC LIMIT 4''').fetchall()
            if rows:
                for r in rows:
                    row=tk.Frame(self.general_recent,bg=panel); row.pack(fill='x',pady=1)
                    date_text=str(r['date'])
                    desc=r['name'] + (f" - {r['brand']}" if r['brand'] else '')
                    tk.Label(row,text=date_text,bg=panel,fg=self.colors['muted'],font=('Segoe UI',8),anchor='w',width=22).pack(side='left')
                    tk.Label(row,text=desc,bg=panel,fg=self.colors['text'],font=('Segoe UI',8),anchor='w').pack(side='left',fill='x',expand=True)
                    tk.Label(row,text='Compra',bg='#123B39',fg='#5EE0B8',font=('Segoe UI',8,'bold'),padx=8,pady=2,width=9).pack(side='left',padx=8)
                    tk.Label(row,text=fmt(r['value']),bg=panel,fg=self.colors['text'],font=('Segoe UI',8),anchor='e',width=15).pack(side='right')
            else:
                tk.Label(self.general_recent,text='Nenhuma movimentação registrada ainda.',bg=panel,fg=self.colors['muted'],font=('Segoe UI',8),anchor='w').pack(fill='x',pady=8)

        for tree in (self.purchase_item_bi, self.purchase_brand_bi):
            for x in tree.get_children(): tree.delete(x)
        with db() as c:
            rows = c.execute('''SELECT m.name, substr(pu.purchase_date,1,7) mes, MIN(pu.value) mn, MAX(pu.value) mx, AVG(pu.value) av
                                FROM purchases pu JOIN materials m ON m.id=pu.material_id
                                GROUP BY m.id, mes ORDER BY mes DESC, m.name''').fetchall()
            for r in rows: self.purchase_item_bi.insert('', 'end', values=(r['name'], r['mes'], fmt(r['mn']), fmt(r['mx']), fmt(r['av'])))
            rows = c.execute('''SELECT m.name, COALESCE(pu.brand,'') brand, substr(pu.purchase_date,1,7) mes, MIN(pu.value) mn, MAX(pu.value) mx, AVG(pu.value) av
                                FROM purchases pu JOIN materials m ON m.id=pu.material_id
                                GROUP BY m.id, pu.brand, mes ORDER BY mes DESC, m.name, pu.brand''').fetchall()
            for r in rows: self.purchase_brand_bi.insert('', 'end', values=(r['name'], r['brand'], r['mes'], fmt(r['mn']), fmt(r['mx']), fmt(r['av'])))
        for x in self.cost_bi.get_children(): self.cost_bi.delete(x)
        with db() as c:
            rows = c.execute('''SELECT ch.entity_type, ch.entity_id, ch.cost, substr(ch.recorded_at,1,7) mes
                                FROM cost_history ch ORDER BY ch.recorded_at DESC, ch.id DESC''').fetchall()
            for r in rows:
                table = 'base_recipes' if r['entity_type'] == 'RECIPE_BASE' else 'products'
                name = c.execute(f'SELECT name FROM {table} WHERE id=?', (r['entity_id'],)).fetchone()
                self.cost_bi.insert('', 'end', values=('Receita' if r['entity_type']=='RECIPE_BASE' else 'Produto', name['name'] if name else '?', r['mes'], fmt(r['cost'])))
        if not rows:
            mes=date.today().strftime('%Y-%m')
            for r in list_names('base_recipes'):
                try:self.cost_bi.insert('', 'end', values=('Receita',r['name'],mes,fmt(recipe_cost(r['id']))))
                except Exception:pass
            for r in list_names('products'):
                try:self.cost_bi.insert('', 'end', values=('Produto',r['name'],mes,fmt(product_unit_cost(r['id']))))
                except Exception:pass
        with db() as c:
            hist_series=c.execute('SELECT substr(recorded_at,1,7) mes, AVG(cost) avg_cost FROM cost_history GROUP BY mes ORDER BY mes').fetchall()
        if hist_series:
            cost_series=[(r['mes'],float(r['avg_cost'])) for r in hist_series]
        else:
            current=[]
            for r in list_names('products'):
                try:current.append(product_unit_cost(r['id']))
                except Exception:pass
            for r in list_names('base_recipes'):
                try:current.append(recipe_cost(r['id']))
                except Exception:pass
            cost_series=[(date.today().strftime('%Y-%m'),sum(current)/len(current))] if current else []
        self._draw_bi_chart(self.purchase_chart,'Custo médio por mês',cost_series)

    def _selection_count(self, tree):
        return len(getattr(self, '_checked_rows', {}).get(str(tree), set()))

    def _set_single_checked(self, tree, iid):
        key=str(tree); self._checked_rows[key]={iid}
        for item in tree.get_children():
            tree.item(item, text='☑' if item==iid else '☐')
        tree.selection_set(iid)
        self._update_action_states()
        
        children = tree.get_children()
        is_all_checked = len(self._checked_rows[key]) == len(children) and len(children) > 0
        if tree == getattr(self, 'mat_tree', None) and hasattr(self, '_redraw_mat_header'):
            self._redraw_mat_header()
        else:
            tree.heading('#0', text='☑' if is_all_checked else '☐')
            
        tree.event_generate('<<TreeviewSelect>>')

    def _toggle_checkbox(self, tree, iid):
        key=str(tree); checked=self._checked_rows.setdefault(key,set())
        if iid in checked:
            checked.remove(iid)
        else:
            checked.add(iid)
        for item in tree.get_children():
            tree.item(item, text='☑' if item in checked else '☐')
        if checked:
            tree.selection_set(iid if len(checked)==1 else tuple(checked))
        else:
            tree.selection_remove(tree.selection())
        self._update_action_states()
        
        children = tree.get_children()
        is_all_checked = len(checked) == len(children) and len(children) > 0
        if tree == getattr(self, 'mat_tree', None) and hasattr(self, '_redraw_mat_header'):
            self._redraw_mat_header()
        else:
            tree.heading('#0', text='☑' if is_all_checked else '☐')
            
        tree.event_generate('<<TreeviewSelect>>')

    def _toggle_all_checkboxes(self, tree):
        key = str(tree)
        checked = self._checked_rows.setdefault(key, set())
        children = tree.get_children()
        if not children: return
        
        if len(checked) == len(children):
            checked.clear()
            tree.selection_remove(tree.selection())
        else:
            checked.update(children)
            tree.selection_set(children)
            
        for item in children:
            tree.item(item, text='☑' if item in checked else '☐')
            
        self._update_action_states()
        tree.event_generate('<<TreeviewSelect>>')
        
        if tree == getattr(self, 'mat_tree', None) and hasattr(self, '_redraw_mat_header'):
            self._redraw_mat_header()
        else:
            is_all_checked = len(checked) == len(children)
            tree.heading('#0', text='☑' if is_all_checked else '☐')

    def _update_action_states(self):
        for tree, cfg in getattr(self, '_action_buttons', {}).items():
            count=self._selection_count(tree)
            normal=cfg.get('normal', []) if isinstance(cfg, dict) else []
            bulk=cfg.get('bulk', []) if isinstance(cfg, dict) else []
            if count >= 2:
                for b in normal:
                    try: b.pack_forget()
                    except Exception: pass
                for b in bulk:
                    try: b.configure(state='normal')
                    except Exception: pass
                    try:
                        if not b.winfo_ismapped(): b.pack(side='left', padx=6)
                    except Exception: pass
            else:
                for b in bulk:
                    try: b.pack_forget()
                    except Exception: pass
                for b in normal:
                    try:
                        if not b.winfo_ismapped(): b.pack(side='left', padx=6)
                    except Exception: pass

    def _cancel_multiselection_for(self, tree):
        self._reset_checked(tree)
        try: tree.selection_remove(tree.selection())
        except Exception: pass

    def _run_normal_action(self, tree, func):
        if self._selection_count(tree) >= 2:
            self._cancel_multiselection_for(tree)
        func()

    def _reset_checked(self, tree):
        self._checked_rows[str(tree)] = set()
        for iid in tree.get_children(): tree.item(iid,text='☐')
        if tree == getattr(self, 'mat_tree', None) and hasattr(self, '_redraw_mat_header'):
            self._redraw_mat_header()
        else:
            tree.heading('#0', text='☐')
        self._update_action_states()

    def _action_photo(self, slug):
        if not hasattr(self, '_action_photo_refs'):
            self._action_photo_refs={}
        if slug not in self._action_photo_refs:
            try:self._action_photo_refs[slug]=tk.PhotoImage(file=str(UI_ASSETS/slug))
            except Exception:self._action_photo_refs[slug]=None
        return self._action_photo_refs[slug]

    def _tree_click(self, event, tree, kind):
        region = tree.identify_region(event.x, event.y)
        col = tree.identify_column(event.x)
        if region == 'heading' and col == '#0':
            self._toggle_all_checkboxes(tree)
            return 'break'
            
        iid=tree.identify_row(event.y)
        if not iid or tree.parent(iid): return
        # Action columns are identified by their fixed position, so image-only
        # headers remain clickable even when the heading text is intentionally blank.
        action_cols={
            'material':('#9','#10'),
            'recipe':('#6','#7'),
            'product':('#6','#7'),
        }
        edit_col,delete_col=action_cols.get(kind,('', ''))
        if col==edit_col:
            self._set_single_checked(tree,iid)
            {'material':self.edit_selected_material,'recipe':self.edit_selected_recipe,'product':self.edit_selected_product}[kind]()
            return 'break'
        if col==delete_col:
            self._set_single_checked(tree,iid)
            {'material':self.delete_selected_materials,'recipe':self.delete_selected_recipes,'product':self.delete_selected_products}[kind]()
            return 'break'
        # Expand/collapse indicator always wins and never changes selection.
        if col=='#0':
            try: element=tree.identify_element(event.x,event.y)
            except Exception: element=''
            if 'indicator' in element:
                tree.item(iid, open=not bool(tree.item(iid,'open')))
                return 'break'
            bbox=tree.bbox(iid,'#0')
            checkbox_zone=(bbox[0], bbox[0]+58) if bbox else (0,58)
            if checkbox_zone[0] <= event.x <= checkbox_zone[1]:
                self._toggle_checkbox(tree,iid)
                return 'break'
        # Any other click in the row always becomes a single selection.
        self._set_single_checked(tree,iid)
        return 'break'

    # ---------- Cadastro ----------
    def _build_page_toolbar(self, parent):
        # Barra em cápsula única, sem molduras extras nos campos.
        shell=RoundedPanel(parent, fill=self.colors['panel'], border='', radius=22, bg=self.colors['bg'], height=84)
        shell.pack(fill='x', padx=0, pady=(0,14)); shell.pack_propagate(False)
        inner=tk.Frame(shell,bg=self.colors['panel'])
        inner.pack(fill='both', expand=True, padx=24, pady=17)
        return shell, inner

    def _build_page_table_panel(self, parent):
        shell=RoundedPanel(parent, fill=self.colors['panel'], border='', radius=22, bg=self.colors['bg'])
        shell.pack(fill='both', expand=True, padx=0, pady=(0,12))
        inner=tk.Frame(shell,bg=self.colors['panel'])
        inner.pack(fill='both', expand=True, padx=12, pady=12)
        return shell, inner

    def _styled_search_entry(self, parent, textvariable, width=28):
        wrap=RoundedEntry(parent,textvariable,width=width,height=40)
        # Search is fixed on the right, but we give it a min size by NOT propagating
        wrap.pack(side='right',padx=(14,0),fill='none',expand=False)
        return wrap

    def _auto_size_tree_column(self, tree, col):
        import tkinter.font as tkfont
        f = tkfont.Font(family='Segoe UI', size=10)
        max_w = 40
        txt = tree.heading(col, 'text')
        if txt: max_w = max(max_w, f.measure(txt) + 24)
        
        if tree == getattr(self, 'mat_tree', None) and hasattr(self, '_mat_header_specs'):
            if str(col).startswith('#'):
                try:
                    idx = int(col[1:])
                    if idx > 0:
                        txt = self._mat_header_specs[idx-1][1]
                        if txt: max_w = max(max_w, f.measure(txt) + 24)
                except Exception: pass

        c_idx = -1
        if str(col).startswith('#'):
            try: c_idx = int(col[1:]) - 1
            except Exception: pass
        else:
            cols = list(tree['columns'])
            if col in cols: c_idx = cols.index(col)
        
        for iid in tree.get_children():
            if col == '#0' or c_idx == -1:
                v = tree.item(iid, 'text')
            else:
                vals = tree.item(iid, 'values')
                v = str(vals[c_idx]) if c_idx < len(vals) else ''
            max_w = max(max_w, f.measure(v) + 24)
            
        tree.column(col, width=min(max_w, 600))

    def _on_native_tree_double_click(self, e, tree, default_action):
        if tree.identify_region(e.x, e.y) == 'separator':
            col = tree.identify_column(e.x)
            if col and col != 'dummy' and 'edit' not in col and 'delete' not in col:
                self._auto_size_tree_column(tree, col)
            return 'break'
        if default_action: default_action()

    def _setup_canvas_header_drag(self, canvas, tree, fixed_cols, redraw_cmd, state_key):
        canvas._drag_col = None
        canvas._drag_start_x = 0
        canvas._drag_start_w = 0
        def get_col_edge(x):
            total_w = sum(int(tree.column(c, 'width')) for c in ['#0'] + list(tree['columns']))
            try: x_offset = float(tree.xview()[0]) * total_w
            except Exception: x_offset = 0
            
            cx = -x_offset
            cols = ['#0'] + list(tree['columns'])
            for col in cols:
                cw = int(tree.column(col, 'width'))
                cx += cw
                if abs(x - cx) < 8: return col
            return None
        def on_press(e):
            col = get_col_edge(e.x)
            if col and col not in fixed_cols:
                canvas._drag_col = col; canvas._drag_start_x = e.x
                canvas._drag_start_w = int(tree.column(col, 'width'))
                setattr(self, f'_{state_key}_user_resized', True)
        def on_drag(e):
            if canvas._drag_col:
                delta = e.x - canvas._drag_start_x
                new_w = max(40, canvas._drag_start_w + delta)
                tree.column(canvas._drag_col, width=new_w)
                canvas.after_idle(redraw_cmd)
        def on_motion(e):
            canvas.config(cursor='sb_h_double_arrow' if get_col_edge(e.x) and get_col_edge(e.x) not in fixed_cols else 'arrow')
        def on_double_click(e):
            col = get_col_edge(e.x)
            if col and col not in fixed_cols and col != 'dummy':
                setattr(self, f'_{state_key}_user_resized', False)
                self._auto_size_tree_column(tree, col)
                canvas.after_idle(redraw_cmd)
        
        canvas.bind('<Button-1>', on_press)
        canvas.bind('<B1-Motion>', on_drag)
        canvas.bind('<Motion>', on_motion)
        canvas.bind('<Double-1>', on_double_click)

    def _make_row_icon(self, kind):
        try:
            from PIL import Image, ImageTk
            import pathlib
            UI_ASSETS = pathlib.Path(__file__).parent / 'ui_assets'
            if kind == 'edit':
                im = Image.open(UI_ASSETS / 'action_edit_reference_exact.png').convert('RGBA')
            elif kind == 'delete':
                im = Image.open(UI_ASSETS / 'action_delete_reference_exact.png').convert('RGBA')
            else:
                return None
            im = im.resize((16, 16), Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(im)
        except Exception: return None

    def _toggle_active(self, kind, iid, current_active):
        table = {'material': 'materials', 'recipe': 'base_recipes', 'product': 'products'}[kind]
        new_val = 0 if current_active else 1
        with db() as c:
            c.execute(f'UPDATE {table} SET active=?, updated_at=? WHERE id=?', (new_val, now_iso(), iid))
        self.refresh_all()
        self.notify(f"Item {'desativado' if current_active else 'ativado'} com sucesso.")

    def _show_row_menu(self, tree, kind, iid, x, y, edit_cmd, delete_cmd):
        self._set_single_checked(tree, iid)
        is_active = 'inactive' not in tree.item(iid, 'tags')
        
        dark = getattr(self, '_dark', False)
        bg = self.colors['panel']
        fg = self.colors['text']
        hover = '#20375F' if dark else '#F4F7FC'
        border = self.colors['line']
        
        if hasattr(self, '_current_menu') and self._current_menu.winfo_exists():
            self._current_menu.destroy()

        menu = tk.Toplevel(self)
        menu.overrideredirect(True)
        menu.attributes('-topmost', True)
        self._current_menu = menu
        
        try:
            menu.configure(bg='#000001')
            menu.wm_attributes('-transparentcolor', '#000001')
            transparent_bg = '#000001'
        except Exception:
            transparent_bg = bg
            menu.configure(bg=bg)
        
        w, h = 180, 145
        menu.geometry(f'{w}x{h}+{x-w+10}+{y+5}')
        
        c = tk.Canvas(menu, bg=transparent_bg, bd=0, highlightthickness=0)
        c.pack(fill='both', expand=True)
        
        r = 8
        c.create_rectangle(r, 0, w-r, h, fill=bg, outline='')
        c.create_rectangle(0, r, w, h-r, fill=bg, outline='')
        c.create_arc(0, 0, 2*r, 2*r, start=90, extent=90, fill=bg, outline='')
        c.create_arc(w-2*r, 0, w, 2*r, start=0, extent=90, fill=bg, outline='')
        c.create_arc(0, h-2*r, 2*r, h, start=180, extent=90, fill=bg, outline='')
        c.create_arc(w-2*r, h-2*r, w, h, start=270, extent=90, fill=bg, outline='')
        
        c.create_line(r, 0, w-r, 0, fill=border)
        c.create_line(r, h-1, w-r, h-1, fill=border)
        c.create_line(0, r, 0, h-r, fill=border)
        c.create_line(w-1, r, w-1, h-r, fill=border)
        c.create_arc(0, 0, 2*r, 2*r, start=90, extent=90, style='arc', outline=border)
        c.create_arc(w-2*r-1, 0, w-1, 2*r, start=0, extent=90, style='arc', outline=border)
        c.create_arc(0, h-2*r-1, 2*r, h-1, start=180, extent=90, style='arc', outline=border)
        c.create_arc(w-2*r-1, h-2*r-1, w-1, h-1, start=270, extent=90, style='arc', outline=border)
        
        c.create_line(16, 72, w-16, 72, fill=border)
        
        try:
            from PIL import Image, ImageDraw, ImageTk
            import pathlib
            UI_ASSETS = pathlib.Path(__file__).parent / 'ui_assets'
            im_e = Image.open(UI_ASSETS / 'action_edit_reference_exact.png').convert('RGBA').resize((16, 16), Image.Resampling.LANCZOS)
            im_d = Image.open(UI_ASSETS / 'action_delete_reference_exact.png').convert('RGBA').resize((16, 16), Image.Resampling.LANCZOS)
            
            icon_color = '#AFC0E2' if dark else '#687796'
            
            im_pause = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
            draw = ImageDraw.Draw(im_pause)
            draw.rectangle([4, 2, 6, 14], fill=icon_color)
            draw.rectangle([10, 2, 12, 14], fill=icon_color)
            
            im_play = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
            draw = ImageDraw.Draw(im_play)
            draw.polygon([5, 2, 5, 14, 13, 8], fill=icon_color)
            
            if not hasattr(self, '_menu_icons'):
                self._menu_icons = {}
            self._menu_icons['edit'] = ImageTk.PhotoImage(im_e)
            self._menu_icons['delete'] = ImageTk.PhotoImage(im_d)
            self._menu_icons['pause'] = ImageTk.PhotoImage(im_pause)
            self._menu_icons['play'] = ImageTk.PhotoImage(im_play)
            
            img_e = self._menu_icons['edit']
            img_d = self._menu_icons['delete']
            img_p = self._menu_icons['pause']
            img_pl = self._menu_icons['play']
        except Exception:
            img_e = img_d = img_p = img_pl = None

        def add_item(oy, text, img, cmd, active=True):
            text_col = fg if active else self.colors['muted']
            hitbox = c.create_rectangle(1, oy, w-1, oy+35, fill='', outline='', tags=(f'item_{oy}',))
            if img:
                c.create_image(24, oy+17, image=img, anchor='center')
            c.create_text(42, oy+17, text=text, fill=text_col, font=('Segoe UI', 10), anchor='w')
            
            if active:
                def on_click(e, c_cmd=cmd):
                    menu.destroy()
                    c_cmd()
                c.tag_bind(f'item_{oy}', '<Enter>', lambda e: c.itemconfig(hitbox, fill=hover))
                c.tag_bind(f'item_{oy}', '<Leave>', lambda e: c.itemconfig(hitbox, fill=''))
                c.tag_bind(f'item_{oy}', '<Button-1>', on_click)
                c.tag_bind(f'item_{oy}', '<Enter>', lambda e: c.config(cursor='hand2'), add='+')
                c.tag_bind(f'item_{oy}', '<Leave>', lambda e: c.config(cursor='arrow'), add='+')

        add_item(5, 'Editar' if is_active else 'Editar (Desativado)', img_e, edit_cmd, is_active)
        add_item(35, 'Excluir', img_d, delete_cmd)
        add_item(75, 'Ativar', img_pl, lambda: self._toggle_active(kind, iid, False), not is_active)
        add_item(105, 'Desativar', img_p, lambda: self._toggle_active(kind, iid, True), is_active)
            
        menu.grab_set()
        def on_click_anywhere(e):
            x_root, y_root = e.x_root, e.y_root
            rx, ry, rw, rh = menu.winfo_rootx(), menu.winfo_rooty(), menu.winfo_width(), menu.winfo_height()
            if not (rx <= x_root <= rx+rw and ry <= y_root <= ry+rh):
                menu.destroy()
        menu.bind('<Button-1>', on_click_anywhere, add='+')

    def _attach_row_icon_overlay(self, tree, table_host, edit_col_idx, delete_col_idx, edit_cmd, delete_cmd):
        ov = tk.Canvas(table_host, bd=0, highlightthickness=0, cursor='arrow', bg=self.colors['field'])
        ov.place(relx=1.0, x=0, y=36, width=90, relheight=1.0, height=-36, anchor='ne')
        ov._icon_refs = []
        
        is_mat = tree == getattr(self, 'mat_tree', None)
        cw0 = int(tree.column('#0', 'width'))
        y_off = 36 if is_mat else 0
        ov_left = tk.Canvas(table_host, bd=0, highlightthickness=0, cursor='arrow', bg=self.colors['field'])
        ov_left.place(relx=0, x=0, y=y_off, width=cw0, relheight=1.0, height=-y_off, anchor='nw')
        
        kind = 'material' if 'mat' in str(tree) else ('recipe' if 'rec' in str(tree) else 'product')

        def _redraw_overlay(*_):
            ov.delete('all')
            ov_left.delete('all')
            ov._icon_refs.clear()
            
            if not is_mat:
                header_bg = '#142544' if getattr(self, '_dark', False) else '#E8EEF8'
                ov_left.create_rectangle(0, 0, cw0, 38, fill=header_bg, outline='')
                
            img_e = self._make_row_icon('edit')
            img_d = self._make_row_icon('delete')
            ex, dx, ox = 15, 45, 75
            selected = set(tree.selection())
            
            from tkinter.font import Font
            f_chk = Font(family='Segoe UI', size=13)
            
            for iid in tree.get_children():
                bb = tree.bbox(iid)
                if not bb: continue
                _, ry, _, rh = bb
                
                # Checkbox Overlay Drawing (Left)
                bg_color = self.colors['accent_soft'] if iid in selected else self.colors['field']
                
                ov_left.create_rectangle(0, ry, cw0, ry + rh, fill=bg_color, outline='', tags=(f'c_{iid}',))
                
                tags = tree.item(iid, 'tags')
                is_active = 'inactive' not in tags
                is_checked = iid in self._checked_rows.get(str(tree), set())
                txt = '☑' if is_checked else '☐'
                color = '#2B3D55' if is_checked else '#A0ABB9'
                if getattr(self, '_dark', False): color = '#FFFFFF' if is_checked else '#60769D'
                
                cy = ry + rh // 2
                ov_left.create_text(cw0/2, cy, text=txt, fill=color, font=f_chk, anchor='center', tags=(f'c_{iid}',))
                
                ov_left.tag_bind(f'c_{iid}', '<Button-1>', lambda ev, i=iid: self._toggle_checkbox(tree, i))
                ov_left.tag_bind(f'c_{iid}', '<Enter>', lambda ev, i=iid: ov_left.config(cursor='hand2'))
                ov_left.tag_bind(f'c_{iid}', '<Leave>', lambda ev, i=iid: ov_left.config(cursor='arrow'))
                
                # Action Buttons Overlay Drawing (Right)
                ov.create_rectangle(0, ry, 90, ry + rh, fill=bg_color, outline='')
                
                if img_e:
                    ov._icon_refs.append(img_e)
                    if is_active:
                        ov.create_image(ex, cy, image=img_e, anchor='center', tags=(f'e_{iid}',))
                        ov.tag_bind(f'e_{iid}', '<Button-1>', lambda ev, i=iid: (self._set_single_checked(tree, i), edit_cmd()))
                        ov.tag_bind(f'e_{iid}', '<Enter>', lambda ev, i=iid: ov.config(cursor='hand2'))
                        ov.tag_bind(f'e_{iid}', '<Leave>', lambda ev, i=iid: ov.config(cursor='arrow'))
                    else:
                        ov.create_rectangle(ex-12, cy-12, ex+12, cy+12, fill=bg_color, stipple='gray50', outline='')
                        
                if img_d:
                    ov._icon_refs.append(img_d)
                    ov.create_image(dx, cy, image=img_d, anchor='center', tags=(f'd_{iid}',))
                    ov.tag_bind(f'd_{iid}', '<Button-1>', lambda ev, i=iid: (self._set_single_checked(tree, i), delete_cmd()))
                    ov.tag_bind(f'd_{iid}', '<Enter>', lambda ev, i=iid: ov.config(cursor='hand2'))
                    ov.tag_bind(f'd_{iid}', '<Leave>', lambda ev, i=iid: ov.config(cursor='arrow'))
                    
                dot_c = self.colors.get('text', '#333333')
                ov.create_oval(ox-1, cy-5, ox+1, cy-3, fill=dot_c, outline='', tags=(f'o_{iid}',))
                ov.create_oval(ox-1, cy-1, ox+1, cy+1, fill=dot_c, outline='', tags=(f'o_{iid}',))
                ov.create_oval(ox-1, cy+3, ox+1, cy+5, fill=dot_c, outline='', tags=(f'o_{iid}',))
                ov.create_rectangle(ox-8, cy-10, ox+8, cy+10, fill='', outline='', tags=(f'o_{iid}',))
                
                ov.tag_bind(f'o_{iid}', '<Button-1>', lambda ev, i=iid: self._show_row_menu(tree, kind, i, ev.x_root, ev.y_root, edit_cmd, delete_cmd))
                ov.tag_bind(f'o_{iid}', '<Enter>', lambda ev, i=iid: ov.config(cursor='hand2'))
                ov.tag_bind(f'o_{iid}', '<Leave>', lambda ev, i=iid: ov.config(cursor='arrow'))

        tree.bind('<Configure>', _redraw_overlay, add='+')
        tree.bind('<<TreeviewSelect>>', _redraw_overlay, add='+')
        
        orig_yscroll = tree.cget('yscrollcommand')
        def _on_yscroll(first, last):
            if orig_yscroll: tree.tk.call(orig_yscroll, first, last)
            tree.after_idle(_redraw_overlay)
        tree.configure(yscrollcommand=_on_yscroll)
        
        ov._redraw = _redraw_overlay
        tree._ov_left = ov_left
        return ov

    def cadastro(self, f):
        _, bar = self._build_page_toolbar(f)
        
        mat_add=RoundedActionButton(bar, '+ Novo item', lambda: self._run_normal_action(self.mat_tree, self.new_material), width=130, height=49, fill='#2F67B1', hover='#255894')
        mat_add.pack(side='left')
        
        mat_history=RoundedActionButton(bar, '<clock> Histórico', lambda: self._run_normal_action(self.mat_tree, self.material_history_dialog), width=120, height=49, fill='#EFF4FB', hover='#E3EBF6', fg='#1D3557')
        mat_history.pack(side='left', padx=(8, 0))
        
        self.mat_bulk_delete_btn=RoundedActionButton(bar, '🗑 Excluir', lambda: self._run_normal_action(self.mat_tree, self.delete_selected_materials), width=120, height=40, fill='#FCE8E8', hover='#F9D1D1', fg='#D93838')
        
        self.mat_search=tk.StringVar(); self.mat_search.trace_add('write',lambda *a:self.refresh_materials())
        
        self.mat_status = tk.StringVar(value='Ativos')
        self.mat_status_wrap = tk.Canvas(bar, bg=self.colors['panel'], bd=0, highlightthickness=0, width=110, height=40, cursor='hand2')
        self.mat_status_wrap.pack(side='right', padx=14)
        def _draw_status(text):
            self.mat_status_wrap.delete('all')
            w = 110; h = 40
            self.mat_status_wrap.create_arc(2, 2, 38, 38, start=90, extent=180, fill='#FFFFFF', outline='#E2EAF5', style='pieslice')
            self.mat_status_wrap.create_arc(2, 2, 38, 38, start=90, extent=180, fill='#FFFFFF', outline='#E2EAF5', style='arc')
            self.mat_status_wrap.create_arc(w-38, 2, w-2, 38, start=-90, extent=180, fill='#FFFFFF', outline='#E2EAF5', style='pieslice')
            self.mat_status_wrap.create_arc(w-38, 2, w-2, 38, start=-90, extent=180, fill='#FFFFFF', outline='#E2EAF5', style='arc')
            self.mat_status_wrap.create_rectangle(20, 2, w-20, 38, fill='#FFFFFF', outline='')
            self.mat_status_wrap.create_line(20, 2, w-20, 2, fill='#E2EAF5')
            self.mat_status_wrap.create_line(20, 38, w-20, 38, fill='#E2EAF5')
            self.mat_status_wrap.create_text(45, 20, text=text, fill=self.colors['text'], font=('Segoe UI', 10, 'bold'), anchor='center')
            self.mat_status_wrap.create_text(90, 20, text='▼', fill=self.colors['muted'], font=('Segoe UI', 8), anchor='center')
        
        _draw_status(self.mat_status.get())
        
        def _open_status_menu(e):
            m = tk.Menu(self.winfo_toplevel(), tearoff=0, bg=self.colors['panel'], fg=self.colors['text'], font=('Segoe UI', 10), activebackground=self.colors['accent_soft'], activeforeground=self.colors['accent'], bd=1)
            for opt in ['Ativos', 'Inativos', 'Todos']:
                m.add_command(label=opt, command=lambda o=opt: (self.mat_status.set(o), _draw_status(o), self.refresh_materials()))
            m.post(e.x_root, e.y_root)
            
        self.mat_status_wrap.bind('<Button-1>', _open_status_menu)
        
        self.mat_search_wrap=self._styled_search_entry(bar,self.mat_search,22)

        _,table_host=self._build_page_table_panel(f)
        
        self.mat_header=tk.Canvas(table_host,bg=self.colors['panel'],bd=0,highlightthickness=0,height=36)
        self.mat_header.pack(fill='x',padx=2,pady=(0,0))
        
        self.mat_tree=ttk.Treeview(table_host,columns=('code','name','brand','qty','unit','value','category','date','mod_date','status','edit','delete','options','dummy'),show='tree')
        self.mat_tree.tag_configure('inactive', foreground='#9AA9BF')
        self.mat_tree.column('#0',width=60,minwidth=60,stretch=False)
        
        for k,w in [('code',100),('name',220),('brand',150),('qty',110),('unit',65),('value',100),('category',130),('date',135),('mod_date',135),('status',90),('edit',30),('delete',30),('options',30)]:
            self.mat_tree.column(k,width=w,minwidth=w,anchor='center' if k in ('qty','unit','value','category','date','mod_date','status') else 'w',stretch=False)
        self.mat_tree.column('dummy', width=0, minwidth=0, stretch=True)
            
        self.mat_hsb = PillScrollbar(table_host, self.mat_tree)
        original_scroll = self.mat_hsb._on_scroll
        def hsb_scroll(first, last):
            original_scroll(first, last)
            self.after_idle(self._redraw_mat_header) if hasattr(self, '_redraw_mat_header') else None
        self.mat_tree.configure(xscrollcommand=hsb_scroll)
        
        self.mat_tree.pack(fill='both',expand=True)

        self._mat_header_specs=[('code','Código',100),('name','Item',220),('brand','Marca',150),('qty','Quantidade',110),('unit','Un.',65),('value','Valor',100),('category','Categoria',130),('date','Data de criação',135),('mod_date','Última modificação',135),('status','Status',90),('edit','',30),('delete','',30),('options','',30)]
        self._mat_header_imgs={}
        
        def redraw_mat_header(_event=None):
            c=self.mat_header; c.delete('all')
            w=max(c.winfo_width(),2); h=max(c.winfo_height(),2)
            r=min(h/2,18); fill='#EEF4FB'
            
            c.create_rectangle(r,0,w-r,h,fill=fill,outline='')
            c.create_rectangle(0,r,w,h-r,fill=fill,outline='')
            c.create_arc(0,0,2*r,2*r,start=90,extent=90,fill=fill,outline=fill)
            c.create_arc(w-2*r,0,w,2*r,start=0,extent=90,fill=fill,outline=fill)
            c.create_arc(0,h-2*r,2*r,h,start=180,extent=90,fill=fill,outline=fill)
            c.create_arc(w-2*r,h-2*r,w,h,start=270,extent=90,fill=fill,outline=fill)
            
            try:
                total_w = sum(int(self.mat_tree.column(col, 'width')) for col in ['#0'] + list(self.mat_tree['columns']))
                x_offset = float(self.mat_tree.xview()[0]) * total_w
            except Exception:
                x_offset = 0
            
            x0 = -x_offset
            
            cols=[('#0','')]+[(f'#{i}',txt) for i,(key,txt, _) in enumerate(self._mat_header_specs,1)]
            for idx,(col,txt) in enumerate(cols):
                try: cw=int(self.mat_tree.column(col,'width'))
                except Exception: cw=0
                
                # We skip drawing fixed columns inside the scrolling loop
                if col in ('#0', '#11', '#12', '#13'):
                    x0+=cw; continue
                
                align = 'w' if col in ('#1', '#2', '#3') else 'center'
                anchor_x = x0+12 if align == 'w' else x0+cw/2
                c.create_text(anchor_x,h/2,text=txt,fill='#60769D',font=('Segoe UI',9,'bold'),anchor=align)
                c.create_line(x0+cw, 6, x0+cw, h-6, fill=self.colors.get('line', '#E5ECF5'))
                x0+=cw
                
            # Draw LEFT fixed cover
            try: cw0=int(self.mat_tree.column('#0','width'))
            except Exception: cw0=60
            if cw0 > 0:
                # Cover the left area, but leave top-left and bottom-left corners empty!
                c.create_rectangle(r, 0, cw0, h, fill=fill, outline='')
                c.create_rectangle(0, r, cw0, h-r, fill=fill, outline='')
                c.create_arc(0, 0, 2*r, 2*r, start=90, extent=90, fill=fill, outline=fill)
                c.create_arc(0, h-2*r, 2*r, h, start=180, extent=90, fill=fill, outline=fill)
                c.create_line(cw0, 6, cw0, h-6, fill=self.colors.get('line', '#E5ECF5'))
                
                # Draw "Select All" checkbox
                key = str(self.mat_tree)
                checked = self._checked_rows.get(key, set())
                children = self.mat_tree.get_children()
                is_all_checked = len(checked) == len(children) and len(children) > 0
                
                txt_chk = '☑' if is_all_checked else '☐'
                color_chk = '#2B3D55' if is_all_checked else '#A0ABB9'
                if getattr(self, '_dark', False): color_chk = '#FFFFFF' if is_all_checked else '#60769D'
                
                chk_id = c.create_text(cw0/2, h/2, text=txt_chk, fill=color_chk, font=('Segoe UI', 13), anchor='center', tags=('header_chk',))
                hitbox_id = c.create_rectangle(0, 0, cw0-2, h, fill='', outline='', tags=('header_chk',))
                c.tag_bind('header_chk', '<Button-1>', lambda e: self._toggle_all_checkboxes(self.mat_tree))
                
            # Draw RIGHT fixed cover
            try:
                cw11 = int(self.mat_tree.column('#11','width'))
                cw12 = int(self.mat_tree.column('#12','width'))
                cw13 = int(self.mat_tree.column('#13','width'))
                fixed_right_w = cw11 + cw12 + cw13
            except Exception:
                fixed_right_w = 120
            
            if fixed_right_w > 0:
                start_x = w - fixed_right_w
                # Cover the right area, but leave top-right and bottom-right corners empty!
                c.create_rectangle(start_x, 0, w-r, h, fill=fill, outline='')
                c.create_rectangle(start_x, r, w, h-r, fill=fill, outline='')
                c.create_arc(w-2*r, 0, w, 2*r, start=0, extent=90, fill=fill, outline=fill)
                c.create_arc(w-2*r, h-2*r, w, h, start=270, extent=90, fill=fill, outline=fill)
                c.create_line(start_x, 6, start_x, h-6, fill=self.colors.get('line', '#E5ECF5'))
                
                cx = start_x
                if cw11 > 0:
                    img=self._mat_header_imgs.get('edit')
                    if img: c.create_image(cx+cw11/2, h/2, image=img, anchor='center')
                    cx += cw11
                if cw12 > 0:
                    img=self._mat_header_imgs.get('delete')
                    if img: c.create_image(cx+cw12/2, h/2, image=img, anchor='center')
        self._redraw_mat_header=redraw_mat_header
        self.mat_header.bind('<Configure>', redraw_mat_header)
        self.mat_tree.bind('<Configure>', lambda e: self.mat_tree.after_idle(redraw_mat_header))
        self.after_idle(redraw_mat_header)
        
        self._setup_canvas_header_drag(self.mat_header, self.mat_tree, ['edit','delete','options'], redraw_mat_header, 'mat')

        self.mat_tree.bind('<Button-1>',lambda e:self._tree_click(e,self.mat_tree,'material'))
        self.mat_tree.bind('<Double-1>',lambda e:self.edit_selected_material())
        
        self.mat_icon_ov=self._attach_row_icon_overlay(
            self.mat_tree, table_host, 10, 11,
            self.edit_selected_material, self.delete_selected_material)
            
        self._action_buttons[self.mat_tree]={'normal':[mat_add,mat_history],'bulk':[self.mat_bulk_delete_btn]}
        
        try:
            from PIL import Image, ImageTk
            img_path = UI_ASSETS / 'empty_state_reference_exact.png'
            self._mat_empty_img = ImageTk.PhotoImage(Image.open(img_path))
            self.mat_empty_overlay = tk.Label(table_host, image=self._mat_empty_img, text='Nenhum insumo encontrado.', compound='top', bg=self.colors['field'], fg=self.colors['muted'], font=('Segoe UI', 10), pady=10)
        except Exception:
            self.mat_empty_overlay = tk.Label(table_host, text='Nenhum insumo encontrado.', bg=self.colors['field'], fg=self.colors['muted'], font=('Segoe UI', 10))

    def material_form(self, edit_id=None):
        is_edit = edit_id is not None
        with db() as c:
            existing = c.execute('SELECT * FROM materials WHERE id=?', (edit_id,)).fetchone() if is_edit else None
        d = Modal(self, 'Editar item' if is_edit else 'Novo item', '720x500')
        vars = {k: tk.StringVar() for k in ('name','brand','qty','unit','value','category','date')}
        if existing:
            for k in vars:
                if k == 'date': vars[k].set(date.today().isoformat())
                elif k == 'qty': vars[k].set(fmt_num(existing['purchase_qty']))
                elif k == 'value': vars[k].set(fmt(existing['purchase_value']))
                elif k == 'unit': vars[k].set(existing['purchase_unit'])
                elif k == 'category': vars[k].set(existing['category'] or 'Comestível')
                elif k == 'name': vars[k].set(existing['name'])
                elif k == 'brand': vars[k].set(existing['brand'] or '')
        else:
            vars['unit'].set(''); vars['category'].set('Comestível'); vars['date'].set(date.today().isoformat())
        form = ttk.Frame(d, padding=18); form.pack(fill='both', expand=True)
        fields = [
            ('Nome *','name',0,0),('Marca','brand',0,1),('Quantidade *','qty',1,0),('Unidade *','unit',1,1),
            ('Valor da compra *','value',2,0),('Categoria *','category',2,1),('Data *','date',3,0)
        ]
        for label,key,row,col in fields:
            ttk.Label(form,text=label).grid(row=row*2,column=col,sticky='w',padx=6,pady=(4,0))
            if key == 'unit':
                w=ttk.Combobox(form,textvariable=vars[key],values=UNITS,state='readonly',width=20)
            elif key == 'category':
                w=ttk.Combobox(form,textvariable=vars[key],values=('Comestível','Não comestível','Doação'),state='readonly',width=20)
            elif key == 'value':
                w=masked_money_entry(form, vars[key], width=28)
            elif key == 'qty':
                w=numeric_entry(form, vars[key], width=28)
            else:
                w,_entry=rounded_entry(form, vars[key], width=28)
            w.grid(row=row*2+1,column=col,sticky='ew',padx=6,pady=(0,8))
        form.columnconfigure(0,weight=1); form.columnconfigure(1,weight=1)
        ttk.Label(form,text='* campo obrigatório').grid(row=8,column=0,columnspan=2,sticky='w',padx=6,pady=8)
        def save():
            try:
                name = vars['name'].get().strip(); brand = vars['brand'].get().strip(); unit = vars['unit'].get().strip(); category = vars['category'].get().strip()
                if not name: raise ValueError('O campo "Nome" é obrigatório.')
                if not unit: raise ValueError('O campo "Unidade" é obrigatório.')
                if not category: raise ValueError('O campo "Categoria" é obrigatório.')
                qty = to_float(vars['qty'].get(),'Quantidade')
                value = money_to_float(vars['value'].get(),'Valor da compra')
                if qty <= 0: raise ValueError('A Quantidade deve ser maior que zero.')
                if value < 0: raise ValueError('O Valor da compra não pode ser negativo.')
                if value == 0 and category != 'Doação': raise ValueError('Valor zero só é permitido para itens da categoria Doação.')
                purchase_date = vars['date'].get().strip()
                if not purchase_date: raise ValueError('O campo "Data" é obrigatório.')
                if is_edit:
                    with db() as c: before = dict(c.execute('SELECT * FROM materials WHERE id=?', (edit_id,)).fetchone())
                    self.ask_edit_reason('INSUMO', edit_id, before, {'name':name,'purchase_qty':qty,'purchase_unit':unit,'purchase_value':value,'brand':brand,'category':category})
                with db() as c:
                    if is_edit:
                        mid = edit_id
                        c.execute('UPDATE materials SET name=?,purchase_qty=?,purchase_unit=?,purchase_value=?,brand=?,category=?,updated_at=? WHERE id=?',
                                  (name,qty,unit,value,brand,category,now_iso(),edit_id))
                    else:
                        code = next_code('materials','INS')
                        cur = c.execute('INSERT INTO materials(code,name,purchase_qty,purchase_unit,purchase_value,brand,category,updated_at) VALUES(?,?,?,?,?,?,?,?)',
                                         (code,name,qty,unit,value,brand,category,now_iso()))
                        mid = cur.lastrowid
                        c.execute('INSERT INTO purchases(material_id,qty,unit,value,brand,purchase_date) VALUES(?,?,?,?,?,?)', (mid,qty,unit,value,brand,purchase_date))
                snapshot_costs(); d.destroy(); self.refresh_all(); self.notify('Insumo salvo com sucesso.')
            except Exception as e: safe_error(d,'Não foi possível salvar o item',e)
        act=d.action_host
        right=tk.Frame(act,bg=d.cget('bg'));right.pack(side='right',fill='y')
        RoundedActionButton(right,'Salvar',save,width=92,height=38,fill='#F28C28',hover='#D96F0B').pack(side='left',padx=(6,0),pady=7)
        RoundedActionButton(right,'Cancelar',d.destroy,width=92,height=38,fill='#6B7280',hover='#4B5563').pack(side='left',padx=(6,0),pady=7)

    def new_material(self): self.material_form()

    def delete_selected_material(self):
        s=self.mat_tree.selection()
        if not s or self._selection_count(self.mat_tree)!=1:return
        code=self.mat_tree.item(s[0])['values'][0]
        with db() as c:r=c.execute('SELECT id,name FROM materials WHERE code=?',(code,)).fetchone()
        if not r:return
        with db() as c:
            refs=(c.execute('SELECT COUNT(*) n FROM base_recipe_items WHERE material_id=?',(r['id'],)).fetchone()['n']
                  + c.execute("SELECT COUNT(*) n FROM product_items WHERE item_type='MATERIAL' AND ref_id=?",(r['id'],)).fetchone()['n'])
        if refs:
            if messagebox.askyesno('Insumo vinculado', 'Este Insumo possui vínculos em receitas/produtos. Deseja inativá-lo em vez de excluir?', parent=self):
                with db() as c:c.execute('UPDATE materials SET active=0,updated_at=? WHERE id=?',(now_iso(),r['id']))
                self.refresh_all();self.notify('Insumo inativado com sucesso.')
            return
        if not messagebox.askyesno('Excluir Insumo', f'Excluir "{r["name"]}"? O histórico de compras e custos também será removido.', parent=self):return
        with db() as c:
            c.execute('DELETE FROM purchases WHERE material_id=?', (r['id'],))
            c.execute("DELETE FROM cost_history WHERE entity_type='MATERIAL' AND entity_id=?", (r['id'],))
            c.execute('DELETE FROM custom_units WHERE material_id=?', (r['id'],))
            c.execute('DELETE FROM materials WHERE id=?', (r['id'],))
        self.refresh_all();self.notify('Insumo excluído com sucesso.')

    def delete_selected_materials(self):
        self._bulk_delete_list(self.mat_tree,'material')

    def delete_selected_recipes(self):
        self._bulk_delete_list(self.rec_tree,'recipe')

    def _bulk_delete_list(self, tree, kind):
        checked=getattr(self,'_checked_rows',{}).get(str(tree),set())
        if len(checked)<2: return
        table={'material':'materials','recipe':'base_recipes','product':'products'}[kind]
        rows=[]
        with db() as c:
            for iid in checked:
                vals=tree.item(iid,'values'); code=vals[0] if vals else ''
                r=c.execute(f'SELECT id,name FROM {table} WHERE code=?',(code,)).fetchone()
                if r: rows.append(r)
        if not rows:return
        
        linked = []
        unlinked = []
        with db() as c:
            for r in rows:
                if kind == 'material':
                    refs = c.execute('SELECT COUNT(*) n FROM base_recipe_items WHERE material_id=?',(r['id'],)).fetchone()['n']
                    refs += c.execute("SELECT COUNT(*) n FROM product_items WHERE item_type='MATERIAL' AND ref_id=?",(r['id'],)).fetchone()['n']
                elif kind == 'recipe':
                    refs = c.execute("SELECT COUNT(*) n FROM product_items WHERE item_type='RECIPE_BASE' AND ref_id=?",(r['id'],)).fetchone()['n']
                elif kind == 'product':
                    refs = 0
                if refs > 0: linked.append(r)
                else: unlinked.append(r)
        
        msg = f'Você selecionou {len(rows)} itens.\n'
        if linked:
            msg += f'\n{len(linked)} itens possuem vínculos/dependências e serão INATIVADOS:\n'
            msg += '\n'.join('  - ' + r['name'] for r in linked) + '\n'
        if unlinked:
            msg += f'\nOs outros {len(unlinked)} itens (sem vínculos) serão EXCLUÍDOS permanentemente.\n'
            
        msg += '\nDeseja prosseguir? (Se escolher Não, toda a operação será cancelada).'
            
        if not messagebox.askyesno('Confirmar exclusão em lote', msg, parent=self): return
        
        with db() as c:
            for r in unlinked:
                if kind == 'material':
                    c.execute('DELETE FROM purchases WHERE material_id=?', (r['id'],))
                    c.execute("DELETE FROM cost_history WHERE entity_type='MATERIAL' AND entity_id=?", (r['id'],))
                    c.execute('DELETE FROM custom_units WHERE material_id=?', (r['id'],))
                elif kind == 'recipe':
                    c.execute("DELETE FROM cost_history WHERE entity_type='RECIPE_BASE' AND entity_id=?", (r['id'],))
                elif kind == 'product':
                    c.execute("DELETE FROM cost_history WHERE entity_type='PRODUCT' AND entity_id=?", (r['id'],))
                c.execute(f'DELETE FROM {table} WHERE id=?',(r['id'],))
            
            for r in linked:
                c.execute(f'UPDATE {table} SET active=0, updated_at=? WHERE id=?', (now_iso(), r['id']))
                
        self.refresh_all()
        self.notify(f'{len(unlinked)} excluídos, {len(linked)} inativados.')

    def edit_selected_material(self):
        s = self.mat_tree.selection()
        if not s:
            messagebox.showwarning('Cadastro','Selecione um item para editar.', parent=self); return
        code = self.mat_tree.item(s[0])['values'][0]
        with db() as c: r = c.execute('SELECT id FROM materials WHERE code=?',(code,)).fetchone()
        if r: self.material_form(r['id'])

    def ask_edit_reason(self, entity_type, entity_id, before, after):
        reason = simpledialog.askstring('Motivo da edição', 'Informe o motivo da alteração:', parent=self)
        if not reason or not reason.strip():
            raise ValueError('A edição exige um motivo.')
        record_edit(entity_type, entity_id, reason.strip(), {'antes': before, 'depois': after})

    def refresh_materials(self):
        if not hasattr(self,'mat_tree'): return
        for x in self.mat_tree.get_children(): self.mat_tree.delete(x)
        query = '%'+self.mat_search.get().strip()+'%' if hasattr(self,'mat_search') else '%'
        status_filter = self.mat_status.get() if hasattr(self, 'mat_status') else 'Ativos'
        status_cond = "COALESCE(active,1)=1" if status_filter == 'Ativos' else ("COALESCE(active,1)=0" if status_filter == 'Inativos' else "1=1")
        with db() as c:
            rows = c.execute(f'''SELECT code,name,COALESCE(brand,''),purchase_qty,purchase_unit,purchase_value,category,
                                       substr(created_at,1,10), substr(COALESCE(updated_at,created_at),1,10), COALESCE(active,1), id
                                FROM materials WHERE {status_cond} AND (name LIKE ? OR COALESCE(brand,'') LIKE ? OR code LIKE ?) ORDER BY name''', (query,query,query)).fetchall()
        for r in rows:
            r_list = list(r)
            val = r_list[5]
            val_str = f'R$ {val:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
            r_list[5] = val_str
            is_active = r_list.pop(9)
            mat_id = r_list.pop(9)
            status_str = 'Ativo' if is_active else 'Inativo'
            self.mat_tree.insert('', 'end', iid=str(mat_id), text='☐', values=tuple(r_list)+(status_str, '','',''), tags=() if is_active else ('inactive',))
        self._reset_checked(self.mat_tree)
        if hasattr(self, 'mat_icon_ov'): self.mat_icon_ov._redraw()
        if hasattr(self,'mat_empty_overlay'):
            if rows:
                self.mat_empty_overlay.place_forget()
            else:
                self.mat_empty_overlay.place(x=0,y=43,relwidth=1,relheight=1,height=-43)

    def material_history_dialog(self):
        s=self.mat_tree.selection()
        if not s: return
        code=self.mat_tree.item(s[0])['values'][0]
        with db() as c:
            mid=c.execute('SELECT id FROM materials WHERE code=?',(code,)).fetchone()['id']
            rows=c.execute('SELECT purchase_date,qty,unit,value,COALESCE(brand,\'\') FROM purchases WHERE material_id=? ORDER BY id DESC',(mid,)).fetchall()
        ListDialog(self,'Histórico de compras',(('data','Data',100),('qtd','Qtd.',90),('un','Un.',65),('valor','Valor',100),('marca','Marca',140)),rows)

    def material_conversion_dialog(self):
        s=self.mat_tree.selection()
        if not s: return
        code=self.mat_tree.item(s[0])['values'][0]
        with db() as c: mat=c.execute('SELECT id,name FROM materials WHERE code=?',(code,)).fetchone()
        if not mat:return
        d=Modal(self,f'Conversões — {mat["name"]}','620x440')
        ttk.Label(d,text='As unidades configuráveis dependem do insumo. Ex.: xícara de leite ≠ xícara de farinha.').pack(anchor='w',padx=16,pady=12)
        form=ttk.Frame(d,padding=10);form.pack(fill='x')
        name=tk.StringVar(); base=tk.StringVar(value='ml'); factor=tk.StringVar()
        ttk.Label(form,text='Unidade configurável *').grid(row=0,column=0,padx=5,sticky='w'); ttk.Entry(form,textvariable=name,width=24).grid(row=1,column=0,padx=5)
        ttk.Label(form,text='Unidade interna *').grid(row=0,column=1,padx=5,sticky='w'); ttk.Combobox(form,textvariable=base,values=('mg','ml','un'),state='readonly',width=12).grid(row=1,column=1,padx=5)
        ttk.Label(form,text='Quantidade na unidade *').grid(row=0,column=2,padx=5,sticky='w'); ttk.Entry(form,textvariable=factor,width=18).grid(row=1,column=2,padx=5)
        tree=ttk.Treeview(d,columns=('name','base','factor'),show='headings')
        for k,t,w in [('name','Unidade',200),('base','Base',100),('factor','Equivale a',160)]: tree.heading(k,text=t);tree.column(k,width=w)
        tree.pack(fill='both',expand=True,padx=16,pady=12)
        def refresh():
            for x in tree.get_children():tree.delete(x)
            for r in custom_units_for_material(mat['id']):tree.insert('','end',values=(r['name'],r['base_unit'],r['factor_to_base']))
        def add():
            try:
                n=name.get().strip(); b=base.get().strip(); f=to_float(factor.get(),'Quantidade na unidade')
                if not n: raise ValueError('O nome da unidade configurável é obrigatório.')
                if not b: raise ValueError('A unidade interna é obrigatória.')
                if f<=0: raise ValueError('A quantidade na unidade configurável deve ser maior que zero.')
                with db() as c:c.execute('INSERT INTO custom_units(material_id,name,base_unit,factor_to_base) VALUES(?,?,?,?)',(mat['id'],n,b,f))
                name.set('');factor.set('');refresh()
            except Exception as e:safe_error(d,'Não foi possível salvar a conversão',e)
        ttk.Button(form,text='Adicionar',command=add).grid(row=1,column=3,padx=8)
        refresh(); ttk.Button(d,text='Fechar',command=d.destroy).pack(pady=(0,12))

    # ---------- Receitas ----------
    def recipes_page(self, f):
        _, bar=self._build_page_toolbar(f)
        rec_add=RoundedActionButton(bar,'＋  Nova Receita',lambda: self._run_normal_action(self.rec_tree, self.new_recipe),width=150,height=40,fill='#2F67B1',hover='#255894'); rec_add.pack(side='left')
        self.rec_bulk_delete_btn=RoundedActionButton(bar, '🗑 Excluir', lambda: self._run_normal_action(self.rec_tree, self.delete_selected_recipes), width=120, height=40, fill='#FCE8E8', hover='#F9D1D1', fg='#D93838')
        rec_import=RoundedActionButton(bar,'Importar Word/PDF',lambda: self._run_normal_action(self.rec_tree, self.import_recipe_document),width=155,height=40,fill='#EFF4FB',hover='#E3EBF6',fg='#1D3557'); rec_import.pack(side='left',padx=10)
        rec_export=RoundedActionButton(bar,'Exportar Receita',lambda: self._run_normal_action(self.rec_tree, self.export_selected_recipe),width=145,height=40,fill='#EFF4FB',hover='#E3EBF6',fg='#1D3557'); rec_export.pack(side='left',padx=10)
        rec_original=RoundedActionButton(bar,'Documento original',lambda: self._run_normal_action(self.rec_tree, self.open_original_document),width=165,height=40,fill='#EFF4FB',hover='#E3EBF6',fg='#1D3557'); rec_original.pack(side='left',padx=10)
        rec_history=RoundedActionButton(bar,'Histórico',lambda: self._run_normal_action(self.rec_tree, self.recipe_history_dialog),width=125,height=40,fill='#EFF4FB',hover='#E3EBF6',fg='#1D3557'); rec_history.pack(side='left',padx=10)
        _, table_host = self._build_page_table_panel(f)
        self.rec_tree=ttk.Treeview(table_host,columns=('code','name','yield','unit','cost','edit','delete','dummy'),show='tree headings')
        self.rec_tree.column('#0',width=44,minwidth=44,stretch=False);self.rec_tree.heading('#0',text='')
        for k,t,w in [('code','Código',95),('name','Receita',280),('yield','Rendimento',120),('unit','Un.',65),('cost','Custo total',120),('edit','',30),('delete','',30)]:
            kw={'text':t}
            if k=='edit': kw['image']=self._action_photo('action_edit_small.png')
            if k=='delete': kw['image']=self._action_photo('action_delete_small.png')
            self.rec_tree.heading(k,**kw)
            self.rec_tree.column(k,width=w,minwidth=w,anchor='center' if k in ('yield','unit','cost') else 'w',stretch=False)
        self.rec_tree.column('dummy', width=0, minwidth=0, stretch=True); self.rec_tree.heading('dummy', text='')
        self.rec_tree.pack(fill='both',expand=True)
        self._action_buttons[self.rec_tree]={'normal':[rec_add,rec_import,rec_export,rec_original,rec_history],'bulk':[self.rec_bulk_delete_btn]};self.rec_tree.bind('<Button-1>',lambda e:self._tree_click(e,self.rec_tree,'recipe'));self.rec_tree.bind('<Double-1>',lambda e:self._on_native_tree_double_click(e,self.rec_tree,self.edit_selected_recipe));self._update_action_states()

    def recipe_form(self, edit_id=None, imported_items=None, imported_source=None):
        is_edit=edit_id is not None
        with db() as c:
            existing=c.execute('SELECT * FROM base_recipes WHERE id=?',(edit_id,)).fetchone() if is_edit else None
            current_items=c.execute('SELECT material_id,qty,unit FROM base_recipe_items WHERE recipe_id=?',(edit_id,)).fetchall() if is_edit else []
        d=Modal(self,'Editar Receita' if is_edit else 'Nova Receita','900x760')
        name=tk.StringVar(value=existing['name'] if existing else '')
        yield_qty=tk.StringVar(value=fmt_num(existing['yield_qty']) if existing and existing['yield_qty'] is not None else '')
        yield_unit=tk.StringVar(value=existing['yield_unit'] if existing and existing['yield_unit'] else 'g')
        notes=tk.StringVar(value=existing['notes'] or '' if existing else '')
        top=ttk.Frame(d,padding=16);top.pack(fill='x')
        ttk.Label(top,text='Nome *').grid(row=0,column=0,sticky='w');rounded_entry(top,name,width=30)[0].grid(row=1,column=0,padx=(0,8),sticky='ew')
        ttk.Label(top,text='Rendimento').grid(row=0,column=1,sticky='w');numeric_entry(top,yield_qty,width=16).grid(row=1,column=1,padx=8)
        ttk.Label(top,text='Unidade').grid(row=0,column=2,sticky='w');ttk.Combobox(top,textvariable=yield_unit,values=UNITS,state='readonly',width=10).grid(row=1,column=2,padx=8)
        ttk.Label(top,text='Observações').grid(row=0,column=3,sticky='w');rounded_entry(top,notes,width=30)[0].grid(row=1,column=3,padx=8,sticky='ew')
        box=ttk.LabelFrame(d,text='Composição — somente itens do Cadastro',padding=12);box.pack(fill='both',expand=True,padx=16,pady=10)
        material_var=tk.StringVar();qty_var=tk.StringVar();unit_var=tk.StringVar(value='g')
        ttk.Label(box,text='Insumo').grid(row=0,column=0,sticky='w'); material_cb=ttk.Combobox(box,textvariable=material_var,width=40)
        material_cb.grid(row=1,column=0,padx=(0,6),sticky='ew')
        ttk.Label(box,text='Quantidade').grid(row=0,column=1,sticky='w');numeric_entry(box,qty_var,width=14).grid(row=1,column=1,padx=6)
        ttk.Label(box,text='Unidade').grid(row=0,column=2,sticky='w');unit_cb=ttk.Combobox(box,textvariable=unit_var,values=UNITS,state='readonly',width=12);unit_cb.grid(row=1,column=2,padx=6)
        items=[]
        if current_items:
            for r in current_items:
                with db() as c: m=c.execute('SELECT id,code,name FROM materials WHERE id=?',(r['material_id'],)).fetchone()
                if m: items.append((m['id'],m['name'],r['qty'],r['unit']))
        if imported_items:
            items.extend(imported_items)
        tree=ttk.Treeview(box,columns=('item','qty','unit','cost'),show='headings')
        for k,t,w in [('item','Item',360),('qty','Quantidade',100),('unit','Un.',70),('cost','Custo',110)]:tree.heading(k,text=t);tree.column(k,width=w)
        tree.grid(row=2,column=0,columnspan=4,sticky='nsew',pady=12);box.rowconfigure(2,weight=1);box.columnconfigure(0,weight=1)
        def load_materials(*_):
            vals=[f'{r["id"]} — {r["name"]} ({r["code"]})' for r in list_names('materials')]
            material_cb['values']=vals
        def load_units(*_):
            if '—' not in material_var.get(): unit_cb['values']=UNITS; return
            mid=int(material_var.get().split(' — ')[0]); custom=[r['name'] for r in custom_units_for_material(mid)]; unit_cb['values']=UNITS+tuple(custom)
        material_cb.bind('<<ComboboxSelected>>',load_units)
        def refresh_items():
            for x in tree.get_children():tree.delete(x)
            for mid,n,q,u in items:
                try: cst=material_cost(mid,q,u)
                except Exception as e: cst=f'Erro'
                tree.insert('','end',values=(n,q,u,fmt(cst) if isinstance(cst,(int,float)) else cst))
        def add_item():
            try:
                if '—' not in material_var.get(): raise ValueError('Selecione um Insumo do Cadastro.')
                mid=int(material_var.get().split(' — ')[0]);q=to_float(qty_var.get(),'Quantidade');u=unit_var.get().strip()
                if q<=0:raise ValueError('A Quantidade deve ser maior que zero.')
                items.append((mid,material_var.get().split(' — ')[1].split(' (')[0],q,u));material_var.set('');qty_var.set('');refresh_items()
            except Exception as e:safe_error(d,'Não foi possível adicionar o item',e)
        ttk.Button(box,text='Adicionar',command=add_item).grid(row=1,column=3,padx=8)
        edit_item_btn=ttk.Button(box,text='✏',command=lambda: edit_item(),width=3)
        delete_item_btn=ttk.Button(box,text='🗑',command=lambda: delete_item(),width=3)
        edit_item_btn.grid(row=3,column=0,sticky='w',pady=(0,4))
        delete_item_btn.grid(row=3,column=1,sticky='w',pady=(0,4))
        def edit_item():
            sel=tree.selection()
            if not sel:
                messagebox.showwarning('Receita','Selecione um item da composição para editar.',parent=d); return
            idx=tree.index(sel[0]); mid,n,q,u=items[idx]
            material_var.set(f'{mid} — {n}')
            load_units()
            qty_var.set(fmt_num(q)); unit_var.set(u)
            items.pop(idx); refresh_items()

        def delete_item():
            sel=tree.selection()
            if not sel:
                messagebox.showwarning('Receita','Selecione um item da composição para excluir.',parent=d); return
            idx=tree.index(sel[0]); items.pop(idx); refresh_items()

        tree.bind('<Double-1>',lambda e: edit_item())
        def save():
            try:
                n=name.get().strip()
                if not n: raise ValueError('O campo "Nome" é obrigatório.')
                y=optional_float(yield_qty.get()); yu=yield_unit.get().strip() if y is not None else None
                if y is not None and y<=0: raise ValueError('O Rendimento deve ser maior que zero.')
                if not items: raise ValueError('Adicione pelo menos um Insumo à receita.')
                if is_edit:
                    with db() as c: before=dict(c.execute('SELECT * FROM base_recipes WHERE id=?',(edit_id,)).fetchone())
                    self.ask_edit_reason('RECEITA_BASE',edit_id,before,{'name':n,'yield_qty':y,'yield_unit':yu,'notes':notes.get().strip(),'items':[(m,q,u) for m,_,q,u in items]})
                with db() as c:
                    if is_edit:
                        rid=edit_id
                        c.execute('UPDATE base_recipes SET name=?,yield_qty=?,yield_unit=?,notes=?,updated_at=? WHERE id=?',(n,y,yu,notes.get().strip(),now_iso(),edit_id))
                        c.execute('DELETE FROM base_recipe_items WHERE recipe_id=?',(rid,))
                    else:
                        code=next_code('base_recipes','RB');cur=c.execute('INSERT INTO base_recipes(code,name,yield_qty,yield_unit,notes,updated_at) VALUES(?,?,?,?,?,?)',(code,n,y,yu,notes.get().strip(),now_iso()));rid=cur.lastrowid
                    for mid,_,q,u in items:c.execute('INSERT INTO base_recipe_items(recipe_id,material_id,qty,unit) VALUES(?,?,?,?)',(rid,mid,q,u))
                if imported_source:
                    save_uploaded_document('RECIPE_BASE', rid, imported_source)
                snapshot_costs();d.destroy();self.refresh_all();self.notify('Receita salva com sucesso.')
            except Exception as e:safe_error(d,'Não foi possível salvar a Receita',e)
        ttk.Label(d,text='* campo obrigatório; Rendimento pode ser definido depois.').pack(anchor='w',padx=16)
        act=d.action_host
        left=tk.Frame(act,bg=d.cget('bg'));left.pack(side='left',fill='y')
        FlatEmojiButton(left,'✏️',edit_item).pack(side='left',padx=(0,8),pady=7)
        FlatEmojiButton(left,'🗑️',delete_item).pack(side='left',pady=7)
        right=tk.Frame(act,bg=d.cget('bg'));right.pack(side='right',fill='y')
        RoundedActionButton(right,'Salvar',save,width=92,height=38,fill='#F28C28',hover='#D96F0B').pack(side='left',padx=(6,0),pady=7)
        RoundedActionButton(right,'Cancelar',d.destroy,width=92,height=38,fill='#6B7280',hover='#4B5563').pack(side='left',padx=(6,0),pady=7)
        load_materials();refresh_items()

    def new_recipe(self): self.recipe_form()

    def edit_selected_recipe(self):
        s=self.rec_tree.selection()
        if not s:return
        code=self.rec_tree.item(s[0])['values'][0]
        with db() as c:r=c.execute('SELECT id FROM base_recipes WHERE code=?',(code,)).fetchone()
        if r:self.recipe_form(r['id'])

    def delete_selected_recipe(self):
        s=self.rec_tree.selection()
        if not s:return
        code=self.rec_tree.item(s[0])['values'][0]
        with db() as c:r=c.execute('SELECT id,name FROM base_recipes WHERE code=?',(code,)).fetchone()
        if not r:return
        with db() as c:
            refs=0
            prodrefs=c.execute("SELECT COUNT(*) n FROM product_items WHERE item_type='RECIPE_BASE' AND ref_id=?",(r['id'],)).fetchone()['n']
        if refs or prodrefs:
            if messagebox.askyesno('Receita vinculada','Esta Receita possui vínculos e não pode ser excluída sem quebrar o histórico. Deseja inativá-la?',parent=self):
                with db() as c:c.execute('UPDATE base_recipes SET active=0,updated_at=? WHERE id=?',(now_iso(),r['id']))
                self.refresh_all();self.notify('Receita inativada com sucesso.')
            return
        if not messagebox.askyesno('Excluir Receita',f'Excluir "{r["name"]}"? Esta ação remove o registro e sua composição.',parent=self):return
        with db() as c:c.execute('DELETE FROM base_recipes WHERE id=?',(r['id'],))
        self.refresh_all()

    def refresh_recipes(self):
        if not hasattr(self,'rec_tree'):return
        for x in self.rec_tree.get_children():self.rec_tree.delete(x)
        with db() as c:rows=c.execute('SELECT id,code,name,yield_qty,yield_unit FROM base_recipes WHERE COALESCE(active,1)=1 ORDER BY name').fetchall()
        for r in rows:
            try:cost=recipe_cost(r['id'])
            except Exception:cost=0
            iid=self.rec_tree.insert('','end',text='☐',values=(r['code'],r['name'],fmt_num(r['yield_qty']),r['yield_unit'] or '-',fmt(cost),'✏️','🗑️'))
            with db() as c:
                comps=c.execute('SELECT m.name,bri.qty,bri.unit FROM base_recipe_items bri JOIN materials m ON m.id=bri.material_id WHERE bri.recipe_id=? ORDER BY bri.id',(r['id'],)).fetchall()
            for comp in comps:
                self.rec_tree.insert(iid,'end',text='  ',values=('',f'↳ {comp[0]}',fmt_num(comp[1]),comp[2],'-','',''))
        self._reset_checked(self.rec_tree)

    def import_recipe_document(self):
        path=filedialog.askopenfilename(parent=self,filetypes=[('Word','*.docx'),('PDF','*.pdf')])
        if not path:return
        try:
            text=extract_docx_text(path) if path.lower().endswith('.docx') else extract_pdf_text(path)
            parsed=parse_recipe_lines(text)
            if not parsed:
                raise ValueError('Não consegui identificar linhas de ingredientes automaticamente. O documento foi lido, mas nada será inventado.')
            items=[]
            unresolved=[]
            with db() as c:
                materials=c.execute('SELECT id,name FROM materials').fetchall()
            for name,qty,unit in parsed:
                matches=[m for m in materials if m['name'].strip().lower()==name.strip().lower()]
                if matches:
                    items.append((matches[0]['id'],matches[0]['name'],qty,unit))
                else:
                    unresolved.append((name,qty,unit))
            d=self.recipe_form(imported_items=items, imported_source=path)
            if unresolved:
                messagebox.showwarning('Importação', 'Alguns itens não foram associados porque não existem no Cadastro:\n\n'+'\n'.join(f'- {n} ({q} {u})' for n,q,u in unresolved)+'\n\nCadastre-os e adicione-os manualmente.', parent=self)
        except Exception as e:safe_error(self,'Não foi possível importar o documento',e)

    def export_selected_recipe(self):
        s=self.rec_tree.selection()
        if not s:return
        code=self.rec_tree.item(s[0])['values'][0]
        with db() as c:r=c.execute('SELECT id,name,yield_qty,yield_unit,notes FROM base_recipes WHERE code=?',(code,)).fetchone()
        if not r:return
        path=filedialog.asksaveasfilename(parent=self,defaultextension='.txt',filetypes=[('Documento de texto','*.txt'),('Word','*.docx'),('PDF','*.pdf')],initialfile=f'{r["name"]}.txt')
        if not path:return
        text=self.recipe_export_text(r['id'])
        try:
            if path.lower().endswith('.txt'):
                Path(path).write_text(text,encoding='utf-8')
            elif path.lower().endswith('.docx'):
                try:
                    from docx import Document
                except ImportError: raise RuntimeError('Para exportar Word, instale "python-docx".')
                doc=Document();doc.add_heading(r['name'],0)
                for line in text.splitlines():doc.add_paragraph(line)
                doc.save(path)
            else:
                try:
                    from reportlab.pdfgen import canvas
                except ImportError: raise RuntimeError('Para exportar PDF, instale "reportlab".')
                c=canvas.Canvas(path);y=800
                for line in text.splitlines():
                    c.drawString(40,y,line[:110]);y-=16
                    if y<50:c.showPage();y=800
                c.save()
            messagebox.showinfo('Exportação','Receita exportada com sucesso.',parent=self)
        except Exception as e:safe_error(self,'Não foi possível exportar a receita',e)

    def recipe_export_text(self,rid):
        with db() as c:
            r=c.execute('SELECT * FROM base_recipes WHERE id=?',(rid,)).fetchone()
            rows=c.execute('''SELECT m.id,m.name,bri.qty,bri.unit FROM base_recipe_items bri JOIN materials m ON m.id=bri.material_id WHERE bri.recipe_id=?''',(rid,)).fetchall()
        lines=[r['name'],'',f'Rendimento: {fmt_num(r["yield_qty"])} {r["yield_unit"] or ""}'.strip(),'','Composição:']
        for x in rows:
            try:cst=material_cost(x['id'],x['qty'],x['unit'])
            except Exception:cst=0
            lines.append(f'- {x["name"]}: {fmt_num(x["qty"])} {x["unit"]} — {fmt(cst)}')
        lines += ['',f'Custo total: {fmt(recipe_cost(rid))}']
        return '\n'.join(lines)

    def _material_id_by_name(self,name):
        with db() as c:return c.execute('SELECT id FROM materials WHERE name=?',(name,)).fetchone()['id']

    def recipe_history_dialog(self):
        s=self.rec_tree.selection()
        if not s:return
        code=self.rec_tree.item(s[0])['values'][0]
        with db() as c:r=c.execute('SELECT id FROM base_recipes WHERE code=?',(code,)).fetchone()
        if not r:return
        with db() as c:rows=c.execute("SELECT substr(recorded_at,1,7),cost,recorded_at FROM cost_history WHERE entity_type='RECIPE_BASE' AND entity_id=? ORDER BY id DESC",(r['id'],)).fetchall()
        ListDialog(self,'Histórico de custo da Receita',(('mes','Mês',100),('custo','Custo',120),('registro','Registro',180)),rows)

    def open_original_document(self):
        s=self.rec_tree.selection()
        if not s:return
        code=self.rec_tree.item(s[0])['values'][0]
        with db() as c:r=c.execute('SELECT id,name FROM base_recipes WHERE code=?',(code,)).fetchone()
        doc=latest_document('RECIPE_BASE',r['id']) if r else None
        if not doc or not Path(doc['stored_path']).exists():messagebox.showinfo('Documento','Esta Receita não possui documento original armazenado.',parent=self);return
        import os; os.startfile(doc['stored_path'])

    # ---------- Produtos ----------
    def products_page(self,f):
        _, bar=self._build_page_toolbar(f)
        prod_add=RoundedActionButton(bar,'＋  Novo Produto',lambda: self._run_normal_action(self.prod_tree, self.new_product),width=150,height=40,fill='#2F67B1',hover='#255894'); prod_add.pack(side='left')
        self.prod_bulk_delete_btn=RoundedActionButton(bar, '🗑 Excluir', lambda: self._run_normal_action(self.prod_tree, self.delete_selected_products), width=120, height=40, fill='#FCE8E8', hover='#F9D1D1', fg='#D93838')
        prod_history=RoundedActionButton(bar,'Histórico',lambda: self._run_normal_action(self.prod_tree, self.product_history_dialog),width=125,height=40,fill='#EFF4FB',hover='#E3EBF6',fg='#1D3557'); prod_history.pack(side='left',padx=10)
        _, table_host = self._build_page_table_panel(f)
        self.prod_tree=ttk.Treeview(table_host,columns=('code','name','weight','cost','price','margin','edit','delete','dummy'),show='tree headings')
        self.prod_tree.column('#0',width=44,minwidth=44,stretch=False);self.prod_tree.heading('#0',text='')
        for k,t,w in [('code','Código',95),('name','Produto',300),('weight','Peso/Rendimento',120),('cost','Custo total',110),('price','Preço',110),('margin','Margem',90),('edit','',30),('delete','',30)]:
            kw={'text':t}
            if k=='edit': kw['image']=self._action_photo('action_edit_small.png')
            if k=='delete': kw['image']=self._action_photo('action_delete_small.png')
            self.prod_tree.heading(k,**kw)
            self.prod_tree.column(k,width=w,minwidth=w,anchor='center' if k in ('weight','cost','price','margin') else 'w',stretch=False)
        self.prod_tree.column('dummy', width=0, minwidth=0, stretch=True); self.prod_tree.heading('dummy', text='')
        self.prod_tree.pack(fill='both',expand=True)
        self._action_buttons[self.prod_tree]={'normal':[prod_add,prod_history],'bulk':[self.prod_bulk_delete_btn]};self.prod_tree.bind('<Button-1>',lambda e:self._tree_click(e,self.prod_tree,'product'));self.prod_tree.bind('<Double-1>',lambda e:self._on_native_tree_double_click(e,self.prod_tree,self.edit_selected_product));self._update_action_states()

    def product_form(self, edit_id=None):
        is_edit=edit_id is not None
        with db() as c:
            existing=c.execute('SELECT * FROM products WHERE id=?',(edit_id,)).fetchone() if is_edit else None
            current=c.execute('SELECT * FROM product_items WHERE product_id=?',(edit_id,)).fetchall() if is_edit else []
        d=Modal(self,'Editar Produto' if is_edit else 'Novo Produto','920x680')
        name=tk.StringVar(value=existing['name'] if existing else '')
        weight=tk.StringVar(value=fmt_num(existing['weight_qty']) if existing and existing['weight_qty'] is not None else '')
        weight_unit=tk.StringVar(value=existing['weight_unit'] if existing and existing['weight_unit'] else 'g')
        price=tk.StringVar(value=fmt(existing['sale_price']) if existing and existing['sale_price'] is not None else '')
        notes=tk.StringVar(value=existing['notes'] or '' if existing else '')
        top=ttk.Frame(d,padding=16);top.pack(fill='x')
        ttk.Label(top,text='Nome *').grid(row=0,column=0,sticky='w');rounded_entry(top,name,width=32)[0].grid(row=1,column=0,padx=(0,8),sticky='ew')
        ttk.Label(top,text='Peso/Rendimento').grid(row=0,column=1,sticky='w');numeric_entry(top,weight,width=16).grid(row=1,column=1,padx=8)
        ttk.Label(top,text='Unidade').grid(row=0,column=2,sticky='w');ttk.Combobox(top,textvariable=weight_unit,values=UNITS,state='readonly',width=10).grid(row=1,column=2,padx=8)
        ttk.Label(top,text='Preço de venda').grid(row=0,column=3,sticky='w');masked_money_entry(top, price, width=16).grid(row=1,column=3,padx=8)
        ttk.Label(top,text='Observações').grid(row=0,column=4,sticky='w');rounded_entry(top,notes,width=28)[0].grid(row=1,column=4,padx=8,sticky='ew')
        box=ttk.LabelFrame(d,text='Composição por unidade vendida',padding=12);box.pack(fill='both',expand=True,padx=16,pady=10)
        typ=tk.StringVar(value='');ref=tk.StringVar();qty=tk.StringVar();unit=tk.StringVar(value='');items=[]
        ttk.Label(box,text='Origem').grid(row=0,column=0,sticky='w');ttk.Combobox(box,textvariable=typ,values=('INSUMO','RECEITA','PRODUTO'),state='readonly',width=16).grid(row=1,column=0,padx=(0,6))
        ttk.Label(box,text='Item').grid(row=0,column=1,sticky='w');cb=ttk.Combobox(box,textvariable=ref,width=40);cb.grid(row=1,column=1,padx=6,sticky='ew')
        ttk.Label(box,text='Quantidade').grid(row=0,column=2,sticky='w');numeric_entry(box,qty,width=12).grid(row=1,column=2,padx=6)
        ttk.Label(box,text='Unidade').grid(row=0,column=3,sticky='w');unit_cb=ttk.Combobox(box,textvariable=unit,values=UNITS,state='readonly',width=9);unit_cb.grid(row=1,column=3,padx=6)
        tree=ttk.Treeview(box,columns=('type','item','qty','unit','cost'),show='headings')
        for k,t,w in [('type','Origem',120),('item','Componente',330),('qty','Qtd.',90),('unit','Un.',70),('cost','Custo',100)]:tree.heading(k,text=t);tree.column(k,width=w)
        tree.grid(row=2,column=0,columnspan=5,sticky='nsew',pady=12);box.rowconfigure(2,weight=1);box.columnconfigure(1,weight=1)
        for r in current:
            with db() as c:
                table={'MATERIAL':'materials','RECIPE_BASE':'base_recipes','PRODUCT':'products'}.get(r['item_type'])
                rr=c.execute(f'SELECT id,name FROM {table} WHERE id=?',(r['ref_id'],)).fetchone() if table else None
            if rr: items.append((r['item_type'],r['ref_id'],rr['name'],r['qty_per_unit'],r['unit']))
        def load_ref(*_):
            typemap={'INSUMO':'materials','RECEITA':'base_recipes','PRODUTO':'products'}
            table=typemap[typ.get()];vals=[]
            current_pid=edit_id
            for r in list_names(table):
                if table=='products' and current_pid and r['id']==current_pid:continue
                vals.append(f'{r["id"]} — {r["name"]}')
            cb['values']=vals;ref.set('');unit_cb['values']=UNITS
        typ.trace_add('write',load_ref)
        def add():
            try:
                if '—' not in ref.get():raise ValueError('Selecione um componente relacionado ao Cadastro, Receita ou Produto.')
                qv=to_float(qty.get(),'Quantidade');uv=unit.get().strip();rid=int(ref.get().split(' — ')[0])
                if qv<=0:raise ValueError('A Quantidade deve ser maior que zero.')
                table={'INSUMO':'materials','RECEITA':'base_recipes','PRODUTO':'products'}[typ.get()]
                with db() as c:rr=c.execute(f'SELECT name FROM {table} WHERE id=?',(rid,)).fetchone()
                if not rr: raise ValueError('O componente selecionado não foi encontrado.')
                internal={'INSUMO':'MATERIAL','RECEITA':'RECIPE_BASE','PRODUTO':'PRODUCT'}[typ.get()]
                items.append((internal,rid,rr['name'],qv,uv));refresh_items();qty.set('')
            except Exception as e:safe_error(d,'Não foi possível adicionar o componente',e)
        def refresh_items():
            for x in tree.get_children():tree.delete(x)
            for it in items:
                t,r,n,qv,uv=it
                try:cst=item_cost(t,r,qv,uv)
                except Exception:cst=0
                tree.insert('','end',values=({'MATERIAL':'INSUMO','RECIPE_BASE':'RECEITA','PRODUCT':'PRODUTO'}.get(t,t),n,qv,uv,fmt(cst)))
        ttk.Button(box,text='Adicionar',command=add).grid(row=1,column=4,padx=7)
        def edit_item():
            sel=tree.selection()
            if not sel:
                messagebox.showwarning('Produto','Selecione um componente para editar.',parent=d); return
            idx=tree.index(sel[0]); t,r,n,qv,uv=items[idx]
            display={'MATERIAL':'INSUMO','RECIPE_BASE':'RECEITA','PRODUCT':'PRODUTO'}[t]
            typ.set(display); load_ref()
            ref.set(f'{r} — {n}'); qty.set(fmt_num(qv)); unit.set(uv)
            items.pop(idx); refresh_items()
        def delete_item():
            sel=tree.selection()
            if not sel:
                messagebox.showwarning('Produto','Selecione um componente para excluir.',parent=d); return
            items.pop(tree.index(sel[0])); refresh_items()
        FlatEmojiButton(box,'✏️',edit_item).grid(row=3,column=0,sticky='w',padx=0,pady=(0,4))
        FlatEmojiButton(box,'🗑️',delete_item).grid(row=3,column=1,sticky='w',padx=8,pady=(0,4))
        tree.bind('<Double-1>',lambda e: edit_item())
        def save():
            try:
                n=name.get().strip()
                if not n:raise ValueError('O campo "Nome" é obrigatório.')
                w=optional_float(weight.get())
                if w is not None and w<=0:raise ValueError('O Peso/Rendimento deve ser maior que zero.')
                pv=money_to_float(price.get(),'Preço de venda') if price.get().strip() else None
                if pv is not None and pv<0:raise ValueError('O Preço de venda não pode ser negativo.')
                if not items:raise ValueError('Adicione pelo menos um componente ao Produto.')
                if is_edit:
                    with db() as c: before=dict(c.execute('SELECT * FROM products WHERE id=?',(edit_id,)).fetchone())
                    self.ask_edit_reason('PRODUTO',edit_id,before,{'name':n,'weight_qty':w,'weight_unit':weight_unit.get(),'sale_price':pv,'notes':notes.get().strip(),'items':[(i[0],i[1],i[3],i[4]) for i in items]})
                with db() as c:
                    if is_edit:
                        pid=edit_id
                        c.execute('UPDATE products SET name=?,weight_qty=?,weight_unit=?,sale_price=?,notes=?,updated_at=? WHERE id=?',(n,w,weight_unit.get() if w is not None else None,pv,notes.get().strip(),now_iso(),edit_id))
                        c.execute('DELETE FROM product_items WHERE product_id=?',(pid,))
                    else:
                        code=next_code('products','PROD');cur=c.execute('INSERT INTO products(code,name,weight_qty,weight_unit,sale_price,notes,updated_at) VALUES(?,?,?,?,?,?,?)',(code,n,w,weight_unit.get() if w is not None else None,pv,notes.get().strip(),now_iso()));pid=cur.lastrowid
                    for t,r,qv,uv in [(i[0],i[1],i[3],i[4]) for i in items]:c.execute('INSERT INTO product_items(product_id,item_type,ref_id,qty_per_unit,unit) VALUES(?,?,?,?,?)',(pid,t,r,qv,uv))
                snapshot_costs();d.destroy();self.refresh_all();self.notify('Produto salvo com sucesso.')
            except Exception as e:safe_error(d,'Não foi possível salvar o Produto',e)
        ttk.Label(d,text='* campo obrigatório; peso/rendimento e preço podem ser definidos depois.').pack(anchor='w',padx=16)
        act=d.action_host
        left=tk.Frame(act,bg=d.cget('bg'));left.pack(side='left',fill='y')
        FlatEmojiButton(left,'✏️',edit_item).pack(side='left',padx=(0,8),pady=7)
        FlatEmojiButton(left,'🗑️',delete_item).pack(side='left',pady=7)
        right=tk.Frame(act,bg=d.cget('bg'));right.pack(side='right',fill='y')
        RoundedActionButton(right,'Salvar',save,width=92,height=38,fill='#F28C28',hover='#D96F0B').pack(side='left',padx=(6,0),pady=7)
        RoundedActionButton(right,'Cancelar',d.destroy,width=92,height=38,fill='#6B7280',hover='#4B5563').pack(side='left',padx=(6,0),pady=7)
        load_ref();refresh_items()

    def new_product(self): self.product_form()

    def edit_selected_product(self):
        s=self.prod_tree.selection()
        if not s:return
        code=self.prod_tree.item(s[0])['values'][0]
        with db() as c:r=c.execute('SELECT id FROM products WHERE code=?',(code,)).fetchone()
        if r:self.product_form(r['id'])

    def delete_selected_product(self):
        s=self.prod_tree.selection()
        if not s:return
        code=self.prod_tree.item(s[0])['values'][0]
        with db() as c:r=c.execute('SELECT id,name FROM products WHERE code=?',(code,)).fetchone()
        if not r:return
        with db() as c:
            refs=c.execute("SELECT COUNT(*) n FROM product_items WHERE item_type='PRODUCT' AND ref_id=?",(r['id'],)).fetchone()['n']
        if refs:
            if messagebox.askyesno('Produto vinculado','Este Produto possui vínculos/histórico e não pode ser excluído sem quebrar o histórico. Deseja inativá-lo?',parent=self):
                with db() as c:c.execute('UPDATE products SET active=0,updated_at=? WHERE id=?',(now_iso(),r['id']))
                self.refresh_all();self.notify('Produto inativado com sucesso.')
            return
        if not messagebox.askyesno('Excluir Produto',f'Excluir "{r["name"]}"? Esta ação remove o registro e sua composição.',parent=self):return
        with db() as c:c.execute('DELETE FROM products WHERE id=?',(r['id'],))
        self.refresh_all()

    def delete_selected_products(self):
        tree=self.prod_tree
        checked=getattr(self,'_checked_rows',{}).get(str(tree),set())
        parents=[iid for iid in checked if not tree.parent(iid)]
        if len(parents)<2:
            return
        rows=[]
        with db() as c:
            for iid in parents:
                vals=tree.item(iid,'values'); code=vals[0] if vals else ''
                r=c.execute('SELECT id,name FROM products WHERE code=?',(code,)).fetchone()
                if r: rows.append(r)
        if not rows:return
        linked=[]
        with db() as c:
            for r in rows:
                refs=c.execute("SELECT COUNT(*) n FROM product_items WHERE item_type='PRODUCT' AND ref_id=?",(r['id'],)).fetchone()['n']
                if refs: linked.append(r['name'])
        if linked:
            msg='Alguns produtos selecionados possuem vínculos/histórico e não podem ser excluídos sem quebrar referências:\n\n'+'\n'.join('• '+n for n in linked)+'\n\nDeseja inativá-los? Se escolher Não, toda a operação será cancelada.'
            if not messagebox.askyesno('Itens vinculados',msg,parent=self):
                return
            with db() as c:
                c.execute('CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY)') if False else None
                cols={x['name'] for x in c.execute('PRAGMA table_info(products)').fetchall()}
                if 'active' in cols:
                    for r in rows:
                        if r['name'] in linked:c.execute('UPDATE products SET active=0,updated_at=? WHERE id=?',(now_iso(),r['id']))
                else:
                    messagebox.showwarning('Inativação','Esta base ainda não possui o campo de inativação. A operação foi cancelada para preservar os vínculos.',parent=self);return
            self.refresh_all();self.notify('Produtos vinculados foram inativados.');return
        if not messagebox.askyesno('Excluir produtos',f'Excluir {len(rows)} produtos selecionados? Esta ação remove suas composições.',parent=self):
            return
        with db() as c:
            for r in rows:c.execute('DELETE FROM products WHERE id=?',(r['id'],))
        self.refresh_all();self.notify(f'{len(rows)} produtos excluídos com sucesso.')

    def refresh_products(self):
        if not hasattr(self,'prod_tree'):return
        for x in self.prod_tree.get_children():self.prod_tree.delete(x)
        with db() as c:rows=c.execute('SELECT id,code,name,weight_qty,weight_unit,sale_price FROM products WHERE COALESCE(active,1)=1 ORDER BY name').fetchall()
        for r in rows:
            try:cost=product_unit_cost(r['id'])
            except Exception:cost=0
            margin=((r['sale_price']-cost)/r['sale_price']*100) if r['sale_price'] else None
            iid=self.prod_tree.insert('','end',text='☐',values=(r['code'],r['name'],(fmt_num(r['weight_qty'])+' '+str(r['weight_unit'] or '')).strip() or '-',fmt(cost),fmt(r['sale_price']),f'{margin:.1f}%' if margin is not None else '-','✏️','🗑️'))
            with db() as c:
                comps=c.execute('SELECT item_type,ref_id,qty_per_unit AS qty,unit FROM product_items WHERE product_id=? ORDER BY id',(r['id'],)).fetchall()
                for comp in comps:
                    if comp['item_type']=='MATERIAL': row=c.execute('SELECT name FROM materials WHERE id=?',(comp['ref_id'],)).fetchone(); label='Insumo'
                    elif comp['item_type']=='RECIPE_BASE': row=c.execute('SELECT name FROM base_recipes WHERE id=?',(comp['ref_id'],)).fetchone(); label='Receita'
                    else: row=c.execute('SELECT name FROM products WHERE id=?',(comp['ref_id'],)).fetchone(); label='Produto'
                    name=row['name'] if row else '?'
                    self.prod_tree.insert(iid,'end',text='  ',values=('',f'↳ {label}: {name}',fmt_num(comp['qty']),comp['unit'],'','','',''))
        self._reset_checked(self.prod_tree)

    def product_history_dialog(self):
        s=self.prod_tree.selection()
        if not s:return
        code=self.prod_tree.item(s[0])['values'][0]
        with db() as c:p=c.execute('SELECT id FROM products WHERE code=?',(code,)).fetchone()
        if not p:return
        with db() as c:rows=c.execute('SELECT substr(recorded_at,1,7),cost,recorded_at FROM cost_history WHERE entity_type=\'PRODUCT\' AND entity_id=? ORDER BY id DESC',(p['id'],)).fetchall()
        ListDialog(self,'Histórico de custo',(('mes','Mês',100),('custo','Custo',120),('registro','Registro',180)),rows)

    # ---------- Configurações ----------
    def settings_page(self,f):
        outer=tk.Frame(f,bg=self.colors['bg'])
        outer.pack(fill='both',expand=True)
        canvas=tk.Canvas(outer,bg=self.colors['bg'],highlightthickness=0,bd=0)
        canvas.pack(side='left',fill='both',expand=True)
        sb=ttk.Scrollbar(outer,orient='vertical',command=canvas.yview)
        sb.pack(side='right',fill='y')
        canvas.configure(yscrollcommand=sb.set)
        pad=tk.Frame(canvas,bg=self.colors['bg'])
        win=canvas.create_window((0,0),window=pad,anchor='nw')
        def _sync(_=None):
            canvas.configure(scrollregion=canvas.bbox('all'))
            canvas.itemconfigure(win,width=canvas.winfo_width())
        pad.bind('<Configure>', _sync)
        canvas.bind('<Configure>', _sync)
        self.settings_vars={}

        def panel(title):
            shell=RoundedPanel(pad, fill=self.colors['panel'], border=self.colors['line'], radius=18, bg=self.colors['bg'])
            shell.pack(fill='x', pady=(0,10))
            tk.Label(shell,text=title,bg=self.colors['panel'],fg=self.colors['text'],font=('Segoe UI',11,'bold')).pack(anchor='w',padx=14,pady=(12,6))
            body=tk.Frame(shell,bg=self.colors['panel'])
            body.pack(fill='x',padx=14,pady=(0,12))
            return shell, body

        _, appearance=panel('Aparência')
        stored_theme=get_setting('theme','light'); theme=tk.StringVar(value={'light':'Claro','dark':'Escuro','system':'Sistema'}.get(stored_theme,'Escuro'));self.settings_vars['theme']=theme
        ttk.Label(appearance,text='Tema').pack(side='left');ttk.Combobox(appearance,textvariable=theme,values=('Claro','Escuro','Sistema'),state='readonly',width=12).pack(side='left',padx=8);ttk.Button(appearance,text='Aplicar',command=self.apply_theme_from_settings).pack(side='left')

        _, company=panel('Empresa')
        name=tk.StringVar(value=get_setting('company_name','Nexo'));self.settings_vars['company']=name
        logo=tk.StringVar(value=get_setting('company_logo',''));self.settings_vars['logo']=logo
        ttk.Label(company,text='Nome da empresa').grid(row=0,column=0,sticky='w');ttk.Entry(company,textvariable=name,width=36).grid(row=1,column=0,padx=(0,10),sticky='ew')
        ttk.Label(company,text='Logo').grid(row=0,column=1,sticky='w');ttk.Entry(company,textvariable=logo,width=45).grid(row=1,column=1,padx=6,sticky='ew');ttk.Button(company,text='Selecionar',command=lambda:self.select_logo(logo)).grid(row=1,column=2,padx=6)
        ttk.Button(company,text='Salvar identidade',command=self.save_company_settings).grid(row=1,column=3,padx=6)
        tk.Label(company,text='Formatos aceitos: PNG, JPG/JPEG, GIF, BMP, WebP, TIFF e ICO. Mínimo recomendado: 500 px no menor lado.',bg=self.colors['panel'],fg=self.colors['muted'],font=('Segoe UI',9),wraplength=980,justify='left').grid(row=2,column=0,columnspan=4,sticky='w',padx=6,pady=(8,0))
        company.columnconfigure(0,weight=1); company.columnconfigure(1,weight=1)

        _, costs=panel('Custos operacionais')
        self.cost_vars={}; settings=get_cost_settings()
        for i,n in enumerate(('Gás','Energia','Água')):
            ttk.Label(costs,text=f'{n} (%)').grid(row=0,column=i,sticky='w',padx=6);v=tk.StringVar(value=fmt_num(settings.get(n,20)));self.cost_vars[n]=v;ttk.Entry(costs,textvariable=v,width=12).grid(row=1,column=i,padx=6)
        ttk.Button(costs,text='Salvar custos',command=self.save_cost_settings).grid(row=1,column=3,padx=10)
        tk.Label(costs,text='Esses percentuais entram no custo final do Produto e ficam registrados no histórico.',bg=self.colors['panel'],fg=self.colors['muted'],font=('Segoe UI',9)).grid(row=2,column=0,columnspan=4,sticky='w',padx=6,pady=8)

        _, units=panel('Unidades internas')
        self.base_vars={}
        for i,(key,label,vals) in enumerate((('mass_base_unit','Massa',UNITS_MASS),('volume_base_unit','Volume',UNITS_VOLUME),('count_base_unit','Quantidade',UNITS_COUNT))):
            ttk.Label(units,text=label).grid(row=0,column=i,padx=6,sticky='w');v=tk.StringVar(value=get_setting(key,BASE_UNITS_DEFAULT[dimension_of_unit(vals[0]) or 'count']));self.base_vars[key]=v;ttk.Combobox(units,textvariable=v,values=vals,state='readonly',width=10).grid(row=1,column=i,padx=6)
        ttk.Button(units,text='Salvar unidades internas',command=self.save_base_units).grid(row=1,column=3,padx=8)

        _, convbox=panel('Unidades configuráveis por insumo')
        tk.Label(convbox,text='Ex.: xícara de leite pode equivaler a 240 ml; xícara de farinha pode equivaler a outro valor.',bg=self.colors['panel'],fg=self.colors['muted'],font=('Segoe UI',9)).grid(row=0,column=0,sticky='w',pady=(0,8))
        ttk.Button(convbox,text='Gerenciar conversões',command=self.settings_conversion_dialog).grid(row=1,column=0,sticky='w')

        _, langbox=panel('Idioma')
        self.language_var=tk.StringVar(value=get_setting('language','Português (Brasil)'))
        ttk.Label(langbox,text='Idioma').pack(side='left');ttk.Combobox(langbox,textvariable=self.language_var,values=('Português (Brasil)',),state='readonly',width=22).pack(side='left',padx=8)
        tk.Label(langbox,text='Outros idiomas serão adicionados na camada de tradução sem alterar os dados.',bg=self.colors['panel'],fg=self.colors['muted'],font=('Segoe UI',9)).pack(side='left')

        _, dbbox=panel('Fonte de dados')
        ttk.Label(dbbox,text='SQLite atual').grid(row=0,column=0,sticky='w');self.db_path_var=tk.StringVar(value=str(DB_PATH));ttk.Entry(dbbox,textvariable=self.db_path_var,width=70).grid(row=1,column=0,padx=(0,8),sticky='ew')
        ttk.Button(dbbox,text='Escolher arquivo SQLite',command=self.choose_db_file).grid(row=1,column=1)
        ttk.Button(dbbox,text='Aplicar banco',command=self.apply_db_file).grid(row=1,column=2,padx=6)
        self.settings_db_status=tk.Label(dbbox,textvariable=self.status,bg=self.colors['panel'],fg=self.colors['muted'],font=('Segoe UI',9,'bold'),anchor='w')
        self.settings_db_status.grid(row=3,column=0,columnspan=3,sticky='w',pady=(4,0))
        tk.Label(dbbox,text='SQLite local/arquivo de rede funciona nesta versão. Conectores PostgreSQL/MySQL podem ser adicionados depois.',bg=self.colors['panel'],fg=self.colors['muted'],font=('Segoe UI',9),wraplength=980,justify='left').grid(row=2,column=0,columnspan=3,sticky='w',pady=8)
        dbbox.columnconfigure(0,weight=1)

        _, audit=panel('Auditoria do banco')
        tk.Label(audit,text='Veja as últimas operações, diferencie INSERT/UPDATE/DELETE e confira o antes/depois das edições.',bg=self.colors['panel'],fg=self.colors['muted'],font=('Segoe UI',9)).pack(anchor='w')
        ttk.Button(audit,text='Visualizar banco / auditoria',command=self.audit_database_dialog).pack(anchor='w',pady=(8,0))

        _, docs=panel('Documentos')
        tk.Label(docs,text=f'Arquivos originais ficam em: {DOCS_DIR}',bg=self.colors['panel'],fg=self.colors['muted'],font=('Segoe UI',9)).pack(anchor='w')
        self.refresh_settings_widgets=pad

    def settings_conversion_dialog(self):
        d=Modal(self,'Unidades configuráveis por insumo','820x600')
        material=tk.StringVar();unit=tk.StringVar();base=tk.StringVar(value='ml');factor=tk.StringVar()
        form=ttk.Frame(d,padding=12);form.pack(fill='x')
        ttk.Label(form,text='Insumo *').grid(row=0,column=0,sticky='w');cb=ttk.Combobox(form,textvariable=material,width=38,state='readonly');cb.grid(row=1,column=0,padx=5)
        ttk.Label(form,text='Unidade configurável *').grid(row=0,column=1,sticky='w');ttk.Entry(form,textvariable=unit,width=20).grid(row=1,column=1,padx=5)
        ttk.Label(form,text='Quantidade equivalente *').grid(row=0,column=2,sticky='w');ttk.Entry(form,textvariable=factor,width=18).grid(row=1,column=2,padx=5)
        ttk.Label(form,text='Unidade interna referenciada *').grid(row=0,column=3,sticky='w');ttk.Combobox(form,textvariable=base,values=('mg','ml','un'),state='readonly',width=18).grid(row=1,column=3,padx=5)
        tree=ttk.Treeview(d,columns=('item','unit','factor','base'),show='headings')
        for k,t,w in [('item','Insumo',220),('unit','Unidade',140),('factor','Quantidade equivalente',170),('base','Unidade interna',150)]:tree.heading(k,text=t);tree.column(k,width=w)
        tree.pack(fill='both',expand=True,padx=12,pady=12)
        def load():cb['values']=[f'{r["id"]} — {r["name"]}' for r in list_names('materials')]
        def refresh():
            for x in tree.get_children():tree.delete(x)
            with db() as c:
                rows=c.execute('''SELECT m.name AS material_name,cu.name AS unit_name,cu.base_unit,cu.factor_to_base FROM custom_units cu JOIN materials m ON m.id=cu.material_id ORDER BY m.name,cu.name''').fetchall()
            for r in rows:tree.insert('','end',values=(r['material_name'],r['unit_name'],r['factor_to_base'],r['base_unit']))
        def add():
            try:
                if '—' not in material.get():raise ValueError('Selecione um Insumo do Cadastro.')
                mid=int(material.get().split(' — ')[0]);n=unit.get().strip();b=base.get();f=to_float(factor.get(),'Quantidade equivalente')
                if not n:raise ValueError('O nome da unidade configurável é obrigatório.')
                if f<=0:raise ValueError('A Quantidade equivalente deve ser maior que zero.')
                with db() as c:c.execute('INSERT INTO custom_units(material_id,name,base_unit,factor_to_base) VALUES(?,?,?,?)',(mid,n,b,f))
                unit.set('');factor.set('');refresh()
            except Exception as e:safe_error(d,'Não foi possível salvar a conversão',e)
        ttk.Button(form,text='Adicionar',command=add).grid(row=1,column=4,padx=6)
        load();refresh()
        actions=ttk.Frame(d,padding=10);actions.pack(fill='x')
        ttk.Button(actions,text='Cancelar',command=d.destroy).pack(side='right')
        ttk.Button(actions,text='Salvar',command=lambda:(self.notify('Unidades configuráveis salvas.'),d.destroy())).pack(side='right',padx=6)

    def audit_database_dialog(self):
        d=Modal(self,'Auditoria do banco de dados','1040x620')
        ttk.Label(d,text='Últimas operações registradas pelo SQLite. Clique duas vezes em uma linha para ver antes/depois.',padding=12).pack(anchor='w')
        tree=ttk.Treeview(d,columns=('date','action','table','id','reason'),show='headings')
        for k,t,w in [('date','Data/hora',150),('action','Ação',90),('table','Tabela',150),('id','ID',70),('reason','Motivo da edição',430)]:
            tree.heading(k,text=t);tree.column(k,width=w)
        tree.pack(fill='both',expand=True,padx=12,pady=8)
        with db() as c:
            rows=c.execute('SELECT id,action,table_name,record_id,changed_at FROM audit_log ORDER BY id DESC LIMIT 100').fetchall()
            for r in rows:
                reason=''
                if r['action']=='UPDATE':
                    eh=c.execute('''SELECT reason FROM edit_history WHERE entity_id=? ORDER BY ABS(strftime('%s',edited_at)-strftime('%s',?)) LIMIT 1''',(r['record_id'],r['changed_at'])).fetchone()
                    reason=eh['reason'] if eh else ''
                tree.insert('', 'end', iid=str(r['id']), values=(r['changed_at'],r['action'],r['table_name'],r['record_id'] or '-',reason))
        def details(_=None):
            sel=tree.selection()
            if not sel:return
            aid=int(sel[0])
            with db() as c:r=c.execute('SELECT * FROM audit_log WHERE id=?',(aid,)).fetchone()
            if not r:return
            detail=Modal(d,'Detalhes da operação','900x560')
            ttk.Label(detail,text=f"{r['action']} — {r['table_name']} — registro ID {r['record_id']}",font=('Segoe UI',12,'bold')).pack(anchor='w',padx=16,pady=(16,8))
            ttk.Label(detail,text=f"Data/hora: {r['changed_at']}").pack(anchor='w',padx=16)
            reason=''
            if r['action']=='UPDATE':
                with db() as c:
                    eh=c.execute('SELECT reason FROM edit_history WHERE entity_id=? ORDER BY id DESC LIMIT 1',(r['record_id'],)).fetchone()
                reason=eh['reason'] if eh else ''
            ttk.Label(detail,text=f"Motivo: {reason or '—'}").pack(anchor='w',padx=16,pady=(2,10))
            txt=tk.Text(detail,wrap='word',height=22)
            txt.pack(fill='both',expand=True,padx=16,pady=8)
            txt.insert('1.0', 'ANTES\n'+(r['before_json'] or '—')+'\n\nDEPOIS\n'+(r['after_json'] or '—'))
            txt.configure(state='disabled')
            ttk.Button(detail,text='Fechar',command=detail.destroy).pack(pady=(0,12))
        tree.bind('<Double-1>',details)
        ttk.Button(d,text='Fechar',command=d.destroy).pack(pady=(0,12))

    def choose_db_file(self):
        path=filedialog.asksaveasfilename(parent=self,defaultextension='.db',filetypes=[('SQLite','*.db'),('Todos os arquivos','*.*')],initialfile=Path(DB_PATH).name)
        if path:self.db_path_var.set(path)

    def apply_db_file(self):
        global DB_PATH
        new_path=Path(self.db_path_var.get().strip())
        if not new_path:
            messagebox.showerror('Banco de dados','Informe um caminho para o banco SQLite.',parent=self);return
        try:
            DB_PATH=new_path;DB_PATH.parent.mkdir(parents=True,exist_ok=True);save_file_config();init_db();self._update_db_status();self.refresh_all();messagebox.showinfo('Banco de dados','Banco SQLite aplicado. O Nexo continuará usando este arquivo nas próximas execuções.',parent=self)
        except Exception as e:safe_error(self,'Não foi possível aplicar o banco',e)

    def refresh_settings(self):
        if hasattr(self,'header_title'):
            name=get_setting('company_name','Nexo') or 'Nexo'
            if getattr(self,'current_page',None) == 'Geral':
                self.header_title.config(text='Início')
                self.header_subtitle.config(text='Visão geral do seu negócio')
            self.company_label.config(text='')
            if hasattr(self, 'sidebar_nav'):
                self.sidebar_nav.set_brand(name)
            logo=get_setting('company_logo','').strip()
            if not logo or not Path(logo).exists():
                self.header_logo.configure(image='',text='')
                self.header_logo_img=None
                return
            source=Path(logo)
            try:
                from PIL import Image, ImageTk
                img=Image.open(source).convert('RGBA')
                max_w,max_h=54,54
                scale=min(max_w/img.width,max_h/img.height,1.0)
                if scale < 1.0:
                    img=img.resize((max(1,int(img.width*scale)),max(1,int(img.height*scale))), Image.Resampling.LANCZOS)
                img2=Image.open(source).convert('RGBA')
                max_w2,max_h2=38,38
                scale2=min(max_w2/img2.width,max_h2/img2.height,1.0)
                if scale2 < 1.0:
                    img2=img2.resize((max(1,int(img2.width*scale2)),max(1,int(img2.height*scale2))), Image.Resampling.LANCZOS)
                self.header_logo_img=ImageTk.PhotoImage(img2)
                self.header_logo.configure(image=self.header_logo_img,text='')
            except Exception:
                try:
                    self.header_logo_img=tk.PhotoImage(file=str(source)); self.header_logo.configure(image=self.header_logo_img,text='')
                except Exception:
                    self.header_logo.configure(image='',text='')

    def select_logo(self,var):
        path=filedialog.askopenfilename(parent=self,filetypes=[('Imagens','*.png;*.jpg;*.jpeg;*.gif;*.bmp;*.webp;*.tif;*.tiff;*.ico'),('PNG','*.png'),('JPEG','*.jpg;*.jpeg'),('GIF','*.gif'),('BMP','*.bmp'),('WebP','*.webp'),('TIFF','*.tif;*.tiff'),('Ícone','*.ico'),('Todos os arquivos','*.*')])
        if path:
            try:
                from PIL import Image
                with Image.open(path) as im:
                    if min(im.size) < 500:
                        messagebox.showwarning('Logo','A imagem selecionada tem menos de 500 px no menor lado. Ela pode perder qualidade ao ser exibida maior. O Nexo não irá corrigir a imagem.',parent=self)
            except Exception:
                pass
            var.set(path)

    def save_company_settings(self):
        name=normalize_text(self.settings_vars['company'].get().strip()) or 'Nexo'
        logo=self.settings_vars['logo'].get().strip()
        set_setting('company_name',name);set_setting('company_logo',logo);self.refresh_settings();self.notify('Identidade da empresa salva.')

    def save_cost_settings(self):
        try:
            vals={n:to_float(v.get(),n) for n,v in self.cost_vars.items()}
            for n,v in vals.items():
                if v<0:raise ValueError(f'O percentual de {n} não pode ser negativo.')
            with db() as c:
                for n,v in vals.items():c.execute('UPDATE cost_settings SET percentage=? WHERE name=?',(v,n))
            snapshot_costs();self.refresh_all();self.notify('Custos operacionais salvos.')
        except Exception as e:safe_error(self,'Não foi possível salvar os custos operacionais',e)

    def save_base_units(self):
        try:
            desired={k:v.get() for k,v in self.base_vars.items()}
            old={k:get_setting(k,BASE_UNITS_DEFAULT[dimension_of_unit({'mass_base_unit':'mg','volume_base_unit':'ml','count_base_unit':'un'}[k])]) for k in desired}
            with db() as c:
                for key,new_unit in desired.items():
                    old_unit=old[key]
                    if old_unit==new_unit: continue
                    old_factor=unit_factor_to_default_base(old_unit);new_factor=unit_factor_to_default_base(new_unit)
                    for row in c.execute('SELECT id,base_unit,factor_to_base FROM custom_units').fetchall():
                        if row['base_unit']==old_unit:
                            factor_new=row['factor_to_base']*old_factor/new_factor
                            c.execute('UPDATE custom_units SET base_unit=?,factor_to_base=? WHERE id=?',(new_unit,factor_new,row['id']))
                    c.execute('UPDATE system_settings SET value=? WHERE key=?',(new_unit,key))
            snapshot_costs();self.notify('Unidades internas salvas e conversões ajustadas.')
        except Exception as e:safe_error(self,'Não foi possível salvar as unidades internas',e)

    def apply_theme_from_settings(self):
        v=self.settings_vars['theme'].get()
        set_setting('theme', {'Claro':'light','Escuro':'dark','Sistema':'system'}.get(v,'light'));self._apply_theme()

    def _bind_combobox_full_click(self):
        def open_combo(event):
            w=event.widget
            try:
                if isinstance(w,ttk.Combobox) and str(w.cget('state'))!='disabled':
                    w.focus_set()
                    w.tk.call('ttk::combobox::Post', w._w)
                    return 'break'
            except Exception:
                pass
        self.bind_class('TCombobox','<Button-1>',open_combo,add='+')

    def _apply_theme(self):
        # O tema escuro é o visual principal do Nexo; o modo claro continua disponível
        # para quem preferir, mas a instalação entregue abre no Nexo Dark.
        theme=get_setting('theme','light')
        dark=theme=='dark'
        if dark:
            bg='#081226'; fg='#F4F7FF'; panel='#111F3B'; muted='#93A4C6'; line='#24385E'; field='#0E1B35'
            accent_soft='#5A3518'; cream='#FFF7EA'
        else:
            bg='#F4F7FC'; fg='#18223A'; panel='#FFFFFF'; muted='#687796'; line='#DDE5F2'; field='#FFFFFF'
            accent_soft='#FFF0D8'; cream='#FFF7EA'
        self.colors.update(bg=bg,text=fg,panel=panel,muted=muted,line=line,field=field,accent_soft=accent_soft,cream=cream)
        self.configure(bg=bg)
        self.style.configure('TFrame',background=bg)
        self.style.configure('TLabel',background=bg,foreground=fg)
        self.style.configure('TLabelframe',background=panel,foreground=fg,borderwidth=1,relief='solid')
        self.style.configure('TLabelframe.Label',background=panel,foreground=fg)
        self.style.configure('Treeview',background=field,fieldbackground=field,foreground=fg,borderwidth=0,relief='flat')
        self.style.configure('Treeview.Heading',background=('#142544' if dark else '#E8EEF8'),foreground=('#AFC0E2' if dark else '#3A4967'))
        self.style.map('Treeview',background=[('selected',accent_soft)],foreground=[('selected',fg)])
        self.style.configure('TEntry',fieldbackground=field,foreground=fg,borderwidth=0,relief='flat')
        self.style.configure('Field.TEntry',fieldbackground=field,foreground=fg,borderwidth=0,relief='flat',padding=4)
        self.style.configure('TCombobox',fieldbackground=field,foreground=fg)
        self.style.configure('TButton',background=('#172746' if dark else '#EEF2F7'),foreground=('#DDE6FF' if dark else '#25324A'),padding=(12,8),font=('Segoe UI',10,'bold'),relief='flat',borderwidth=0)
        self.style.map('TButton',background=[('active','#20375F' if dark else '#E2E8F0'),('pressed','#2A3F6A' if dark else '#D7DEE9')],foreground=[('active','#FFFFFF' if dark else '#18223A')])
        self.style.map('TCombobox',fieldbackground=[('readonly',field)],foreground=[('readonly',fg)])
        self.style.configure('TCheckbutton',background=bg,foreground=fg)
        self.style.configure('Primary.TButton',background=self.colors['accent'],foreground='#FFFFFF')
        self.style.configure('Soft.TButton',background=('#172746' if dark else '#EFF4FB'),foreground=('#DDE6FF' if dark else '#1D3557'),padding=(13,9),font=('Segoe UI',10,'bold'),relief='flat',borderwidth=0)
        self.style.map('Primary.TButton',background=[('active',self.colors['accent_dark'])],foreground=[('active','#FFFFFF')])
        for attr in ('_root_frame','_content','_body'):
            w=getattr(self,attr,None)
            if w:
                try:w.configure(bg=bg)
                except Exception:pass
        if hasattr(self,'_header'):
            try:self._header.configure(bg=bg)
            except Exception:pass
        for attr in ('header_identity','header_logo','header_title','header_subtitle','company_label'):
            w=getattr(self,attr,None)
            if w:
                try:w.configure(bg=bg)
                except Exception:pass
                try:w.configure(fg=fg if attr not in ('header_subtitle','company_label') else muted)
                except Exception:pass
        for attr in ('status_label','footer_brand'):
            w=getattr(self,attr,None)
            if w:
                try:w.configure(bg=bg,fg=muted)
                except Exception:pass
        if hasattr(self,'sidebar_nav'):
            self.sidebar_nav.set_theme(dark,bg)
        if hasattr(self,'nexo_brand_label') and self.nexo_brand_label:
            try:
                from PIL import Image, ImageTk
                source=UI_ASSETS / ('nexo_logo_dark_clean.png' if dark else 'nexo_logo_light_clean.png')
                self._nexo_brand_img=ImageTk.PhotoImage(Image.open(source).convert('RGBA'))
                self.nexo_brand_label.configure(image=self._nexo_brand_img,bg=bg)
            except Exception: pass
        if hasattr(self,'purchase_chart'):
            self.after_idle(self.refresh_general)


class ListDialog(Modal):
    def __init__(self,master,title,columns,rows):
        super().__init__(master,title,'820x460')
        tree=ttk.Treeview(self,columns=[c[0] for c in columns],show='headings')
        for k,t,w in columns:tree.heading(k,text=t);tree.column(k,width=w)
        for r in rows:tree.insert('','end',values=tuple(r))
        tree.pack(fill='both',expand=True,padx=12,pady=12)
        ttk.Button(self,text='Fechar',command=self.destroy).pack(pady=(0,12))


if __name__=='__main__':
    init_db()
    App().mainloop()
