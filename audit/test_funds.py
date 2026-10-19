# audit/test_funds.py
# Tests the full pipeline: Parse -> Check -> Result

import sys
import os

# Add the project root directory to Python's path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))



import json

# 1. Import your parsers and checks
from parsers.bank_parser import parse_bank_statement
from parsers.cas_parser import parse_cas
from audit.funds_check import check_funds

# 2. Load the rules
with open("rules/student_visa_rules.json", "r") as f:
    rules = json.load(f)

# 3. Define file paths
CAS_PATH = "data/sample_docs/cas/fake_cas.pdf"
BANK_PATH = "data/sample_docs/bank_statements/fake_bank_statement.pdf"

# 4. Parse the documents
print("Parsing documents...")
cas = parse_cas(CAS_PATH)
bank = parse_bank_statement(BANK_PATH)

print(f"CAS Tuition Remaining: £{cas.get('tuition_remaining', 0):,}")
print(f"CAS is London: {cas.get('is_london')}")
print(f"Bank Balances Found: {len(bank.get('daily_balances', {}))} days")

# 5. Run the funds check
print("\nRunning Funds Check...")
result = check_funds(
    bank_data=bank,
    cas_data=cas,
    rules=rules,
    application_date_str="2026-09-01",  # Assume they applied on Sep 1
)

print("\n" + "="*40)
print("FUNDS CHECK RESULT")
print("="*40)
print(f"Status: {result['status'].upper()}")
print(f"Message: {result['message']}")
if "max_consecutive" in result:
    print(f"Longest Consecutive Days: {result['max_consecutive']}")