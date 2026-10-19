# parsers/bank_parser.py
# Extracts account holder, currency, and daily balances from bank statements

import pdfplumber
import re
from datetime import datetime


def parse_bank_statement(pdf_path: str) -> dict:
    """
    Extracts account holder, currency, and daily balances from a bank statement.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"

        extracted = {
            "valid": False,
            "account_holder": None,
            "currency": "PKR",
            "daily_balances": {},
            "error": None,
        }

        # 1. Extract Account Holder
        holder_match = re.search(
            r"Account\s+Holder[:\s]+(.+?)(?:\n|$)",
            full_text
        )
        if holder_match:
            extracted["account_holder"] = holder_match.group(1).strip()

        # 2. Extract Currency
        curr_match = re.search(
            r"Currency[:\s]+([A-Z]{3})",
            full_text
        )
        if curr_match:
            extracted["currency"] = curr_match.group(1).strip()

        # 3. Extract Daily Balances
        lines = full_text.split("\n")
        for line in lines:
            # Find dates at the start of each line (DD/MM/YYYY)
            date_match = re.match(
                r"^(\d{2}/\d{2}/\d{4})",
                line.strip()
            )
            if date_match:
                date_str = date_match.group(1)
                try:
                    dt = datetime.strptime(date_str, "%d/%m/%Y")
                    iso_date = dt.strftime("%Y-%m-%d")

                    # Extract all numbers from the line
                    numbers = re.findall(r"[\d,]+", line)
                    if numbers:
                        # Last number on the line = running balance
                        balance_str = numbers[-1].replace(",", "")
                        balance = float(balance_str)
                        extracted["daily_balances"][iso_date] = balance
                except ValueError:
                    pass

        if len(extracted["daily_balances"]) > 0:
            extracted["valid"] = True
        else:
            extracted["error"] = "Could not find daily balances in the table."

        return extracted

    except Exception as e:
        return {"valid": False, "error": str(e)}


if __name__ == "__main__":
    test_path = "data/sample_docs/bank_statements/fake_bank_statement.pdf"
    print(f"Testing Bank Parser on: {test_path}")
    result = parse_bank_statement(test_path)

    print("\n--- Extracted Data ---")
    for k, v in result.items():
        if k == "daily_balances":
            print(f"daily_balances: Found {len(v)} days")
            for i, (date, bal) in enumerate(v.items()):
                if i < 3:
                    print(f"  {date}: {bal:,.2f}")
        else:
            print(f"{k}: {v}")