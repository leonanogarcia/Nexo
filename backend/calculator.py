from .database import db, get_cost_settings, get_cost_settings_detailed, get_setting, now_iso
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


def recipe_direct_cost(recipe_id, stack=None):
    stack = set() if stack is None else stack
    if recipe_id in stack:
        raise ValueError('Ciclo detectado na Receita.')
    with db() as c:
        rows = c.execute('SELECT * FROM base_recipe_items WHERE recipe_id=?', (recipe_id,)).fetchall()
    if not rows:
        return 0.0
    mat_total = 0.0
    stack.add(recipe_id)
    for r in rows:
        mat_total += material_cost(r['material_id'], r['qty'], r['unit'])
    stack.remove(recipe_id)
    return mat_total


def recipe_operational_breakdown(recipe_id):
    with db() as c:
        rec = c.execute('SELECT cooking_appliance, cooking_time_minutes FROM base_recipes WHERE id=?', (recipe_id,)).fetchone()
    if not rec:
        return {'gas': 0.0, 'energy': 0.0, 'water': 0.0, 'total': 0.0, 'items': []}
    appliance = rec['cooking_appliance'] if 'cooking_appliance' in rec.keys() and rec['cooking_appliance'] else 'none'
    ctime = float(rec['cooking_time_minutes'] or 0.0) if 'cooking_time_minutes' in rec.keys() else 0.0
    if ctime > 0 and appliance != 'none':
        res = calculate_product_operational_breakdown(0.0, appliance, ctime, batch_yield_units=1.0)
        gas = 0.0
        energy = 0.0
        water = 0.0
        for it in res.get('items', []):
            n = it.get('name', '').lower()
            if 'g' in n:
                gas += float(it.get('cost') or 0.0)
            elif 'energia' in n:
                energy += float(it.get('cost') or 0.0)
            elif 'gua' in n:
                water += float(it.get('cost') or 0.0)
        return {
            'gas': gas,
            'energy': energy,
            'water': water,
            'total': float(res.get('total_cost') or 0.0),
            'items': res.get('items', []),
        }
    return {'gas': 0.0, 'energy': 0.0, 'water': 0.0, 'total': 0.0, 'items': []}


def product_operational_breakdown(product_id, stack=None):
    stack = set() if stack is None else stack
    if product_id in stack:
        raise ValueError('Ciclo detectado na composição de Produtos.')
    with db() as c:
        rows = c.execute('SELECT * FROM product_items WHERE product_id=?', (product_id,)).fetchall()
    
    tot_gas = 0.0
    tot_energy = 0.0
    tot_water = 0.0

    stack.add(product_id)
    for r in rows:
        itype = r['item_type']
        ref_id = r['ref_id']
        qty = r['qty_per_unit']
        unit = r['unit']
        if itype == 'RECIPE_BASE':
            with db() as c:
                rec = c.execute('SELECT yield_qty, yield_unit FROM base_recipes WHERE id=?', (ref_id,)).fetchone()
            if rec and rec['yield_qty'] and rec['yield_qty'] > 0:
                try:
                    q = convert_generic(qty, unit, rec['yield_unit'])
                    factor = q / rec['yield_qty']
                    rb = recipe_operational_breakdown(ref_id)
                    tot_gas += rb['gas'] * factor
                    tot_energy += rb['energy'] * factor
                    tot_water += rb['water'] * factor
                except Exception:
                    pass
        elif itype == 'PRODUCT':
            try:
                sub_res = product_operational_breakdown(ref_id, stack)
                tot_gas += sub_res['gas'] * qty
                tot_energy += sub_res['energy'] * qty
                tot_water += sub_res['water'] * qty
            except Exception:
                pass
    stack.remove(product_id)

    total_op = tot_gas + tot_energy + tot_water
    items = [
        {
            'id': 1,
            'name': 'Gás',
            'cost': round(tot_gas, 4),
            'cost_fmt': f"R$ {tot_gas:.2f}".replace('.', ','),
            'rate_label': 'Herdado das receitas' if tot_gas > 0.0001 else 'Sem cocção a gás',
        },
        {
            'id': 2,
            'name': 'Energia',
            'cost': round(tot_energy, 4),
            'cost_fmt': f"R$ {tot_energy:.2f}".replace('.', ','),
            'rate_label': 'Equipamentos / Ativação' if tot_energy > 0.0001 else 'Sem cocção elétrica',
        },
        {
            'id': 3,
            'name': 'Água',
            'cost': round(tot_water, 4),
            'cost_fmt': f"R$ {tot_water:.2f}".replace('.', ','),
            'rate_label': 'Rateio da cozinha' if tot_water > 0.0001 else 'Rateio cozinha',
        },
    ]

    return {
        'gas': tot_gas,
        'energy': tot_energy,
        'water': tot_water,
        'items': items,
        'total_cost': round(total_op, 4),
        'total_cost_fmt': f"R$ {total_op:.2f}".replace('.', ','),
    }

