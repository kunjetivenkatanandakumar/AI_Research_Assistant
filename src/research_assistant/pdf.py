from __future__ import annotations

from html import escape
from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from research_assistant.models import ResearchReport


def _p(text: object) -> str:
    return escape(str(text))


def build_pdf(report: ResearchReport, output_path: str) -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(str(path), pagesize=LETTER, title=report.title)
    styles = getSampleStyleSheet()
    story = [
        Paragraph(_p(report.title), styles["Title"]),
        Spacer(1, 12),
        Paragraph("Executive Summary", styles["Heading1"]),
        Paragraph(_p(report.executive_summary), styles["BodyText"]),
        Spacer(1, 12),
    ]

    for finding in report.findings:
        story.extend(
            [
                Paragraph(_p(finding.heading), styles["Heading2"]),
                Paragraph(_p(finding.summary), styles["BodyText"]),
                Spacer(1, 8),
            ]
        )

    if report.limitations:
        story.append(Paragraph("Limitations", styles["Heading1"]))
        for limitation in report.limitations:
            story.append(Paragraph(_p(f"- {limitation}"), styles["BodyText"]))

    story.append(Spacer(1, 12))
    story.append(Paragraph("Sources", styles["Heading1"]))
    for index, source in enumerate(report.sources, start=1):
        story.append(Paragraph(_p(f"{index}. {source.title} - {source.url}"), styles["BodyText"]))

    doc.build(story)
    return str(path)
