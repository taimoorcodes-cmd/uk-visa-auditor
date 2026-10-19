"""Run with:  python tests/test_services.py
Uses only short plain-text snippets (no fake documents) and a temporary database."""
import os
import sys
import tempfile
import types
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ["OPENROUTER_API_KEY"] = ""  # force the no-AI fallbacks
os.environ["DEV_SHOW_CODE"] = "1"

from services import auth_email, config, db, doc_checks, interview, narrator, payments, pipeline, report_pdf, textutil  # noqa: E402

passed = 0


def check(name, cond):
    global passed
    assert cond, f"FAILED: {name}"
    passed += 1
    print("ok  ", name)


db.init_db()

# ---------- textutil ----------
ds = [d for d, _ in textutil.find_dates("Issued 05/03/2026, test date 12 March 2026, also Mar 7, 2026 and 2026-04-01 and 12/MAR/2026")]
check("dates parsed (5 formats)", date(2026, 3, 5) in ds and date(2026, 3, 12) in ds and date(2026, 3, 7) in ds and date(2026, 4, 1) in ds and len(ds) == 5)
check("date_near label", textutil.date_near("Name: X\nTest Date: 12/03/2026\nDOB 01/01/2000", ["test date"]) == date(2026, 3, 12))
check("passport name from MRZ", textutil.passport_name_from_text("P<PAKKHAN<<ALI<AHMED<<<<<<<<<<<<<<<<<<<<<<<<<<<") == "ALI AHMED KHAN")
check("name_score exact", textutil.name_score("Candidate: Ali Ahmed Khan", "ALI AHMED KHAN") == 1.0)
check("name_score typo is close, not exact", 0.6 < textutil.name_score("Candidate: Ali Ahmad Khan", "ALI AHMED KHAN") < 0.99)
check("name_score other person", textutil.name_score("Candidate: Sara Malik", "ALI AHMED KHAN") < 0.5)
check("names_match order", textutil.names_match_score("Khan Ali Ahmed", "Ali Ahmed Khan") > 0.95)

ctx = {"passport_name": "ALI AHMED KHAN", "application_date": date(2026, 9, 1), "english_level": "B2"}


def ids(res):
    return {i["id"] for i in res["issues"]}


# ---------- TB ----------
good_tb = "Certificate of TB clearance. Name: Ali Ahmed Khan. Chest x-ray shows no evidence of active tuberculosis. Date of issue: 10/07/2026"
r = doc_checks.analyze_tb(good_tb, ctx)
check("TB good has no critical", not any(i["severity"] == "critical" for i in r["issues"]))
old_tb = good_tb.replace("10/07/2026", "10/01/2026")
check("TB expired", "TB_EXPIRED" in ids(doc_checks.analyze_tb(old_tb, ctx)))
check("TB other name", "TB_NAME_MISMATCH" in ids(doc_checks.analyze_tb(good_tb.replace("Ali Ahmed Khan", "Sara Malik"), ctx)))
check("TB bad result", "TB_RESULT_BAD" in ids(doc_checks.analyze_tb("TB screening. Result: active tuberculosis suspected. Name: Ali Ahmed Khan. Date of issue 10/07/2026", ctx)))
check("TB not a TB file", "TB_NOT_TB" in ids(doc_checks.analyze_tb("Electricity bill for July", ctx)))

# ---------- IELTS ----------
ielts = ("IELTS for UKVI Academic Test Report Form. Candidate Ali Ahmed Khan. Test Date: 14/05/2026. "
         "Listening 6.5 Reading 6.0 Writing 5.5 Speaking 6.0 Overall Band Score 6.0")
r = doc_checks.analyze_ielts(ielts, ctx)
check("IELTS good", not any(i["severity"] == "critical" for i in r["issues"]) and r["fields"]["bands"]["writing"] == 5.5)
low = ielts.replace("Writing 5.5", "Writing 5.0")
check("IELTS low writing", "IELTS_LOW_SCORE" in ids(doc_checks.analyze_ielts(low, ctx)))
check("IELTS custom band", "IELTS_LOW_SCORE" in ids(doc_checks.analyze_ielts(ielts, {**ctx, "english_level": "custom", "min_band": 6.5})))
check("IELTS expired", "IELTS_EXPIRED" in ids(doc_checks.analyze_ielts(ielts.replace("14/05/2026", "14/05/2023"), ctx)))
check("IELTS not UKVI", "IELTS_NOT_UKVI" in ids(doc_checks.analyze_ielts(ielts.replace("for UKVI ", ""), ctx)))

# ---------- other docs ----------
ref = ("To whom it may concern. I am Professor of Computer Science at ABC University. " + "Ali Ahmed Khan studied under me for two years and is hard working. " * 12 +
       "Date: 01/08/2026. Email: prof@abc.edu.pk. Sincerely, Dr Prof")
