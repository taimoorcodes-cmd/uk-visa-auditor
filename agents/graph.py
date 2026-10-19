# agents/graph.py
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.graph import StateGraph, END
from agents.state import AgentState
from agents.nodes.rules_node import rules_node
from agents.nodes.ai_node import ai_node

def build_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("run_rules", rules_node)
    workflow.add_node("generate_ai", ai_node)
    
    workflow.set_entry_point("run_rules")
    workflow.add_edge("run_rules", "generate_ai")
    workflow.add_edge("generate_ai", END)
    
    return workflow.compile()

def run_audit(application_date, is_london, passport_path, cas_path, bank_path) -> AgentState:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from parsers.passport_parser import parse_passport
    from parsers.cas_parser import parse_cas
    from parsers.bank_parser import parse_bank_statement
    
    print("Parsing documents for graph...")
    passport = parse_passport(passport_path)
    cas = parse_cas(cas_path)
    bank = parse_bank_statement(bank_path)
    
    initial_state = {
        "application_date": application_date,
        "is_london": is_london,
        "has_dependants": False,
        "passport_data": passport,
        "cas_data": cas,
        "bank_data": bank,
        "issues": [],
        "readiness_score": 0,
        "ai_summary": "",
    }
    
    graph = build_graph()
    return graph.invoke(initial_state)