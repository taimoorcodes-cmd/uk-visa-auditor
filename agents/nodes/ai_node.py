# agents/nodes/ai_node.py
import os
import sys
from openai import OpenAI
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from agents.state import AgentState

load_dotenv()
client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

def ai_node(state: AgentState) -> AgentState:
    print("[GRAPH] Running ai_node...")
    
    score = state["readiness_score"]
    issues = state["issues"]
    
    if score >= 90:
        tone = "Congratulations! Your application looks excellent."
    elif score >= 60:
        tone = "Your application is almost ready, but you need to fix a few things."
    else:
        tone = "Please be careful. There are critical issues with your application right now."

    issue_text = "\n".join([f"- {i['message']}" for i in issues]) or "- No issues found."

    prompt = f"""You are a helpful UK visa advisor.
The student's readiness score is {score}/100.
Here are the issues found:
{issue_text}

Write a short, friendly 2-3 sentence summary for the student in simple English.
Start with: "{tone}"
Then summarize the main issue they need to fix. Do not use markdown."""

    try:
        response = client.chat.completions.create(
            model="openrouter/auto",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150
        )
        state["ai_summary"] = response.choices[0].message.content.strip()
    except Exception as e:
        state["ai_summary"] = f"{tone} Please review your documents. (AI unavailable)"
        
    return state