# agents/state.py
from typing import TypedDict, Optional

class AgentState(TypedDict):
    # Inputs
    application_date: str
    is_london: bool
    has_dependants: bool
    
    # Document paths
    passport_path: Optional[str]
    cas_path: Optional[str]
    bank_path: Optional[str]
    
    # Parsed data
    passport_data: dict
    cas_data: dict
    bank_data: dict
    
    # Rules results
    funds_result: dict
    name_match_result: dict
    
    # Final Output
    readiness_score: int
    issues: list
    ai_summary: str
    error: Optional[str]