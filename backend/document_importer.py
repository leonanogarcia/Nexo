"""Extração de texto de PDF para o Nexo 2.0."""


def extract_pdf_text(path: str) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        raise RuntimeError('Para importar PDF, instale a dependência "pypdf".')
    reader = PdfReader(path)
    return "\n".join((p.extract_text() or "") for p in reader.pages)
