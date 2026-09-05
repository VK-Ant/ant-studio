"""Load ANY file type — PDF, DOCX, Excel, CSV, images, TXT."""

def load_text(raw_bytes: bytes, filename: str) -> str:
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

    if ext == "pdf":
        return _load_pdf(raw_bytes)
    elif ext == "docx":
        return _load_docx(raw_bytes)
    elif ext in ("xlsx", "xls"):
        return _load_excel(raw_bytes, filename)
    elif ext == "csv":
        return raw_bytes.decode("utf-8", errors="ignore")
    elif ext in ("png", "jpg", "jpeg", "bmp", "tiff", "webp"):
        return _load_image_ocr(raw_bytes, filename)
    elif ext in ("txt", "md", "json", "xml", "html", "log", "yaml", "yml"):
        return raw_bytes.decode("utf-8", errors="ignore")
    else:
        try:
            return raw_bytes.decode("utf-8", errors="ignore")
        except Exception:
            return f"[Binary file: {filename}]"

def _load_pdf(raw_bytes):
    try:
        import fitz
        doc = fitz.open(stream=raw_bytes, filetype="pdf")
        return "\n".join(page.get_text() for page in doc)
    except ImportError:
        try:
            from docqwise import DocQWise
            return DocQWise().load_pdf(raw_bytes)
        except ImportError:
            return "[pip install PyMuPDF]"

def _load_docx(raw_bytes):
    try:
        import docx, io
        doc = docx.Document(io.BytesIO(raw_bytes))
        return "\n".join(p.text for p in doc.paragraphs)
    except ImportError:
        return "[pip install python-docx]"

def _load_excel(raw_bytes, filename):
    try:
        import pandas as pd, io
        df = pd.read_excel(io.BytesIO(raw_bytes))
        return df.to_string(index=False)
    except ImportError:
        return "[pip install openpyxl pandas]"

def _load_image_ocr(raw_bytes, filename):
    try:
        import pytesseract
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(raw_bytes))
        return pytesseract.image_to_string(img)
    except ImportError:
        try:
            import easyocr, io, numpy as np
            from PIL import Image
            img = np.array(Image.open(io.BytesIO(raw_bytes)))
            reader = easyocr.Reader(["en"])
            results = reader.readtext(img)
            return "\n".join(r[1] for r in results)
        except ImportError:
            return f"[Image: {filename} — pip install pytesseract Pillow OR easyocr]"
