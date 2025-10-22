"""PDF report generator."""

import logging
import os
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

logger = logging.getLogger(__name__)


class PDFReportGenerator:
    """Generate PDF reports from analysis results."""

    def __init__(self):
        """Initialize PDF generator."""
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        # Title style
        self.styles.add(
            ParagraphStyle(
                name="CustomTitle",
                parent=self.styles["Heading1"],
                fontSize=24,
                textColor=colors.HexColor("#1a1a1a"),
                spaceAfter=30,
                alignment=1,  # Center
            )
        )

        # Heading style
        self.styles.add(
            ParagraphStyle(
                name="CustomHeading",
                parent=self.styles["Heading2"],
                fontSize=16,
                textColor=colors.HexColor("#2c3e50"),
                spaceAfter=12,
                spaceBefore=12,
            )
        )

        # Body style
        self.styles.add(
            ParagraphStyle(
                name="CustomBody",
                parent=self.styles["BodyText"],
                fontSize=11,
                textColor=colors.HexColor("#333333"),
                spaceAfter=12,
                leading=14,
            )
        )

    def generate_report(
        self,
        aggregation: Dict[str, Any],
        analysis: Dict[str, Any],
        start_date: datetime,
        end_date: datetime,
        chart_paths: Optional[list] = None,
        table_data: Optional[list] = None,
    ) -> str:
        """Generate PDF report from analysis result.

        Args:
            aggregation: Aggregated statistics from metadata collection
            analysis: Analysis result from AI agent
            start_date: Start date of analysis period
            end_date: End date of analysis period
            chart_paths: List of chart file paths to embed in PDF
            table_data: List of TableData objects for detailed metadata display

        Returns:
            Path to the generated PDF file
        """
        logger.info("Generating PDF report...")

        # Create temporary file for PDF
        temp_file = tempfile.NamedTemporaryFile(
            mode="wb", suffix=".pdf", delete=False
        )
        pdf_path = temp_file.name
        temp_file.close()

        # Create PDF document
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=letter,
            rightMargin=inch,
            leftMargin=inch,
            topMargin=inch,
            bottomMargin=inch,
        )

        # Build content
        story = []

        # Title
        title = Paragraph(
            "Metadata Analytics Report",
            self.styles["CustomTitle"],
        )
        story.append(title)
        story.append(Spacer(1, 0.2 * inch))

        # Date and period
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        period_str = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        date_para = Paragraph(
            f"<i>Generated: {date_str}<br/>Analysis Period: {period_str}</i>",
            self.styles["CustomBody"],
        )
        story.append(date_para)
        story.append(Spacer(1, 0.3 * inch))

        # Executive Summary
        story.append(
            Paragraph(
                "Executive Summary",
                self.styles["CustomHeading"],
            )
        )
        summary = analysis.get("executive_summary", "No summary available")
        story.append(Paragraph(summary, self.styles["CustomBody"]))
        story.append(Spacer(1, 0.2 * inch))

        # Key Findings
        story.append(
            Paragraph(
                "Key Findings",
                self.styles["CustomHeading"],
            )
        )
        findings = analysis.get("key_findings", [])
        if findings:
            for finding in findings:
                bullet = Paragraph(f"• {finding}", self.styles["CustomBody"])
                story.append(bullet)
        else:
            story.append(Paragraph("No key findings available.", self.styles["CustomBody"]))
        story.append(Spacer(1, 0.2 * inch))

        # Statistics Summary
        story.append(
            Paragraph(
                "Statistics Overview",
                self.styles["CustomHeading"],
            )
        )
        stats_table = self._create_statistics_table(aggregation)
        story.append(stats_table)
        story.append(Spacer(1, 0.3 * inch))

        # Charts section with embedded images
        if chart_paths:
            story.append(PageBreak())
            story.append(
                Paragraph(
                    "Data Visualizations",
                    self.styles["CustomHeading"],
                )
            )
            story.append(Spacer(1, 0.2 * inch))

            # Embed each chart image
            for i, chart_path in enumerate(chart_paths, 1):
                if os.path.exists(chart_path):
                    try:
                        # Add chart image
                        img = Image(chart_path, width=6 * inch, height=3.6 * inch)
                        story.append(img)
                        story.append(Spacer(1, 0.3 * inch))

                        # Add page break after every 2 charts for better layout
                        if i % 2 == 0 and i < len(chart_paths):
                            story.append(PageBreak())
                    except Exception as e:
                        logger.warning(f"Failed to embed chart {chart_path}: {e}")
                        # Add placeholder text if image fails
                        error_para = Paragraph(
                            f"<i>Chart {i}: Image embedding failed</i>",
                            self.styles["CustomBody"],
                        )
                        story.append(error_para)
                        story.append(Spacer(1, 0.2 * inch))

        # Detailed metadata text section
        if table_data:
            story.append(PageBreak())
            story.append(
                Paragraph(
                    "Detailed Metadata Distribution",
                    self.styles["CustomHeading"],
                )
            )
            story.append(
                Paragraph(
                    "<i>The following fields contain long text or many categories. "
                    "All values are displayed in full text format.</i>",
                    self.styles["CustomBody"],
                )
            )
            story.append(Spacer(1, 0.2 * inch))

            # Add each field as text
            for table_info in table_data:
                # Field title with reason
                title_text = f"<b>{table_info.title}</b> <i>({table_info.reason})</i>"
                story.append(Paragraph(title_text, self.styles["CustomBody"]))
                story.append(Spacer(1, 0.1 * inch))

                # Add all values as text paragraphs
                self._add_metadata_text_entries(story, table_info)
                story.append(Spacer(1, 0.3 * inch))

        # Build PDF
        doc.build(story)

        logger.info(f"PDF report generated: {pdf_path}")
        return pdf_path

    def _create_statistics_table(self, aggregation: Dict[str, Any]) -> Table:
        """Create statistics summary table.

        Args:
            aggregation: Aggregation dictionary with schema, aggregations, and by_file_type

        Returns:
            ReportLab Table object
        """
        data = [
            ["Metric", "Value"],
        ]

        # Add file type breakdown if available
        by_file_type = aggregation.get("by_file_type", {})
        if by_file_type:
            data.append(["", ""])  # Empty row
            data.append(["File Types", "Count"])
            for ext, count in sorted(by_file_type.items(), key=lambda x: x[1], reverse=True):
                data.append([ext or "unknown", str(count)])

        table = Table(data, colWidths=[3 * inch, 2 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3498db")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                    ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 1), (-1, -1), 10),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.HexColor("#f8f9fa")],
                    ),
                ]
            )
        )

        return table

    def _add_metadata_text_entries(self, story, table_info):
        """Add metadata entries as text paragraphs (no truncation).

        Args:
            story: ReportLab story list to append to
            table_info: TableData object with field information
        """
        # Sort by count descending
        sorted_data = sorted(
            table_info.data.items(), key=lambda x: x[1], reverse=True
        )

        # Calculate total for percentages
        total = sum(table_info.data.values())

        # Add custom style for metadata entries with smaller font
        entry_style = ParagraphStyle(
            name="MetadataEntry",
            parent=self.styles["BodyText"],
            fontSize=9,
            textColor=colors.HexColor("#333333"),
            spaceAfter=8,
            leftIndent=20,
            leading=11,
        )

        # Display all entries (no limit)
        for i, (value, count) in enumerate(sorted_data, 1):
            percentage = (count / total) * 100

            # Format the value - escape special characters for ReportLab
            value_str = str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

            # Create entry text
            entry_text = (
                f"<b>{i}.</b> Count: {count} ({percentage:.1f}%)<br/>"
                f"<font name='Courier' size='8'>{value_str}</font>"
            )

            entry_para = Paragraph(entry_text, entry_style)
            story.append(entry_para)
