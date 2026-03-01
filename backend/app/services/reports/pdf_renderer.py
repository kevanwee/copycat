from __future__ import annotations

from pathlib import Path
from typing import Any

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas



def render_report_pdf(report: dict[str, Any], output_path: str | Path) -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(path), pagesize=A4)
    width, height = A4

    x = 15 * mm
    y = height - 20 * mm

    def line(text: str, step: float = 6.5 * mm) -> None:
        nonlocal y
        c.drawString(x, y, text)
        y -= step

    c.setFont("Helvetica-Bold", 14)
    line("Copycat Evidence Report", step=9 * mm)

    c.setFont("Helvetica", 10)
    line(f"Report ID: {report.get('report_id', '-')}")
    line(f"Case ID: {report.get('case_id', '-')}")
    line(f"Jurisdiction: {report.get('jurisdiction', '-')}")
    line(f"Media Type: {report.get('media_type', '-')}")
    line(f"Headline Overlap: {report.get('headline_overlap_percentage', 0)}%")
    line(f"Risk Band: {report.get('risk_band', '-')}")

    line("", step=4 * mm)
    c.setFont("Helvetica-Bold", 11)
    line("Component Scores")
    c.setFont("Helvetica", 10)
    for key, value in report.get("component_scores", {}).items():
        line(f"- {key}: {value}")

    line("", step=4 * mm)
    c.setFont("Helvetica-Bold", 11)
    line("Legal Flow")
    c.setFont("Helvetica", 10)
    for node in report.get("legal_flow", [])[:20]:
        line(f"- [{node.get('phase')}] {node.get('node_id')}: {node.get('answer')} (conf {node.get('confidence')})")
        if y < 20 * mm:
            c.showPage()
            c.setFont("Helvetica", 10)
            y = height - 20 * mm

    line("", step=4 * mm)
    c.setFont("Helvetica-Bold", 11)
    line("Disclaimers")
    c.setFont("Helvetica", 10)
    for d in report.get("disclaimers", []):
        line(f"- {d}")

    c.showPage()
    c.save()
    return str(path)