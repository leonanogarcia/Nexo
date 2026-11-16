"""Gerador de relatórios completos e auditoria do banco de dados Nexo.

Suporta os formatos PDF, Excel (.xlsx), CSV (ou .zip multi-abas no modo Geral) e XML,
com divisão por módulo (Insumos, Receitas, Produtos, Unidades Personalizadas, Auditoria)
e sinalização de obsolescência.
"""
from __future__ import annotations

import csv
import io
import zipfile
from datetime import datetime
from typing import Any
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape as xml_escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .database import db, get_setting


SCOPE_LABELS = {
    "all": "Geral (Banco Completo)",
    "materials": "Insumos",
    "recipes": "Receitas",
    "products": "Produtos",
    "custom_units": "Unidades Personalizadas",
    "audit": "Histórico e Auditoria",
}


def _fmt_dt(val: Any) -> str:
    if not val:
        return "-"
    return str(val).replace("T", " ")[:19]


def _fmt_money(val: Any) -> str:
    try:
        num = float(val or 0.0)
        return f"R$ {num:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def _fmt_num(val: Any, decimals: int = 2) -> str:
    try:
        num = float(val or 0.0)
        return f"{num:.{decimals}f}".replace(".", ",")
    except Exception:
        return "0"


def _obsolescence_label(active: Any, archived: Any, in_use: bool) -> str:
    if archived:
        return "Arquivado (Obsoleto)"
    if active is not None and int(active) == 0:
        return "Inativo"
    if not in_use:
        return "Ativo (Sem vínculo)"
    return "Ativo (Em uso)"


