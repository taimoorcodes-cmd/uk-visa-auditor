import pdfplumber

pdf_path = "data/sample_docs/passports/fake_passport.pdf"

with pdfplumber.open(pdf_path) as pdf:
    for i, page in enumerate(pdf.pages):
        text = page.extract_text()
        print(f"--- Page {i+1} ---")
        print(text)
        print("--- End of page ---")