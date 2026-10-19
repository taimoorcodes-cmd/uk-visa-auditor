"""Checks for the extra documents: TB, IELTS, reference letter, qualification, tuition receipt, sponsor letter.
Every message is written in easy English on purpose.
Each analyzer returns {"fields": {...}, "issues": [...]}.
"""
import re
from datetime import date

from . import config
from .textutil import date_near, find_dates, name_score

L = config.LINKS


def issue(id_, severity, doc, message, fix="", link=""):
    return {"id": id_, "severity": severity, "doc": doc, "message": message, "fix": fix, "link": link}


def _name_issues(doc: str, label: str, text: str, ctx: dict) -> list:
    name = ctx.get("passport_name")
    if not name:
        return []
    score = name_score(text, name)
    if score >= 0.99:
        return []
    if score >= 0.6:
        return [issue(f"{doc.upper()}_NAME_CLOSE", "warning", doc, f"The name on your {label} is close to your passport name, but not exactly the same.", "Make sure the spelling is exactly as in your passport.", L["documents"])]
    return [issue(f"{doc.upper()}_NAME_MISMATCH", "critical", doc, f"We could not find your passport name on your {label}.", "Check that this is the right file.", L["documents"])]


_TB_CLEAR = re.compile(r"no evidence of (active )?(pulmonary )?(tb|tuberculosis)|(tb|tuberculosis)[\s\-]*(clear|free)|(tb|tuberculosis) (was |is )?not (detected|found|seen)|certificate of (tb|tuberculosis) clearance|clear(ed)? (of|from) (tb|tuberculosis)")
_TB_BAD = re.compile(r"(evidence of|active|suspected|positive for) (pulmonary )?(tb|tuberculosis)|further (tests?|evaluation|investigation)s? (is |are )?required|sputum")

def analyze_tb(text: str, ctx: dict) -> dict:
    low = text.lower()
    issues, fields = [], {}
    if not re.search(r"\b(tb|tuberculosis)\b", low):
        issues.append(issue("TB_NOT_TB", "warning", "tb", "This file does not look like a TB test certificate.", "Upload the certificate you got from the approved clinic.", L["tb"]))
        return {"fields": fields, "issues": issues}
    if _TB_CLEAR.search(low):
        fields["result"] = "clear"
    elif _TB_BAD.search(low):
        fields["result"] = "not clear"
        issues.append(issue("TB_RESULT_BAD", "critical", "tb", "The certificate may not show a clear TB result.", "Talk to the clinic.", L["tb"]))
    else:
        fields["result"] = "unknown"
        issues.append(issue("TB_RESULT_UNKNOWN", "warning", "tb", "We could not find the TB result words in this file.", "Check the certificate yourself.", L["tb"]))
    tested = date_near(text, ["date of test", "test date", "date of screening", "date of examination", "date of x-ray", "date of issue", "issued on", "issue date", "date of certificate"])
    app_date = ctx.get("application_date") or date.today()
    if tested:
        fields["certificate_date"] = tested.isoformat()
        age = (app_date - tested).days
        if age > config.TB_VALID_DAYS:
            issues.append(issue("TB_EXPIRED", "critical", "tb", f"Your TB certificate is about {age // 30} months old. It is only valid for about 6 months.", "Book a new TB test.", L["tb"]))
        elif age < 0:
            issues.append(issue("TB_DATE_FUTURE", "warning", "tb", "The TB date is after your planned application date.", "Check the date.", L["tb"]))
    else:
        issues.append(issue("TB_NO_DATE", "warning", "tb", "We could not find the date on your TB certificate.", "Make sure the issue date is clear.", L["tb"]))
    issues += _name_issues("tb", "TB certificate", text, ctx)
    issues.append(issue("TB_CLINIC_INFO", "info", "tb", "The TB test must be done at a clinic on the official approved list.", "Check the list on gov.uk.", L["tb"]))
    return {"fields": fields, "issues": issues}


_BAND = r"([0-9](?:\.[05])?)"

def _bands(text: str) -> dict:
    out = {}
    for skill in ("listening", "reading", "writing", "speaking"):
        m = re.search(skill + r"\D{0,15}?\b" + _BAND + r"\b", text, re.I)
        if m and 0 <= float(m.group(1)) <= 9:
            out[skill] = float(m.group(1))
    m = re.search(r"overall(?: band)?(?: score)?\D{0,25}?\b" + _BAND + r"\b", text, re.I)
    if m and 0 <= float(m.group(1)) <= 9:
        out["overall"] = float(m.group(1))
    return out

