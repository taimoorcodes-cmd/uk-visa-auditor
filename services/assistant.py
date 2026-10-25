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


def answer(history: list) -> str:
    text = llm.chat([{"role": "system", "content": SYSTEM}] + history[-6:], max_tokens=250, temperature=0.3)
    return text or OFFLINE