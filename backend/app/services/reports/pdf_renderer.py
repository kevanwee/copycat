"""Escaped, paginated report. Never drop evidence or reasoning in a fallback."""

from pathlib import Path
from xml.sax.saxutils import escape
import json
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import reportlab

_FONT_DIR = Path(reportlab.__file__).parent / "fonts"
pdfmetrics.registerFont(TTFont("CopycatSans", str(_FONT_DIR / "Vera.ttf")))
pdfmetrics.registerFont(TTFont("CopycatBold", str(_FONT_DIR / "VeraBd.ttf")))


def portable_text(text):
    widths = pdfmetrics.getFont("CopycatSans").face.charWidths
    return "".join(
        c if ord(c) in widths or c == "\n" else f"[U+{ord(c):04X}]" for c in str(text)
    )


def render_report_pdf(report: dict, path: Path) -> str:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    for style in styles.byName.values():
        style.fontName = (
            "CopycatBold"
            if style.name.startswith("Heading") or style.name == "Title"
            else "CopycatSans"
        )
    styles["BodyText"].fontSize = 9
    styles["BodyText"].leading = 13
    story = []

    def add(text, style="BodyText"):
        story.append(
            Paragraph(escape(portable_text(text)).replace("\n", "<br/>"), styles[style])
        )
        story.append(Spacer(1, 5))

    add("Copycat | Singapore copyright triage", "Title")
    add(report["intake"].get("title", "Untitled comparison"), "Heading1")
    add(report["assessment"]["title"], "Heading2")
    add(report["assessment"]["summary"])
    add(f"Technical similarity index: {report['headline_overlap_percentage']:.2f}/100")
    add(f"Report fingerprint: {report['report_id']}")
    add(
        f"Generated: {report['generated_at']} | Legal review: {report['legal_reviewed_on']}"
    )
    for note in report["assessment"]["scope_notes"]:
        add(note)
    add("Files and recorded context", "Heading2")
    for a in report["artifacts"]:
        add(
            f"{a['role'].title()}: {a['filename']} ({a['size_bytes']} bytes); SHA-256 {a['sha256']}"
        )
    add(
        f"Category: {report['intake'].get('work_category', 'unknown')}; route: {report['intake'].get('claim_route', 'unknown')}; conduct date: {report['intake'].get('conduct_date') or 'unknown'}"
    )
    add("Legal requirements and evidence gaps", "Heading2")
    for node in report["legal_flow"]:
        add(f"{node['prompt']} — {node['answer'].upper()}", "Heading3")
        add(node["explanation"])
        add("Recorded basis: " + (node["basis"] or "Not supplied"))
        add("Evidence to review: " + node["evidence_needed"])
        for ref in node["legal_refs"]:
            cite = report["citations"][ref]
            add(cite["title"] + " — " + cite["url"])
    add("Fair-use factors", "Heading2")
    for key, val in report["intake"].get("fair_use_factors", {}).items():
        add(f"{key.replace('_', ' ').title()}: {val or 'Not supplied'}")
    add("Technical evidence", "Heading2")
    for key, val in report["component_scores"].items():
        add(f"{key}: {val}")
    for key, val in report["evidence"].items():
        add(key.replace("_", " ").title(), "Heading3")
        if isinstance(val, list):
            for item in val:
                add(json.dumps(item, ensure_ascii=False))
        else:
            add(json.dumps(val, ensure_ascii=False))
    add("Method and limitations", "Heading2")
    add(
        "Characters outside the embedded font are preserved as [U+XXXX] code points. The JSON export preserves the original Unicode text."
    )
    add(
        f"Scoring {report['scoring_version']}; rulepack {report['rule_pack_id']} {report['rule_pack_version']}; SHA-256 {report['rule_pack_sha256']}"
    )
    add(json.dumps(report["dependencies"], sort_keys=True))
    add(report["source_status"])
    for note in report["disclaimers"]:
        add(note)

    def footer(canvas, doc):
        canvas.setFillColor(colors.HexColor("#52665f"))
        canvas.setFont("Helvetica", 8)
        canvas.drawString(36, 20, "Copycat · Evidence triage · " + str(doc.page))

    SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    ).build(story, onFirstPage=footer, onLaterPages=footer)
    return str(path)