r = doc_checks.analyze_reference(ref, ctx)
check("Reference good", not any(i["severity"] in ("critical", "warning") for i in r["issues"]))
check("Reference short", "REF_SHORT" in ids(doc_checks.analyze_reference("Ali Ahmed Khan is good. Regards", ctx)))
qual = "Bachelor of Science in Computer Science. Ali Ahmed Khan. Punjab University. CGPA 3.2. Session 2022"
check("Qualification good", not any(i["severity"] in ("critical", "warning") for i in doc_checks.analyze_qualification(qual, ctx)["issues"]))
tui = "Payment receipt. Received from Ali Ahmed Khan GBP 4,000.00 tuition deposit. Date 02/06/2026"
check("Tuition good", not any(i["severity"] in ("critical", "warning") for i in doc_checks.analyze_tuition(tui, ctx)["issues"]))
spo = "I, the father of Ali Ahmed Khan, give my consent to support his studies in the UK. Date: 01/07/2026. Signed"
check("Sponsor good", not any(i["severity"] in ("critical", "warning") for i in doc_checks.analyze_sponsor(spo, ctx)["issues"]))

# ---------- score + narrator ----------
mk = lambda sev, doc="tb": {"id": "x", "severity": sev, "doc": doc, "message": "msg", "fix": "", "link": ""}
check("score caps at 60 with critical", pipeline.compute_score(95, [mk("critical", "core")]) == 60)
check("score penalties", pipeline.compute_score(90, [mk("warning"), mk("warning")]) == 82)
check("score no negative", pipeline.compute_score(10, [mk("critical")] * 10) == 0)
fb = narrator.summarize(70, [mk("critical"), mk("warning")])
check("fallback summary", "70 out of 100" in fb and "not a promise" in fb)
check("simplify w/o AI keeps text", narrator.simplify_messages(["Hello 12"]) == ["Hello 12"])
check("score labels", narrator.score_label(90) == "Looking good" and narrator.score_label(10) == "Serious problems to fix")

# ---------- email code + db ----------
ok, msg, code = auth_email.send_code("student@example.com")
check("OTP sent in dev mode", ok and code and len(code) == 6)
ok2, msg2, _ = auth_email.send_code("student@example.com")
check("OTP resend blocked", not ok2)
check("OTP wrong code", db.verify_otp("student@example.com", "000000" if code != "000000" else "111111")[0] is False)
check("OTP right code", db.verify_otp("student@example.com", code)[0] is True)
check("OTP cannot be reused", db.verify_otp("student@example.com", code)[0] is False)
check("bad email refused", auth_email.send_code("not-an-email")[0] is False)
auth_email.send_code("lock@example.com")
for _ in range(5):
    db.verify_otp("lock@example.com", "bad000")
check("OTP locks after 5 tries", "Too many" in db.verify_otp("lock@example.com", "bad000")[1])

e = "student@example.com"
check("quota starts at limit", db.quota_left(e, "audit") == config.FREE_LIMITS["audit"])
for _ in range(config.FREE_LIMITS["audit"]):
    db.bump_usage(e, "audit")
check("quota runs out", db.quota_left(e, "audit") == 0)
ok, m = payments.submit_payment(e, "Easypaisa", config.PRO_PRICE_PKR, "TXN123456", "03001234567")
check("payment submitted", ok)
check("payment duplicate refused", payments.submit_payment(e, "Easypaisa", config.PRO_PRICE_PKR, "txn123456", "03001234567")[0] is False)
check("payment too small refused", payments.submit_payment(e, "JazzCash", 10, "TXN999999", "03001234567")[0] is False)
pid = db.list_payments(status="pending")[0]["id"]
check("approve gives Pro", payments.approve(pid)[0] and db.is_pro(e) and db.quota_left(e, "audit") is None)
check("approve twice refused", payments.approve(pid)[0] is False)

# ---------- audit history + PDF ----------
result = {"readiness_score": 72, "score_label": "Needs some fixes", "ai_summary": fb,
          "issues": [{"id": "a", "severity": "critical", "doc": "tb", "message": "Your TB certificate is old.", "fix": "Book a new test.", "link": config.LINKS["tb"]},
                     {"id": "b", "severity": "info", "doc": "tb", "message": "Check clinic. £ and emoji 🎉", "fix": "", "link": ""}],
          "checklist": [{"slug": "passport", "label": "Passport", "icon": "🛂", "required": True, "status": "ok"}],
          "created_at": "2026-10-17 10:00 UTC"}
