# app.py  -  UK Visa Auditor (V2)
import html
import os
import sys
from datetime import date

import streamlit as st

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from services import (assistant, auth_email, config, db, interview, narrator,
                      payments, pipeline, report_pdf, screenshot_help)
from ui_style import CSS_TEMPLATE

st.set_page_config(page_title="UK Visa Auditor", page_icon="🇬🇧", layout="wide",
                   initial_sidebar_state="collapsed")


@st.cache_resource
def _setup():
    db.init_db()
    return True


_setup()
st.markdown(CSS_TEMPLATE.replace("__VIDEO__", config.VIDEO_URL), unsafe_allow_html=True)

STATUS_ICON = {"ok": "✅", "check": "⚠️", "problem": "❌", "missing": "⬜"}
STATUS_TEXT = {"ok": "Looks fine", "check": "Please check", "problem": "Problem found", "missing": "Not uploaded"}
LANG_OPTIONS = {"Easy English": "en", "اردو (Urdu)": "ur"}


# ---------------- small helpers ----------------
def cube(size: str) -> str:
    faces = "".join(f'<div class="face f{i}">{e}</div>'
                    for i, e in enumerate(["🛂", "🎓", "🏦", "🩺", "📝", "🇬🇧"], start=1))
    return f'<div class="cube-wrap cube-{size}"><div class="cube">{faces}</div></div>'


def topbar(email: str = "") -> str:
    right = ""
    if email:
        right += '<span class="chip pro">PRO</span>' if db.is_pro(email) else '<span class="chip hot">FREE</span>'
        right += f'<span class="chip">{html.escape(email)}</span>'
    else:
        right = '<span class="chip hot">FREE TOOL</span>'
    return f'<div class="topbar"><div class="logo">UK VISA AUDITOR</div><div>{right}</div></div>'


def sec(title: str) -> None:
    st.markdown(f'<div class="sec">{html.escape(title)}</div>', unsafe_allow_html=True)


def quota_text(email: str, feature: str) -> str:
    left = db.quota_left(email, feature)
    return "Pro: unlimited" if left is None else f"Free uses left this month: {left}"


def show_issue(i: dict) -> None:
    text = i["message"]
    if i.get("fix"):
        text += f"\n\n**What to do:** {i['fix']}"
    if i.get("link"):
        text += f"\n\n[Official gov.uk page]({i['link']})"
    {"critical": st.error, "warning": st.warning}.get(i["severity"], st.info)(text)


def show_result(result: dict) -> None:
    score = max(0, min(100, int(result["readiness_score"])))
    color = "#22c55e" if score >= 80 else "#ff4d00" if score >= 50 else "#ef4444"
    r1, r2 = st.columns([1, 2])
    with r1:
        st.markdown(
            f'<div class="ring" style="background:conic-gradient({color} {score}%, #1f1f1f 0);'
            f'box-shadow:0 30px 50px -20px {color};"><div class="ring-in">{score}</div></div>'
            f'<div class="ring-label">{html.escape(result.get("score_label", "Readiness score"))}</div>',
            unsafe_allow_html=True)
    with r2:
        st.markdown("#### 🤖 Summary")
        st.info(result["ai_summary"])

    st.markdown("#### 📋 Your documents")
    for c in result.get("checklist", []):
        tag = "required" if c["required"] else "optional"
        st.markdown(
            f"<div class='status-line'>{STATUS_ICON[c['status']]} {c['icon']} <b>{html.escape(c['label'])}</b> "
            f"<span style='color:#8a8a8a'>({tag})</span> — {STATUS_TEXT[c['status']]}</div>",
            unsafe_allow_html=True)

    st.markdown("#### ⚠️ Things to check")
    shown = [i for i in result["issues"]]
    if not shown:
        st.success("✅ No problems found in the documents we checked.")
    for i in shown:
        show_issue(i)

    if result.get("fields_read"):
        with st.expander("What we read from your extra documents"):
            for slug, fields in result["fields_read"].items():
                if fields:
                    st.markdown(f"**{pipeline.DOCS[slug][0]}**")
                    st.json(fields)
    st.caption("A high score does not guarantee approval. This is a readiness check, not a prediction. "
               "It is not immigration advice.")