def recipe_operational_cost(recipe_id):
    with db() as c:
        rec = c.execute('SELECT cooking_appliance, cooking_time_minutes FROM base_recipes WHERE id=?', (recipe_id,)).fetchone()
    if not rec:
        return 0.0
    appliance = rec['cooking_appliance'] if 'cooking_appliance' in rec.keys() and rec['cooking_appliance'] else 'none'
    ctime = float(rec['cooking_time_minutes'] or 0.0) if 'cooking_time_minutes' in rec.keys() else 0.0
    if ctime > 0 and appliance != 'none':
        op_breakdown = calculate_product_operational_breakdown(0.0, appliance, ctime, batch_yield_units=1.0)
        return float(op_breakdown.get('total_cost') or 0.0)
    return 0.0


def recipe_cost(recipe_id, stack=None):
    return recipe_direct_cost(recipe_id, stack) + recipe_operational_cost(recipe_id)


def item_direct_cost(item_type, ref_id, qty, unit, stack=None):
    if item_type == 'MATERIAL':
        return material_cost(ref_id, qty, unit)
    if item_type == 'RECIPE_BASE':
        with db() as c:
            r = c.execute('SELECT yield_qty,yield_unit FROM base_recipes WHERE id=?', (ref_id,)).fetchone()
        if not r or not r['yield_qty'] or r['yield_qty'] <= 0:
            raise ValueError('A Receita precisa ter rendimento definido antes de ser usada em um Produto.')
        q = convert_generic(qty, unit, r['yield_unit'])
        return q * recipe_direct_cost(ref_id, stack) / r['yield_qty']
    if item_type == 'PRODUCT':
        return qty * product_direct_cost(ref_id, stack)
    raise ValueError('Tipo de componente inválido.')


def item_operational_cost(item_type, ref_id, qty, unit):
    if item_type == 'MATERIAL':
        return 0.0
    if item_type == 'RECIPE_BASE':
        with db() as c:
            r = c.execute('SELECT yield_qty,yield_unit FROM base_recipes WHERE id=?', (ref_id,)).fetchone()
        if not r or not r['yield_qty'] or r['yield_qty'] <= 0:
            return 0.0
        q = convert_generic(qty, unit, r['yield_unit'])
        return q * recipe_operational_cost(ref_id) / r['yield_qty']
    if item_type == 'PRODUCT':
        return qty * product_operational_cost(ref_id)
    return 0.0


def item_cost(item_type, ref_id, qty, unit, stack=None):
    return item_direct_cost(item_type, ref_id, qty, unit, stack) + item_operational_cost(item_type, ref_id, qty, unit)



EQUIPMENT_PRESETS = {
    'none': {
        'id': 'none',
        'name': 'Sem cocção (Produto frio / Montagem)',
        'type': 'none',
        'icon': '❄️',
        'power_watts': 0,
        'gas_kg_h': 0.0,
    },
    'gas_oven': {
        'id': 'gas_oven',
        'name': 'Forno a Gás (Fogo médio)',
        'type': 'gas',
        'icon': '🔥',
        'power_watts': 0,
        'gas_kg_h': 0.300,
    },
    'gas_stove_burner': {
        'id': 'gas_stove_burner',
        'name': 'Boca de Fogão / Panela (Chama média)',
        'type': 'gas',
        'icon': '🔥',
        'power_watts': 0,
        'gas_kg_h': 0.180,
    },
    'electric_oven': {
        'id': 'electric_oven',
        'name': 'Forno Elétrico Convector',
        'type': 'electric',
        'icon': '⚡',
        'power_watts': 2500,
        'gas_kg_h': 0.0,
    },
    'mixer_planetary': {
        'id': 'mixer_planetary',
        'name': 'Batedeira Planetária',
        'type': 'electric',
        'icon': '⚡',
        'power_watts': 500,
        'gas_kg_h': 0.0,
    },
    'induction_cooktop': {
        'id': 'induction_cooktop',
        'name': 'Cooktop de Indução',
        'type': 'electric',
        'icon': '⚡',
        'power_watts': 2000,
        'gas_kg_h': 0.0,
    },
    'microwave': {
        'id': 'microwave',
        'name': 'Micro-ondas',
        'type': 'electric',
        'icon': '⚡',
        'power_watts': 1200,
        'gas_kg_h': 0.0,
    },
}


