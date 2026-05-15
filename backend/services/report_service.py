"""
PDF report generation.

Produces a single-document period report containing:
  - Executive summary (total kWh, cost, peak, avg)
  - Period comparison (vs previous period)
  - Consumption trend chart
  - Hourly profile chart
  - Statistical outliers (readings beyond ±2σ)
  - Optimization recommendations

Charts are rendered with matplotlib to in-memory PNG bytes and embedded
into the PDF; no temp files on disk. Output is returned as raw bytes
suitable for streaming directly to the client.
"""
from __future__ import annotations

import io
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

import matplotlib

matplotlib.use("Agg")  # headless backend; must be set before importing pyplot
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy import func

from backend.database.postgres import SessionLocal
from backend.models.energy import EnergyReading
from backend.services.analytics_service import analytics_service
from backend.services.optimization_service import (
    DEFAULT_COST_PER_KWH,
    optimization_service,
)


_BRAND = colors.HexColor("#0f766e")  # teal-700
_MUTED = colors.HexColor("#64748b")  # slate-500
_BG_ROW = colors.HexColor("#f8fafc")  # slate-50


class ReportService:
    """Builds period reports as PDF bytes."""

    def build_period_report(
        self,
        start: datetime,
        end: datetime,
        cost_per_kwh: float = DEFAULT_COST_PER_KWH,
        report_title: str = "EnerSight Period Report",
        author_name: Optional[str] = None,
    ) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=1.6 * cm,
            rightMargin=1.6 * cm,
            topMargin=1.6 * cm,
            bottomMargin=1.6 * cm,
            title=report_title,
            author="EnerSight",
        )

        story = []
        styles = self._styles()

        story.extend(self._header_block(report_title, start, end, author_name, styles))
        story.append(self._summary_block(start, end, cost_per_kwh, styles))
        story.append(Spacer(1, 0.4 * cm))
        story.append(self._comparison_block(start, end, styles))
        story.append(Spacer(1, 0.4 * cm))

        trend_png = self._render_trend_chart(start, end)
        if trend_png is not None:
            story.append(Paragraph("Consumption trend", styles["section"]))
            story.append(Image(io.BytesIO(trend_png), width=16 * cm, height=7 * cm))
            story.append(Spacer(1, 0.4 * cm))

        hourly_png = self._render_hourly_profile_chart(start, end)
        if hourly_png is not None:
            story.append(Paragraph("Average consumption by hour-of-day", styles["section"]))
            story.append(Image(io.BytesIO(hourly_png), width=16 * cm, height=6 * cm))
            story.append(Spacer(1, 0.4 * cm))

        story.append(PageBreak())
        story.append(Paragraph("Statistical outliers", styles["section"]))
        story.append(self._outliers_block(start, end, styles))
        story.append(Spacer(1, 0.4 * cm))

        story.append(Paragraph("Optimization recommendations", styles["section"]))
        story.append(self._recommendations_block(start, end, cost_per_kwh, styles))

        doc.build(story, onFirstPage=self._draw_footer, onLaterPages=self._draw_footer)
        return buffer.getvalue()

    # ------------------------------------------------------------------
    # Styles + chrome
    # ------------------------------------------------------------------
    def _styles(self):
        s = getSampleStyleSheet()
        return {
            "title": ParagraphStyle(
                "title", parent=s["Title"], textColor=_BRAND, alignment=TA_LEFT,
                fontSize=22, spaceAfter=2,
            ),
            "subtitle": ParagraphStyle(
                "subtitle", parent=s["Normal"], textColor=_MUTED,
                fontSize=10, spaceAfter=12,
            ),
            "section": ParagraphStyle(
                "section", parent=s["Heading2"], textColor=_BRAND,
                fontSize=13, spaceBefore=4, spaceAfter=6,
            ),
            "body": ParagraphStyle("body", parent=s["Normal"], fontSize=10, leading=14),
            "muted": ParagraphStyle(
                "muted", parent=s["Normal"], fontSize=9, textColor=_MUTED, leading=12,
            ),
            "kpi_label": ParagraphStyle(
                "kpi_label", parent=s["Normal"], fontSize=9,
                textColor=_MUTED, alignment=TA_CENTER,
            ),
            "kpi_value": ParagraphStyle(
                "kpi_value", parent=s["Normal"], fontSize=14,
                textColor=_BRAND, alignment=TA_CENTER, leading=18,
            ),
        }

    def _draw_footer(self, canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(_MUTED)
        canvas.drawString(
            1.6 * cm,
            1.0 * cm,
            f"EnerSight  ·  Generated {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        )
        canvas.drawRightString(
            A4[0] - 1.6 * cm, 1.0 * cm, f"Page {doc.page}",
        )
        canvas.restoreState()

    def _header_block(self, title, start, end, author_name, styles):
        out = [
            Paragraph(title, styles["title"]),
            Paragraph(
                f"Period: {start.strftime('%Y-%m-%d')} → {end.strftime('%Y-%m-%d')}"
                + (f"  ·  Prepared for: {author_name}" if author_name else ""),
                styles["subtitle"],
            ),
        ]
        return out

    # ------------------------------------------------------------------
    # Sections
    # ------------------------------------------------------------------
    def _summary_block(self, start, end, cost_per_kwh, styles) -> Table:
        summary = analytics_service.get_summary(start, end, cost_per_kwh=cost_per_kwh)
        cells = [
            self._kpi_cell("Total consumption", f"{summary.total_consumption:,.1f} kWh", styles),
            self._kpi_cell("Estimated cost", f"${(summary.total_cost or 0):,.2f}", styles),
            self._kpi_cell("Average daily", f"{summary.average_daily:,.1f} kWh", styles),
            self._kpi_cell("Peak reading", f"{summary.peak_consumption:,.1f} kWh", styles),
        ]
        table = Table([cells], colWidths=[4 * cm] * 4)
        table.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("BACKGROUND", (0, 0), (-1, -1), _BG_ROW),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        return table

    def _kpi_cell(self, label, value, styles):
        return [Paragraph(label, styles["kpi_label"]), Paragraph(value, styles["kpi_value"])]

    def _comparison_block(self, start, end, styles) -> Table:
        try:
            cmp = analytics_service.compare_periods(start, end, "previous_period")
        except Exception:
            return Paragraph("Comparison data unavailable.", styles["muted"])

        change_pct = cmp.percentage_change
        arrow = "▲" if cmp.difference > 0 else "▼" if cmp.difference < 0 else "—"
        change_color = (
            colors.HexColor("#dc2626") if cmp.difference > 0
            else colors.HexColor("#16a34a") if cmp.difference < 0
            else _MUTED
        )

        data = [
            ["", "Current period", "Previous period", "Change"],
            [
                "Total (kWh)",
                f"{cmp.current_period.total:,.1f}",
                f"{cmp.comparison_period.total:,.1f}",
                f"{arrow} {cmp.difference:+,.1f} ({change_pct:+.1f}%)",
            ],
            [
                "Average (kWh)",
                f"{cmp.current_period.average:,.2f}",
                f"{cmp.comparison_period.average:,.2f}",
                "",
            ],
            [
                "Peak (kWh)",
                f"{cmp.current_period.max:,.1f}",
                f"{cmp.comparison_period.max:,.1f}",
                "",
            ],
        ]
        table = Table(data, colWidths=[4 * cm, 4 * cm, 4 * cm, 4 * cm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), _BRAND),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _BG_ROW]),
            ("TEXTCOLOR", (3, 1), (3, 1), change_color),
            ("FONTNAME", (3, 1), (3, 1), "Helvetica-Bold"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        return table

    def _outliers_block(self, start, end, styles):
        outliers = self._compute_outliers(start, end)
        if not outliers:
            return Paragraph(
                "No statistically extreme readings (|z| > 2) in this period.",
                styles["muted"],
            )

        data = [["When", "Consumption (kWh)", "z-score", "Direction"]]
        for ts, value, z in outliers[:10]:
            direction = "Spike ↑" if z > 0 else "Dip ↓"
            data.append([
                ts.strftime("%Y-%m-%d %H:%M"),
                f"{value:,.2f}",
                f"{z:+.2f}",
                direction,
            ])
        table = Table(data, colWidths=[5 * cm, 4 * cm, 3 * cm, 4 * cm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), _BRAND),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _BG_ROW]),
        ]))
        return table

    def _recommendations_block(self, start, end, cost_per_kwh, styles):
        report = optimization_service.generate_report(start, end, cost_per_kwh)
        if not report.recommendations:
            return Paragraph(
                "No optimization opportunities flagged for this period.",
                styles["muted"],
            )

        data = [["Title", "Category", "Severity", "Savings / month"]]
        for r in report.recommendations:
            data.append([
                Paragraph(r.title, styles["body"]),
                r.category.value.upper(),
                r.severity.value.upper(),
                f"${r.estimated_savings_usd:,.2f}\n({r.estimated_savings_kwh:,.0f} kWh)",
            ])
        # Sum row.
        data.append([
            Paragraph("<b>Total projected savings</b>", styles["body"]),
            "", "",
            f"${report.total_estimated_savings_usd:,.2f}\n"
            f"({report.total_estimated_savings_kwh:,.0f} kWh)",
        ])
        table = Table(data, colWidths=[7 * cm, 2.6 * cm, 2.6 * cm, 3.8 * cm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), _BRAND),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, _BG_ROW]),
            ("BACKGROUND", (0, -1), (-1, -1), _BG_ROW),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        return table

    # ------------------------------------------------------------------
    # Data + charts
    # ------------------------------------------------------------------
    def _render_trend_chart(self, start, end) -> Optional[bytes]:
        # Daily buckets for any window > 2 days; otherwise hourly.
        bucket = "day" if (end - start).days >= 2 else "hour"
        data = analytics_service.get_data_range(start, end, aggregation=bucket)
        if not data:
            return None
        timestamps = [datetime.fromisoformat(d["timestamp"]) for d in data]
        values = [d["value"] for d in data]

        fig, ax = plt.subplots(figsize=(9, 3.5), dpi=110)
        ax.plot(timestamps, values, color="#0f766e", linewidth=2)
        ax.fill_between(timestamps, values, color="#0f766e", alpha=0.12)
        ax.set_ylabel("kWh")
        ax.set_xlabel(bucket.capitalize())
        ax.grid(True, linestyle="--", alpha=0.3)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        fig.autofmt_xdate()
        fig.tight_layout()
        return self._fig_to_png(fig)

    def _render_hourly_profile_chart(self, start, end) -> Optional[bytes]:
        with SessionLocal() as session:
            hour = func.extract("hour", EnergyReading.recorded_at).label("hour")
            rows = (
                session.query(hour, func.avg(EnergyReading.consumption).label("avg"))
                .filter(
                    EnergyReading.recorded_at >= start,
                    EnergyReading.recorded_at < end,
                )
                .group_by(hour)
                .order_by(hour.asc())
                .all()
            )
        if not rows:
            return None
        hours = [int(r.hour) for r in rows]
        values = [float(r.avg or 0) for r in rows]

        fig, ax = plt.subplots(figsize=(9, 3), dpi=110)
        ax.bar(hours, values, color="#0f766e", alpha=0.85, width=0.7)
        ax.set_xticks(range(0, 24, 2))
        ax.set_xlabel("Hour of day")
        ax.set_ylabel("Avg kWh")
        ax.grid(True, axis="y", linestyle="--", alpha=0.3)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        fig.tight_layout()
        return self._fig_to_png(fig)

    def _fig_to_png(self, fig) -> bytes:
        out = io.BytesIO()
        fig.savefig(out, format="png", bbox_inches="tight")
        plt.close(fig)
        return out.getvalue()

    def _compute_outliers(self, start, end) -> List[Tuple[datetime, float, float]]:
        """Returns (recorded_at, consumption, z_score) for |z| > 2, sorted by |z| desc."""
        with SessionLocal() as session:
            stats = (
                session.query(
                    func.avg(EnergyReading.consumption).label("mu"),
                    func.stddev_samp(EnergyReading.consumption).label("sigma"),
                )
                .filter(
                    EnergyReading.recorded_at >= start,
                    EnergyReading.recorded_at < end,
                )
                .one()
            )
            mu = float(stats.mu or 0.0)
            sigma = float(stats.sigma or 0.0)
            if sigma <= 0:
                return []

            rows = (
                session.query(
                    EnergyReading.recorded_at,
                    EnergyReading.consumption,
                )
                .filter(
                    EnergyReading.recorded_at >= start,
                    EnergyReading.recorded_at < end,
                )
                .all()
            )

        out: List[Tuple[datetime, float, float]] = []
        for ts, value in rows:
            if value is None:
                continue
            z = (float(value) - mu) / sigma
            if abs(z) > 2.0:
                out.append((ts, float(value), z))
        out.sort(key=lambda t: abs(t[2]), reverse=True)
        return out


report_service = ReportService()
