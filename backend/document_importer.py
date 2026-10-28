import re
import shutil
from pathlib import Path
from . import paths
from .database import db, now_iso


def save_uploaded_document(entity_type, entity_id, source_path):
    src = Path(source_path)
    paths.DOCS_DIR.mkdir(parents=True, exist_ok=True)
    target = paths.DOCS_DIR / f'{entity_type.lower()}_{entity_id}_{src.name}'
    shutil.copy2(src, target)
    with db() as c:
        c.execute('INSERT INTO document_links(entity_type,entity_id,original_name,stored_path,uploaded_at) VALUES(?,?,?,?,?)',
                  (entity_type, entity_id, src.name, str(target), now_iso()))
        c.commit()
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