def collect_report_sections(scope: str, health: dict[str, Any]) -> list[dict[str, Any]]:
    """Coleta seções estruturadas do banco conforme o escopo escolhido."""
    sections: list[dict[str, Any]] = []
    retention_months = int(get_setting("history_retention_months", "36") or 36)
    company_name = get_setting("company_name", "Nexo")

    with db() as c:
        used_mat_ids = {
            r["material_id"]
            for r in c.execute("SELECT DISTINCT material_id FROM base_recipe_items").fetchall()
        } | {
            r["ref_id"]
            for r in c.execute("SELECT DISTINCT ref_id FROM product_items WHERE item_type = 'material'").fetchall()
        }
        used_rec_ids = {
            r["ref_id"]
            for r in c.execute("SELECT DISTINCT ref_id FROM product_items WHERE item_type = 'recipe'").fetchall()
        }

        if scope == "all":
            mat_total = c.execute("SELECT COUNT(*) FROM materials").fetchone()[0]
            mat_obs = c.execute("SELECT COUNT(*) FROM materials WHERE active = 0 OR archived = 1").fetchone()[0]
            rec_total = c.execute("SELECT COUNT(*) FROM base_recipes").fetchone()[0]
            rec_obs = c.execute("SELECT COUNT(*) FROM base_recipes WHERE active = 0 OR archived = 1").fetchone()[0]
            prod_total = c.execute("SELECT COUNT(*) FROM products").fetchone()[0]
            prod_obs = c.execute("SELECT COUNT(*) FROM products WHERE active = 0 OR archived = 1").fetchone()[0]
            cu_total = c.execute("SELECT COUNT(*) FROM custom_units").fetchone()[0]
            audit_total = c.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
            edit_total = c.execute("SELECT COUNT(*) FROM edit_history").fetchone()[0]

            sections.append({
                "key": "Resumo",
                "title": "Resumo Geral e Saúde do Banco",
                "headers": ["Indicador", "Valor", "Observação"],
                "rows": [
                    ["Empresa", company_name, "Identidade configurada no sistema"],
                    ["Data da Exportação", datetime.now().strftime("%d/%m/%Y %H:%M:%S"), "Horário local"],
                    ["Tamanho do Banco", health.get("size_fmt", "-"), f"Teto configurado: {health.get('max_size_label', '-')}"],
                    ["Espaço Morto (Fragmentação)", health.get("wasted_fmt", "0 KB"), f"{health.get('wasted_pct', 0):.1f}% do arquivo"],
                    ["Espaço Livre em Disco", health.get("disk_free_fmt", "-"), f"Status: {health.get('health_label', 'Saudável')}"],
                    ["Retenção de Histórico", f"{retention_months} meses", "Limpeza automática de registros mais antigos"],
                    ["Total de Insumos", str(mat_total), f"{mat_obs} inativo(s)/arquivado(s)"],
                    ["Total de Receitas", str(rec_total), f"{rec_obs} inativa(s)/arquivada(s)"],
                    ["Total de Produtos", str(prod_total), f"{prod_obs} inativo(s)/arquivado(s)"],
                    ["Unidades Personalizadas", str(cu_total), "Medidas como xícara, colher, etc."],
                    ["Registros de Auditoria / Edições", f"{audit_total} / {edit_total}", "Logs técnicos (audit_log) / Edições (edit_history)"],
                ],
            })

        if scope in ("all", "materials"):
            rows_raw = c.execute(
                """
                SELECT id, code, name, brand, category, purchase_qty, purchase_unit, purchase_value,
                       barcode, active, archived, created_at, updated_at
                FROM materials
                ORDER BY name COLLATE NOCASE ASC
                """
            ).fetchall()
            rows = [
                [
                    r["code"] or f"INS-{r['id']}",
                    r["name"],
                    r["brand"] or "-",
                    r["category"] or "-",
                    f"{_fmt_num(r['purchase_qty'])} {r['purchase_unit']}",
                    _fmt_money(r["purchase_value"]),
                    r["barcode"] or "-",
                    _obsolescence_label(r["active"], r["archived"], r["id"] in used_mat_ids),
                    _fmt_dt(r["updated_at"] or r["created_at"]),
                ]
                for r in rows_raw
            ]
            sections.append({
                "key": "Insumos",
                "title": "Insumos Cadastrados",
                "headers": ["Código", "Nome", "Marca", "Categoria", "Embalagem", "Valor Pago", "Cód. Barras", "Status / Obsolescência", "Atualizado em"],
                "rows": rows,
            })

        if scope in ("all", "recipes"):
            rows_raw = c.execute(
                """
                SELECT br.id, br.code, br.name, br.yield_qty, br.yield_unit, br.cooking_appliance,
                       br.cooking_time_minutes, br.active, br.archived, br.created_at, br.updated_at,
                       (SELECT COUNT(*) FROM base_recipe_items bri WHERE bri.recipe_id = br.id) AS item_count
                FROM base_recipes br
                ORDER BY br.name COLLATE NOCASE ASC
                """
            ).fetchall()
            rows = [
                [
                    r["code"] or f"REC-{r['id']}",
                    r["name"],
                    f"{_fmt_num(r['yield_qty'])} {r['yield_unit'] or ''}".strip(),
                    str(r["item_count"]),
                    r["cooking_appliance"] or "none",
                    f"{_fmt_num(r['cooking_time_minutes'], 0)} min",
                    _obsolescence_label(r["active"], r["archived"], r["id"] in used_rec_ids),
                    _fmt_dt(r["updated_at"] or r["created_at"]),
                ]
                for r in rows_raw
            ]
            sections.append({
                "key": "Receitas",
                "title": "Receitas Base",
                "headers": ["Código", "Nome", "Rendimento", "Qtd. Itens", "Equipamento", "Tempo", "Status / Obsolescência", "Atualizado em"],
                "rows": rows,
            })

        if scope in ("all", "products"):
            rows_raw = c.execute(
                """
                SELECT p.id, p.code, p.name, p.weight_qty, p.weight_unit, p.sale_price,
                       p.batch_yield_units, p.active, p.archived, p.created_at, p.updated_at,
                       (SELECT COUNT(*) FROM product_items pi WHERE pi.product_id = p.id) AS comp_count
                FROM products p
                ORDER BY p.name COLLATE NOCASE ASC
                """
            ).fetchall()
            rows = [
                [
                    r["code"] or f"PROD-{r['id']}",
                    r["name"],
                    f"{_fmt_num(r['weight_qty'])} {r['weight_unit'] or ''}".strip() if r["weight_qty"] else "-",
                    _fmt_money(r["sale_price"]),
                    _fmt_num(r["batch_yield_units"] or 1, 0),
                    str(r["comp_count"]),
                    _obsolescence_label(r["active"], r["archived"], True),
                    _fmt_dt(r["updated_at"] or r["created_at"]),
                ]
                for r in rows_raw
            ]
            sections.append({
                "key": "Produtos",
                "title": "Produtos Finais",
                "headers": ["Código", "Nome", "Peso/Porção", "Preço Venda", "Lote (un.)", "Componentes", "Status / Obsolescência", "Atualizado em"],
                "rows": rows,
            })

        if scope in ("all", "custom_units"):
            rows_raw = c.execute(
                """
                SELECT cu.id, m.name AS material_name, cu.name AS unit_name, cu.base_unit, cu.factor_to_base,
                       m.active AS material_active, m.archived AS material_archived
                FROM custom_units cu
                LEFT JOIN materials m ON m.id = cu.material_id
                ORDER BY m.name COLLATE NOCASE ASC, cu.name COLLATE NOCASE ASC
                """
            ).fetchall()
            rows = [
                [
                    r["material_name"] or "(Insumo removido)",
                    r["unit_name"],
                    r["base_unit"],
                    _fmt_num(r["factor_to_base"], 4),
                    f"1 {r['unit_name']} = {_fmt_num(r['factor_to_base'], 2)} {r['base_unit']}",
                    "Insumo inativo/removido" if (not r["material_name"] or r["material_archived"] or r["material_active"] == 0) else "Ativa",
                ]
                for r in rows_raw
            ]
            sections.append({
                "key": "Unidades",
                "title": "Unidades Personalizadas (Medidas de Conversão)",
                "headers": ["Insumo", "Unidade Personalizada", "Unidade Base", "Fator", "Equivalência", "Status"],
                "rows": rows,
            })

        if scope in ("all", "audit"):
            audit_rows = c.execute(
                """
                SELECT id, action, table_name, record_id, before_json, after_json, changed_at
                FROM audit_log
                ORDER BY id DESC
                LIMIT 1000
                """
            ).fetchall()
            rows = [
                [
                    str(r["id"]),
                    r["action"],
                    r["table_name"],
                    str(r["record_id"] or "-"),
                    (r["before_json"] or "-")[:180],
                    (r["after_json"] or "-")[:180],
                    _fmt_dt(r["changed_at"]),
                ]
                for r in audit_rows
            ]
            sections.append({
                "key": "Auditoria",
                "title": "Histórico de Auditoria (INSERT / UPDATE / DELETE)",
                "headers": ["ID", "Operação", "Tabela", "ID Reg.", "Antes", "Depois", "Data/Hora"],
                "rows": rows,
            })

        if scope == "all":
            settings_rows = c.execute(
                "SELECT key, value FROM system_settings WHERE key != 'ai_api_key' ORDER BY key ASC"
            ).fetchall()
            sections.append({
                "key": "Configuracoes",
                "title": "Configurações do Sistema",
                "headers": ["Chave", "Valor"],
                "rows": [[r["key"], (r["value"] or "")[:200]] for r in settings_rows],
            })

    return sections