db.save_audit(e, result)
hist = db.list_audits(e)
check("history saved", len(hist) == 1 and hist[0]["readiness_score"] == 72 and hist[0]["issues"][0]["id"] == "a")
pdf = report_pdf.build_report(e, result)
check("PDF is valid", pdf[:4] == b"%PDF" and len(pdf) > 1500)
import pdfplumber, io  # noqa: E402
with pdfplumber.open(io.BytesIO(pdf)) as p:
    txt = p.pages[0].extract_text()
check("PDF has score and issue text", "72" in txt and "TB certificate is old" in txt)

# ---------- interview ----------
check("20 questions", len(interview.QUESTIONS) == 20 and len({q["id"] for q in interview.QUESTIONS}) == 20)
q = interview.get_question(1)
short = interview.evaluate_answer(q, "Because UK good.")
longer = interview.evaluate_answer(q, "I want to study in the UK because the course quality is high and the university has strong research. " * 3)
check("interview fallback scores", short["score"] < longer["score"] and short["source"] == "basic")
check("interview empty answer", interview.evaluate_answer(q, "")["score"] == 0)

# ---------- full pipeline with a fake core audit ----------
fake_agents = types.ModuleType("agents")
fake_graph = types.ModuleType("agents.graph")
fake_graph.run_audit = lambda **kw: {"readiness_score": 88, "ai_summary": "x",
                                      "issues": [{"message": "Funds dropped below the limit on 05/08/2026.", "severity": "critical"}]}
sys.modules["agents"], sys.modules["agents.graph"] = fake_agents, fake_graph

texts = {"passport": "P<PAKKHAN<<ALI<AHMED<<<<<<<<<<<<<<<<<<<<<<<<<<<", "tb": good_tb, "ielts": ielts}
import services.pipeline as pl  # noqa: E402

pl.extract_text = lambda path: (texts.get(os.path.basename(path).split("__")[0], "core text"), "text")


class Up:
    def __init__(self, name):
        self.name = name

    def getvalue(self):
        return b"%PDF-1.4 test"


order = []
orig_ntf = tempfile.NamedTemporaryFile


def ntf(*a, **k):
    f = orig_ntf(*a, **k)
    order.append(f.name)
    return f


pl.tempfile.NamedTemporaryFile = ntf
slugs = ["passport", "cas", "bank", "tb", "ielts"]
texts_by_path = {}


def fake_extract(path):
    return texts_by_path.get(path, ("", "failed"))


pl.extract_text = fake_extract
files = {s: Up(f"{s}.pdf") for s in slugs}
orig_run = pl.run_full_audit


def run_with_map():
    return orig_run(files, date(2026, 9, 1), False, "B2", 6.0, "en")


order.clear()
res = run_with_map()
check("pipeline survives unreadable files", res["readiness_score"] <= 60 and any(i["id"] == "TB_UNREADABLE" for i in res["issues"]))
check("temp files deleted", not any(os.path.exists(p) for p in order))
order.clear()
paths_guess = {}
orig_extract_hook = pl.extract_text


def late_extract(path):
    if path not in paths_guess:
        paths_guess[path] = slugs[len(paths_guess) % len(slugs)] if False else None
    return texts_by_path.get(path, ("", "failed"))


created = []


def ntf2(*a, **k):
    f = orig_ntf(*a, **k)
    created.append(f.name)
    texts_by_path[f.name] = (list(texts.values())[0], "text")
    return f


def ntf3(*a, **k):
    f = orig_ntf(*a, **k)
    idx = len(created)
    created.append(f.name)
    slug = slugs[idx]
    texts_by_path[f.name] = ({"passport": texts["passport"], "tb": good_tb, "ielts": ielts}.get(slug, "core text"), "text")
    return f


pl.tempfile.NamedTemporaryFile = ntf3
res = orig_run(files, date(2026, 9, 1), False, "B2", 6.0, "en")
check("pipeline full run", res["readiness_score"] <= 60 and res["issues"][0]["severity"] == "critical")
check("pipeline reads passport name & extras ok", not any(i["id"].startswith(("TB_NAME", "IELTS_NAME", "TB_EXPIRED", "IELTS_LOW")) for i in res["issues"]))
check("pipeline flags missing docs", any(i["id"] == "QUALIFICATION_MISSING" for i in res["issues"]))
check("checklist statuses", {c["slug"]: c["status"] for c in res["checklist"]}["tb"] in ("ok", "check") and {c["slug"]: c["status"] for c in res["checklist"]}["reference"] == "missing")
check("temp files deleted (2)", not any(os.path.exists(p) for p in created))

# ---------- delete my data ----------
db.delete_user_data(e)
check("delete removes everything", db.list_audits(e) == [] and not db.is_pro(e) and db.list_payments(email=e) == [])

print(f"\nALL {passed} CHECKS PASSED")