"""Read text from PDFs and photos. Tries real text first, then OCR for scans."""
import os

MIN_TEXT = 40


def _ocr_image(img) -> str:
    import pytesseract
    return pytesseract.image_to_string(img, lang=os.getenv("OCR_LANG", "eng"))


def extract_text(path: str):
    """Returns (text, method). method is 'text', 'ocr' or 'failed'."""
    ext = os.path.splitext(path)[1].lower()

    if ext in (".png", ".jpg", ".jpeg"):
        try:
            from PIL import Image
            with Image.open(path) as img:
                text = _ocr_image(img.convert("L"))
            return (text, "ocr") if len(text.strip()) >= MIN_TEXT else (text, "failed")
        except Exception:
            return "", "failed"

    text = ""
    try:
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            parts = [(page.extract_text() or "") for page in pdf.pages[:10]]
        text = "\n".join(parts)
    except Exception:
        text = ""
    if len(text.strip()) >= MIN_TEXT:
        return text, "text"

    try:
        from pdf2image import convert_from_path
        pages = convert_from_path(path, dpi=200, first_page=1, last_page=5)
        text = "\n".join(_ocr_image(p) for p in pages)
        if len(text.strip()) >= MIN_TEXT:
            return text, "ocr"
    except Exception:
        pass
    return text, "failed"