def get_kitchen_rates():
    try:
        days = float(get_setting('kitchen_days_month', '26') or 26)
    except Exception:
        days = 26.0
    try:
        hours = float(get_setting('kitchen_hours_day', '8') or 8)
    except Exception:
        hours = 8.0
    monthly_hours = max(1.0, days * hours)

    gas_type = get_setting('gas_supply_type', 'cylinder_13') or 'cylinder_13'
    try:
        gas_price = float(get_setting('gas_price', '125.00') or 125.0)
    except Exception:
        gas_price = 125.0
    try:
        elec_bill = float(get_setting('electricity_bill_monthly', '350.00') or 350.0)
    except Exception:
        elec_bill = 350.0
    try:
        water_bill = float(get_setting('water_bill_monthly', '80.00') or 80.0)
    except Exception:
        water_bill = 80.0

    if gas_type == 'cylinder_45':
        gas_price_per_kg = gas_price / 45.0
    elif gas_type == 'piped':
        gas_price_per_kg = (gas_price / monthly_hours) / 0.300
    else:
        gas_price_per_kg = gas_price / 13.0

    elec_cost_per_hour = elec_bill / monthly_hours
    elec_cost_per_minute = elec_cost_per_hour / 60.0

    water_cost_per_hour = water_bill / monthly_hours
    water_cost_per_minute = water_cost_per_hour / 60.0

    tarifa_kwh = max(0.65, min(1.40, (elec_bill / (monthly_hours * 1.8))))

    return {
        'days_per_month': days,
        'hours_per_day': hours,
        'monthly_hours': monthly_hours,
        'gas_supply_type': gas_type,
        'gas_price': gas_price,
        'gas_price_per_kg': gas_price_per_kg,
        'elec_bill': elec_bill,
        'water_bill': water_bill,
        'elec_cost_per_hour': elec_cost_per_hour,
        'elec_cost_per_minute': elec_cost_per_minute,
        'water_cost_per_hour': water_cost_per_hour,
        'water_cost_per_minute': water_cost_per_minute,
        'tarifa_kwh': tarifa_kwh,
        'indirect_cost_per_hour': elec_cost_per_hour + water_cost_per_hour,
        'indirect_cost_per_minute': elec_cost_per_minute + water_cost_per_minute,
    }