# ---------- Format Builders ----------

def build_pdf_report(sections: list[dict[str, Any]], scope: str) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title=f"Relatório Nexo - {SCOPE_LABELS.get(scope, scope)}",
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "NexoTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=15,
        textColor=colors.HexColor("#18223A"),
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "NexoSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        textColor=colors.HexColor("#60769D"),
        spaceAfter=10,
    )
    section_style = ParagraphStyle(
        "NexoSection",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11.5,
        textColor=colors.HexColor("#BA5200"),
        spaceBefore=6,
        spaceAfter=6,
    )
    cell_style = ParagraphStyle(
        "NexoCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#18223A"),
    )
    header_style = ParagraphStyle(
        "NexoHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.white,
    )

    story: list[Any] = [
        Paragraph(f"Nexo — Relatório de {xml_escape(SCOPE_LABELS.get(scope, scope))}", title_style),
        Paragraph(f"Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}", subtitle_style),
    ]

    usable_width = landscape(A4)[0] - 24 * mm

    for idx, sec in enumerate(sections):
        if idx > 0:
            story.append(PageBreak())
        story.append(Paragraph(xml_escape(sec["title"]), section_style))

        headers = sec["headers"]
        rows = sec["rows"]
        if not rows:
            story.append(Paragraph("Nenhum registro encontrado nesta seção.", subtitle_style))
            continue

        col_count = len(headers)
        col_widths = [usable_width / col_count] * col_count
        table_data = [[Paragraph(xml_escape(str(h)), header_style) for h in headers]]
        for r in rows:
            table_data.append([Paragraph(xml_escape(str(cell)), cell_style) for cell in r])

        tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
        tbl.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#18223A")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFD")]),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#DCE4F0")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ])
        )
        story.append(tbl)
        story.append(Spacer(1, 6))

    def _footer(canvas_obj: Any, doc_obj: Any) -> None:
        canvas_obj.saveState()
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.setFillColor(colors.HexColor("#60769D"))
        canvas_obj.drawRightString(
            landscape(A4)[0] - 12 * mm,
            8 * mm,
            f"Página {doc_obj.page}",
        )
        canvas_obj.restoreState()

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()


