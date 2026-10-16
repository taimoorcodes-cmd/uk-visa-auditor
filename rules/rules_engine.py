# rules/rules_engine.py
# Deterministic rules engine — AI does NOT decide pass/fail

import json
from pathlib import Path

RULES_PATH = Path(__file__).parent / "student_visa_rules.json"


def load_rules():
    """Load the JSON rules file."""
    with open(RULES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def run_rules(rules_config, extracted_data):
    """
    Run all rules against extracted data.
    Returns a list of result dicts.
    """
    results = []

    # Map check names to functions
    checks = {
        "funds_full_check": check_funds_full,
        "name_fuzzy_match": check_name_fuzzy,
    }

    for rule in rules_config.get("rules", []):
        check_fn = checks.get(rule["check"])

        # If check function not found → mark as unknown
        if not check_fn:
            results.append({
                "rule_id": rule["id"],
                "title": rule["title"],
                "severity": rule["severity"],
                "status": "unknown",
                "message": f"Check not found: {rule['check']}",
                "source_url": rule["source_url"],
            })
            continue

        # Run the check
        result = check_fn(rule, extracted_data)

        results.append({
            "rule_id": rule["id"],
            "title": rule["title"],
            "severity": rule["severity"],
            "status": result["status"],
            "message": result.get("message", ""),
            "source_url": rule["source_url"],
        })

    return results


def check_funds_full(rule, data):
    """
    Placeholder for the funds check.
    Will be fully implemented on Day 3.

    Expected to check:
    - Balance >= required amount
    - For 28 consecutive days
    - Ending within 31 days of application
    """
    return {
        "status": "unknown",
        "message": "Funds check not yet implemented"
    }


def check_name_fuzzy(rule, data):
    """
    Placeholder for the name match check.
    Will be implemented on Day 4 with fuzzy logic.

    Expected to compare:
    - Name from passport
    - Name from CAS
    - Flag warnings on close match, critical on clear mismatch
    """
    return {
        "status": "unknown",
        "message": "Name match check not yet implemented"
    }


def calculate_score(results):
    """
    Calculate readiness score 0-100.

    Rules:
    - Start at 100
    - Critical failure: -30
    - Major failure: -15
    - Minor failure: -5
    - Any critical failure caps score at 60
    - Unknowns don't subtract
    """
    score = 100
    critical_failed = False

    for r in results:
        if r["status"] == "fail":
            if r["severity"] == "critical":
                score -= 30
                critical_failed = True
            elif r["severity"] == "major":
                score -= 15
            elif r["severity"] == "minor":
                score -= 5

    # Cap at 60 if any critical failure
    if critical_failed and score > 60:
        score = 60

    return max(0, score)


# --- Test when run directly ---
if __name__ == "__main__":
    print("Testing rules engine...")
    rules = load_rules()
    print(f"Loaded {len(rules['rules'])} rules")

    # Fake data for testing
    fake_data = {
        "passport": {"name": "ALI AHMED KHAN", "expiry": "2030-01-01"},
        "cas": {"name": "Ali Ahmed Khan", "course_end": "2027-09-01"},
        "bank": {"daily_balances": {}, "statement_date": "2026-10-01"},
    }

    results = run_rules(rules, fake_data)
    for r in results:
        print(f"  {r['rule_id']}: {r['status']}")

    score = calculate_score(results)
    print(f"Score: {score}/100")
    print("✅ Rules engine works!")