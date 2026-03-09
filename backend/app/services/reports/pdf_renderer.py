from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.flowables import Flowable

# ── Palette ──────────────────────────────────────────────────────────────────
DARK_STONE = HexColor("#1c1917")
DARK_STONE_2 = HexColor("#292524")
STONE_MUTED = HexColor("#78716c")
STONE_LIGHT = HexColor("#e7e5e4")
ACCENT = HexColor("#f45d22")
SUCCESS = HexColor("#16a34a")
DANGER = HexColor("#dc2626")
WARN = HexColor("#d97706")
WHITE = HexColor("#ffffff")

# ── Risk helpers ──────────────────────────────────────────────────────────────

def _risk_color(band: str) -> HexColor:
    if band == "HIGH":
        return DANGER
    if band == "MEDIUM":
        return WARN
    return SUCCESS


def _answer_color(answer: str) -> HexColor:
    a = (answer or "").lower()
    if a == "yes":
        return HexColor("#14532d")  # dark green
    if a == "no":
        return HexColor("#450a0a")  # dark red
    return DARK_STONE_2


# ── Score-bar flowable ────────────────────────────────────────────────────────

class ScoreBar(Flowable):
    """Horizontal filled bar representing a 0-1 score value."""

    def __init__(self, value: float, color: HexColor, width: float = 120 * mm, height: float = 5 * mm) -> None:
        super().__init__()
        self._value = max(0.0, min(1.0, float(value)))
        self._color = color
        self.width = width
        self._bar_height = height

    def wrap(self, *_):
        return self.width, self._bar_height

    def draw(self):
        # Track
        self.canv.setFillColor(STONE_LIGHT)
        self.canv.rect(0, 0, self.width, self._bar_height, fill=1, stroke=0)
        # Fill
        self.canv.setFillColor(self._color)
        self.canv.rect(0, 0, self.width * self._value, self._bar_height, fill=1, stroke=0)


# ── Page template with header/footer ─────────────────────────────────────────

def _build_page_template(doc: BaseDocTemplate) -> PageTemplate:
    W, H = A4

    header_h = 18 * mm
    footer_h = 10 * mm
    margin = 15 * mm

    frame = Frame(
        margin,
        footer_h + 6 * mm,
        W - 2 * margin,
        H - header_h - footer_h - 10 * mm,
        id="main",
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
    )

    def on_page(canvas_obj, doc_obj):
        canvas_obj.saveState()
        # ── Header band ──
        canvas_obj.setFillColor(DARK_STONE)
        canvas_obj.rect(0, H - header_h, W, header_h, fill=1, stroke=0)
        # Orange accent line at bottom of header
        canvas_obj.setFillColor(ACCENT)
        canvas_obj.rect(0, H - header_h, W, 1.5, fill=1, stroke=0)
        # Logo text
        canvas_obj.setFillColor(WHITE)
        canvas_obj.setFont("Helvetica-Bold", 13)
        canvas_obj.drawString(margin, H - header_h + 5 * mm, "Copycat")
        # Orange dot
        canvas_obj.setFillColor(ACCENT)
        canvas_obj.circle(margin + 46, H - header_h + 5 * mm + 3.5, 3, fill=1, stroke=0)
        # Right sub-title
        canvas_obj.setFillColor(STONE_MUTED)
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.drawRightString(W - margin, H - header_h + 5 * mm, "Evidence Triage Report")
        # ── Footer ──
        canvas_obj.setFillColor(STONE_LIGHT)
        canvas_obj.rect(0, 0, W, footer_h, fill=1, stroke=0)
        canvas_obj.setFillColor(STONE_MUTED)
        canvas_obj.setFont("Helvetica-Oblique", 7.5)
        canvas_obj.drawString(margin, footer_h - 4 * mm, "Not legal advice. For triage purposes only.")
        canvas_obj.setFont("Helvetica", 7.5)
        canvas_obj.drawRightString(W - margin, footer_h - 4 * mm, f"Page {doc_obj.page}")
        canvas_obj.restoreState()

    return PageTemplate(id="main_tpl", frames=[frame], onPage=on_page)


