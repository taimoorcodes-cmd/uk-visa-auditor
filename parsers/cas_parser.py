# parsers/cas_parser.py
# Extracts data from CAS (Confirmation of Acceptance for Studies) PDFs

import pdfplumber
import re
from datetime import datetime


def parse_cas(pdf_path: str) -> dict:
    """
    Extracts information from a CAS PDF.
    """
    try:
        # 1. Extract text from PDF
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"

        if not full_text.strip():
            return {
                "valid": False,
                "error": "PDF has no extractable text"
            }

        # 2. Extract each field using regex patterns
        extracted_data = {
            "valid": False,
            "student_name": None,
            "cas_number": None,
            "course_name": None,
            "course_start_date": None,
            "course_end_date": None,
            "tuition_fee": None,
            "tuition_paid": None,
            "tuition_remaining": None,
            "campus_location": None,
            "is_london": False,
            "error": None
        }

        # --- Extract Student Name ---
        name_match = re.search(
            r"(?:Student\s+)?Name[:\s]+([A-Z][a-zA-Z\s]+?)(?:\n|$)",
            full_text
        )
        if name_match:
            extracted_data["student_name"] = name_match.group(1).strip()

        # --- Extract CAS Number ---
        cas_match = re.search(
            r"CAS\s+Number[:\s]+([A-Z0-9\-]+)",
            full_text
        )
        if cas_match:
            extracted_data["cas_number"] = cas_match.group(1).strip()

        # --- Extract Course Name ---
        # FIXED: Require a colon and exclude "Details", "Start", "End"
        course_match = re.search(
            r"Course:[ \t]+(?!Details|Start|End)(.+?)(?:\n|$)",
            full_text
        )
        if course_match:
            extracted_data["course_name"] = course_match.group(1).strip()

        # --- Extract Course Start Date ---
        start_match = re.search(
            r"Course\s+Start\s+Date[:\s]+(.+?)(?:\n|$)",
            full_text
        )
        if start_match:
            extracted_data["course_start_date"] = start_match.group(1).strip()

        # --- Extract Course End Date ---
        end_match = re.search(
            r"Course\s+End\s+Date[:\s]+(.+?)(?:\n|$)",
            full_text
        )
        if end_match:
            extracted_data["course_end_date"] = end_match.group(1).strip()

        # --- Extract Tuition Fee ---
        fee_match = re.search(
            r"Tuition\s+Fee[:\s]+[£$]?\s*([\d,]+)",
            full_text
        )
        if fee_match:
            try:
                extracted_data["tuition_fee"] = int(
                    fee_match.group(1).replace(",", "")
                )
            except ValueError:
                pass

        # --- Extract Tuition Paid ---
        paid_match = re.search(
            r"Tuition\s+Paid[:\s]+[£$]?\s*([\d,]+)",
            full_text
        )
        if paid_match:
            try:
                extracted_data["tuition_paid"] = int(
                    paid_match.group(1).replace(",", "")
                )
            except ValueError:
                pass

        # --- Extract Tuition Remaining ---
        remaining_match = re.search(
            r"Tuition\s+Remaining[:\s]+[£$]?\s*([\d,]+)",
            full_text
        )
        if remaining_match:
            try:
                extracted_data["tuition_remaining"] = int(
                    remaining_match.group(1).replace(",", "")
                )
            except ValueError:
                pass

        # --- Extract Campus Location ---
        # FIXED: "Outside London" must be checked before "London"
        campus_match = re.search(
            r"Campus[:\s]+(.+?)(?:\n|$)",
            full_text
        )
        if campus_match:
            campus_text = campus_match.group(1).strip()
            extracted_data["campus_location"] = campus_text
            
            # Check for London ONLY if "Outside London" is not in the text
            if "London" in campus_text and "Outside London" not in campus_text:
                extracted_data["is_london"] = True
            else:
                extracted_data["is_london"] = False

        # 3. Mark as valid if we got the key fields
        if (extracted_data["student_name"] and 
            extracted_data["tuition_remaining"] is not None):
            extracted_data["valid"] = True

        return extracted_data

    except Exception as e:
        return {
            "valid": False,
            "error": f"CAS parsing error: {str(e)}"
        }


# --- Test when run directly ---
if __name__ == "__main__":
    test_path = "data/sample_docs/cas/fake_cas.pdf"
    print(f"Testing CAS parser on: {test_path}")
    
    result = parse_cas(test_path)
    
    print("\n--- Extracted Data ---")
    for key, value in result.items():
        print(f"{key}: {value}")