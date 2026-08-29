from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from html import escape
from io import BytesIO
from typing import Any, Iterable, List, Mapping, Sequence

from services.cache_service import compute_report_signature, report_cache
from services.telemetry import time_stage


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
    consultant_report: Mapping[str, Any] | None = None,
) -> List[str]:
    recommendations = [
        item.get("recommendation", item) if isinstance(item, Mapping) else item
        for item in (insights or {}).get("final_ai_recommendations", (insights or {}).get("recommendations", []))
    ]
    top_decisions = (consultant_report or {}).get("top_decisions", [])
    decision_lines = [f"Decision: {d.get('title', '')} | Priority {d.get('priority', '')}/100" for d in top_decisions]

    return [
        "AI Research Studio - Synthetic User Intelligence Report",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "Notice: Synthetic Research Simulation - For Internal Product Strategy & Discovery",
        "--------------------------------------------------------------------------------",
        f"Experiment: {experiment.get('experiment_name', 'Untitled')}",
        f"Product: {experiment.get('product_name', 'N/A')}",
        f"Target Audience: {experiment.get('target_audience', 'N/A')}",
        f"Research Objective: {experiment.get('research_objective', experiment.get('research_goal', 'N/A'))}",
        "Executive Summary",
        str((insights or {}).get("product_feedback", "Insights have not been extracted yet.")),
        "Launch Readiness & Strategy",
        f"Launch Readiness: {(consultant_report or {}).get('launch_readiness', 'N/A')}% | Market Fit: {(consultant_report or {}).get('market_fit', 'N/A')}/100",
        *decision_lines,
        "Generated Personas",
        *[f"- {p.get('name', 'Persona')} | {p.get('occupation', 'N/A')} | Quality: {p.get('quality_score', 'N/A')}/100 ({p.get('quality_status', 'Valid')})" for p in personas[:10]],
        "Survey Analytics",
        f"Total Responses: {len((survey_results or {}).get('responses', []))}",
        f"Product Fit Score: {(survey_results or {}).get('product_fit_score', (insights or {}).get('product_fit_score', 0))}/100",
        "Key Recommendations",
        *[f"- {r}" for r in recommendations[:6]],
    ]


def export_markdown_report(
    *,
    experiment: Mapping[str, Any],
    personas: Sequence[Mapping[str, Any]],
    survey_results: Mapping[str, Any] | None,
    interview_rows: Sequence[Mapping[str, Any]],
    insights: Mapping[str, Any] | None,
    consultant_report: Mapping[str, Any] | None = None,
) -> str:
    lines = _fallback_lines(
        experiment=experiment,
        personas=personas,
        survey_results=survey_results,
        interview_rows=interview_rows,
        insights=insights,
        consultant_report=consultant_report,
    )
    return "\n".join(lines)


