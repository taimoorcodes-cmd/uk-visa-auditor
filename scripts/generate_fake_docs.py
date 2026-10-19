# scripts/generate_fake_docs.py
# Generates fake passport, CAS, and bank statement PDFs for testing parsers

import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

PASSPORT_PATH = "data/sample_docs/passports/fake_passport.pdf"
CAS_PATH = "data/sample_docs/cas/fake_cas.pdf"
BANK_PATH = "data/sample_docs/bank_statements/fake_bank_statement.pdf"


def create_fake_passport():
    """Create a fake passport PDF with MRZ lines."""
    os.makedirs(os.path.dirname(PASSPORT_PATH), exist_ok=True)

    c = canvas.Canvas(PASSPORT_PATH, pagesize=A4)
    width, height = A4

    # Header
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, height - 50, "PAKISTAN")
    c.setFont("Helvetica", 14)
    c.drawString(50, height - 75, "PASSPORT")

    # Personal info
    c.setFont("Helvetica", 11)
    c.drawString(50, height - 120, "Surname: KHAN")
    c.drawString(50, height - 140, "Given Names: ALI AHMED")
    c.drawString(50, height - 160, "Passport No: AA1234567")
    c.drawString(50, height - 180, "Date of Birth: 15/05/2002")
    c.drawString(50, height - 200, "Nationality: PAKISTANI")
    c.drawString(50, height - 220, "Date of Issue: 01/01/2025")
    c.drawString(50, height - 240, "Date of Expiry: 01/01/2030")
    c.drawString(50, height - 260, "Place of Birth: LAHORE")

    # Fake MRZ lines (2 lines at bottom, monospaced font)
    c.setFont("Courier", 10)
    mrz_line_1 = "P<PAKKHAN<<ALI<AHMED<<<<<<<<<<<<<<<<<<<<<<<"
    mrz_line_2 = "AA12345678PAK0205154M3001012<<<<<<<<<<<<<<04"

    c.drawString(50, 80, mrz_line_1)
    c.drawString(50, 65, mrz_line_2)

    c.save()
    print(f"✅ Created: {PASSPORT_PATH}")


def create_fake_cas():
    """Create a fake CAS PDF."""
    os.makedirs(os.path.dirname(CAS_PATH), exist_ok=True)

    c = canvas.Canvas(CAS_PATH, pagesize=A4)
    width, height = A4

    # Header
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, height - 50, "CONFIRMATION OF ACCEPTANCE FOR STUDIES (CAS)")
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 70, "University of Birmingham")

    # Student details
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 120, "Student Details")
    c.setFont("Helvetica", 11)
    c.drawString(50, height - 145, "Name: Ali Ahmed Khan")
    c.drawString(50, height - 165, "Date of Birth: 15 May 2002")
    c.drawString(50, height - 185, "Nationality: Pakistani")
    c.drawString(50, height - 205, "Passport Number: AA1234567")
    c.drawString(50, height - 225, "CAS Number: CAS-2026-12345-ABCDE")

    # Course details
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 270, "Course Details")
    c.setFont("Helvetica", 11)
    c.drawString(50, height - 295, "Course: MSc Artificial Intelligence")
    c.drawString(50, height - 315, "Course Start Date: 15 September 2026")
    c.drawString(50, height - 335, "Course End Date: 15 September 2027")
    c.drawString(50, height - 355, "Tuition Fee: £18,500")
    c.drawString(50, height - 375, "Tuition Paid: £5,000")
    c.drawString(50, height - 395, "Tuition Remaining: £13,500")
    c.drawString(50, height - 415, "Campus: Birmingham (Outside London)")

    c.save()
    print(f"✅ Created: {CAS_PATH}")


def create_fake_bank_statement():
    """Create a fake bank statement PDF."""
    os.makedirs(os.path.dirname(BANK_PATH), exist_ok=True)
    
    c = canvas.Canvas(BANK_PATH, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "HABIB BANK LIMITED (HBL)")
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 70, "Account Statement")
    c.drawString(50, height - 85, "Account Holder: Ali Ahmed Khan")
    c.drawString(50, height - 100, "Account Number: 1234-5678901-01")
    c.drawString(50, height - 115, "Statement Period: 01 August 2026 to 31 August 2026")
    c.drawString(50, height - 130, "Currency: PKR")

    # Table Header
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, height - 160, "Date")
    c.drawString(150, height - 160, "Description")
    c.drawString(400, height - 160, "Debit")
    c.drawString(480, height - 160, "Credit")
    c.drawString(550, height - 160, "Balance")

    # Table Rows
    c.setFont("Helvetica", 10)
    y = height - 180
    
    # Opening Balance (High enough to pass the funds check)
    c.drawString(50, y, "01/08/2026")
    c.drawString(150, y, "Opening Balance")
    c.drawString(550, y, "10,000,000")
    y -= 20

    # 30 days of history (balances stay above 8.9 million, which is > required 8.4M PKR)
    for day in range(2, 32):
        date_str = f"{day:02d}/08/2026"
        c.drawString(50, y, date_str)
        
        if day % 5 == 0:
            c.drawString(150, y, "ATM Withdrawal")
            c.drawString(400, y, "10,000")
        else:
            c.drawString(150, y, "POS Purchase")
            c.drawString(400, y, "2,000")
            
        # --- FIXED: This line must be OUTSIDE the if/else so it prints every day ---
        c.drawString(550, y, f"{10000000 - (day*2000):,}")
        
        y -= 15
        if y < 50:
            c.showPage()
            y = height - 50

    c.save()
    print(f"✅ Created: {BANK_PATH}")


if __name__ == "__main__":
    print("Generating fake test documents...")
    create_fake_passport()
    create_fake_cas()
    create_fake_bank_statement()
    print("✅ Done!")