# ── Style sheet ───────────────────────────────────────────────────────────────

def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "h1": ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=18, textColor=DARK_STONE, spaceAfter=4),
        "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=12, textColor=DARK_STONE, spaceAfter=2, spaceBefore=6),
        "body": ParagraphStyle("body", fontName="Helvetica", fontSize=9, textColor=DARK_STONE, leading=13, spaceAfter=2),
        "muted": ParagraphStyle("muted", fontName="Helvetica", fontSize=8, textColor=STONE_MUTED, leading=11),
        "mono": ParagraphStyle("mono", fontName="Courier", fontSize=8, textColor=DARK_STONE, leading=11),
        "label": ParagraphStyle("label", fontName="Helvetica-Bold", fontSize=8, textColor=STONE_MUTED, spaceAfter=1),
        "disclaimer": ParagraphStyle("disclaimer", fontName="Helvetica-Oblique", fontSize=8, textColor=STONE_MUTED, leading=12),
    }


# ── Component-score label map ─────────────────────────────────────────────────

_SCORE_LABELS: dict[str, str] = {
    "M1_5gram_jaccard": "M1 — 5-gram Jaccard",
    "M2_lcs_ratio": "M2 — LCS Ratio",
    "M3_tfidf_cosine": "M3 — TF-IDF Cosine",
    "M4_named_entity_overlap": "M4 — Named Entity Overlap",
    "V1_frame_phash_alignment": "V1 — Frame pHash Alignment",
    "V2_ssim": "V2 — Structural Similarity (SSIM)",
    "V3_psnr_supporting": "V3 — PSNR (supporting)",
    "V4_transcript_similarity": "V4 — Transcript Similarity",
    "I1_phash_similarity": "I1 — Perceptual Hash",
    "I2_color_histogram": "I2 — Colour Histogram",
    "I3_ssim": "I3 — Structural Similarity (SSIM)",
    "I4_orb_feature_match": "I4 — ORB Feature Match",
}


# ── Main render function ──────────────────────────────────────────────────────

