import ast
import csv
import io
import json
import math
import platform
import shutil
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from pydantic import BaseModel

from ..reports import (
    build_csv_or_zip_report,
    build_pdf_report,
    build_xlsx_report,
    build_xml_report,
    collect_report_sections,
)
from .. import (
    UNITS,
    custom_units_for_material,
    db,
    fmt,
    fmt_num,
    get_db_path,
    get_setting,
    init_db,
    material_cost,
    money_to_float,
    next_code,
    normalize_text,
    now_iso,
    paths,
    recipe_cost,
    item_cost,
    item_direct_cost,
    item_operational_cost,
    calculate_product_operational_breakdown,
    get_kitchen_rates,
    EQUIPMENT_PRESETS,
    get_cost_settings_detailed,
    product_unit_cost,
    product_direct_cost,
    product_operational_cost,
    recipe_operational_breakdown,
    product_operational_breakdown,
    convert_generic,
    record_edit,
    set_setting,
    snapshot_costs,
    to_float,
)


from .common import *

router = APIRouter()


class DocumentUploadPayload(BaseModel):
    filename: str
    data_base64: str


def _extract_docx_text_builtin(path: Path) -> str:
    import zipfile
    import xml.etree.ElementTree as ET
    with zipfile.ZipFile(path, "r") as zf:
        if "word/document.xml" not in zf.namelist():
            return ""
        xml_bytes = zf.read("word/document.xml")
    root = ET.fromstring(xml_bytes)
    lines: List[str] = []
    for p in root.iter():
        if p.tag.endswith("}p"):
            texts = [t.text for t in p.iter() if t.tag.endswith("}t") and t.text]
            line = "".join(texts).strip()
            if line:
                lines.append(line)
    return "\n".join(lines)


def _extract_document_text(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".txt":
        return path.read_text(encoding="utf-8", errors="ignore")
    if ext == ".docx":
        return _extract_docx_text_builtin(path)
    if ext == ".pdf":
        try:
            from .document_importer import extract_pdf_text
            return extract_pdf_text(str(path))
        except Exception:
            return ""
    return ""


@router.get("/api/documents/{entity_type}/{entity_id}")
def list_entity_documents(entity_type: str, entity_id: int):
    init_db()
    with db() as c:
        rows = c.execute(
            "SELECT id, entity_type, entity_id, original_name, stored_path, uploaded_at FROM document_links WHERE entity_type = ? AND entity_id = ? ORDER BY id DESC",
            (entity_type.upper(), entity_id),
        ).fetchall()
    return {
        "documents": [
            {
                "id": r["id"],
                "entity_type": r["entity_type"],
                "entity_id": r["entity_id"],
                "original_name": r["original_name"],
                "uploaded_at": r["uploaded_at"],
                "ext": Path(r["original_name"]).suffix.lower(),
                "exists": Path(r["stored_path"]).exists(),
            }
            for r in rows
        ]
    }


@router.post("/api/documents/{entity_type}/{entity_id}")
def upload_entity_document(entity_type: str, entity_id: int, payload: DocumentUploadPayload):
    import base64
    init_db()
    raw_b64 = payload.data_base64.split(",", 1)[-1]
    try:
        file_bytes = base64.b64decode(raw_b64)
    except Exception:
        raise HTTPException(status_code=400, detail="Arquivo inválido (base64).")

    safe_name = Path(payload.filename).name.replace(" ", "_")
    if not safe_name:
        raise HTTPException(status_code=400, detail="Nome do arquivo inválido.")

    paths.DOCS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = paths.DOCS_DIR / f"{entity_type.lower()}_{entity_id}_{stamp}_{safe_name}"
    target.write_bytes(file_bytes)

    with db() as c:
        cur = c.execute(
            "INSERT INTO document_links(entity_type, entity_id, original_name, stored_path, uploaded_at) VALUES(?,?,?,?,?)",
            (entity_type.upper(), entity_id, Path(payload.filename).name, str(target), now_iso()),
        )
        doc_id = cur.lastrowid
        c.commit()

    return {
        "ok": True,
        "id": doc_id,
        "original_name": Path(payload.filename).name,
        "message": "Documento anexado com sucesso!",
    }


def _build_pdf_bytes(title: str, text_content: str, image_path: Optional[Path] = None) -> bytes:
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
    from PIL import Image as PILImage
    import html

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
    )
    styles = getSampleStyleSheet()
    story = [Paragraph(f"<b>{html.escape(title)}</b>", styles["Title"]), Spacer(1, 10)]

    if text_content and text_content.strip():
        for line in text_content.splitlines():
            clean = line.strip()
            if not clean:
                story.append(Spacer(1, 6))
            else:
                story.append(Paragraph(html.escape(clean), styles["Normal"]))
                story.append(Spacer(1, 4))

    if image_path and image_path.exists():
        if text_content and text_content.strip():
            story.append(Spacer(1, 12))
        with PILImage.open(image_path) as im:
            iw, ih = im.size
        max_w = A4[0] - 3.6 * cm
        max_h = A4[1] - 5.0 * cm
        scale = min(max_w / max(iw, 1), max_h / max(ih, 1))
        story.append(RLImage(str(image_path), width=iw * scale, height=ih * scale))

    doc.build(story)
    return buf.getvalue()