def _col_letter(idx_1_based: int) -> str:
    res = ""
    n = idx_1_based
    while n > 0:
        n, rem = divmod(n - 1, 26)
        res = chr(65 + rem) + res
    return res


def build_xlsx_report(sections: list[dict[str, Any]]) -> bytes:
    """Gera arquivo .xlsx multi-abas nativo (sem dependências externas)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        sheet_overrides = []
        workbook_sheets = []
        workbook_rels = []

        for idx, sec in enumerate(sections, start=1):
            sheet_name = sec["key"][:31].replace("/", "-").replace("\\", "-").replace("*", "").replace("?", "").replace("[", "").replace("]", "")
            sheet_overrides.append(
                f'<Override PartName="/xl/worksheets/sheet{idx}.xml" '
                f'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            )
            workbook_sheets.append(
                f'<sheet name="{xml_escape(sheet_name)}" sheetId="{idx}" r:id="rId{idx}"/>'
            )
            workbook_rels.append(
                f'<Relationship Id="rId{idx}" '
                f'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
                f'Target="worksheets/sheet{idx}.xml"/>'
            )

            all_rows = [sec["headers"]] + sec["rows"]
            col_widths = [max(len(str(h)), 10) for h in sec["headers"]]
            for r in sec["rows"][:200]:
                for c_i, val in enumerate(r):
                    col_widths[c_i] = min(max(col_widths[c_i], len(str(val)) + 2), 48)

            cols_xml = "".join(
                f'<col min="{i+1}" max="{i+1}" width="{w}" customWidth="1"/>'
                for i, w in enumerate(col_widths)
            )

            rows_xml_parts = []
            for r_idx, row in enumerate(all_rows, start=1):
                style_attr = ' s="1"' if r_idx == 1 else ""
                cells_xml = []
                for c_idx, val in enumerate(row, start=1):
                    ref = f"{_col_letter(c_idx)}{r_idx}"
                    text = xml_escape(str(val))
                    cells_xml.append(
                        f'<c r="{ref}" t="inlineStr"{style_attr}><is><t xml:space="preserve">{text}</t></is></c>'
                    )
                rows_xml_parts.append(f'<row r="{r_idx}">{"".join(cells_xml)}</row>')

            sheet_xml = (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                f'<cols>{cols_xml}</cols>'
                f'<sheetData>{"".join(rows_xml_parts)}</sheetData>'
                '</worksheet>'
            )
            zf.writestr(f"xl/worksheets/sheet{idx}.xml", sheet_xml.encode("utf-8"))

        content_types = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
            f'{"".join(sheet_overrides)}'
            '</Types>'
        )
        root_rels = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            '</Relationships>'
        )
        workbook_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            f'<sheets>{"".join(workbook_sheets)}</sheets>'
            '</workbook>'
        )
        wb_rels_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f'{"".join(workbook_rels)}'
            '<Relationship Id="rId999" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
            '</Relationships>'
        )
        styles_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<fonts count="2">'
            '<font><sz val="10"/><name val="Calibri"/></font>'
            '<font><b/><color rgb="FFFFFFFF"/><sz val="10"/><name val="Calibri"/></font>'
            '</fonts>'
            '<fills count="3">'
            '<fill><patternFill patternType="none"/></fill>'
            '<fill><patternFill patternType="gray125"/></fill>'
            '<fill><patternFill patternType="solid"><fgColor rgb="FF18223A"/></patternFill></fill>'
            '</fills>'
            '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
            '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
            '<cellXfs count="2">'
            '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
            '<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"/>'
            '</cellXfs>'
            '</styleSheet>'
        )

        zf.writestr("[Content_Types].xml", content_types.encode("utf-8"))
        zf.writestr("_rels/.rels", root_rels.encode("utf-8"))
        zf.writestr("xl/workbook.xml", workbook_xml.encode("utf-8"))
        zf.writestr("xl/_rels/workbook.xml.rels", wb_rels_xml.encode("utf-8"))
        zf.writestr("xl/styles.xml", styles_xml.encode("utf-8"))

    return buf.getvalue()


def build_csv_or_zip_report(sections: list[dict[str, Any]]) -> tuple[bytes, str, str]:
    """Retorna (bytes, media_type, extensao). Para múltiplas seções, empacota em .zip."""
    def _section_csv_bytes(sec: dict[str, Any]) -> bytes:
        s_buf = io.StringIO()
        writer = csv.writer(s_buf, delimiter=";")
        writer.writerow(sec["headers"])
        for row in sec["rows"]:
            writer.writerow(row)
        return ("\ufeff" + s_buf.getvalue()).encode("utf-8")

    if len(sections) == 1:
        return _section_csv_bytes(sections[0]), "text/csv; charset=utf-8", "csv"

    z_buf = io.BytesIO()
    with zipfile.ZipFile(z_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for idx, sec in enumerate(sections, start=1):
            fname = f"{idx:02d}_{sec['key'].lower()}.csv"
            zf.writestr(fname, _section_csv_bytes(sec))
    return z_buf.getvalue(), "application/zip", "zip"


def build_xml_report(sections: list[dict[str, Any]], scope: str) -> bytes:
    root = ET.Element("NexoRelatorio")
    root.set("escopo", scope)
    root.set("geradoEm", datetime.now().isoformat(timespec="seconds"))

    for sec in sections:
        sec_el = ET.SubElement(root, "Secao")
        sec_el.set("chave", sec["key"])
        sec_el.set("titulo", sec["title"])
        sec_el.set("total", str(len(sec["rows"])))
        headers = sec["headers"]
        for row in sec["rows"]:
            reg_el = ET.SubElement(sec_el, "Registro")
            for col_name, val in zip(headers, row):
                campo = ET.SubElement(reg_el, "Campo")
                campo.set("nome", col_name)
                campo.text = str(val)

    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)