# ---------------- state ----------------
defaults = {
    "logged_in": False, "email": "", "otp_email": "", "dev_code": None,
    "result": None, "report_bytes": None, "reset_n": 0,
    "messages": [{"role": "assistant",
                  "content": "Hi! Ask me where to get any document, and I'll give you the official gov.uk link."}],
    "iv_feedback": None,
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

# =====================================================================
# LOGIN (email + 6-digit code)
# =====================================================================
if not st.session_state.logged_in:
    st.markdown(topbar(), unsafe_allow_html=True)
    st.markdown(cube("lg"), unsafe_allow_html=True)
    st.markdown(
        '<h1 class="hero-title">Check your UK Student Visa<br>documents <span class="hl">before you submit</span></h1>'
        '<p class="hero-sub">A free document checker for students. Your uploaded files are deleted after each check.</p>',
        unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.6, 1])
    with col:
        with st.container(key="login_card"):
            if not st.session_state.otp_email:
                email = st.text_input("Email address", placeholder="name@email.com")
                if st.button("Send my code", use_container_width=True, type="primary"):
                    ok, msg, dev = auth_email.send_code(email)
                    if ok:
                        st.session_state.otp_email = email.strip().lower()
                        st.session_state.dev_code = dev
                        st.rerun()
                    else:
                        st.error(msg)
                st.caption("We will email you a 6-digit code. No password needed.")
            else:
                st.write(f"We sent a 6-digit code to **{html.escape(st.session_state.otp_email)}**.")
                if st.session_state.dev_code:
                    st.warning(f"Test mode. Your code is: **{st.session_state.dev_code}**")
                code = st.text_input("6-digit code", max_chars=6, placeholder="123456")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Verify", use_container_width=True, type="primary"):
                        ok, msg = db.verify_otp(st.session_state.otp_email, code)
                        if ok:
                            st.session_state.logged_in = True
                            st.session_state.email = st.session_state.otp_email
                            st.session_state.otp_email = ""
                            st.session_state.dev_code = None
                            st.rerun()
                        else:
                            st.error(msg)
                with c2:
                    if st.button("Use another email", use_container_width=True):
                        st.session_state.otp_email = ""
                        st.session_state.dev_code = None
                        st.rerun()
    st.stop()

# =====================================================================
# DASHBOARD
# =====================================================================
email = st.session_state.email
is_admin = email in config.ADMIN_EMAILS

st.markdown(topbar(email), unsafe_allow_html=True)
h1, h2 = st.columns([5, 1])
with h1:
    st.markdown(
        '<div style="display:flex; align-items:center;">' + cube("sm") +
        '<div><div style="font-size:1.6rem; font-weight:800;">Document Audit Dashboard</div>'
        '<div class="disclaimer">Information and document-checking tool only. Not immigration advice. '
        f'Always confirm on <a href="{config.LINKS["student_visa"]}" target="_blank">gov.uk</a>.</div></div></div>',
        unsafe_allow_html=True)