def _build_docx_bytes(title: str, text_content: str, image_path: Optional[Path] = None) -> bytes:
    from io import BytesIO
    from docx import Document
    from docx.shared import Inches

    doc = Document()
    doc.add_heading(title, level=1)
    if text_content and text_content.strip():
        for line in text_content.splitlines():
            doc.add_paragraph(line)
    if image_path and image_path.exists():
        doc.add_picture(str(image_path), width=Inches(5.8))
    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()


def _build_jpg_bytes(title: str, text_content: str, image_path: Optional[Path] = None) -> bytes:
    from io import BytesIO
    import textwrap
    from PIL import Image as PILImage, ImageDraw, ImageFont

    if image_path and image_path.exists():
        with PILImage.open(image_path) as im:
            if im.mode in ("RGBA", "LA", "P"):
                bg = PILImage.new("RGB", im.size, (255, 255, 255))
                if im.mode == "P":
                    im = im.convert("RGBA")
                bg.paste(im, mask=im.split()[-1] if im.mode in ("RGBA", "LA") else None)
                rgb = bg
            else:
                rgb = im.convert("RGB")
            out = BytesIO()
            rgb.save(out, format="JPEG", quality=92)
            return out.getvalue()

    width = 1080
    margin = 56
    font_title = ImageFont.load_default()
    font_body = ImageFont.load_default()
    for font_path in ("C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf"):
        if Path(font_path).exists():
            font_title = ImageFont.truetype(font_path, 34)
            font_body = ImageFont.truetype(font_path, 24)
            break

    wrapped: List[str] = []
    for raw_line in (text_content or "(Documento sem texto)").splitlines():
        if not raw_line.strip():
            wrapped.append("")
        else:
            wrapped.extend(textwrap.wrap(raw_line, width=68) or [""])

    line_h = 34
    height = max(600, 160 + len(wrapped) * line_h + 60)
    canvas = PILImage.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([(0, 0), (width, 16)], fill=(242, 140, 40))
    draw.text((margin, 44), title[:60], fill=(24, 34, 58), font=font_title)
    draw.line([(margin, 102), (width - margin, 102)], fill=(226, 234, 245), width=2)

    y = 124
    for ln in wrapped:
        draw.text((margin, y), ln, fill=(51, 65, 85), font=font_body)
        y += line_h

    out = BytesIO()
    canvas.save(out, format="JPEG", quality=92)
    return out.getvalue()