def render_report_pdf(report: dict[str, Any], output_path: str | Path) -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    S = _styles()
    W, H = A4

    doc = BaseDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=22 * mm,
        bottomMargin=16 * mm,
    )
    doc.addPageTemplates([_build_page_template(doc)])

    story: list[Any] = []

    risk_band = report.get("risk_band", "UNKNOWN")
    risk_col = _risk_color(risk_band)
    overlap_pct = report.get("headline_overlap_percentage", 0)
    now_str = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    # ── Section helper ────────────────────────────────────────────────────────
    def section(title: str) -> None:
        story.append(Spacer(1, 5 * mm))
        story.append(Paragraph(title, S["h2"]))
        story.append(HRFlowable(width="100%", thickness=0.5, color=STONE_LIGHT, spaceAfter=3))

    # ── 1. Executive summary table ────────────────────────────────────────────
    story.append(Paragraph("Evidence Triage Report", S["h1"]))
    story.append(Spacer(1, 2 * mm))

    meta_data = [
        [Paragraph("<b>Report ID</b>", S["label"]), Paragraph(str(report.get("report_id", "—")), S["mono"])],
        [Paragraph("<b>Case ID</b>", S["label"]), Paragraph(str(report.get("case_id", "—")), S["mono"])],
        [Paragraph("<b>Jurisdiction</b>", S["label"]), Paragraph(str(report.get("jurisdiction", "—")), S["body"])],
        [Paragraph("<b>Media Type</b>", S["label"]), Paragraph(str(report.get("media_type", "—")).title(), S["body"])],
        [Paragraph("<b>Generated</b>", S["label"]), Paragraph(now_str, S["body"])],
        [Paragraph("<b>Risk Band</b>", S["label"]), Paragraph(f"<b>{risk_band}</b>", ParagraphStyle("rb", fontName="Helvetica-Bold", fontSize=9, textColor=WHITE))],
    ]
    meta_table = Table(meta_data, colWidths=[40 * mm, 100 * mm], hAlign="LEFT")
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), STONE_LIGHT),
        ("BACKGROUND", (1, 0), (1, -2), WHITE),
        ("BACKGROUND", (1, -1), (1, -1), risk_col),
        ("BOX", (0, 0), (-1, -1), 0.5, STONE_LIGHT),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, STONE_LIGHT),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)

    # ── 2. Headline overlap ───────────────────────────────────────────────────
    section("Headline Overlap Score")

    headline_text = f"<b><font size='28' color='{risk_col.hexval()}'>{overlap_pct:.1f}%</font></b>"
    story.append(Paragraph(headline_text, ParagraphStyle("big", alignment=TA_CENTER, spaceAfter=4)))

    bar_width = W - 30 * mm
    story.append(ScoreBar(overlap_pct / 100, risk_col, width=bar_width, height=8 * mm))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(f"Composite similarity score — <b>{risk_band}</b> risk", S["muted"]))

    # ── 3. Component scores ───────────────────────────────────────────────────
    section("Component Scores")

    score_rows = []
    for key, val in report.get("component_scores", {}).items():
        if not isinstance(val, (int, float)):
            continue
        label = _SCORE_LABELS.get(key, key)
        pct_str = f"{val * 100:.1f}%"
        bar = ScoreBar(float(val), risk_col, width=70 * mm, height=4 * mm)
        score_rows.append([
            Paragraph(label, S["body"]),
            bar,
            Paragraph(f"<b>{pct_str}</b>", ParagraphStyle("num", fontName="Helvetica-Bold", fontSize=9, textColor=DARK_STONE, alignment=TA_RIGHT)),
        ])

    if score_rows:
        score_table = Table(score_rows, colWidths=[65 * mm, 70 * mm, 20 * mm], hAlign="LEFT")
        score_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LINEBELOW", (0, 0), (-1, -2), 0.25, STONE_LIGHT),
        ]))
        story.append(score_table)

    # ── 4. Legal reasoning flow ───────────────────────────────────────────────
    section("Legal Reasoning Flow")

    legal_flow = report.get("legal_flow", [])
    if legal_flow:
        flow_rows = [[
            Paragraph("<b>Phase</b>", S["label"]),
            Paragraph("<b>Node</b>", S["label"]),
            Paragraph("<b>Answer</b>", S["label"]),
            Paragraph("<b>Confidence</b>", S["label"]),
        ]]
        for node in legal_flow:
            ans = str(node.get("answer", "—"))
            ans_display = "✓ Yes" if ans.lower() == "yes" else ("✗ No" if ans.lower() == "no" else ans.title())
            ans_col = SUCCESS if ans.lower() == "yes" else (DANGER if ans.lower() == "no" else STONE_MUTED)
            conf = node.get("confidence", 0)
            conf_pct = f"{float(conf) * 100:.0f}%"
            flow_rows.append([
                Paragraph(str(node.get("phase", "—")), S["muted"]),
                Paragraph(str(node.get("node_id", "—")), S["body"]),
                Paragraph(f"<b>{ans_display}</b>", ParagraphStyle("ans", fontName="Helvetica-Bold", fontSize=9, textColor=ans_col)),
                Paragraph(conf_pct, S["body"]),
            ])

        flow_table = Table(flow_rows, colWidths=[28 * mm, 85 * mm, 27 * mm, 25 * mm], hAlign="LEFT")
        flow_style = [
            ("BACKGROUND", (0, 0), (-1, 0), STONE_LIGHT),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("LINEBELOW", (0, 0), (-1, -1), 0.25, STONE_LIGHT),
            ("BOX", (0, 0), (-1, -1), 0.5, STONE_LIGHT),
        ]
        # Stripe rows by answer
        for i, node in enumerate(legal_flow, start=1):
            ans = str(node.get("answer", "")).lower()
            if ans == "yes":
                flow_style.append(("BACKGROUND", (0, i), (-1, i), HexColor("#f0fdf4")))
            elif ans == "no":
                flow_style.append(("BACKGROUND", (0, i), (-1, i), HexColor("#fef2f2")))
        flow_table.setStyle(TableStyle(flow_style))
        story.append(flow_table)
    else:
        story.append(Paragraph("No legal flow data available.", S["muted"]))

    # ── 5. Evidence summary ───────────────────────────────────────────────────
    evidence = report.get("evidence", {})
    if evidence:
        section("Evidence Summary")
        if isinstance(evidence, dict):
            passages = evidence.get("matched_passages") or evidence.get("passages") or []
            extra_keys = {k: v for k, v in evidence.items() if k not in ("matched_passages", "passages")}

            if extra_keys:
                ev_rows = [[Paragraph(f"<b>{k}</b>", S["label"]), Paragraph(str(v), S["body"])] for k, v in extra_keys.items()]
                ev_table = Table(ev_rows, colWidths=[55 * mm, 110 * mm], hAlign="LEFT")
                ev_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (0, -1), STONE_LIGHT),
                    ("INNERGRID", (0, 0), (-1, -1), 0.25, STONE_LIGHT),
                    ("BOX", (0, 0), (-1, -1), 0.5, STONE_LIGHT),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ]))
                story.append(ev_table)
                story.append(Spacer(1, 3 * mm))

            if passages:
                story.append(Paragraph("<b>Matched Passages</b>", S["h2"]))
                for p in passages[:10]:
                    story.append(Preformatted(str(p), ParagraphStyle(
                        "pre", fontName="Courier", fontSize=7.5, leading=11,
                        textColor=DARK_STONE, backColor=HexColor("#f5f5f4"),
                        borderWidth=0.5, borderColor=STONE_LIGHT,
                        borderPadding=6,
                    )))
                    story.append(Spacer(1, 2 * mm))

    # ── 6. Disclaimers ────────────────────────────────────────────────────────
    disclaimers = report.get("disclaimers", [])
    if disclaimers:
        section("Disclaimers & Limitations")
        disc_text = "<br/>".join(f"• {d}" for d in disclaimers)
        disc_para = Paragraph(disc_text, S["disclaimer"])
        disc_table = Table([[disc_para]], colWidths=[W - 30 * mm], hAlign="LEFT")
        disc_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), HexColor("#fff7ed")),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LINEAFTER", (0, 0), (0, -1), 3, ACCENT),
        ]))
        story.append(disc_table)

    try:
        doc.build(story)
    except TypeError as exc:
        message = str(exc)
        if "NoneType" not in message or "iterable" not in message:
            raise

        fallback_doc = BaseDocTemplate(
            str(path),
            pagesize=A4,
            leftMargin=15 * mm,
            rightMargin=15 * mm,
            topMargin=22 * mm,
            bottomMargin=16 * mm,
        )
        fallback_doc.addPageTemplates([_build_page_template(fallback_doc)])

        fallback_story: list[Any] = []
        fallback_story.append(Paragraph("Evidence Triage Report", S["h1"]))
        fallback_story.append(Spacer(1, 3 * mm))
        fallback_story.append(Paragraph(f"Case ID: {report.get('case_id', '—')}", S["body"]))
        fallback_story.append(Paragraph(f"Media Type: {str(report.get('media_type', '—')).title()}", S["body"]))
        fallback_story.append(Paragraph(f"Risk Band: {report.get('risk_band', 'UNKNOWN')}", S["body"]))
        fallback_story.append(
            Paragraph(
                f"Headline Overlap: {float(report.get('headline_overlap_percentage', 0) or 0):.1f}%",
                S["body"],
            ),
        )

        component_scores = report.get("component_scores", {})
        if isinstance(component_scores, dict) and component_scores:
            fallback_story.append(Spacer(1, 4 * mm))
            fallback_story.append(Paragraph("Component Scores", S["h2"]))
            for key, value in component_scores.items():
                if isinstance(value, (int, float)):
                    fallback_story.append(Paragraph(f"- {key}: {value:.6f}", S["body"]))

        fallback_story.append(Spacer(1, 4 * mm))
        fallback_story.append(
            Paragraph(
                "Fallback PDF renderer was used because advanced table styling failed.",
                S["muted"],
            ),
        )
        fallback_doc.build(fallback_story)

    return str(path)