def analyze_ielts(text: str, ctx: dict) -> dict:
    low = text.lower()
    issues, fields = [], {}
    if "ielts" not in low and "english" not in low:
        issues.append(issue("IELTS_NOT_FOUND", "warning", "ielts", "This file does not look like an English test result.", "Upload your IELTS Test Report Form.", L["english"]))
        return {"fields": fields, "issues": issues}
    ukvi = "ukvi" in low or "for uk visas" in low or "uk visas and immigration" in low
    fields["ukvi_version"] = ukvi
    if not ukvi:
        issues.append(issue("IELTS_NOT_UKVI", "warning", "ielts", "This looks like a normal IELTS, not 'IELTS for UKVI'.", "Check your CAS and university offer.", L["english"]))
    bands = _bands(text)
    fields["bands"] = bands
    level = ctx.get("english_level", "B2")
    need = ctx.get("min_band") if level == "custom" else config.ENGLISH_LEVELS.get(level, 5.5)
    need = float(need or 5.5)
    missing = [s for s in ("listening", "reading", "writing", "speaking") if s not in bands]
    if missing:
        issues.append(issue("IELTS_BANDS_UNREADABLE", "warning", "ielts", "We could not read these scores: " + ", ".join(missing) + ".", "Check them yourself, or upload a clearer copy.", L["english"]))
    low_parts = [f"{s} ({bands[s]})" for s in ("listening", "reading", "writing", "speaking") if s in bands and bands[s] < need]
    if low_parts:
        issues.append(issue("IELTS_LOW_SCORE", "critical", "ielts", f"You need at least {need} in each part. These are lower: " + ", ".join(low_parts) + ".", "You may need to retake the test.", L["english"]))
    tested = date_near(text, ["test date", "date of test", "date of exam"])
    app_date = ctx.get("application_date") or date.today()
    if tested:
        fields["test_date"] = tested.isoformat()
        if (app_date - tested).days > config.IELTS_VALID_DAYS:
            issues.append(issue("IELTS_EXPIRED", "critical", "ielts", "Your English test result is more than 2 years old.", "Take a new test.", L["english"]))
    else:
        issues.append(issue("IELTS_NO_DATE", "warning", "ielts", "We could not find the test date.", "Make sure the test date is clear.", L["english"]))
    issues += _name_issues("ielts", "English test result", text, ctx)
    return {"fields": fields, "issues": issues}


_ROLES = r"professor|lecturer|head of|principal|manager|supervisor|director|dean|teacher|hod|coordinator|registrar|employer"
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE = re.compile(r"(\+?\d[\d\s\-]{8,}\d)")

def analyze_reference(text: str, ctx: dict) -> dict:
    low = text.lower()
    issues, fields = [], {}
    words = len(text.split())
    fields["words"] = words
    if words < 120:
        issues.append(issue("REF_SHORT", "warning", "reference", "This reference letter is very short.", "A good letter says who the writer is and how long they know you.", L["documents"]))
    dates = find_dates(text)
    app_date = ctx.get("application_date") or date.today()
    if not dates:
        issues.append(issue("REF_NO_DATE", "warning", "reference", "We could not find a date on the letter.", "Ask the writer to add the date.", ""))
    else:
        newest = max(d for d, _ in dates)
        fields["letter_date"] = newest.isoformat()
        if (app_date - newest).days > config.REFERENCE_MAX_AGE_DAYS:
            issues.append(issue("REF_OLD", "warning", "reference", "The letter is more than 1 year old.", "Ask for a new one if needed.", ""))
    if not re.search(_ROLES, low):
        issues.append(issue("REF_NO_ROLE", "warning", "reference", "We could not find the writer's job title.", "The letter should show who wrote it and their position.", ""))
    if not (_EMAIL.search(text) or _PHONE.search(text)):
        issues.append(issue("REF_NO_CONTACT", "warning", "reference", "No email or phone number found for the writer.", "Add contact details.", ""))
    if not re.search(r"sincerely|regards|yours|faithfully|signature|signed", low):
        issues.append(issue("REF_NO_SIGN", "warning", "reference", "The letter may not be signed.", "Make sure it has a signature.", ""))
    if not re.search(r"university|college|school|institute|company|limited|ltd|organi[sz]ation|department", low):
        issues.append(issue("REF_NO_LETTERHEAD", "info", "reference", "We could not see an institution or company name.", "Letters on official letterhead look more trusted.", ""))
    issues += _name_issues("reference", "reference letter", text, ctx)
    issues.append(issue("REF_INFO", "info", "reference", "A reference letter is usually asked for by the university, not by the visa office.", "Check your university offer.", L["documents"]))
    return {"fields": fields, "issues": issues}


