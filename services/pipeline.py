"""Runs the full audit: your existing core audit + the extra document checks + easy-English summary."""
import os
import tempfile
from datetime import date, datetime, timezone

from . import config, narrator
from .doc_checks import ANALYZERS, issue
from .extract import extract_text
from .textutil import passport_name_from_text

# slug: (label, icon, required, allowed file types)
DOCS = {
    "passport": ("Passport", "🛂", True, ["pdf"]),
    "cas": ("CAS Letter", "🎓", True, ["pdf"]),
    "bank": ("Bank Statement", "🏦", True, ["pdf"]),
    "tb": ("TB Test Certificate", "🩺", False, ["pdf", "png", "jpg", "jpeg"]),
    "ielts": ("IELTS / English Test", "📝", False, ["pdf", "png", "jpg", "jpeg"]),
    "qualification": ("Degree / Transcript", "📜", False, ["pdf", "png", "jpg", "jpeg"]),
    "tuition": ("Tuition Payment Receipt", "🧾", False, ["pdf", "png", "jpg", "jpeg"]),
    "reference": ("Reference Letter", "✉️", False, ["pdf", "png", "jpg", "jpeg"]),
    "sponsor": ("Sponsor / Parent Letter", "🤝", False, ["pdf", "png", "jpg", "jpeg"]),
}
CORE = ("passport", "cas", "bank")

# Missing-document notes. (severity, easy message, fix, link)
MISSING = {
    "tb": ("warning", "You did not upload a TB test certificate. Students from Pakistan usually need one.",
           "Check the gov.uk TB page and book a test at an approved clinic.", config.LINKS["tb"]),
    "ielts": ("warning", "You did not upload an English test result.",
              "Check your CAS or offer letter. If you need a test, upload the result.", config.LINKS["english"]),
    "qualification": ("warning", "You did not upload the certificate or transcript you used for your offer.",
                      "Keep it ready. You may need to show it.", config.LINKS["documents"]),
    "tuition": ("info", "You did not upload a tuition payment receipt.",
                "Upload it if you already paid a deposit or fees.", config.LINKS["money"]),
}

_SEV_MAP = {
    "critical": "critical", "high": "critical", "error": "critical", "fail": "critical",
    "warning": "warning", "medium": "warning", "major": "warning", "minor": "warning", "warn": "warning",
    "info": "info", "low": "info",
}


def _normalize_core_issue(raw) -> dict:
    if isinstance(raw, str):
        raw = {"message": raw}
    sev = _SEV_MAP.get(str(raw.get("severity", "warning")).lower(), "warning")
    return {
        "id": raw.get("id", raw.get("rule", "CORE")),
        "severity": sev,
        "doc": "core",
        "message": str(raw.get("message", "")).strip(),
        "fix": raw.get("fix", ""),
        "link": raw.get("link", raw.get("source_url", "")),
    }


def compute_score(core_score: int, issues: list) -> int:
    extra = [i for i in issues if i["doc"] != "core"]
    penalty = sum(12 if i["severity"] == "critical" else 4 if i["severity"] == "warning" else 0 for i in extra)
    score = max(0, int(core_score) - min(penalty, 40))
    if any(i["severity"] == "critical" for i in issues):
        score = min(score, 60)
    return max(0, min(100, score))


def build_checklist(uploaded: set, issues: list) -> list:
    rows = []
    for slug, (label, icon, required, _) in DOCS.items():
        if slug not in uploaded:
            status = "missing"
        else:
            sevs = {i["severity"] for i in issues if i["doc"] == slug}
            status = "problem" if "critical" in sevs else "check" if "warning" in sevs else "ok"
        rows.append({"slug": slug, "label": label, "icon": icon, "required": required, "status": status})
    return rows


def run_full_audit(files: dict, application_date: date, is_london: bool, english_level: str = "B2",
                   min_band: float = 6.0, language: str = "en") -> dict:
    """`files` maps slug -> uploaded file object (needs .name and .getvalue()), or None."""
    temp_paths, paths = [], {}
    try:
        for slug, f in files.items():
            if f is None:
                continue
            suffix = os.path.splitext(f.name)[1].lower() or ".pdf"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(f.getvalue())
                paths[slug] = tmp.name
                temp_paths.append(tmp.name)

        # 1) Your existing core audit (passport + CAS + bank)
        from agents.graph import run_audit  # your existing code

        core = run_audit(
            application_date=str(application_date),
            is_london=is_london,
            passport_path=paths["passport"],
            cas_path=paths["cas"],
            bank_path=paths["bank"],
        )
        issues = [_normalize_core_issue(i) for i in core.get("issues", [])]
        issues = [i for i in issues if i["message"]]

        # 2) Extra documents
        passport_text, _ = extract_text(paths["passport"])
        ctx = {
            "passport_name": passport_name_from_text(passport_text),
            "application_date": application_date,
            "english_level": english_level,
            "min_band": min_band,
        }
        if not ctx["passport_name"]:
            issues.append(issue("PASSPORT_NAME_UNREADABLE", "info", "core",
                                "We could not read the name in your passport, so we skipped the name checks on the other documents.",
                                "Upload a clearer passport photo page.", ""))
        fields_read = {}
        for slug, analyzer in ANALYZERS.items():
            if slug not in paths:
                continue
            text, method = extract_text(paths[slug])
            label = DOCS[slug][0]
            if method == "failed":
                issues.append(issue(f"{slug.upper()}_UNREADABLE", "warning", slug,
                                    f"We could not read your {label}.",
                                    "Upload a clearer PDF or photo (good light, no blur).", ""))
                continue
            res = analyzer(text, ctx)
            issues += res["issues"]
            fields_read[slug] = res["fields"]

        # 3) Missing documents
        for slug, (sev, msg, fix, link) in MISSING.items():
            if slug not in paths:
                issues.append(issue(f"{slug.upper()}_MISSING", sev, slug, msg, fix, link))

        # 4) Easy English for the old messages (numbers are protected)
        core_items = [i for i in issues if i["doc"] == "core"]
        simple = narrator.simplify_messages([i["message"] for i in core_items])
        for item, text in zip(core_items, simple):
            item["message"] = text

        order = {"critical": 0, "warning": 1, "info": 2}
        issues.sort(key=lambda i: order.get(i["severity"], 3))

        score = compute_score(int(core.get("readiness_score", 0)), issues)
        summary = narrator.summarize(score, issues, language)
        return {
            "readiness_score": score,
            "score_label": narrator.score_label(score),
            "ai_summary": summary,
            "issues": issues,
            "checklist": build_checklist(set(paths), issues),
            "fields_read": fields_read,
            "language": language,
            "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        }
    finally:
        for p in temp_paths:  # privacy: always delete uploaded files
            try:
                os.remove(p)
            except OSError:
                pass