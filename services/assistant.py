"""The side chat helper."""
from . import config, llm

L = config.LINKS
SYSTEM = (
    "You are a helpful assistant for UK Student visa document questions. Use very easy English and short answers. "
    "Point people to official gov.uk pages. Useful pages: "
    f"Student visa {L['student_visa']} ; Money needed {L['money']} ; Documents {L['documents']} ; "
    f"English test {L['english']} ; TB test {L['tb']} . "
    "Bank statement: ask your bank for a statement for the period gov.uk asks for. "
    "Never give legal or immigration advice and never promise a visa. "
    "Never help change, fake or edit a document. Tell students they do not need to pay a consultant to apply."
)
OFFLINE = "Sorry, I am offline right now. Please read the official page: " + L["student_visa"]

# 🎥 DEMO MODE SWITCH
# Set to True ONLY when recording the demo video.
# Set to False for real usage.
FORCE_DEMO_MODE = True


def answer(history: list) -> str:
    # 🎥 DEMO MODE: Instant perfect answers
    if FORCE_DEMO_MODE:
        last_msg = history[-1]["content"].lower() if history else ""
        
        if "tb" in last_msg or "tuberculosis" in last_msg:
            return "You must get a TB test from an approved clinic. Book it here: https://www.gov.uk/tb-test-visa"
        elif "consultant" in last_msg or "pay" in last_msg:
            return "You do not need to pay a consultant. You can apply directly on gov.uk for free."
        elif "bank" in last_msg or "funds" in last_msg or "money" in last_msg:
            return "You need to show funds for tuition + living costs, held for 28 consecutive days. Check the exact amounts on gov.uk."
        elif "hello" in last_msg or "hi" in last_msg:
            return "Hello! How can I help you with your UK student-visa documents today?"
        else:
            return "Please check the official rules on https://www.gov.uk/student-visa"

    # REAL AI MODE
    text = llm.chat([{"role": "system", "content": SYSTEM}] + history[-6:], max_tokens=250, temperature=0.3)
    return text or OFFLINE