def analyze_qualification(text: str, ctx: dict) -> dict:
    low = text.lower()
    issues, fields = [], {}
    if not re.search(r"degree|bachelor|master|diploma|transcript|certificate|intermediate|a[\s\-]?level|fsc|hssc|ssc|matric|marks|cgpa|gpa", low):
        issues.append(issue("QUAL_NOT_FOUND", "warning", "qualification", "This file does not look like a degree, transcript or certificate.", "Upload the certificate that you used for your university offer.", L["documents"]))
        return {"fields": fields, "issues": issues}
    if not re.search(r"university|college|board|institute|school", low):
        issues.append(issue("QUAL_NO_INSTITUTE", "warning", "qualification", "We could not find the name of the university, college or board.", "Make sure the issuing place is clear.", ""))
    years = [int(y) for y in re.findall(r"\b(19[9]\d|20[0-3]\d)\b", text)]
    if years:
        fields["latest_year"] = max(years)
    grade = re.search(r"(cgpa|gpa|percentage|grade|marks)\D{0,15}(\d+(?:\.\d+)?)", low)
    if grade:
        fields["grade"] = grade.group(2)
    else:
        issues.append(issue("QUAL_NO_GRADE", "info", "qualification", "We could not find a grade, GPA or marks.", "Check that your result page is included.", ""))
    if "provisional" in low:
        issues.append(issue("QUAL_PROVISIONAL", "info", "qualification", "This is a provisional document.", "Keep your final certificate ready.", ""))
    issues += _name_issues("qualification", "certificate", text, ctx)
    return {"fields": fields, "issues": issues}


_MONEY = re.compile(r"(?:£|gbp|pkr|rs\.?|usd|\$)\s?([\d,]+(?:\.\d{1,2})?)", re.I)

def analyze_tuition(text: str, ctx: dict) -> dict:
    low = text.lower()
    issues, fields = [], {}
    if not re.search(r"receipt|paid|payment|transaction|deposit|received|invoice|remittance|swift", low):
        issues.append(issue("TUI_NOT_RECEIPT", "warning", "tuition", "This file does not look like a payment receipt.", "Upload the receipt or bank transfer proof.", L["money"]))
        return {"fields": fields, "issues": issues}
    amounts = [m.group(1) for m in _MONEY.finditer(text)]
    if amounts:
        fields["amounts_found"] = amounts[:5]
    else:
        issues.append(issue("TUI_NO_AMOUNT", "warning", "tuition", "We could not find an amount on the receipt.", "Make sure the amount and currency are clear.", L["money"]))
    if not find_dates(text):
        issues.append(issue("TUI_NO_DATE", "warning", "tuition", "We could not find a payment date.", "Make sure the payment date is clear.", ""))
    issues += [i for i in _name_issues("tuition", "payment receipt", text, ctx) if i["severity"] != "critical"]
    issues.append(issue("TUI_INFO", "info", "tuition", "If you already paid fees, your CAS should show the amount you paid.", "The money you need to show in the bank is lower when fees are already paid.", L["money"]))
    return {"fields": fields, "issues": issues}


def analyze_sponsor(text: str, ctx: dict) -> dict:
    low = text.lower()
    issues, fields = [], {}
    if not re.search(r"father|mother|parent|guardian|husband|wife|sponsor|uncle|brother|sister", low):
        issues.append(issue("SPO_NO_RELATION", "warning", "sponsor", "We could not find how the writer is related to you.", "The letter should say the relationship clearly.", L["money"]))
    if not re.search(r"consent|permission|agree|allow|no objection|support|sponsor|bear|pay", low):
        issues.append(issue("SPO_NO_CONSENT", "warning", "sponsor", "We could not find words that show the writer agrees to support you.", "The letter should clearly say you can use their money.", L["money"]))
    if not find_dates(text):
        issues.append(issue("SPO_NO_DATE", "warning", "sponsor", "We could not find a date on the letter.", "Add the date.", ""))
    if not re.search(r"sincerely|regards|yours|signature|signed|sign", low):
        issues.append(issue("SPO_NO_SIGN", "warning", "sponsor", "The letter may not be signed.", "Make sure it is signed.", ""))
    issues += _name_issues("sponsor", "sponsor letter", text, ctx)
    issues.append(issue("SPO_INFO", "info", "sponsor", "If the money is in a parent's account, you usually also need your birth certificate.", "Read the money page on gov.uk.", L["money"]))
    return {"fields": fields, "issues": issues}


ANALYZERS = {
    "tb": analyze_tb,
    "ielts": analyze_ielts,
    "reference": analyze_reference,
    "qualification": analyze_qualification,
    "tuition": analyze_tuition,
    "sponsor": analyze_sponsor,
}