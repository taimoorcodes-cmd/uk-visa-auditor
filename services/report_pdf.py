"""Makes the downloadable PDF report (English only)."""
import re
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ORANGE = colors.HexColor("#ff4d00")
SEV_COLORS = {"critical": "#dc2626", "warning": "#d97706", "info": "#2563eb"}
STATUS_TEXT = {"ok": "OK", "check": "Check", "problem": "Problem", "missing": "Not uploaded"}


def _clean(text: str) -> str:
    """Remove emoji and non-Latin letters (the standard PDF font cannot show them)."""
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r"\1 (\2)", text or "")
    return text.encode("latin-1", "ignore").decode("latin-1")


def _rich(text: str) -> str:
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escape(_clean(text)))


def build_report(email: str, result: dict) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=16 * mm, bottomMargin=16 * mm, title="UK Visa Document Check")
    ss = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=ss["Title"], textColor=ORANGE, fontSize=20, alignment=0)
    h2 = ParagraphStyle("h2", parent=ss["Heading2"], textColor=colors.HexColor("#111111"), spaceBefore=10)
    body = ParagraphStyle("body", parent=ss["BodyText"], fontSize=10, leading=14)
    small = ParagraphStyle("small", parent=body, fontSize=8, textColor=colors.HexColor("#555555"))

    score = int(result.get("readiness_score", 0))
    story = [
        Paragraph("UK Student Visa - Document Check Report", h1),
        Paragraph(f"Created: {escape(_clean(result.get('created_at', '')))}", small),
        Spacer(1, 6),
    ]

    score_tbl = Table(
        [[Paragraph(f"<font size=30><b>{score}</b></font><font size=11> / 100</font>", body),
          Paragraph(f"<b>{escape(_clean(result.get('score_label', '')))}</b><br/>"
                    "This is a readiness check, not a prediction of the visa decision.", body)]],
        colWidths=[45 * mm, 125 * mm],
    )
    score_tbl.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, ORANGE), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10), ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story += [score_tbl, Paragraph("Summary", h2)]

    for line in _clean(result.get("ai_summary", "")).split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("- "):
            story.append(Paragraph(_rich(line[2:]), body, bulletText="•"))
        else:
            story.append(Paragraph(_rich(line), body))

    story.append(Paragraph("Documents", h2))
    rows = [["Document", "Status"]]
    for c in result.get("checklist", []):
        rows.append([_clean(c["label"]) + (" (required)" if c.get("required") else ""),
                     STATUS_TEXT.get(c["status"], c["status"])])
    t = Table(rows, colWidths=[110 * mm, 60 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ORANGE), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#bbbbbb")), ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))
    story.append(t)

    story.append(Paragraph("What to check", h2))
    issues = result.get("issues", [])
    if not issues:
        story.append(Paragraph("No problems found in the documents we checked.", body))
    for i in issues:
        color = SEV_COLORS.get(i["severity"], "#444444")
        text = f"<font color='{color}'><b>{escape(i['severity'].upper())}</b></font> - {_rich(i['message'])}"
        if i.get("fix"):
            text += f"<br/><b>What to do:</b> {_rich(i['fix'])}"
        if i.get("link"):
            text += f"<br/><font size=8>Official page: {escape(i['link'])}</font>"
        story += [Paragraph(text, body), Spacer(1, 5)]

    story += [
        Spacer(1, 8),
        Paragraph("Important: This tool only checks documents. It is not immigration advice and it cannot promise "
                  "a visa. Always read the official rules on gov.uk/student-visa before you apply. "
                  "Never change or fake a document: false documents can lead to a refusal and a ban.", small),
    ]
    doc.build(story)
    return buf.getvalue()