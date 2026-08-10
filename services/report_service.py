from __future__ import annotations

import json
from html import escape
from io import BytesIO
from typing import Any, Mapping, Sequence


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _minimal_pdf(lines: Sequence[str]) -> bytes:
    y = 760
    commands = ["BT", "/F1 11 Tf", "50 790 Td"]
    first = True
    for line in lines[:70]:
        safe = _pdf_escape(str(line)[:110])
        if first:
            commands.append(f"({safe}) Tj")
            first = False
        else:
            y -= 14
            commands.append(f"0 -14 Td ({safe}) Tj")
        if y < 60:
            break
    commands.append("ET")
    stream = "\n".join(commands)
    objects = [
        "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj",
        "2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj",
        "3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj",
        "4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj",
        f"5 0 obj << /Length {len(stream.encode('utf-8'))} >> stream\n{stream}\nendstream endobj",
    ]
    pdf = ["%PDF-1.4"]
    offsets = [0]
    for obj in objects:
        offsets.append(sum(len(part.encode("utf-8")) + 1 for part in pdf))
        pdf.append(obj)
    xref_start = sum(len(part.encode("utf-8")) + 1 for part in pdf)
    pdf.append("xref")
    pdf.append(f"0 {len(objects) + 1}")
    pdf.append("0000000000 65535 f ")
    for offset in offsets[1:]:
        pdf.append(f"{offset:010d} 00000 n ")
    pdf.append("trailer << /Size 6 /Root 1 0 R >>")
    pdf.append("startxref")
    pdf.append(str(xref_start))
    pdf.append("%%EOF")
    return ("\n".join(pdf) + "\n").encode("utf-8")


def export_full_research_report_pdf(
    *,
    experiment: Mapping[str, Any],
    personas: Sequence[Mapping[str, Any]],
    survey_results: Mapping[str, Any] | None,
    interview_rows: Sequence[Mapping[str, Any]],
    insights: Mapping[str, Any] | None,
    focus_group_results: Sequence[Mapping[str, Any]] | None = None,
    consultant_report: Mapping[str, Any] | None = None,
) -> bytes:
    fallback_lines = [
        "Synthetic User Generation Platform - Research Report",
        f"Experiment: {experiment.get('experiment_name', 'N/A')}",
        f"Product: {experiment.get('product_name', 'N/A')}",
        f"Personas: {len(personas)}",
        f"Survey responses: {len((survey_results or {}).get('responses', []))}",
        f"Interview messages: {len(interview_rows)}",
        f"Sentiment: {(insights or {}).get('sentiment', 'N/A')}",
        f"Would use product score: {(insights or {}).get('would_use_product_score', 0)}",
        "Recommendations:",
        *[f"- {item}" for item in (insights or {}).get("recommendations", [])],
    ]

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    except Exception:
        return _minimal_pdf(fallback_lines)

    def para(text: Any, style_name: str = "BodyText") -> Paragraph:
        return Paragraph(escape(str(text)), styles[style_name])

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=42, leftMargin=42, topMargin=42, bottomMargin=42)
    styles = getSampleStyleSheet()
    story = [para("Synthetic User Generation Platform - Research Report", "Title"), Spacer(1, 12)]

    story.append(para("Experiment", "Heading2"))
    for key in ["experiment_name", "product_name", "industry", "simulation_type", "target_audience", "research_objective"]:
        story.append(para(f"{key.replace('_', ' ').title()}: {experiment.get(key, 'N/A')}"))
    story.append(Spacer(1, 10))

    story.append(para("Personas", "Heading2"))
    for persona in list(personas)[:10]:
        story.append(
            para(
                f"{persona.get('name', 'Persona')} | Age {persona.get('age', 'N/A')} | "
                f"{persona.get('gender', 'N/A')} | {persona.get('occupation', 'N/A')} | "
                f"Quality {persona.get('quality_score', 'N/A')}"
            )
        )
    story.append(Spacer(1, 10))

    story.append(para("Survey", "Heading2"))
    if survey_results:
        story.append(para(f"Product Fit Score: {survey_results.get('product_fit_score', 0)}"))
        story.append(para(f"Responses: {len(survey_results.get('responses', []))}"))
    else:
        story.append(para("No survey results captured."))
    story.append(Spacer(1, 10))

    story.append(para("Interview", "Heading2"))
    story.append(para(f"Interview messages: {len(interview_rows)}"))
    for row in list(interview_rows)[:8]:
        story.append(para(f"{row.get('persona_name', row.get('role', ''))}: {row.get('message', '')}"))
    story.append(Spacer(1, 10))

    story.append(para("Insights", "Heading2"))
    if insights:
        story.append(para(f"Sentiment: {insights.get('sentiment', 'N/A')}"))
        story.append(para(f"Would Use Product Score: {insights.get('would_use_product_score', 0)}"))
        story.append(para(f"Themes: {json.dumps(insights.get('themes', []))}"))
        story.append(para("Recommendations:", "Heading3"))
        for item in insights.get("recommendations", []):
            story.append(para(f"- {item}"))
        story.append(para("Chart Summary:", "Heading3"))
        story.append(para("Charts represented in the dashboard: persona distribution, age distribution, occupation, sentiment, product fit, theme frequency, response count, and recommendation score."))
    else:
        story.append(para("No insights generated."))

    story.append(Spacer(1, 10))
    story.append(para("Focus Group & Executive Recommendation", "Heading2"))
    story.append(para(f"Focus group turns: {len(focus_group_results or [])}"))
    if consultant_report:
        story.append(para(f"Launch readiness: {consultant_report.get('launch_readiness', 'N/A')}%"))
        story.append(para(f"Market fit: {consultant_report.get('market_fit', 'N/A')}/100"))
        story.append(para(f"Recommendation rationale: {consultant_report.get('why', '')}"))

    try:
        doc.build(story)
        return buffer.getvalue()
    except Exception:
        return _minimal_pdf(fallback_lines)
