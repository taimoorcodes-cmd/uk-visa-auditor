# parsers/passport_parser.py
# Extracts data from passport PDFs using MRZ lines

import pdfplumber
from mrz.checker.td3 import TD3CodeChecker
from datetime import datetime


def parse_passport(pdf_path: str) -> dict:
    """
    Extracts information from a passport PDF using MRZ (Machine Readable Zone).
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
                "extraction_method": None,
                "error": "PDF has no extractable text (may be scanned image)"
            }

        # 2. Find MRZ lines
        lines = [line.strip() for line in full_text.split("\n") if line.strip()]
        cleaned_lines = [line.replace(" ", "") for line in lines]

        mrz_lines = []
        for line in cleaned_lines:
            # Line 1: starts with P< (passport) 
            if line.startswith("P<") and len(line) >= 38:
                mrz_lines.append(line)
            # Line 2: contains lots of <<< and digits
            elif "<<<" in line and len(line) >= 38 and any(c.isdigit() for c in line):
                mrz_lines.append(line)

        if len(mrz_lines) < 2:
            return {
                "valid": False,
                "extraction_method": None,
                "error": "Could not find 2 valid MRZ lines in the document"
            }

        # Use last 2 MRZ lines
        line1 = mrz_lines[-2]
        line2 = mrz_lines[-1]

        # FORCE exactly 44 characters each by padding with '<'
        line1 = (line1 + "<" * 44)[:44]
        line2 = (line2 + "<" * 44)[:44]
        mrz_code = f"{line1}\n{line2}"

        # 3. Try official MRZ library first
        try:
            mrz_checker = TD3CodeChecker(mrz_code)
            
            # FIXED: Removed .check() and .return_fields()
            # If TD3CodeChecker doesn't throw an error, the MRZ is valid.
            extracted_data = {
                "valid": True,  # If we are here, the checksum passed!
                "extraction_method": "mrz",
                "surname": mrz_checker.surname,
                "given_names": mrz_checker.given_names,
                "name": f"{mrz_checker.given_names} {mrz_checker.surname}".strip(),
                "passport_number": mrz_checker.document_number,
                "nationality": mrz_checker.nationality,
                "date_of_birth": mrz_checker.birth_date,
                "sex": mrz_checker.sex,
                "expiry_date": mrz_checker.expiry_date,
                "error": None,
            }
            return extracted_data

        except Exception as mrz_error:
            # Official library rejected it — use manual fallback
            print(f"[DEBUG] MRZ library rejected: {mrz_error}")
            print("[DEBUG] Using manual fallback extraction...")

            extracted = {
                "valid": False,  # NOT officially verified
                "extraction_method": "fallback",
                "surname": None,
                "given_names": None,
                "name": None,
                "passport_number": None,
                "nationality": None,
                "date_of_birth": None,
                "sex": None,
                "expiry_date": None,
                "error": f"MRZ library error, used fallback: {mrz_error}",
            }

            # --- Extract Passport Number (line2, chars 0-9) ---
            if len(line2) >= 9:
                extracted["passport_number"] = line2[:9].replace("<", "").strip()

            # --- Extract Nationality (line2, chars 10-13) ---
            if len(line2) >= 13:
                extracted["nationality"] = line2[10:13].strip()

            # --- Extract Sex (line2, char 20) ---
            if len(line2) >= 21:
                extracted["sex"] = line2[20]

            # --- Extract DOB (line2, chars 13-19, YYMMDD) ---
            if len(line2) >= 19:
                dob_raw = line2[13:19]
                try:
                    extracted["date_of_birth"] = datetime.strptime(
                        dob_raw, "%y%m%d"
                    ).strftime("%Y-%m-%d")
                except ValueError:
                    pass

            # --- Extract Expiry (line2, chars 21-27, YYMMDD) ---
            if len(line2) >= 27:
                exp_raw = line2[21:27]
                try:
                    extracted["expiry_date"] = datetime.strptime(
                        exp_raw, "%y%m%d"
                    ).strftime("%Y-%m-%d")
                except ValueError:
                    pass

            # --- Extract Name (line1, after country code) ---
            if line1.startswith("P<") and len(line1) >= 5:
                # Skip "P<" + 3-char country code
                name_part = line1[5:]
                # Split surname and given names by '<<'
                if "<<" in name_part:
                    surname_part, given_part = name_part.split("<<", 1)
                    extracted["surname"] = surname_part.replace("<", " ").strip()
                    # Given names may have single < for multiple names
                    extracted["given_names"] = given_part.replace("<", " ").strip().rstrip("<")
                else:
                    # No << found, treat all as surname
                    extracted["surname"] = name_part.replace("<", " ").strip()

                # Build full name
                if extracted["surname"] and extracted["given_names"]:
                    extracted["name"] = f"{extracted['given_names']} {extracted['surname']}"
                elif extracted["surname"]:
                    extracted["name"] = extracted["surname"]

            return extracted

    except Exception as e:
        return {
            "valid": False,
            "extraction_method": None,
            "error": f"Passport parsing error: {str(e)}"
        }


# --- Test when run directly ---
if __name__ == "__main__":
    test_path = "data/sample_docs/passports/fake_passport.pdf"
    print(f"Testing passport parser on: {test_path}")

    result = parse_passport(test_path)

    print("\n--- Extracted Data ---")
    for key, value in result.items():
        print(f"{key}: {value}")