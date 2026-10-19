# agents/nodes/rules_node.py
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.state import AgentState
from audit.funds_check import check_funds
from rapidfuzz import fuzz

def rules_node(state: AgentState) -> AgentState:
    print("[GRAPH] Running rules_node...")
    
    # Load rules
    rules_path = os.path.join(os.path.dirname(__file__), "..", "..", "rules", "student_visa_rules.json")
    with open(rules_path, "r", encoding="utf-8") as f:
        rules = json.load(f)

    issues = []

    # 1. Run Funds Check
    funds = check_funds(
        bank_data=state["bank_data"],
        cas_data=state["cas_data"],
        rules=rules,
        application_date_str=state["application_date"]
    )
    state["funds_result"] = funds
    if funds["status"] != "pass":
        issues.append({"severity": "critical", "message": funds["message"]})

    # 2. Run Name Match Check (Fuzzy Match)
    p_name = state["passport_data"].get("name", "").lower()
    c_name = state["cas_data"].get("student_name", "").lower()
    
    match_score = fuzz.token_sort_ratio(p_name, c_name)
    if match_score > 80:
        state["name_match_result"] = {"status": "pass", "score": match_score}
    else:
        state["name_match_result"] = {"status": "fail", "score": match_score}
        issues.append({"severity": "critical", "message": f"Name mismatch: Passport says '{p_name.title()}', CAS says '{c_name.title()}'."})

    # 3. Calculate Score
    score = 100
    for issue in issues:
        if issue["severity"] == "critical":
            score -= 30
    
    # Cap at 60 if any critical fail
    if score < 100 and score > 60:
        score = 60
    score = max(0, score)
    
    state["readiness_score"] = score
    state["issues"] = issues
    print(f"[GRAPH] Score: {score}/100. Issues: {len(issues)}")
    
    return state