def calculate_product_operational_breakdown(direct_cost, cooking_appliance=None, cooking_time_minutes=0.0, batch_yield_units=1.0):
    try:
        ctime = float(cooking_time_minutes or 0.0)
    except Exception:
        ctime = 0.0
    try:
        byield = max(1.0, float(batch_yield_units or 1.0))
    except Exception:
        byield = 1.0

    appliance_id = str(cooking_appliance or 'none').strip()

    # Se informado tempo de preparo > 0, calcula com a física real de horas/equipamento
    if ctime > 0 and appliance_id != 'none':
        preset = EQUIPMENT_PRESETS.get(appliance_id, EQUIPMENT_PRESETS['gas_oven'])
        rates = get_kitchen_rates()

        gas_fornada = 0.0
        elec_direct = 0.0

        if preset['type'] == 'gas':
            custo_hora_gas = preset['gas_kg_h'] * rates['gas_price_per_kg']
            gas_fornada = (custo_hora_gas / 60.0) * ctime
        elif preset['type'] == 'electric':
            kwh = (preset['power_watts'] / 1000.0) * (ctime / 60.0)
            elec_direct = kwh * rates['tarifa_kwh']

        # Rateio do tempo da cozinha ativa (energia de geladeiras/salão + água)
        elec_base = rates['elec_cost_per_minute'] * ctime * 0.4
        elec_fornada = elec_direct + elec_base
        water_fornada = rates['water_cost_per_minute'] * ctime

        total_fornada = gas_fornada + elec_fornada + water_fornada

        gas_unit = gas_fornada / byield
        elec_unit = elec_fornada / byield
        water_unit = water_fornada / byield
        total_unit = total_fornada / byield

        items = [
            {
                'id': 1,
                'name': 'Gás',
                'cost_type': 'PRECISE',
                'rate_label': f"{ctime:.0f} min no {preset['name']}",
                'cost': round(gas_unit, 4),
                'cost_fmt': f"R$ {gas_unit:.2f}".replace('.', ','),
            },
            {
                'id': 2,
                'name': 'Energia',
                'cost_type': 'PRECISE',
                'rate_label': f"Ativação ({rates['hours_per_day']:.0f}h/dia)",
                'cost': round(elec_unit, 4),
                'cost_fmt': f"R$ {elec_unit:.2f}".replace('.', ','),
            },
            {
                'id': 3,
                'name': 'Água',
                'cost_type': 'PRECISE',
                'rate_label': f"Rateio de cozinha ({rates['days_per_month']:.0f} dias)",
                'cost': round(water_unit, 4),
                'cost_fmt': f"R$ {water_unit:.2f}".replace('.', ','),
            },
        ]

        return {
            'is_precise': True,
            'appliance_id': appliance_id,
            'appliance_name': preset['name'],
            'cooking_time_minutes': ctime,
            'batch_yield_units': byield,
            'batch_total_cost': round(total_fornada, 4),
            'batch_total_cost_fmt': f"R$ {total_fornada:.2f}".replace('.', ','),
            'items': items,
            'total_cost': round(total_unit, 4),
            'total_cost_fmt': f"R$ {total_unit:.2f}".replace('.', ','),
        }

    # Fallback para as métricas globais de cost_settings
    res = operational_cost_breakdown(direct_cost)
    res['is_precise'] = False
    res['appliance_id'] = 'none'
    res['appliance_name'] = 'Sem cocção ativa'
    res['cooking_time_minutes'] = 0.0
    res['batch_yield_units'] = byield
    res['batch_total_cost'] = res['total_cost'] * byield
    res['batch_total_cost_fmt'] = f"R$ {(res['total_cost'] * byield):.2f}".replace('.', ',')
    return res


def operational_cost(direct_cost):
    settings = get_cost_settings_detailed()
    tot = 0.0
    for s in settings:
        if s.get('cost_type') == 'FIXED':
            tot += float(s.get('fixed_value') or 0.0)
        else:
            tot += direct_cost * (float(s.get('percentage') or 0.0) / 100.0)
    return tot


def operational_cost_breakdown(direct_cost):
    settings = get_cost_settings_detailed()
    items = []
    tot = 0.0
    for s in settings:
        ctype = s.get('cost_type', 'PERCENT')
        pct = float(s.get('percentage') or 0.0)
        fixed = float(s.get('fixed_value') or 0.0)
        if ctype == 'FIXED':
            val = fixed
            rate_label = f"R$ {fixed:.2f}".replace('.', ',')
        else:
            val = direct_cost * (pct / 100.0)
            rate_label = f"{pct:.1f}%".replace('.', ',')
        tot += val
        items.append({
            'id': s.get('id'),
            'name': s.get('name'),
            'cost_type': ctype,
            'percentage': pct,
            'fixed_value': fixed,
            'rate_label': rate_label,
            'cost': float(val),
            'cost_fmt': f"R$ {val:.2f}".replace('.', ','),
        })
    return {
        'items': items,
        'total_cost': float(tot),
        'total_cost_fmt': f"R$ {tot:.2f}".replace('.', ','),
    }


def product_direct_cost(product_id, stack=None):
    stack = set() if stack is None else stack
    if product_id in stack:
        raise ValueError('Ciclo detectado na composição de Produtos.')
    with db() as c:
        rows = c.execute('SELECT * FROM product_items WHERE product_id=?', (product_id,)).fetchall()
    total = 0.0
    stack.add(product_id)
    for r in rows:
        total += item_direct_cost(r['item_type'], r['ref_id'], r['qty_per_unit'], r['unit'], stack)
    stack.remove(product_id)
    return total


def product_operational_cost(product_id, stack=None):
    stack = set() if stack is None else stack
    if product_id in stack:
        raise ValueError('Ciclo detectado na composição de Produtos.')
    with db() as c:
        rows = c.execute('SELECT * FROM product_items WHERE product_id=?', (product_id,)).fetchall()
    inherited_op = 0.0
    stack.add(product_id)
    for r in rows:
        inherited_op += item_operational_cost(r['item_type'], r['ref_id'], r['qty_per_unit'], r['unit'])
    stack.remove(product_id)
    return inherited_op


def product_unit_cost(product_id, stack=None):
    return product_direct_cost(product_id, stack) + product_operational_cost(product_id, stack)


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
