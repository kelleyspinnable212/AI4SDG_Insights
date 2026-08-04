"""
Utility helpers for AI4SDG Insights.
Formatting, theming, PDF/CSV export, and UI styling.
"""

from __future__ import annotations

import io
from datetime import datetime
from typing import Any, Dict, Optional

import pandas as pd
import plotly.graph_objects as go


# ---------------------------------------------------------------------------
# Color palettes (UN / UNDP inspired)
# ---------------------------------------------------------------------------

LIGHT_THEME: Dict[str, str] = {
    "primary": "#009EDB",
    "primary_dark": "#00689D",
    "secondary": "#023047",
    "accent": "#00A0DC",
    "background": "#F5F8FA",
    "card": "#FFFFFF",
    "text": "#1A1A2E",
    "text_muted": "#5A6A7A",
    "border": "#E1E8ED",
    "success": "#2E7D32",
    "warning": "#ED6C02",
    "danger": "#D32F2F",
    "shadow": "rgba(0, 110, 182, 0.12)",
}

DARK_THEME: Dict[str, str] = {
    "primary": "#4FC3F7",
    "primary_dark": "#0288D1",
    "secondary": "#E3F2FD",
    "accent": "#81D4FA",
    "background": "#0D1B2A",
    "card": "#1B2838",
    "text": "#E8F1F8",
    "text_muted": "#90A4AE",
    "border": "#2C3E50",
    "success": "#66BB6A",
    "warning": "#FFA726",
    "danger": "#EF5350",
    "shadow": "rgba(0, 0, 0, 0.35)",
}

# Consistent colours for country comparison charts
COUNTRY_COLORS: Dict[str, str] = {
    "Pakistan": "#009EDB",
    "India": "#FF6B35",
    "Bangladesh": "#2E7D32",
}


def get_theme(dark_mode: bool = False) -> Dict[str, str]:
    """Return the active colour palette."""
    return DARK_THEME if dark_mode else LIGHT_THEME


def format_number(value: Optional[float], decimals: int = 2) -> str:
    """
    Format a numeric value for display with compact notation for large numbers.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "N/A"
    abs_val = abs(value)
    if abs_val >= 1_000_000_000_000:
        return f"{value / 1_000_000_000_000:.{decimals}f}T"
    if abs_val >= 1_000_000_000:
        return f"{value / 1_000_000_000:.{decimals}f}B"
    if abs_val >= 1_000_000:
        return f"{value / 1_000_000:.{decimals}f}M"
    if abs_val >= 1_000:
        return f"{value / 1_000:.{decimals}f}K"
    if abs_val >= 100:
        return f"{value:.1f}"
    return f"{value:.{decimals}f}"


def format_percent(value: Optional[float], decimals: int = 2) -> str:
    """Format a percentage value with sign."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "N/A"
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.{decimals}f}%"


def trend_label(growth: Optional[float], threshold: float = 0.5) -> str:
    """Map growth percentage to a human-readable trend label."""
    if growth is None or (isinstance(growth, float) and pd.isna(growth)):
        return "Insufficient data"
    if growth > threshold:
        return "⬆ Improving / Rising"
    if growth < -threshold:
        return "⬇ Declining"
    return "➡ Stable"