@router.get("/api/documents/file/{doc_id}/download")
def download_document_file(doc_id: int, fmt: str = "original"):
    import mimetypes
    from fastapi.responses import Response

    with db() as c:
        row = c.execute("SELECT original_name, stored_path FROM document_links WHERE id = ?", (doc_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Documento não encontrado.")
    fp = Path(row["stored_path"])
    if not fp.exists():
        raise HTTPException(status_code=404, detail="Arquivo físico não encontrado no disco.")

    req_fmt = (fmt or "original").strip().lower()
    orig_name = row["original_name"]
    ext = fp.suffix.lower()
    stem = Path(orig_name).stem or "documento"

    if req_fmt == "original" or (req_fmt == "pdf" and ext == ".pdf") or (req_fmt == "docx" and ext == ".docx") or (req_fmt == "jpg" and ext in (".jpg", ".jpeg")):
        return FileResponse(str(fp), filename=orig_name)

    is_image = ext in (".png", ".jpg", ".jpeg", ".webp", ".gif")
    text_content = ""
    if is_image and req_fmt in ("pdf", "docx"):
        try:
            from .ai_vision import transcribe_image_to_text
            mime, _ = mimetypes.guess_type(str(fp))
            text_content = transcribe_image_to_text(fp.read_bytes(), mime or "image/jpeg")
        except Exception:
            text_content = ""
    elif not is_image:
        text_content = _extract_document_text(fp)

    if req_fmt == "pdf":
        data = _build_pdf_bytes(stem, text_content, fp if is_image else None)
        return Response(
            content=data,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{stem}.pdf"'},
        )
    if req_fmt == "docx":
        data = _build_docx_bytes(stem, text_content, fp if is_image else None)
        return Response(
            content=data,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{stem}.docx"'},
        )
    if req_fmt == "jpg":
        data = _build_jpg_bytes(stem, text_content, fp if is_image else None)
        return Response(
            content=data,
            media_type="image/jpeg",
            headers={"Content-Disposition": f'attachment; filename="{stem}.jpg"'},
        )

    return FileResponse(str(fp), filename=orig_name)


@router.get("/api/documents/file/{doc_id}/raw")
def view_document_raw(doc_id: int):
    import mimetypes
    with db() as c:
        row = c.execute("SELECT original_name, stored_path FROM document_links WHERE id = ?", (doc_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Documento não encontrado.")
    fp = Path(row["stored_path"])
    if not fp.exists():
        raise HTTPException(status_code=404, detail="Arquivo físico não encontrado.")
    mime, _ = mimetypes.guess_type(str(fp))
    return FileResponse(
        str(fp),
        media_type=mime or "application/octet-stream",
        headers={"Content-Disposition": f'inline; filename="{row["original_name"]}"'},
    )


@router.get("/api/documents/file/{doc_id}/view")
def view_document_metadata(doc_id: int):
    with db() as c:
        row = c.execute("SELECT id, original_name, stored_path, uploaded_at FROM document_links WHERE id = ?", (doc_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Documento não encontrado.")
    fp = Path(row["stored_path"])
    if not fp.exists():
        raise HTTPException(status_code=404, detail="Arquivo físico não encontrado no disco.")
    ext = fp.suffix.lower()
    if ext in (".png", ".jpg", ".jpeg", ".webp", ".gif"):
        return {"kind": "image", "name": row["original_name"], "raw_url": f"/api/documents/file/{doc_id}/raw"}
    if ext == ".pdf":
        return {"kind": "pdf", "name": row["original_name"], "raw_url": f"/api/documents/file/{doc_id}/raw"}
    if ext in (".txt", ".docx"):
        txt = _extract_document_text(fp)
        return {"kind": "text", "name": row["original_name"], "content": txt or "(Documento sem texto legível)"}
    return {"kind": "download_only", "name": row["original_name"]}


@router.delete("/api/documents/file/{doc_id}")
def delete_document_file(doc_id: int):
    with db() as c:
        row = c.execute("SELECT stored_path FROM document_links WHERE id = ?", (doc_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Documento não encontrado.")
        c.execute("DELETE FROM document_links WHERE id = ?", (doc_id,))
        c.commit()
    try:
        fp = Path(row["stored_path"])
        if fp.exists():
            fp.unlink()
    except Exception:
        pass
    return {"ok": True, "message": "Anexo removido."}


# ---------- AI Vision Endpoints (Etapa 5) ----------

class AiImagePayload(BaseModel):
    filename: str = "imagem.jpg"
    mime_type: str = "image/jpeg"
    data_base64: str


class AiApplyReceiptItem(BaseModel):
    name: str
    brand: str = ""
    no_brand: bool = False
    qty: float = 1.0
    unit: str = "un"
    value: float = 0.0
    category: str = "Comestível"
    barcode: str = ""
    action: str = "create"
    matched_material_id: Optional[int] = None
    reason: str = "Compra via Notinha (IA)"


class AiApplyReceiptPayload(BaseModel):
    purchase_date: str = ""
    items: List[AiApplyReceiptItem]


class AiParseRecipePayload(BaseModel):
    target_kind: str = "recipe"
    filename: str = "receita.jpg"
    mime_type: str = "image/jpeg"
    data_base64: str


@router.post("/api/ai/parse-receipt")
def api_ai_parse_receipt(payload: AiImagePayload):
    import base64
    from .ai_vision import parse_receipt_with_ai

    raw_b64 = payload.data_base64.split(",", 1)[-1]
    try:
        img_bytes = base64.b64decode(raw_b64)
    except Exception:
        raise HTTPException(status_code=400, detail="Imagem inválida.")

    try:
        return parse_receipt_with_ai(img_bytes, payload.mime_type or "image/jpeg")
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha ao interpretar notinha com IA: {str(e)}")


@router.post("/api/ai/apply-receipt")
def api_ai_apply_receipt(payload: AiApplyReceiptPayload):
    init_db()
    p_date = (payload.purchase_date or date.today().isoformat())[:10]
    created_count = 0
    updated_count = 0

    try:
        with db() as c:
            for it in payload.items:
                qty_val = float(it.qty or 0)
                val_num = float(it.value or 0)
                unit_val = (it.unit or "").strip()
                cat_val = (it.category or "").strip() or "Comestível"
                if qty_val <= 0:
                    raise ValueError(f'Quantidade inválida para "{it.name}".')
                if not unit_val:
                    raise ValueError(f'Unidade obrigatória para "{it.name}".')
                if val_num < 0 or (val_num == 0 and cat_val != "Doação"):
                    raise ValueError(f'Valor da compra obrigatório para "{it.name}" (maior que zero, exceto Doação).')

                if it.action == "update":
                    if not it.matched_material_id:
                        raise ValueError(f'Selecione o insumo existente para atualizar "{it.name}".')
                    mat_id = int(it.matched_material_id)
                    existing = c.execute(
                        "SELECT id, name, brand, purchase_qty, purchase_unit FROM materials WHERE id = ? AND COALESCE(archived, 0)=0",
                        (mat_id,),
                    ).fetchone()
                    if not existing:
                        raise ValueError(f'Insumo vinculado para "{it.name}" não encontrado.')
                    reason = (it.reason or "").strip()
                    if not reason:
                        raise ValueError(f'Informe o motivo da atualização para "{existing["name"]}".')

                    # Regra rígida: atualização pela notinha altera apenas valor e registra compra; não muda embalagem/marca do insumo.
                    c.execute(
                        "UPDATE materials SET purchase_value = ?, updated_at = ? WHERE id = ?",
                        (val_num, now_iso(), mat_id),
                    )
                    c.execute(
                        "INSERT INTO purchases(material_id, qty, unit, value, brand, purchase_date) VALUES(?,?,?,?,?,?)",
                        (
                            mat_id,
                            float(existing["purchase_qty"] or qty_val),
                            existing["purchase_unit"] or unit_val,
                            val_num,
                            f'{existing["brand"] or "Sem marca"} ({reason})',
                            p_date,
                        ),
                    )
                    updated_count += 1
                else:
                    clean_name = _validate_quality_text(it.name, "Nome do insumo")
                    clean_brand = _validate_quality_text(
                        it.brand,
                        "Marca",
                        is_brand=True,
                        no_brand=bool(it.no_brand),
                    )
                    _check_material_duplicate_or_typo(c, clean_name, clean_brand, qty_val, unit_val)
                    code = next_code("materials", "INS")
                    now_val = now_iso()
                    cur = c.execute(
                        """
                        INSERT INTO materials(code, name, purchase_qty, purchase_unit, purchase_value, brand, category, barcode, updated_at)
                        VALUES(?,?,?,?,?,?,?,?,?)
                        """,
                        (code, clean_name, qty_val, unit_val, val_num, clean_brand, cat_val, it.barcode.strip(), now_val),
                    )
                    mat_id = cur.lastrowid
                    c.execute(
                        "INSERT INTO purchases(material_id, qty, unit, value, brand, purchase_date) VALUES(?,?,?,?,?,?)",
                        (mat_id, qty_val, unit_val, val_num, clean_brand, p_date),
                    )
                    created_count += 1
            c.commit()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    snapshot_costs()
    return {
        "ok": True,
        "created": created_count,
        "updated": updated_count,
        "message": f"Notinha aplicada: {created_count} insumo(s) criado(s) e {updated_count} atualizado(s)!",
    }


@router.post("/api/ai/parse-recipe")
def api_ai_parse_recipe(payload: AiParseRecipePayload):
    import base64
    from .ai_vision import parse_recipe_or_product_with_ai

    raw_b64 = payload.data_base64.split(",", 1)[-1]
    try:
        file_bytes = base64.b64decode(raw_b64)
    except Exception:
        raise HTTPException(status_code=400, detail="Arquivo inválido.")

    ext = Path(payload.filename).suffix.lower()
    image_bytes: Optional[bytes] = None
    extra_text = ""

    if ext in (".png", ".jpg", ".jpeg", ".webp", ".gif") or (payload.mime_type or "").startswith("image/"):
        image_bytes = file_bytes
    else:
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=ext or ".txt", delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = Path(tmp.name)
        try:
            extra_text = _extract_document_text(tmp_path)
        finally:
            try:
                tmp_path.unlink()
            except Exception:
                pass
        if not extra_text.strip():
            raise HTTPException(status_code=400, detail="Não foi possível extrair texto deste arquivo. Tente enviar uma foto ou .docx/.txt.")

    try:
        return parse_recipe_or_product_with_ai(
            target_kind=payload.target_kind,
            image_bytes=image_bytes,
            mime_type=payload.mime_type or "image/jpeg",
            extra_text=extra_text,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha ao interpretar receita com IA: {str(e)}")