def export_full_research_report_pdf(
    *,
    experiment: Mapping[str, Any],
    personas: Sequence[Mapping[str, Any]],
    survey_results: Mapping[str, Any] | None,
    interview_rows: Sequence[Mapping[str, Any]],
    insights: Mapping[str, Any] | None,
    focus_group_results: Sequence[Mapping[str, Any]] | None = None,
    consultant_report: Mapping[str, Any] | None = None,
    bypass_cache: bool = False,
) -> bytes:
    """Generates an executive PDF report with deterministic caching and evidence sections."""
    exp_sig = str(experiment.get("experiment_id", experiment.get("experiment_name", "")))
    ins_sig = str((insights or {}).get("product_fit_score", 0)) + f":{len((insights or {}).get('themes', []))}"
    report_sig = compute_report_signature(
        experiment_sig=exp_sig,
        insight_sig=ins_sig,
        has_consultant_report=bool(consultant_report),
        persona_count=len(personas),
    )

    if not bypass_cache:
        cached_pdf = report_cache.get(report_sig)
        if cached_pdf:
            return cached_pdf

    with time_stage("report_generation"):
        fallback_lines = _fallback_lines(
            experiment=experiment,
            personas=personas,
            survey_results=survey_results,
            interview_rows=interview_rows,
            insights=insights,
            consultant_report=consultant_report,
        )

        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
            from reportlab.platypus import HRFlowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                leftMargin=40,
                rightMargin=40,
                topMargin=40,
                bottomMargin=40,
            )

            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                "CoverTitle",
                parent=styles["Title"],
                fontName="Helvetica-Bold",
                fontSize=22,
                leading=26,
                textColor=colors.HexColor("#1e293b"),
                alignment=0,
            )
            sub_style = ParagraphStyle(
                "CoverSub",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=11,
                leading=15,
                textColor=colors.HexColor("#64748b"),
            )
            h1_style = ParagraphStyle(
                "Heading1_Custom",
                parent=styles["Heading1"],
                fontName="Helvetica-Bold",
                fontSize=14,
                leading=18,
                textColor=colors.HexColor("#0f172a"),
                spaceAfter=8,
            )
            body_style = ParagraphStyle(
                "Body_Custom",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=9.5,
                leading=13.5,
                textColor=colors.HexColor("#334155"),
            )
            callout_style = ParagraphStyle(
                "Callout",
                parent=body_style,
                fontName="Helvetica-Oblique",
                fontSize=9,
                textColor=colors.HexColor("#475569"),
            )

            story = []

            # Header
            story.append(Paragraph("◈ AI Research Studio — Executive Intelligence Report", title_style))
            story.append(Spacer(1, 4))
            story.append(
                Paragraph(
                    f"Product: <b>{escape(str(experiment.get('product_name', 'N/A')))}</b> | "
                    f"Experiment: <b>{escape(str(experiment.get('experiment_name', 'N/A')))}</b> | "
                    f"Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
                    sub_style,
                )
            )
            story.append(Spacer(1, 4))
            story.append(
                Paragraph(
                    "<b>Notice:</b> <i>This report compiles findings from synthetic persona generation, simulated surveys, "
                    "and memory-audited interviews. Used for rapid product discovery and strategy validation.</i>",
                    callout_style,
                )
            )
            story.append(Spacer(1, 8))
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=14))

            # Executive Summary & Strategy
            story.append(Paragraph("1. Executive Summary & Launch Strategy", h1_style))
            exec_summary = (insights or {}).get("executive_summary") or (insights or {}).get("product_feedback") or "Pending research extraction."
            story.append(Paragraph(escape(str(exec_summary)), body_style))
            story.append(Spacer(1, 8))

            if consultant_report:
                top_decs = consultant_report.get("top_decisions", [])
                if top_decs:
                    story.append(Paragraph("<b>Top Strategic Decisions (What Should We Do Next?)</b>", body_style))
                    for d in top_decs:
                        dec_text = f"• <b>{escape(d.get('title', ''))}</b> (Priority: {d.get('priority', 0)}/100, Impact: {d.get('impact', 0)}, Effort: {d.get('effort', 0)})<br/>" \
                                   f"&nbsp;&nbsp;<i>Action:</i> {escape(d.get('recommendation', ''))}"
                        story.append(Paragraph(dec_text, body_style))
                        story.append(Spacer(1, 4))

            story.append(Spacer(1, 10))

            # Persona Cohort Summary Table
            story.append(Paragraph("2. Synthetic Persona Cohort", h1_style))
            persona_rows = [["Name", "Age / Gender", "Occupation", "Tech Adoption", "Quality Score", "Status"]]
            for p in personas[:8]:
                persona_rows.append([
                    escape(str(p.get("name", "Persona"))[:18]),
                    f"{p.get('age', 'N/A')} / {str(p.get('gender', 'N/A'))[:6]}",
                    escape(str(p.get("occupation", "N/A"))[:20]),
                    escape(str(p.get("technology_usage", "Medium"))[:12]),
                    f"{p.get('quality_score', 'N/A')}/100",
                    str(p.get("quality_status", "Valid")),
                ])
            p_table = Table(persona_rows, colWidths=[100, 75, 120, 85, 75, 75])
            p_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ]))
            story.append(p_table)
            story.append(Spacer(1, 12))

            # Survey & Insights
            story.append(Paragraph("3. Survey & Clustered Insights", h1_style))
            fit_score = (survey_results or {}).get("product_fit_score", (insights or {}).get("product_fit_score", 0))
            story.append(Paragraph(f"<b>Overall Product Fit Score:</b> {fit_score}/100 | <b>Survey Responses:</b> {len((survey_results or {}).get('responses', []))}", body_style))
            story.append(Spacer(1, 6))

            recs = (insights or {}).get("final_ai_recommendations", (insights or {}).get("recommendations", []))
            if recs:
                story.append(Paragraph("<b>Prioritized Research Recommendations:</b>", body_style))
                for r in recs[:5]:
                    r_text = r.get("recommendation", r) if isinstance(r, Mapping) else str(r)
                    story.append(Paragraph(f"• {escape(r_text)}", body_style))
                    story.append(Spacer(1, 3))

            doc.build(story)
            pdf_bytes = buffer.getvalue()
            report_cache.set(report_sig, pdf_bytes)
            return pdf_bytes

        except Exception:
            pdf_bytes = _minimal_pdf(fallback_lines)
            report_cache.set(report_sig, pdf_bytes)
            return pdf_bytes
