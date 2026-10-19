"""Turns results into easy words. The AI only explains. Python decides pass or fail."""
import json
import re

from . import llm

BAD_WORDS = re.compile(r"guarantee|will be approved|100% safe|certain to|you will get (your )?visa", re.I)


def score_label(score: int) -> str:
    if score >= 85:
        return "Looking good"
    if score >= 60:
        return "Needs some fixes"
    return "Serious problems to fix"


def _bullets(items, limit):
    return "\n".join(f"- {i['message']}" for i in items[:limit])


def fallback_summary(score: int, issues: list) -> str:
    crit = [i for i in issues if i["severity"] == "critical"]
    warn = [i for i in issues if i["severity"] == "warning"]
    parts = [f"Your readiness score is **{score} out of 100** ({score_label(score).lower()})."]
    if crit:
        parts.append("**Fix these first:**\n" + _bullets(crit, 4))
    if warn:
        parts.append("**Please check these:**\n" + _bullets(warn, 4))
    if not crit and not warn:
        parts.append("We did not find any problems in the documents we checked.")
    parts.append("This is a check, not a promise. Only the Home Office can decide your visa.")
    return "\n\n".join(parts)


def summarize(score: int, issues: list, language: str = "en") -> str:
    real = [i for i in issues if i["severity"] in ("critical", "warning")]
    listing = "\n".join(f"[{i['severity']}] {i['message']}" for i in real[:12]) or "No problems found."
    lang = "simple Urdu (keep numbers and the words gov.uk as they are)" if language == "ur" else "very easy English"
    prompt = (
        f"Score: {score}/100. Problems: {listing}\n\n"
        f"Write a friendly summary in {lang}.\n"
        "Rules:\n"
        "- Just start with: 'Your score is {score} out of 100.'\n"
        "- Then write 'Main problems:' and list the problems above.\n"
        "- Do not add any other information.\n"
        "- Do not say you are an AI.\n"
        "- Maximum 50 words."
    )
    text = llm.chat(
        [{"role": "system", "content": "You are a kind helper who explains document checks in very simple words."},
         {"role": "user", "content": prompt}],
        max_tokens=350, temperature=0.2,
    )
    if not text or BAD_WORDS.search(text) or len(text) > 1500:
        return fallback_summary(score, issues)
    return text


def _digits(s: str) -> list:
    return sorted(re.findall(r"\d+(?:\.\d+)?", s))


def simplify_messages(messages: list) -> list:
    """Rewrite hard sentences in easy English. Keeps the original if the AI changes any number."""
    if not messages:
        return messages
    numbered = "\n".join(f"{i + 1}. {m}" for i, m in enumerate(messages))
    out = llm.chat(
        [{"role": "system", "content": "You rewrite sentences in very easy English. You never change numbers, dates or names."},
         {"role": "user", "content": "Rewrite each numbered sentence in very easy English (short words, under 20 words). "
                                     "Keep every number and date exactly the same. "
                                     "Return ONLY a JSON list of strings, same order.\n\n" + numbered}],
        max_tokens=900, temperature=0.1,
    )
    if not out:
        return messages
    m = re.search(r"\[.*\]", out, re.S)
    try:
        data = json.loads(m.group(0)) if m else None
    except (ValueError, AttributeError):
        data = None
    if not isinstance(data, list) or len(data) != len(messages):
        return messages
    result = []
    for old, new in zip(messages, data):
        ok = isinstance(new, str) and new.strip() and _digits(old) == _digits(new)
        result.append(new.strip() if ok else old)
    return result