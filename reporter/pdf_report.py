import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY


def generate_report(session_log, output_path, case_name="Forensic Investigation", examiner="Investigator"):
    """
    Generates a professional PDF forensic report from the Q&A session log.

    Args:
        session_log : list of dicts returned by qa_engine.ask()
        output_path : full path where the PDF will be saved
        case_name   : name of the case (shown on cover page)
        examiner    : examiner name (shown on cover page)
    """

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
    )

    styles = getSampleStyleSheet()

    # ── Custom styles ──────────────────────────────────────────────────────────
    style_title = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=24,
        textColor=colors.HexColor("#1a1a2e"),
        spaceAfter=6,
        alignment=TA_CENTER,
    )
    style_subtitle = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=12,
        textColor=colors.HexColor("#555577"),
        spaceAfter=4,
        alignment=TA_CENTER,
    )
    style_h1 = ParagraphStyle(
        "H1",
        parent=styles["Heading1"],
        fontSize=14,
        textColor=colors.HexColor("#1a1a2e"),
        spaceBefore=16,
        spaceAfter=6,
        borderPad=4,
    )
    style_h2 = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontSize=11,
        textColor=colors.HexColor("#313244"),
        spaceBefore=10,
        spaceAfter=4,
    )
    style_body = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=10,
        leading=15,
        textColor=colors.HexColor("#222222"),
        alignment=TA_JUSTIFY,
    )
    style_question = ParagraphStyle(
        "Question",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#1a56a0"),
        fontName="Helvetica-Bold",
        spaceBefore=8,
    )
    style_answer = ParagraphStyle(
        "Answer",
        parent=styles["Normal"],
        fontSize=10,
        leading=15,
        textColor=colors.HexColor("#222222"),
        leftIndent=12,
        alignment=TA_JUSTIFY,
    )
    style_ref = ParagraphStyle(
        "Reference",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#2d6a2d"),
        leftIndent=12,
        fontName="Courier",
    )
    style_meta = ParagraphStyle(
        "Meta",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#555555"),
        fontName="Courier",
        leftIndent=20,
    )

    story = []
    now = datetime.now()

    # ══════════════════════════════════════════════════════════════════════════
    # COVER PAGE
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Spacer(1, 3 * cm))
    story.append(Paragraph("DIGITAL FORENSICS", style_subtitle))
    story.append(Paragraph("AI-Assisted Investigation Report", style_title))
    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1a1a2e")))
    story.append(Spacer(1, 0.5 * cm))

    cover_data = [
        ["Case Name", case_name],
        ["Examiner", examiner],
        ["Report Generated", now.strftime("%Y-%m-%d %H:%M:%S")],
        ["Tool", "Windows Forensics AI Chatbot v1.0"],
        ["Total Questions", str(len(session_log))],
    ]
    cover_table = Table(cover_data, colWidths=[5 * cm, 11 * cm])
    cover_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR", (1, 0), (1, -1), colors.HexColor("#333333")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#f0f0f8"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#ccccdd")),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(cover_table)
    story.append(Spacer(1, 1 * cm))

    story.append(Paragraph(
        "This report was generated automatically by the Windows Forensics AI Chatbot. "
        "All answers are based solely on evidence extracted from the loaded Windows Event Logs "
        "and Registry hives. Evidence references are included for each answer.",
        style_body
    ))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # EXECUTIVE SUMMARY
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("1. Executive Summary", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#ccccdd")))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph(
        f"This forensic report documents an AI-assisted investigation conducted on "
        f"{now.strftime('%B %d, %Y')}. A total of {len(session_log)} investigative "
        f"question(s) were asked and answered using evidence retrieved from Windows "
        f"Event Logs and Registry hives. The AI system used Retrieval-Augmented Generation "
        f"(RAG) to find relevant log entries and answer each question with direct evidence references.",
        style_body
    ))
    story.append(Spacer(1, 0.3 * cm))

    # Summary table
    total_refs = sum(len(r.get("references", [])) for r in session_log)
    summary_data = [
        ["Metric", "Value"],
        ["Total Questions Asked", str(len(session_log))],
        ["Total Evidence References", str(total_refs)],
        ["Average References per Question", f"{total_refs / max(len(session_log), 1):.1f}"],
        ["Report Date", now.strftime("%Y-%m-%d")],
    ]
    summary_table = Table(summary_data, colWidths=[8 * cm, 8 * cm])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f0f0f8"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#ccccdd")),
        ("PADDING", (0, 0), (-1, -1), 8),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
    ]))
    story.append(summary_table)
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # Q&A TRANSCRIPT
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("2. Investigation Q&A Transcript", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#ccccdd")))
    story.append(Spacer(1, 0.3 * cm))

    for i, entry in enumerate(session_log, 1):
        story.append(Paragraph(f"Q{i}: {entry['question']}", style_question))
        story.append(Spacer(1, 0.2 * cm))

        # Answer (replace newlines with <br/>)
        answer_text = entry['answer'].replace('\n', '<br/>')
        story.append(Paragraph(f"<b>Answer:</b> {answer_text}", style_answer))
        story.append(Spacer(1, 0.2 * cm))

        # Evidence references
        if entry.get('references'):
            story.append(Paragraph("Evidence References:", style_ref))
            for ref in entry['references']:
                meta = ref.get('meta', {})
                if meta.get('type') == 'event':
                    ref_text = (
                        f"{ref['ref_id']}  EVENT LOG | "
                        f"EventID: {meta.get('event_id', 'N/A')} | "
                        f"Time: {meta.get('timestamp', 'N/A')} | "
                        f"Source: {meta.get('source', 'N/A')}"
                    )
                else:
                    ref_text = (
                        f"{ref['ref_id']}  REGISTRY | "
                        f"Hive: {meta.get('hive', 'N/A')} | "
                        f"Key: {meta.get('key_path', 'N/A')[:60]}..."
                    )
                story.append(Paragraph(ref_text, style_meta))

        story.append(Spacer(1, 0.2 * cm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#ddddee")))
        story.append(Spacer(1, 0.3 * cm))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # EVIDENCE APPENDIX
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("3. Evidence Appendix", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#ccccdd")))
    story.append(Paragraph(
        "All raw evidence records referenced in the Q&A transcript are listed below.",
        style_body
    ))
    story.append(Spacer(1, 0.3 * cm))

    seen_refs = set()
    for entry in session_log:
        for ref in entry.get('references', []):
            key = f"{ref['type']}-{ref['db_id']}"
            if key in seen_refs:
                continue
            seen_refs.add(key)

            meta = ref.get('meta', {})
            story.append(Paragraph(f"{ref['ref_id']} — {ref['type'].upper()} Record", style_h2))

            if meta.get('type') == 'event':
                rows = [
                    ["Field", "Value"],
                    ["EventID", str(meta.get('event_id', 'N/A'))],
                    ["Timestamp", str(meta.get('timestamp', 'N/A'))],
                    ["Source", str(meta.get('source', 'N/A'))],
                    ["Computer", str(meta.get('computer', 'N/A'))],
                    ["Level", str(meta.get('level', 'N/A'))],
                    ["Log File", str(meta.get('file_source', 'N/A'))],
                    ["DB ID", str(meta.get('db_id', 'N/A'))],
                ]
            else:
                rows = [
                    ["Field", "Value"],
                    ["Hive", str(meta.get('hive', 'N/A'))],
                    ["Key Path", str(meta.get('key_path', 'N/A'))],
                    ["Value Name", str(meta.get('value_name', 'N/A'))],
                    ["Value Data", str(meta.get('value_data', 'N/A'))[:200]],
                    ["Hive File", str(meta.get('file_source', 'N/A'))],
                    ["DB ID", str(meta.get('db_id', 'N/A'))],
                ]

            t = Table(rows, colWidths=[4 * cm, 12 * cm])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#313244")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f5f5ff"), colors.white]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#ccccdd")),
                ("PADDING", (0, 0), (-1, -1), 6),
                ("WORDWRAP", (1, 1), (1, -1), True),
            ]))
            story.append(t)
            story.append(Spacer(1, 0.4 * cm))

    # ── Build PDF ──────────────────────────────────────────────────────────────
    def add_page_number(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#888888"))
        page_num = f"Page {doc.page}  |  Windows Forensics AI Chatbot  |  {now.strftime('%Y-%m-%d')}"
        canvas.drawCentredString(A4[0] / 2, 1.2 * cm, page_num)
        canvas.restoreState()

    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    print(f"[REPORT] PDF saved to: {output_path}")
    return output_path


if __name__ == "__main__":
    # Quick test with dummy data
    dummy_log = [
        {
            "question": "Were there any failed login attempts?",
            "answer": "Based on the evidence, EventID 4625 was recorded at 2026-02-20 06:42:10. This indicates a failed logon attempt on computer DESKTOP-ABC. [REF-1]",
            "references": [
                {
                    "ref_id": "[REF-1]",
                    "type": "event",
                    "db_id": 1234,
                    "meta": {
                        "type": "event",
                        "event_id": "4625",
                        "timestamp": "2026-02-20 06:42:10",
                        "source": "Microsoft-Windows-Security-Auditing",
                        "computer": "DESKTOP-ABC",
                        "level": "Information",
                        "file_source": "Security.evtx",
                        "db_id": 1234
                    }
                }
            ],
            "evidence_text": ""
        }
    ]
    generate_report(dummy_log, "test_report.pdf", case_name="Test Case", examiner="Test Examiner")
    print("Test report generated: test_report.pdf")