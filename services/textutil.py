"""Small helpers: dates, names, passport name from MRZ."""
import re
from datetime import date
from rapidfuzz import fuzz

MONTHS = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, "jul": 7, "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12}
_NUM = re.compile(r"\b(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})\b")
_ISO = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
_DMY_TXT = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?[\s/\-]+([A-Za-z]{3,9})\.?,?[\s/\-]+(\d{4})\b")
_MDY_TXT = re.compile(r"\b([A-Za-z]{3,9})\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\b")

def _safe_date(y: int, m: int, d: int):
    try:
        return date(y, m, d)
    except ValueError:
        return None

def _month(word: str):
    return MONTHS.get(word.lower()[:4] if word.lower().startswith("sept") else word.lower()[:3])

def find_dates(text: str) -> list:
    found = []
    for m in _NUM.finditer(text):
        d = _safe_date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        if d:
            found.append((d, m.start()))
    for m in _ISO.finditer(text):
        d = _safe_date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        if d:
            found.append((d, m.start()))
    for m in _DMY_TXT.finditer(text):
        mon = _month(m.group(2))
        if mon:
            d = _safe_date(int(m.group(3)), mon, int(m.group(1)))
            if d:
                found.append((d, m.start()))
    for m in _MDY_TXT.finditer(text):
        mon = _month(m.group(1))
        if mon:
            d = _safe_date(int(m.group(3)), mon, int(m.group(2)))
            if d:
                found.append((d, m.start()))
    return sorted(found, key=lambda x: x[1])

def date_near(text: str, labels: list, window: int = 60):
    low = text.lower()
    best = None
    for label in labels:
        for m in re.finditer(re.escape(label.lower()), low):
            end = m.end()
            for d, pos in find_dates(text[end: end + window]):
                cand = (end + pos, d)
                if best is None or cand[0] < best[0]:
                    best = cand
                break
    return best[1] if best else None

def _tokens(name: str) -> list:
    return [t for t in re.sub(r"[^A-Za-z ]", " ", (name or "").upper()).split() if len(t) >= 2]

def name_score(text: str, name: str) -> float:
    want = _tokens(name)
    have = set(_tokens(text))
    if not want or not have:
        return 0.0
    total = 0.0
    for tok in want:
        if tok in have:
            total += 1.0
        elif any(fuzz.ratio(tok, h) >= 80 for h in have if len(tok) >= 5 and abs(len(h) - len(tok)) <= 2):
            total += 0.85
    return total / len(want)

def names_match_score(a: str, b: str) -> float:
    ta, tb = " ".join(sorted(_tokens(a))), " ".join(sorted(_tokens(b)))
    if not ta or not tb:
        return 0.0
    return fuzz.token_sort_ratio(ta, tb) / 100

_MRZ1 = re.compile(r"P[A-Z<]([A-Z]{3})([A-Z<]{4,40})")

def passport_name_from_text(text: str):
    for line in text.upper().splitlines():
        line = line.replace(" ", "")
        m = _MRZ1.search(line)
        if m and "<<" in m.group(2):
            surname, given = m.group(2).rstrip("<").split("<<", 1)
            full = f"{given.replace('<', ' ')} {surname.replace('<', ' ')}".strip()
            if len(full) >= 3:
                return re.sub(r"\s+", " ", full)
    m = re.search(r"SURNAME[:\s]+([A-Z ]{2,30})\s+GIVEN NAMES?[:\s]+([A-Z ]{2,40})", text.upper())
    if m:
        return re.sub(r"\s+", " ", f"{m.group(2)} {m.group(1)}").strip()
    return None
