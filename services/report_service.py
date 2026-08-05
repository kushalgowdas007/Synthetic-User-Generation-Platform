from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from html import escape
from io import BytesIO
from typing import Any, Iterable, List, Mapping, Sequence


def _as_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, Mapping):
        return [f"{key}: {item}" for key, item in value.items() if str(item).strip()]
    return [item.strip() for item in str(value).split(",") if item.strip()]


def _score(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    try:
        return float(str(value).replace("%", ""))
    except ValueError:
        return 0.0


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _minimal_pdf(lines: Sequence[str]) -> bytes:
    y = 760
    commands = ["BT", "/F1 10 Tf", "44 790 Td"]
    first = True
    for line in lines[:95]:
        safe = _pdf_escape(str(line)[:118])
        if first:
            commands.append(f"({safe}) Tj")
            first = False
        else:
            y -= 13
            commands.append(f"0 -13 Td ({safe}) Tj")
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


def _fallback_lines(
    *,
    experiment: Mapping[str, Any],
    personas: Sequence[Mapping[str, Any]],
    survey_results: Mapping[str, Any] | None,
    interview_rows: Sequence[Mapping[str, Any]],
    insights: Mapping[str, Any] | None,
) -> List[str]:
    recommendations = [
        item.get("recommendation", item) if isinstance(item, Mapping) else item
        for item in (insights or {}).get("final_ai_recommendations", (insights or {}).get("recommendations", []))
    ]
    return [
        "Synthetic User Generation Platform - Professional Research Report",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "Cover Page",
        f"Experiment: {experiment.get('experiment_name', 'N/A')}",
        f"Product: {experiment.get('product_name', 'N/A')}",
        "Executive Summary",
        str((insights or {}).get("product_feedback", "Insights have not been generated yet.")),
        "Experiment Details",
        f"Audience: {experiment.get('target_audience', 'N/A')}",
        f"Research Objective: {experiment.get('research_objective', experiment.get('research_goal', 'N/A'))}",
        "Generated Personas",
        *[f"{persona.get('name', 'Persona')} | {persona.get('occupation', 'N/A')} | Quality {persona.get('quality_score', 'N/A')}" for persona in personas[:12]],
        "Survey Results",
        f"Responses: {len((survey_results or {}).get('responses', []))}",
        f"Product Fit: {(survey_results or {}).get('product_fit_score', (insights or {}).get('product_fit_score', 0))}",
        "Interview Results",
        f"Interview Messages: {len(interview_rows)}",
        "Insights",
        f"Sentiment: {(insights or {}).get('sentiment', 'N/A')}",
        f"Recommendation Score: {(insights or {}).get('recommendation_score', 0)}",
        "Charts",
        "Dashboard charts include pie, bar, line, radar, gauge, word cloud, and trend visualizations.",
        "Product Validation",
        str((insights or {}).get("product_feedback", "Pending insight extraction.")),
        "Recommendations",
        *[f"- {recommendation}" for recommendation in recommendations[:10]],
        "Appendix",
        "Full JSON exports are available from the dashboard.",
    ]


def _paragraphs_from_items(items: Iterable[Any]) -> List[str]:
    return [str(item.get("recommendation", item)) if isinstance(item, Mapping) else str(item) for item in items]


def export_full_research_report_pdf(
    *,
    experiment: Mapping[str, Any],
    personas: Sequence[Mapping[str, Any]],
    survey_results: Mapping[str, Any] | None,
    interview_rows: Sequence[Mapping[str, Any]],
    insights: Mapping[str, Any] | None,
) -> bytes:
    fallback_lines = _fallback_lines(
        experiment=experiment,
        personas=personas,
        survey_results=survey_results,
        interview_rows=interview_rows,
        insights=insights,
    )

    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except Exception:
        return _minimal_pdf(fallback_lines)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=42, leftMargin=42, topMargin=42, bottomMargin=42)
    styles = getSampleStyleSheet()

    def para(text: Any, style_name: str = "BodyText") -> Paragraph:
        return Paragraph(escape(str(text)), styles[style_name])

    def heading(title: str) -> List[Any]:
        return [Spacer(1, 8), para(title, "Heading2"), Spacer(1, 4)]

    def table(rows: Sequence[Sequence[Any]]) -> Table:
        prepared = [[escape(str(cell)) for cell in row] for row in rows]
        output = Table(prepared, hAlign="LEFT", repeatRows=1)
        output.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d4ed8")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        return output

    survey_responses = (survey_results or {}).get("responses", [])
    recommendations = _paragraphs_from_items((insights or {}).get("final_ai_recommendations", (insights or {}).get("recommendations", [])))
    quality_values = [_score(persona.get("quality_score")) for persona in personas if persona.get("quality_score") is not None]
    average_quality = round(sum(quality_values) / len(quality_values), 1) if quality_values else 0
    product_fit = (insights or {}).get("product_fit_score", (survey_results or {}).get("product_fit_score", 0))
    recommendation_score = (insights or {}).get("recommendation_score", (insights or {}).get("would_use_product_score", 0))

    story: List[Any] = [
        para("Synthetic User Generation Platform", "Title"),
        para("Professional Research Report", "Heading2"),
        para(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"),
        Spacer(1, 18),
        table(
            [
                ["Experiment", experiment.get("experiment_name", "N/A")],
                ["Product", experiment.get("product_name", "N/A")],
                ["Industry", experiment.get("industry", "N/A")],
                ["Simulation Type", experiment.get("simulation_type", "N/A")],
            ]
        ),
        PageBreak(),
    ]

    story.extend(heading("Executive Summary"))
    story.append(para((insights or {}).get("product_feedback", "Insight extraction is pending.")))
    story.append(
        table(
            [
                ["Metric", "Value"],
                ["Total Personas", len(personas)],
                ["Survey Responses", len(survey_responses)],
                ["Interview Messages", len(interview_rows)],
                ["Product Fit Score", product_fit],
                ["Recommendation Score", recommendation_score],
                ["Persona Quality Score", average_quality],
            ]
        )
    )

    story.extend(heading("Experiment Details"))
    for key in ["description", "target_audience", "research_objective", "age", "gender", "profession", "location", "interests"]:
        story.append(para(f"{key.replace('_', ' ').title()}: {experiment.get(key, 'N/A')}"))

    story.extend(heading("Generated Personas"))
    persona_rows = [["Name", "Age", "Occupation", "Education", "Technology", "Quality"]]
    for persona in list(personas)[:18]:
        persona_rows.append(
            [
                persona.get("name", "Persona"),
                persona.get("age", "N/A"),
                persona.get("occupation", "N/A"),
                persona.get("education", "N/A"),
                persona.get("technology_usage", "N/A"),
                persona.get("quality_score", "N/A"),
            ]
        )
    story.append(table(persona_rows))

    story.extend(heading("Survey Results"))
    if survey_results:
        story.append(para(f"Template: {survey_results.get('template_name', 'N/A')}"))
        story.append(para(f"Product Fit Score: {survey_results.get('product_fit_score', 0)}"))
        category_rows = [["Category", "Average Score"]]
        for category, score in (survey_results.get("analytics", {}).get("average_by_category", {}) or {}).items():
            category_rows.append([category, score])
        if len(category_rows) > 1:
            story.append(table(category_rows))
    else:
        story.append(para("No survey results captured."))

    story.extend(heading("Interview Results"))
    story.append(para(f"Interview messages captured: {len(interview_rows)}"))
    for row in list(interview_rows)[:10]:
        story.append(para(f"{row.get('persona_name', row.get('role', 'Persona'))}: {row.get('message', '')}"))

    story.extend(heading("Insights"))
    if insights:
        story.append(para(f"Sentiment: {insights.get('sentiment', 'N/A')}"))
        story.append(para(f"Recommendation Score: {recommendation_score}"))
        theme_rows = [["Theme", "Count", "Confidence"]]
        for item in insights.get("themes", [])[:10]:
            if isinstance(item, Mapping):
                theme_rows.append([item.get("theme", ""), item.get("count", 0), item.get("confidence_score", 0)])
        if len(theme_rows) > 1:
            story.append(table(theme_rows))
    else:
        story.append(para("No insights generated."))

    story.extend(heading("Charts"))
    story.append(
        para(
            "Interactive dashboard charts include pie charts, bar charts, line charts, radar charts, gauge charts, "
            "word cloud visualization, trend charts, and filtered data tables."
        )
    )

    story.extend(heading("Product Validation"))
    story.append(para((insights or {}).get("product_feedback", "Product validation will be available after survey and insight extraction.")))

    story.extend(heading("Recommendations"))
    if recommendations:
        for item in recommendations:
            story.append(para(f"- {item}"))
    else:
        story.append(para("No AI recommendations available yet."))

    story.extend(heading("Appendix"))
    occupation_counter = Counter(str(persona.get("occupation", "N/A")) for persona in personas)
    story.append(para("Occupation distribution: " + json.dumps(dict(occupation_counter), ensure_ascii=False)))
    story.append(para("Full structured JSON exports are available from the Dashboard export tab."))

    try:
        doc.build(story)
        return buffer.getvalue()
    except Exception:
        return _minimal_pdf(fallback_lines)
