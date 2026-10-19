# audit/funds_check.py
# The core logic for the 28-day funds rule

from datetime import datetime, timedelta


def check_funds(
    bank_data: dict,
    cas_data: dict,
    rules: dict,
    application_date_str: str
) -> dict:
    """
    Checks if the student has held enough money for 28 consecutive days.
    """
    try:
        # 1. Get Rules
        financial_rules = rules["financial_rules"]
        holding_days = financial_rules["holding_period_days"]          # 28
        validity_days = financial_rules["statement_validity_days"]     # 31
        gbp_to_pkr_rate = 350.0  # Temporary fixed rate (1 GBP = 350 PKR)

        # 2. Calculate Required Funds (in GBP)
        tuition_remaining_gbp = cas_data.get("tuition_remaining", 0)
        
        if cas_data.get("is_london"):
            monthly_living = financial_rules["living_costs_per_month_gbp_london"]
        else:
            monthly_living = financial_rules["living_costs_per_month_gbp_outside_london"]
            
        living_costs_gbp = monthly_living * financial_rules["living_costs_months"]
        total_required_gbp = tuition_remaining_gbp + living_costs_gbp

        # 3. Convert Required Funds to PKR
        total_required_pkr = total_required_gbp * gbp_to_pkr_rate

        # 4. Check Application Date
        app_date = datetime.strptime(application_date_str, "%Y-%m-%d")
        statement_valid_from = app_date - timedelta(days=validity_days)

        # 5. Analyze Daily Balances
        balances = bank_data.get("daily_balances", {})
        if not balances:
            return {
                "status": "fail",
                "message": "No balance data found in bank statement.",
                "required_pkr": total_required_pkr,
            }

        sorted_dates = sorted(balances.keys())
        
        consecutive_days = 0
        max_consecutive = 0
        balance_dropped_date = None

        for date_str in sorted_dates:
            current_date = datetime.strptime(date_str, "%Y-%m-%d")
            balance = balances[date_str]

            # Only check dates within the valid 31-day statement window
            if current_date < statement_valid_from or current_date > app_date:
                continue

            if balance >= total_required_pkr:
                consecutive_days += 1
                if consecutive_days > max_consecutive:
                    max_consecutive = consecutive_days
            else:
                consecutive_days = 0
                if balance_dropped_date is None:
                    balance_dropped_date = date_str

        # 6. Verdict
        readable_required = f"£{total_required_gbp:,.2f} (approx Rs {total_required_pkr:,.0f})"

        if max_consecutive >= holding_days:
            return {
                "status": "pass",
                "message": f"Funds successfully held for {max_consecutive} consecutive days. Required: {readable_required}.",
                "required_pkr": total_required_pkr,
                "max_consecutive": max_consecutive,
            }
        else:
            return {
                "status": "fail",
                "message": f"Funds held for only {max_consecutive} consecutive days. You need {holding_days} days. Required: {readable_required}.",
                "required_pkr": total_required_pkr,
                "max_consecutive": max_consecutive,
                "balance_dropped": balance_dropped_date,
            }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Funds check error: {str(e)}",
        }