def inject_custom_css(dark_mode: bool = False, accent: str | None = None) -> str:
    """
    Build custom CSS for a polished UNDP-style Streamlit layout.
    Optional accent colour tints SDG-aligned highlights.
    """
    t = get_theme(dark_mode)
    accent_color = accent or t["primary"]
    hero_grad = (
        f"linear-gradient(135deg, #003A5D 0%, {accent_color} 48%, #00A0DC 100%)"
        if not dark_mode
        else f"linear-gradient(135deg, #071521 0%, #0D2A3F 45%, {accent_color} 100%)"
    )
    soft_bg = (
        f"radial-gradient(1200px 400px at 10% -10%, {accent_color}22, transparent),"
        f"radial-gradient(900px 380px at 90% 0%, #00A0DC18, transparent),"
        f"{t['background']}"
    )

    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700&family=Montserrat:wght@600;700;800&display=swap');

    .stApp {{
        background: {soft_bg};
        font-family: 'Source Sans 3', 'Segoe UI', sans-serif;
        color: {t['text']};
    }}

    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}

    .block-container {{
        padding-top: 1.1rem;
        padding-bottom: 2.5rem;
        max-width: 1180px;
    }}

    /* Hero banner */
    .hero-banner {{
        background: {hero_grad};
        border-radius: 22px;
        padding: 1.55rem 1.7rem 1.35rem;
        margin-bottom: 1.15rem;
        box-shadow: 0 16px 40px {t['shadow']};
        color: #fff;
        position: relative;
        overflow: hidden;
        animation: heroFade 0.55s ease-out;
    }}
    .hero-banner::after {{
        content: "";
        position: absolute;
        right: -40px;
        top: -50px;
        width: 220px;
        height: 220px;
        border-radius: 50%;
        background: rgba(255,255,255,0.12);
    }}
    .hero-banner::before {{
        content: "";
        position: absolute;
        right: 70px;
        bottom: -70px;
        width: 180px;
        height: 180px;
        border-radius: 50%;
        background: rgba(255,255,255,0.08);
    }}
    .hero-kicker {{
        font-size: 0.78rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        opacity: 0.9;
        font-weight: 700;
        margin-bottom: 0.35rem;
    }}
    .hero-title {{
        font-family: 'Montserrat', sans-serif;
        font-size: 2rem;
        font-weight: 800;
        margin: 0 0 0.25rem 0;
        letter-spacing: -0.02em;
        position: relative;
        z-index: 1;
    }}
    .hero-subtitle {{
        font-size: 1.02rem;
        opacity: 0.92;
        margin: 0;
        max-width: 640px;
        position: relative;
        z-index: 1;
    }}
    .hero-chip-row {{
        display: flex;
        flex-wrap: wrap;
        gap: 0.45rem;
        margin-top: 0.95rem;
        position: relative;
        z-index: 1;
    }}
    .hero-chip {{
        background: rgba(255,255,255,0.16);
        border: 1px solid rgba(255,255,255,0.28);
        backdrop-filter: blur(6px);
        border-radius: 999px;
        padding: 0.28rem 0.75rem;
        font-size: 0.78rem;
        font-weight: 600;
    }}

    @keyframes heroFade {{
        from {{ opacity: 0; transform: translateY(8px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    @keyframes riseIn {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}

    .panel {{
        background: {t['card']};
        border-radius: 16px;
        padding: 1.2rem 1.4rem;
        box-shadow: 0 8px 28px {t['shadow']};
        border: 1px solid {t['border']};
        margin-bottom: 1.1rem;
        animation: riseIn 0.45s ease-out;
    }}
    .panel-title {{
        font-family: 'Montserrat', sans-serif;
        font-size: 1.05rem;
        font-weight: 700;
        color: {t['secondary']};
        margin-bottom: 0.7rem;
        padding-bottom: 0.4rem;
        border-bottom: 3px solid {accent_color};
        display: inline-block;
    }}

    .sdg-badge {{
        display: flex;
        align-items: flex-start;
        gap: 1rem;
        background: {t['card']};
        border-radius: 16px;
        padding: 1.15rem 1.3rem;
        box-shadow: 0 8px 28px {t['shadow']};
        border: 1px solid {t['border']};
        border-left: 6px solid {accent_color};
        margin-bottom: 1.1rem;
        animation: riseIn 0.5s ease-out;
    }}
    .sdg-icon {{ font-size: 2.3rem; line-height: 1; }}
    .sdg-code {{
        font-family: 'Montserrat', sans-serif;
        font-weight: 700;
        font-size: 0.88rem;
        color: {accent_color};
        letter-spacing: 0.04em;
    }}
    .sdg-title {{
        font-weight: 700;
        font-size: 1.05rem;
        color: {t['text']};
        margin: 0.15rem 0;
    }}
    .sdg-desc {{
        font-size: 0.88rem;
        color: {t['text_muted']};
        line-height: 1.45;
    }}

    .briefing-grid {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.85rem;
        margin-top: 0.4rem;
    }}
    @media (max-width: 800px) {{
        .briefing-grid {{ grid-template-columns: 1fr; }}
        .hero-title {{ font-size: 1.55rem; }}
    }}
    .briefing-card {{
        background: {t['card']};
        border: 1px solid {t['border']};
        border-radius: 14px;
        padding: 0.95rem 1.05rem;
        box-shadow: 0 6px 20px {t['shadow']};
        border-top: 3px solid {accent_color};
        min-height: 110px;
        animation: riseIn 0.55s ease-out;
    }}
    .briefing-label {{
        font-size: 0.72rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: {accent_color};
        font-weight: 700;
        margin-bottom: 0.35rem;
    }}
    .briefing-text {{
        font-size: 0.9rem;
        color: {t['text']};
        line-height: 1.45;
        margin: 0;
    }}

    .ai-insight {{
        background: linear-gradient(
            135deg,
            {t['card']} 0%,
            {'#E8F4FC' if not dark_mode else '#152535'} 100%
        );
        border-radius: 16px;
        padding: 1.35rem 1.5rem;
        box-shadow: 0 8px 28px {t['shadow']};
        border: 1px solid {accent_color};
        margin-bottom: 1.1rem;
    }}
    .ai-insight h4 {{
        font-family: 'Montserrat', sans-serif;
        color: {t['primary_dark'] if not dark_mode else t['primary']};
        margin: 0.85rem 0 0.3rem 0;
        font-size: 0.92rem;
    }}
    .ai-insight p {{
        color: {t['text']};
        font-size: 0.9rem;
        line-height: 1.55;
        margin: 0;
    }}
    .ai-header {{
        font-family: 'Montserrat', sans-serif;
        font-size: 1.1rem;
        font-weight: 700;
        color: {t['primary_dark'] if not dark_mode else t['primary']};
        margin-bottom: 0.45rem;
    }}

    section[data-testid="stSidebar"] {{
        background: {t['card']};
        border-right: 1px solid {t['border']};
    }}
    section[data-testid="stSidebar"] .stMarkdown {{
        color: {t['text']};
    }}

    div[data-testid="stMetric"] {{
        background: {t['card']};
        border-radius: 16px;
        padding: 1rem 1.1rem;
        box-shadow: 0 8px 24px {t['shadow']};
        border: 1px solid {t['border']};
        border-top: 3px solid {accent_color};
        transition: transform 0.18s ease, box-shadow 0.18s ease;
    }}
    div[data-testid="stMetric"]:hover {{
        transform: translateY(-3px);
        box-shadow: 0 12px 30px {t['shadow']};
    }}
    div[data-testid="stMetric"] label {{
        color: {t['text_muted']} !important;
    }}
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {{
        color: {t['primary_dark'] if not dark_mode else t['primary']} !important;
        font-family: 'Montserrat', sans-serif;
    }}

    .stButton > button {{
        border-radius: 11px;
        font-weight: 700;
        border: none;
        transition: all 0.2s ease;
    }}
    .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, {t['primary_dark']}, {accent_color});
    }}
    .stDownloadButton > button {{
        border-radius: 11px;
        font-weight: 700;
    }}

    div[data-testid="stPlotlyChart"] {{
        background: {t['card']};
        border-radius: 16px;
        padding: 0.55rem;
        border: 1px solid {t['border']};
        box-shadow: 0 8px 28px {t['shadow']};
    }}

    .app-footer {{
        text-align: center;
        padding: 1.6rem 1rem 0.6rem;
        margin-top: 2rem;
        border-top: 1px solid {t['border']};
        color: {t['text_muted']};
        font-size: 0.82rem;
    }}
    .app-footer a {{
        color: {t['primary']};
        text-decoration: none;
        font-weight: 600;
    }}

    .risk-pill {{
        display: inline-block;
        padding: 0.35rem 0.9rem;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.85rem;
        letter-spacing: 0.03em;
    }}

    .context-strip {{
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin: 0.2rem 0 0.9rem 0;
    }}
    .context-pill {{
        background: {t['card']};
        border: 1px solid {t['border']};
        color: {t['text']};
        border-radius: 999px;
        padding: 0.28rem 0.75rem;
        font-size: 0.8rem;
        font-weight: 600;
        box-shadow: 0 2px 10px {t['shadow']};
    }}
    .context-pill span {{
        color: {accent_color};
        font-weight: 700;
    }}
    </style>
    """


def build_sparkline(
    df: pd.DataFrame,
    color: str = "#009EDB",
    dark_mode: bool = False,
) -> go.Figure:
    """Compact sparkline for recent trend context."""
    fig = go.Figure()
    if df is not None and not df.empty:
        clean = df.dropna(subset=["Value"]).sort_values("Year")
        fig.add_trace(
            go.Scatter(
                x=clean["Year"],
                y=clean["Value"],
                mode="lines",
                line=dict(color=color, width=2.5, shape="spline"),
                fill="tozeroy",
                fillcolor="rgba(0, 158, 219, 0.12)",
                hovertemplate="Year %{x}<br>%{y:,.2f}<extra></extra>",
            )
        )
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        height=90,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        showlegend=False,
        template="plotly_white" if not dark_mode else "plotly_dark",
    )
    return fig


def build_line_chart(
    df: pd.DataFrame,
    title: str,
    y_label: str,
    color: str = "#009EDB",
    dark_mode: bool = False,
    forecast_df: Optional[pd.DataFrame] = None,
) -> go.Figure:
    """
    Build an interactive Plotly line chart with optional forecast overlay.
    """
    t = get_theme(dark_mode)
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["Year"],
            y=df["Value"],
            mode="lines+markers",
            name="Observed",
            line=dict(color=color, width=2.5),
            marker=dict(size=7, color=color, line=dict(width=1, color="#fff")),
            hovertemplate="<b>Year %{x}</b><br>Value: %{y:,.2f}<extra></extra>",
        )
    )

    if forecast_df is not None and not forecast_df.empty:
        # Connect last observed point to first forecast for visual continuity
        bridge = pd.concat(
            [df.tail(1)[["Year", "Value"]], forecast_df[["Year", "Value"]]],
            ignore_index=True,
        )
        fig.add_trace(
            go.Scatter(
                x=bridge["Year"],
                y=bridge["Value"],
                mode="lines+markers",
                name="Forecast (5yr)",
                line=dict(color="#FF6B35", width=2.5, dash="dash"),
                marker=dict(size=6, symbol="diamond"),
                hovertemplate="<b>Forecast %{x}</b><br>Value: %{y:,.2f}<extra></extra>",
            )
        )

    fig.update_layout(
        title=dict(text=title, font=dict(size=16, family="Montserrat, sans-serif")),
        template="plotly_white" if not dark_mode else "plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)" if dark_mode else "#FAFBFC",
        xaxis=dict(
            title="Year",
            showgrid=True,
            gridcolor=t["border"],
            zeroline=False,
        ),
        yaxis=dict(
            title=y_label,
            showgrid=True,
            gridcolor=t["border"],
            zeroline=False,
        ),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=20, t=60, b=40),
        height=420,
        modebar=dict(bgcolor="rgba(0,0,0,0)"),
    )
    return fig


def build_comparison_chart(
    data_by_country: Dict[str, pd.DataFrame],
    title: str,
    y_label: str,
    dark_mode: bool = False,
) -> go.Figure:
    """Build a multi-country comparison line chart."""
    t = get_theme(dark_mode)
    fig = go.Figure()

    for country, df in data_by_country.items():
        if df is None or df.empty:
            continue
        color = COUNTRY_COLORS.get(country, "#888888")
        fig.add_trace(
            go.Scatter(
                x=df["Year"],
                y=df["Value"],
                mode="lines+markers",
                name=country,
                line=dict(color=color, width=2.5),
                marker=dict(size=6),
                hovertemplate=f"<b>{country}</b><br>Year %{{x}}<br>Value: %{{y:,.2f}}<extra></extra>",
            )
        )

    fig.update_layout(
        title=dict(text=title, font=dict(size=16, family="Montserrat, sans-serif")),
        template="plotly_white" if not dark_mode else "plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)" if dark_mode else "#FAFBFC",
        xaxis=dict(title="Year", showgrid=True, gridcolor=t["border"]),
        yaxis=dict(title=y_label, showgrid=True, gridcolor=t["border"]),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=20, t=60, b=40),
        height=440,
    )
    return fig


def build_equity_chart(
    series_map: Dict[str, pd.DataFrame],
    color_map: Dict[str, str],
    title: str,
    y_label: str,
    dark_mode: bool = False,
) -> go.Figure:
    """Build a leave-no-one-behind equity comparison chart."""
    t = get_theme(dark_mode)
    fig = go.Figure()
    palette = ["#009EDB", "#C5192D", "#2E7D32", "#FD9D24", "#6A1B9A"]

    for idx, (label, df) in enumerate(series_map.items()):
        if df is None or df.empty:
            continue
        color = color_map.get(label, palette[idx % len(palette)])
        fig.add_trace(
            go.Scatter(
                x=df["Year"],
                y=df["Value"],
                mode="lines+markers",
                name=label,
                line=dict(color=color, width=2.5),
                marker=dict(size=6),
                hovertemplate=(
                    f"<b>{label}</b><br>Year %{{x}}<br>Value: %{{y:,.2f}}<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        title=dict(text=title, font=dict(size=16, family="Montserrat, sans-serif")),
        template="plotly_white" if not dark_mode else "plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)" if dark_mode else "#FAFBFC",
        xaxis=dict(title="Year", showgrid=True, gridcolor=t["border"]),
        yaxis=dict(title=y_label, showgrid=True, gridcolor=t["border"]),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=20, t=60, b=40),
        height=420,
    )
    return fig


def build_scenario_chart(
    historical_df: pd.DataFrame,
    baseline_df: pd.DataFrame,
    adjusted_df: pd.DataFrame,
    title: str,
    y_label: str,
    dark_mode: bool = False,
) -> go.Figure:
    """Build historical + baseline/adjusted 2030 scenario chart."""
    t = get_theme(dark_mode)
    fig = go.Figure()

    if historical_df is not None and not historical_df.empty:
        fig.add_trace(
            go.Scatter(
                x=historical_df["Year"],
                y=historical_df["Value"],
                mode="lines+markers",
                name="Observed",
                line=dict(color="#009EDB", width=2.5),
                marker=dict(size=6),
            )
        )

    if baseline_df is not None and not baseline_df.empty:
        bridge_b = pd.concat(
            [historical_df.tail(1)[["Year", "Value"]], baseline_df],
            ignore_index=True,
        )
        fig.add_trace(
            go.Scatter(
                x=bridge_b["Year"],
                y=bridge_b["Value"],
                mode="lines+markers",
                name="Baseline to 2030",
                line=dict(color="#5A6A7A", width=2.2, dash="dash"),
                marker=dict(size=5, symbol="diamond"),
            )
        )

    if adjusted_df is not None and not adjusted_df.empty:
        bridge_a = pd.concat(
            [historical_df.tail(1)[["Year", "Value"]], adjusted_df],
            ignore_index=True,
        )
        fig.add_trace(
            go.Scatter(
                x=bridge_a["Year"],
                y=bridge_a["Value"],
                mode="lines+markers",
                name="Adjusted scenario",
                line=dict(color="#FF6B35", width=2.2, dash="dot"),
                marker=dict(size=5, symbol="diamond"),
            )
        )

    fig.update_layout(
        title=dict(text=title, font=dict(size=16, family="Montserrat, sans-serif")),
        template="plotly_white" if not dark_mode else "plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)" if dark_mode else "#FAFBFC",
        xaxis=dict(title="Year", showgrid=True, gridcolor=t["border"]),
        yaxis=dict(title=y_label, showgrid=True, gridcolor=t["border"]),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=20, t=60, b=40),
        height=420,
        shapes=[
            dict(
                type="line",
                x0=2030,
                x1=2030,
                y0=0,
                y1=1,
                yref="paper",
                line=dict(color="#90A4AE", width=1, dash="dot"),
            )
        ],
    )
    return fig


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Serialize a DataFrame to CSV bytes for download."""
    return df.to_csv(index=False).encode("utf-8")


def generate_pdf_report(
    country: str,
    indicator: str,
    stats: Dict[str, Any],
    sdg_info: Dict[str, Any],
    ai_insight: str,
    chart_fig: Optional[go.Figure] = None,
    unit: str = "",
    data_quality: Optional[Dict[str, Any]] = None,
    scenario: Optional[Dict[str, Any]] = None,
    equity_gap: Optional[Dict[str, Any]] = None,
    equity_dimension: str = "",
) -> bytes:
    """
    Generate a one-page-style SDG Progress Note PDF.

    Includes KPIs, data limitations, optional equity/scenario notes,
    chart image, and AI insight. Clearly marked as unofficial/educational.
    """
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        Image,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
        HRFlowable,
        KeepTogether,
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
    )

    styles = getSampleStyleSheet()
    banner_style = ParagraphStyle(
        "Banner",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.white,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        leading=11,
    )
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontSize=15,
        textColor=colors.HexColor("#00689D"),
        spaceAfter=2,
        spaceBefore=8,
        alignment=TA_LEFT,
        fontName="Helvetica-Bold",
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=9.5,
        textColor=colors.HexColor("#5A6A7A"),
        alignment=TA_LEFT,
        spaceAfter=8,
    )
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontSize=10.5,
        textColor=colors.HexColor("#023047"),
        spaceBefore=9,
        spaceAfter=4,
        fontName="Helvetica-Bold",
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=8.5,
        textColor=colors.HexColor("#1A1A2E"),
        alignment=TA_JUSTIFY,
        leading=11.5,
        spaceAfter=4,
    )
    meta_style = ParagraphStyle(
        "Meta",
        parent=styles["Normal"],
        fontSize=8.5,
        textColor=colors.HexColor("#5A6A7A"),
        alignment=TA_LEFT,
        spaceAfter=2,
    )
    footer_style = ParagraphStyle(
        "FooterNote",
        parent=styles["Normal"],
        fontSize=7.5,
        textColor=colors.HexColor("#90A4AE"),
        alignment=TA_CENTER,
        leading=10,
    )
    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontSize=7.5,
        textColor=colors.HexColor("#A21942"),
        alignment=TA_CENTER,
        fontName="Helvetica-Oblique",
        spaceBefore=4,
        spaceAfter=6,
    )

    story = []
    generated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    # Top banner
    banner = Table(
        [[Paragraph(
            "SDG PROGRESS NOTE  ·  AI4SDG Insights  ·  Portfolio / Educational Tool",
            banner_style,
        )]],
        colWidths=[7.0 * inch],
    )
    banner.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#00689D")),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    story.append(banner)
    story.append(
        Paragraph(
            "Not an official United Nations or UNDP document. For learning and portfolio use only.",
            disclaimer_style,
        )
    )

    story.append(
        Paragraph(
            f"SDG Progress Note: {country} — {indicator}",
            title_style,
        )
    )
    story.append(
        Paragraph(
            f"{sdg_info.get('sdg_code', '')}: {sdg_info.get('goal_title', '')}",
            subtitle_style,
        )
    )
    story.append(Paragraph(f"<b>Generated:</b> {generated_at}", meta_style))
    if unit:
        story.append(Paragraph(f"<b>Unit:</b> {unit}", meta_style))
    story.append(
        Paragraph(
            f"<b>Data source:</b> World Bank Open Data API",
            meta_style,
        )
    )

    story.append(Paragraph("1. Situation snapshot", section_style))
    kpi_data = [
        ["Metric", "Value"],
        ["Latest value", format_number(stats.get("latest_value"))],
        ["Latest year", str(stats.get("latest_year", "N/A"))],
        ["YoY growth", format_percent(stats.get("growth_pct"))],
        ["Trend", str(stats.get("trend", "N/A"))],
        ["Period average", format_number(stats.get("average"))],
        ["Min / Max", f"{format_number(stats.get('minimum'))} / {format_number(stats.get('maximum'))}"],
    ]
    if stats.get("risk_score") is not None:
        kpi_data.append(
            ["Heuristic SDG risk score", f"{stats['risk_score']:.0f} / 100"]
        )

    table = Table(kpi_data, colWidths=[2.4 * inch, 4.4 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#009EDB")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#E1E8ED")),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#F5F8FA")],
                ),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(table)

    # Data integrity
    story.append(Paragraph("2. Data integrity & limitations", section_style))
    if data_quality:
        story.append(
            Paragraph(
                f"Coverage in selected window: <b>{data_quality.get('coverage_pct', 0):.0f}%</b> "
                f"({data_quality.get('observed_years', 0)} / "
                f"{data_quality.get('expected_years', 0)} years). "
                f"Quality label: <b>{data_quality.get('quality_label', 'N/A')}</b>. "
                f"Latest observation: <b>{data_quality.get('latest_year', 'N/A')}</b> "
                f"({data_quality.get('staleness_label', 'N/A')}). "
                f"Missing years: {data_quality.get('gap_count', 0)}.",
                body_style,
            )
        )
        for note in (data_quality.get("limitations") or [])[:4]:
            story.append(Paragraph(f"• {note}", body_style))
    else:
        story.append(
            Paragraph(
                "Validate all figures against official national statistics before policy use.",
                body_style,
            )
        )

    # Equity
    if equity_gap and equity_gap.get("available"):
        story.append(
            Paragraph(
                f"3. Leave-no-one-behind lens ({equity_dimension or 'Equity'})",
                section_style,
            )
        )
        story.append(
            Paragraph(
                f"Latest comparable gap: <b>{format_number(equity_gap.get('gap'))}</b> "
                f"between <b>{equity_gap.get('lead_group')}</b> and "
                f"<b>{equity_gap.get('lag_group')}</b>"
                + (
                    f" ({format_percent(equity_gap.get('gap_pct'))} relative)."
                    if equity_gap.get("gap_pct") is not None
                    else "."
                )
                + (
                    f" Reference year: {equity_gap.get('common_year')}."
                    if equity_gap.get("common_year")
                    else ""
                ),
                body_style,
            )
        )

    # Scenario
    if scenario and scenario.get("baseline_2030") is not None:
        story.append(Paragraph("4. Illustrative 2030 scenario", section_style))
        story.append(
            Paragraph(
                f"Baseline linear path to 2030: <b>{format_number(scenario.get('baseline_2030'))}</b>. "
                f"Adjusted path: <b>{format_number(scenario.get('adjusted_2030'))}</b>. "
                f"{scenario.get('note', '')}",
                body_style,
            )
        )

    # Chart
    if chart_fig is not None:
        story.append(Paragraph("Trend visualization", section_style))
        try:
            img_bytes = chart_fig.to_image(format="png", width=720, height=360, scale=2)
            img = Image(io.BytesIO(img_bytes), width=6.5 * inch, height=3.25 * inch)
            story.append(img)
        except Exception:
            story.append(
                Paragraph(
                    "<i>Chart could not be embedded (install kaleido for static export).</i>",
                    meta_style,
                )
            )

    # AI insight
    story.append(Paragraph("5. AI-assisted policy notes", section_style))
    if ai_insight and ai_insight.strip():
        cleaned = ai_insight.replace("\n", "<br/>")
        for heading in (
            "Executive Summary",
            "Why it Matters",
            "Potential Challenge",
            "Recommended Action",
            "Confidence",
        ):
            cleaned = (
                cleaned.replace(f"**{heading}**", f"<b>{heading}</b>")
                .replace(f"## {heading}", f"<b>{heading}</b>")
                .replace(f"### {heading}", f"<b>{heading}</b>")
                .replace(f"{heading}:", f"<b>{heading}:</b>")
            )
        story.append(Paragraph(cleaned, body_style))
    else:
        story.append(
            Paragraph(
                "<i>No AI insight was attached. Generate one in the app before export.</i>",
                meta_style,
            )
        )

    story.append(Spacer(1, 10))
    story.append(
        HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor("#E1E8ED"),
            spaceBefore=4,
            spaceAfter=6,
        )
    )
    story.append(
        Paragraph(
            "AI4SDG Insights · World Bank Open Data · Google Gemini · "
            "Scenarios and risk scores are heuristic. "
            "Cross-check with national SDG reports and UNDP country office analysis "
            "before any operational use.",
            footer_style,
        )
    )

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


def risk_score_color(score: float, dark_mode: bool = False) -> str:
    """Return a hex colour for a risk score (0–100, higher = more risk)."""
    if score < 35:
        return "#2E7D32" if not dark_mode else "#66BB6A"
    if score < 65:
        return "#ED6C02" if not dark_mode else "#FFA726"
    return "#D32F2F" if not dark_mode else "#EF5350"


def risk_score_label(score: float) -> str:
    """Human label for SDG risk score."""
    if score < 35:
        return "Low Risk"
    if score < 65:
        return "Moderate Risk"
    return "Elevated Risk"
