from .database import db, get_setting

UNITS_MASS = ('mg', 'g', 'kg', 't')
UNITS_VOLUME = ('ml', 'L', 'kL')
UNITS_COUNT = ('un',)
UNITS = UNITS_MASS + UNITS_VOLUME + UNITS_COUNT
BASE_UNITS_DEFAULT = {'mass': 'mg', 'volume': 'ml', 'count': 'un'}


def to_float(value, field_name='valor'):
    text = str(value).strip()
    if not text:
        raise ValueError(f'O campo "{field_name}" é obrigatório.')
    try:
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


def fmt(v):
    if v is None:
        return '-'
    return f'R$ {v:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def fmt_num(v):
    if v is None:
        return '-'
    s = f'{float(v):,.3f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    return s.rstrip('0').rstrip(',')


def normalize_text(value):
    """Normaliza textos digitados manualmente: primeira letra em maiúscula."""
    text = str(value)
    for i, ch in enumerate(text):
        if ch.isalpha():
            return text[:i] + ch.upper() + text[i+1:]
    return text


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
    return get_setting({'mass': 'mass_base_unit', 'volume': 'volume_base_unit', 'count': 'count_base_unit'}.get(dimension), BASE_UNITS_DEFAULT[dimension])


def unit_factor_to_internal(unit):
    factor = unit_factor_to_default_base(unit)
    if factor is None:
        return None, None
    dim = dimension_of_unit(unit)
    internal = configured_base_unit(dim)
    base_factor = unit_factor_to_default_base(internal)
    return factor / base_factor, internal


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
        f_from, current_base = unit_factor_to_internal(row['base_unit'])
        if f_from is None:
            raise ValueError(f'A unidade base "{row["base_unit"]}" configurada para "{unit}" não é válida.')
        return qty * row['factor_to_base'] * f_from, current_base
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