with h2:
    if st.button("Logout", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

st.write("")
col_main, col_chat = st.columns([2, 1], gap="large")

with col_main:
    tab_names = ["📄 Audit", "🎤 Interview Coach", "📸 Screenshot Help", "🕘 History", "⭐ Upgrade"]
    if is_admin:
        tab_names.append("🛠 Admin")
    tabs = st.tabs(tab_names)

    # ---------------- AUDIT ----------------
    with tabs[0]:
        sec("Application details")
        with st.container(key="details_panel"):
            d1, d2 = st.columns(2)
            with d1:
                app_date = st.date_input("Planned application date", value=date.today())
            with d2:
                is_london = st.selectbox("Course location", ["Outside London", "Inside London"]) == "Inside London"
            d3, d4 = st.columns(2)
            with d3:
                level_label = st.selectbox("English level your course needs", [
                    "B2 - degree level or above (5.5 in each part)",
                    "B1 - below degree level (4.0 in each part)",
                    "My university needs a different score"])
            with d4:
                min_band = st.number_input("Score needed in each part", 4.0, 9.0, 6.0, 0.5,
                                           disabled=not level_label.startswith("My"))
            language = LANG_OPTIONS[st.radio("Summary language", list(LANG_OPTIONS), horizontal=True)]
        level = "B2" if level_label.startswith("B2") else "B1" if level_label.startswith("B1") else "custom"

        sec("Upload your documents")
        st.caption("Passport, CAS and Bank Statement are required. The others are checked if you upload them.")
        uploaded = {}
        grid = st.columns(3)
        for i, (slug, (label, icon, required, types)) in enumerate(pipeline.DOCS.items()):
            with grid[i % 3]:
                with st.container(key=f"card_{slug}"):
                    badge = "" if required else '<span class="badge">OPTIONAL</span>'
                    st.markdown(f'<div class="card-icon">{icon}</div>'
                                f'<div class="card-title">{html.escape(label)}{badge}</div>', unsafe_allow_html=True)
                    uploaded[slug] = st.file_uploader(label, type=types, key=f"up_{slug}_{st.session_state.reset_n}",
                                                      label_visibility="collapsed")
                st.write("")

        st.caption(quota_text(email, "audit") + " (full audits)")
        if st.button("🚀 Run Audit", type="primary", use_container_width=True):
            left = db.quota_left(email, "audit")
            if left == 0:
                st.error("You used all free audits this month. Open the Upgrade tab for unlimited audits.")
            elif not all(uploaded.get(k) for k in pipeline.CORE):
                st.error("Please upload at least Passport, CAS and Bank Statement.")
            else:
                try:
                    with st.spinner("🔍 Checking your documents..."):
                        result = pipeline.run_full_audit(
                            files=uploaded, application_date=app_date, is_london=is_london,
                            english_level=level, min_band=float(min_band), language=language)
                    st.session_state.result = result
                    try:
                        st.session_state.report_bytes = report_pdf.build_report(email, result)
                    except Exception:
                        st.session_state.report_bytes = None
                    db.save_audit(email, result)
                    db.bump_usage(email, "audit")
                except Exception as e:
                    st.session_state.result = None
                    st.error(f"Something went wrong while checking your documents: {e}")

        result = st.session_state.result
        if result:
            sec("Audit results")
            with st.container(key="result_panel"):
                show_result(result)
                if st.session_state.report_bytes:
                    st.download_button("⬇️ Download PDF report", data=st.session_state.report_bytes,
                                       file_name="visa_document_check.pdf", mime="application/pdf")
                with st.expander("Was this helpful?"):
                    rating = st.radio("Your rating", [5, 4, 3, 2, 1], horizontal=True, key="fb_rating")
                    comment = st.text_input("Anything we should fix? (optional)", key="fb_comment")
                    if st.button("Send feedback"):
                        db.add_feedback(email, rating, comment)
                        st.success("Thank you!")

    # ---------------- INTERVIEW COACH ----------------
    with tabs[1]:
        sec("Interview coach - 20 practice questions")
        with st.container(key="iv_panel"):
            st.caption("Practice speaking your answer, then type it here for feedback. " + quota_text(email, "interview"))
            cats = ["All"] + interview.CATEGORIES
            cat = st.selectbox("Topic", cats)
            pool = [q for q in interview.QUESTIONS if cat == "All" or q["cat"] == cat]
            labels = {f"{q['id']}. {q['q']}": q for q in pool}
            chosen = labels[st.selectbox("Question", list(labels))]
            st.markdown(f"<div class='tip-box'><b>What to include:</b> {html.escape(chosen['tip'])}</div>",
                        unsafe_allow_html=True)
            answer = st.text_area("Your answer (be honest and use your real facts)", height=160, key=f"ans_{chosen['id']}")
            iv_lang = LANG_OPTIONS[st.radio("Feedback language", list(LANG_OPTIONS), horizontal=True, key="iv_lang")]
            if st.button("Get feedback", type="primary"):
                if db.quota_left(email, "interview") == 0:
                    st.error("You used all free interview feedback this month. Open the Upgrade tab.")
                elif len(answer.strip()) < 5:
                    st.warning("Please write your answer first.")
                else:
                    with st.spinner("Reading your answer..."):
                        st.session_state.iv_feedback = (chosen["id"], interview.evaluate_answer(chosen, answer, iv_lang))
                    db.bump_usage(email, "interview")
            fb = st.session_state.iv_feedback
            if fb and fb[0] == chosen["id"]:
                data = fb[1]
                st.metric("Your score", f"{data['score']} / 10")
                for g in data["good"]:
                    st.success(g)
                for imp in data["improve"]:
                    st.warning(imp)
                if data["tip"]:
                    st.info(data["tip"])
                if data["source"] == "basic":
                    st.caption("Basic feedback (AI was not available).")

    # ---------------- SCREENSHOT HELP ----------------
    with tabs[2]:
        sec("Screenshot help")
        with st.container(key="shot_panel"):
            st.caption("Upload a screenshot of a form question you do not understand. "
                       "Hide your name and passport number first. " + quota_text(email, "screenshot"))
            shot = st.file_uploader("Screenshot", type=["png", "jpg", "jpeg"], key=f"shot_{st.session_state.reset_n}")
            q = st.text_input("Which part is confusing? (optional)")
            s_lang = LANG_OPTIONS[st.radio("Answer language", list(LANG_OPTIONS), horizontal=True, key="s_lang")]
            if shot:
                st.image(shot, width=380)
            if st.button("Explain it to me", type="primary"):
                if not shot:
                    st.warning("Please upload a screenshot.")
                elif db.quota_left(email, "screenshot") == 0:
                    st.error("You used all free screenshot help this month. Open the Upgrade tab.")
                else:
                    with st.spinner("Looking at your screenshot..."):
                        ok, text = screenshot_help.explain_screenshot(shot.getvalue(), q, s_lang)
                    if ok:
                        db.bump_usage(email, "screenshot")
                        st.success("Here is the help:")
                        st.write(text)
                    else:
                        st.error(text)

    # ---------------- HISTORY ----------------
    with tabs[3]:
        sec("Your past audits")
        with st.container(key="hist_panel"):
            rows = db.list_audits(email)
            if not rows:
                st.info("No saved audits yet. Run your first audit in the Audit tab.")
            for r in rows:
                with st.expander(f"{r['created_at']}  -  score {r['readiness_score']}/100"):
                    st.info(r["ai_summary"])
                    for i in r["issues"]:
                        show_issue(i)
            st.divider()
            st.markdown("**Privacy:** we save only your results, never your files.")
            sure = st.checkbox("I want to delete my account and all my saved data")
            if st.button("Delete everything", disabled=not sure):
                db.delete_user_data(email)
                for k in list(st.session_state.keys()):
                    del st.session_state[k]
                st.rerun()

    # ---------------- UPGRADE ----------------
    with tabs[4]:
        sec("Pro plan")
        with st.container(key="pay_panel"):
            until = db.pro_until(email)
            if until:
                st.success(f"You are Pro until {until.strftime('%d %b %Y')}.")
            info = payments.payment_instructions()
            st.markdown(
                f"**Free plan:** {config.FREE_LIMITS['audit']} audits, {config.FREE_LIMITS['screenshot']} screenshot helps "
                f"and {config.FREE_LIMITS['interview']} interview feedbacks every month.\n\n"
                f"**Pro plan:** unlimited use for {info['days']} days - **Rs {info['price']}**.")
            st.markdown("**How to pay**")
            shown = False
            for method, number in info["numbers"].items():
                if number:
                    shown = True
                    st.write(f"{method}: **{number}**" + (f" ({info['account_name']})" if info["account_name"] else ""))
            if not shown:
                st.warning("Payment numbers are not set yet. The owner must add them to the .env file.")
            st.caption("After you pay, send the transaction ID below. We check it by hand, then turn on Pro.")
            with st.form("pay_form", clear_on_submit=True):
                method = st.selectbox("Payment method", payments.METHODS)
                amount = st.number_input("Amount paid (Rs)", min_value=0, value=info["price"], step=100)
                txn = st.text_input("Transaction ID")
                sender = st.text_input("Phone number you paid from")
                if st.form_submit_button("Send payment details"):
                    ok, msg = payments.submit_payment(email, method, int(amount), txn, sender)
                    (st.success if ok else st.error)(msg)
            mine = db.list_payments(email=email)
            if mine:
                st.markdown("**Your payments**")
                for p in mine:
                    st.write(f"- {p['created_at'][:10]} - {p['method']} - Rs {p['amount']} - **{p['status']}**")

    # ---------------- ADMIN ----------------
    if is_admin:
        with tabs[5]:
            sec("Payments waiting")
            with st.container(key="admin_panel"):
                waiting = db.list_payments(status="pending")
                if not waiting:
                    st.info("No payments waiting.")
                for p in waiting:
                    a, b, c = st.columns([4, 1, 1])
                    a.write(f"**{p['email']}** - {p['method']} - Rs {p['amount']} - ID `{p['txn_ref']}` - from {p['sender']}")
                    if b.button("Approve", key=f"ap_{p['id']}"):
                        st.success(payments.approve(p["id"])[1])
                        st.rerun()
                    if c.button("Reject", key=f"rj_{p['id']}"):
                        payments.reject(p["id"])
                        st.rerun()

# ---------------- CHAT ----------------
with col_chat:
    sec("AI assistant")
    with st.container(key="chat_panel", height=450):
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
    prompt = st.chat_input("Ask about documents...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.messages.append({"role": "assistant", "content": assistant.answer(st.session_state.messages)})
        st.rerun()