from .database import db, get_cost_settings, now_iso
from .units import conversion_to_base, convert_generic


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
        c.commit()

