import json
import re
import sqlite3
from datetime import datetime, timedelta
from . import paths


def db():
    c = sqlite3.connect(paths.get_db_path())
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON')
    return c


def now_iso():
    return datetime.now().isoformat(timespec='seconds')


def init_db():
    paths.DOCS_DIR.mkdir(parents=True, exist_ok=True)
    paths.get_db_path().parent.mkdir(parents=True, exist_ok=True)
    with db() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS ai_usage_logs(
            date_str TEXT PRIMARY KEY,
            request_count INTEGER DEFAULT 0
          );
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

        def add_col(table, col, definition):
            cols = {r['name'] for r in c.execute(f'PRAGMA table_info({table})').fetchall()}
            if col not in cols:
                c.execute(f'ALTER TABLE {table} ADD COLUMN {col} {definition}')

        add_col('materials', 'code', 'TEXT')
        add_col('materials', 'updated_at', 'TEXT')
        add_col('products', 'active', 'INTEGER NOT NULL DEFAULT 1')
        add_col('materials', 'active', 'INTEGER NOT NULL DEFAULT 1')
        add_col('materials', 'archived', 'BOOLEAN NOT NULL DEFAULT 0')
        add_col('base_recipes', 'active', 'INTEGER NOT NULL DEFAULT 1')
        add_col('base_recipes', 'archived', 'BOOLEAN NOT NULL DEFAULT 0')
        add_col('base_recipes', 'code', 'TEXT')
        add_col('base_recipes', 'updated_at', 'TEXT')
        add_col('products', 'code', 'TEXT')
        add_col('products', 'archived', 'BOOLEAN NOT NULL DEFAULT 0')
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
        c.execute('INSERT OR IGNORE INTO system_settings(key,value) VALUES(?,?)', ('history_retention_months', '36'))
        _ensure_codes(c)
        _ensure_audit_triggers(c)

        try:
            retention_str = c.execute("SELECT value FROM system_settings WHERE key='history_retention_months'").fetchone()
            if retention_str and retention_str['value']:
                months = int(retention_str['value'])
                if months > 0:
                    cutoff = (datetime.now() - timedelta(days=months * 30)).isoformat()
                    c.execute("DELETE FROM edit_history WHERE edited_at < ?", (cutoff,))
        except Exception:
            pass
        c.commit()
    paths.ensure_daily_backup()


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
    for table, (before, after) in specs.items():
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


def set_setting(key, value):
    with db() as c:
        c.execute('INSERT INTO system_settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value', (key, str(value)))
        c.commit()


def get_cost_settings():
    with db() as c:
        rows = c.execute('SELECT name, percentage FROM cost_settings ORDER BY id').fetchall()
    return {r['name']: float(r['percentage']) for r in rows}


def record_edit(entity_type, entity_id, reason, changes):
    with db() as c:
        c.execute('INSERT INTO edit_history(entity_type,entity_id,reason,changes_json,edited_at) VALUES(?,?,?,?,?)',
                  (entity_type, entity_id, reason, json.dumps(changes, ensure_ascii=False), now_iso()))
        c.commit()


def list_names(table):
    with db() as c:
        if table == 'products':
            return c.execute('SELECT id,name,code FROM products WHERE COALESCE(active,1)=1 ORDER BY name').fetchall()
        return c.execute(f'SELECT id,name,code FROM {table} WHERE COALESCE(active,1)=1 ORDER BY name').fetchall()

