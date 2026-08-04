"""
AI4SDG Insights — Main Streamlit Application

AI-powered Sustainable Development Analytics Platform.
World Bank Open Data + Gemini AI policy insights.
"""

from __future__ import annotations

import streamlit as st

from ai_insights import format_insight_html, generate_ai_insight
from analytics import (
    build_country_office_briefing,
    compute_data_quality,
    compute_equity_gap,
    compute_sdg_risk_score,
    compute_statistics,
    forecast_linear,
    project_to_2030,
    summary_table,
)
from data_loader import (
    clear_data_cache,
    load_comparison_data,
    load_country_indicator,
    load_equity_series,
)
from sdg_mapping import (
    get_country_list,
    get_equity_lens,
    get_indicator_list,
    get_sdg_info,
    get_unit,
    search_indicators,
)
from utils import (
    COUNTRY_COLORS,
    build_comparison_chart,
    build_equity_chart,
    build_line_chart,
    build_scenario_chart,
    build_sparkline,
    dataframe_to_csv_bytes,
    format_number,
    format_percent,
    generate_pdf_report,
    inject_custom_css,
    risk_score_color,
    risk_score_label,
)


# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AI4SDG Insights",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)


def init_session_state() -> None:
    """Initialise session state defaults."""
    defaults = {
        "dark_mode": False,
        "ai_insight_text": "",
        "ai_insight_meta": {},
        "last_refresh": None,
        "show_forecast": True,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_sidebar() -> dict:
    """
    Render sidebar controls and return the current selection context.
    """
    with st.sidebar:
        st.markdown("### 🌍 AI4SDG Insights")
        st.caption("Sustainable Development Analytics")
        st.markdown("---")

        # Theme toggle
        dark_mode = st.toggle(
            "🌙 Dark Mode",
            value=st.session_state.dark_mode,
            help="Switch between light and dark themes",
        )
        st.session_state.dark_mode = dark_mode

        st.markdown("#### 📍 Country")
        countries = get_country_list()
        country = st.selectbox(
            "Select country",
            options=countries,
            index=0,
            label_visibility="collapsed",
        )

        st.markdown("#### 📊 Indicator")
        search_q = st.text_input(
            "🔍 Search indicators",
            placeholder="e.g. health, climate, education…",
            help="Filter indicators by name or SDG theme",
        )
        filtered = search_indicators(search_q)
        if not filtered:
            st.warning("No indicators match your search. Showing all.")
            filtered = get_indicator_list()

        indicator = st.selectbox(
            "Select indicator",
            options=filtered,
            index=0,
            label_visibility="collapsed",
        )

        st.markdown("#### 📅 Year Range")
        year_range = st.slider(
            "Period",
            min_value=1990,
            max_value=2024,
            value=(2000, 2024),
            help="Filter World Bank series by year",
        )

        st.session_state.show_forecast = st.checkbox(
            "📈 Show 5-year forecast",
            value=st.session_state.show_forecast,
            help="Overlay linear regression forecast on the trend chart",
        )

        growth_adj = st.slider(
            "2030 scenario growth adjustment (%)",
            min_value=-50,
            max_value=50,
            value=0,
            step=5,
            help=(
                "Shifts the implied annual change vs the historical linear trend "
                "(e.g. -20 = 20% slower progress)."
            ),
        )

        st.markdown("---")
        st.markdown("#### ⚡ Actions")

        col_a, col_b = st.columns(2)
        with col_a:
            refresh = st.button("🔄 Refresh", use_container_width=True)
        with col_b:
            generate_ai = st.button(
                "✨ AI Insight",
                use_container_width=True,
                type="primary",
            )

        download_report = st.button(
            "📥 Prepare Report",
            use_container_width=True,
            help="Prepare CSV and PDF downloads in the main panel",
        )

        if refresh:
            clear_data_cache()
            st.session_state.ai_insight_text = ""
            st.toast("Data cache cleared. Reloading…", icon="🔄")
            st.rerun()

        st.markdown("---")
        st.caption("Data: World Bank Open Data API")
        st.caption("AI: Google Gemini")
        st.caption("© AI4SDG Insights")

    return {
        "country": country,
        "indicator": indicator,
        "start_year": year_range[0],
        "end_year": year_range[1],
        "generate_ai": generate_ai,
        "download_report": download_report,
        "dark_mode": dark_mode,
        "growth_adj": growth_adj,
    }


def render_header(sdg_info: dict | None = None, country: str = "", indicator: str = "") -> None:
    """Render application hero banner."""
    sdg_code = (sdg_info or {}).get("sdg_code", "SDG Analytics")
    goal = (sdg_info or {}).get("goal_title", "Sustainable Development")
    icon = (sdg_info or {}).get("icon", "🌍")
    st.markdown(
        f"""
        <div class="hero-banner">
            <div class="hero-kicker">Portfolio · South Asia · Open Data + AI</div>
            <div class="hero-title">{icon} AI4SDG Insights</div>
            <p class="hero-subtitle">
                AI-powered Sustainable Development Analytics Platform —
                evidence-grounded dashboards for policy learning and internship portfolios.
            </p>
            <div class="hero-chip-row">
                <div class="hero-chip">World Bank Open Data</div>
                <div class="hero-chip">{sdg_code}</div>
                <div class="hero-chip">{goal}</div>
                <div class="hero-chip">{country or 'Select country'} · {indicator or 'Select indicator'}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_context_strip(country: str, indicator: str, quality: dict, unit: str) -> None:
    """Compact status pills under the hero."""
    st.markdown(
        f"""
        <div class="context-strip">
            <div class="context-pill"><span>Country</span> · {country}</div>
            <div class="context-pill"><span>Indicator</span> · {indicator}</div>
            <div class="context-pill"><span>Unit</span> · {unit or 'n/a'}</div>
            <div class="context-pill"><span>Data quality</span> · {quality.get('quality_label', 'N/A')}</div>
            <div class="context-pill"><span>Coverage</span> · {quality.get('coverage_pct', 0):.0f}%</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_country_office_briefing(briefing: dict) -> None:
    """Render four-card country office briefing (Streamlit columns = reliable layout)."""
    import html as html_lib

    st.markdown(
        '<div class="panel-title">🗂️ Country Office Briefing</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Deterministic 4-bullet brief from verified World Bank stats — "
        "no generative AI. Useful for interview demos."
    )
    items = list(briefing.items())
    # 2x2 grid via columns — avoids Streamlit HTML sanitizer stripping card CSS
    for row_start in range(0, len(items), 2):
        cols = st.columns(2)
        for col, (label, text) in zip(cols, items[row_start : row_start + 2]):
            with col:
                st.markdown(
                    f"""
                    <div class="briefing-card">
                        <div class="briefing-label">{html_lib.escape(label)}</div>
                        <p class="briefing-text">{html_lib.escape(text)}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def render_sdg_badge(indicator: str) -> None:
    """Render SDG mapping card for the selected indicator."""
    info = get_sdg_info(indicator)
    st.markdown(
        f"""
        <div class="sdg-badge">
            <div class="sdg-icon">{info['icon']}</div>
            <div>
                <div class="sdg-code">{info['sdg_code']} · Goal {info['sdg_number']}</div>
                <div class="sdg-title">{info['goal_title']}</div>
                <div class="sdg-desc">{info['description']}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_cards(stats: dict, unit: str) -> None:
    """Render four top-level KPI metrics."""
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            label="Latest Value",
            value=format_number(stats.get("latest_value")),
            delta=unit if unit else None,
            delta_color="off",
        )
    with c2:
        st.metric(
            label="Latest Year",
            value=str(stats.get("latest_year") or "N/A"),
        )
    with c3:
        growth = stats.get("growth_pct")
        st.metric(
            label="Growth %",
            value=format_percent(growth) if growth is not None else "N/A",
            delta=(
                "vs previous year"
                if growth is not None
                else None
            ),
            delta_color=(
                "normal"
                if growth is not None and growth >= 0
                else "inverse"
                if growth is not None
                else "off"
            ),
        )
    with c4:
        st.metric(
            label="Trend",
            value=stats.get("trend", "N/A"),
        )


def render_data_quality(quality: dict) -> None:
    """Render data integrity / limitations panel."""
    st.markdown(
        '<div class="panel-title">🔎 Data Integrity & Limitations</div>',
        unsafe_allow_html=True,
    )
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Coverage", f"{quality.get('coverage_pct', 0):.0f}%")
    with c2:
        st.metric(
            "Observed years",
            f"{quality.get('observed_years', 0)} / {quality.get('expected_years', 0)}",
        )
    with c3:
        st.metric("Quality", quality.get("quality_label", "N/A"))
    with c4:
        st.metric("Freshness", quality.get("staleness_label", "N/A"))

    missing = quality.get("missing_years") or []
    if missing:
        preview = ", ".join(str(y) for y in missing[:12])
        more = f" (+{len(missing) - 12} more)" if len(missing) > 12 else ""
        st.caption(f"Missing years in selected window: {preview}{more}")
    else:
        st.caption("No missing years in the selected window.")

    with st.expander("What this indicator cannot tell us", expanded=True):
        for note in quality.get("limitations") or []:
            st.markdown(f"- {note}")
        st.caption(
            "National aggregates often hide who is left behind. "
            "Use the equity lens below where disaggregated series exist."
        )


def render_equity_section(
    country: str,
    indicator: str,
    start_year: int,
    end_year: int,
    dark_mode: bool,
) -> dict:
    """Render leave-no-one-behind equity comparison when available."""
    st.markdown("---")
    st.markdown(
        '<div class="panel-title">🧭 Leave No One Behind — Equity Lens</div>',
        unsafe_allow_html=True,
    )

    lens = get_equity_lens(indicator)
    if not lens:
        st.info(
            f"**{indicator}** is shown as a national aggregate only. "
            "Try **Access to Electricity**, **Unemployment**, **Life Expectancy**, "
            "**Primary School Enrollment**, or **Population** for urban–rural or "
            "gender disaggregation."
        )
        return {"gap": None, "dimension": "", "series": {}}

    st.caption(
        f"**{lens['dimension']}** · {lens.get('sdg_link', '')} — {lens.get('narrative', '')}"
    )

    with st.spinner(f"Loading {lens['dimension'].lower()} series…"):
        series_map = load_equity_series(
            country,
            lens["series"],
            start_year=start_year,
            end_year=end_year,
        )

    available = {k: v for k, v in series_map.items() if v is not None and not v.empty}
    if len(available) < 1:
        st.warning(
            "Disaggregated series were unavailable for this country/period "
            "(API gaps or network timeout)."
        )
        return {"gap": None, "dimension": lens["dimension"], "series": series_map}

    color_map = {s["label"]: s.get("color", "#009EDB") for s in lens["series"]}
    fig = build_equity_chart(
        series_map=available,
        color_map=color_map,
        title=f"{indicator} — {lens['dimension']} ({country})",
        y_label=lens["dimension"],
        dark_mode=dark_mode,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})

    gap = compute_equity_gap(available)
    if gap.get("available"):
        g1, g2, g3 = st.columns(3)
        with g1:
            st.metric("Lead group", gap.get("lead_group", "—"))
        with g2:
            st.metric("Lagging group", gap.get("lag_group", "—"))
        with g3:
            st.metric(
                "Gap",
                format_number(gap.get("gap")),
                delta=format_percent(gap.get("gap_pct"))
                if gap.get("gap_pct") is not None
                else None,
                delta_color="off",
            )
        if gap.get("common_year"):
            st.caption(
                f"Gap calculated for common year **{gap['common_year']}** "
                "(preferring same-year comparison)."
            )
    else:
        st.caption("Not enough overlapping observations to compute a clean equity gap.")

    return {"gap": gap, "dimension": lens["dimension"], "series": series_map}


def render_scenario_section(
    df,
    indicator: str,
    country: str,
    unit: str,
    growth_adj: float,
    dark_mode: bool,
) -> dict:
    """Render illustrative 2030 scenario with growth adjustment slider value."""
    st.markdown("---")
    st.markdown(
        '<div class="panel-title">🎯 2030 Scenario Explorer</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Illustrative linear paths only — useful for briefing questions like "
        "*“what if progress slows/accelerates?”* Not an official projection."
    )

    scenario = project_to_2030(
        df,
        growth_adjustment_pct=float(growth_adj),
        indicator_name=indicator,
    )
    if scenario.get("baseline_2030") is None and scenario.get("latest_year") is None:
        st.info(scenario.get("note", "Insufficient data for a 2030 scenario."))
        return scenario

    s1, s2, s3 = st.columns(3)
    with s1:
        st.metric(
            f"Latest ({scenario.get('latest_year', '—')})",
            format_number(scenario.get("latest_value")),
        )
    with s2:
        st.metric("Baseline 2030", format_number(scenario.get("baseline_2030")))
    with s3:
        label = f"Adjusted 2030 ({growth_adj:+.0f}% pace)"
        st.metric(label, format_number(scenario.get("adjusted_2030")))

    y_label = f"{indicator}" + (f" ({unit})" if unit else "")
    scen_fig = build_scenario_chart(
        historical_df=df,
        baseline_df=scenario.get("baseline_df"),
        adjusted_df=scenario.get("adjusted_df"),
        title=f"{indicator} — path to 2030 ({country})",
        y_label=y_label,
        dark_mode=dark_mode,
    )
    st.plotly_chart(scen_fig, use_container_width=True, config={"displaylogo": False})
    if scenario.get("r_squared") is not None:
        st.caption(
            f"{scenario.get('note', '')} Historical fit R² = {scenario['r_squared']:.3f}."
        )
    else:
        st.caption(scenario.get("note", ""))

    return scenario


def render_risk_score(risk: dict, dark_mode: bool) -> None:
    """Render SDG risk score pill and factors."""
    score = risk.get("risk_score")
    if score is None:
        return

    color = risk_score_color(score, dark_mode)
    label = risk.get("risk_label") or risk_score_label(score)
    confidence = risk.get("confidence", "N/A")

    st.markdown(
        f"""
        <div class="panel">
            <div class="panel-title">🛡️ SDG Risk Score</div>
            <p style="margin:0.4rem 0 0.8rem 0;">
                <span class="risk-pill" style="background:{color}22;color:{color};border:1px solid {color};">
                    {score:.0f} / 100 — {label}
                </span>
                &nbsp;&nbsp;<span style="opacity:0.7;font-size:0.85rem;">
                    Assessment confidence: <b>{confidence}</b>
                </span>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Risk assessment factors", expanded=False):
        for factor in risk.get("factors", []):
            st.markdown(f"- {factor}")
        st.caption(
            "Heuristic score based on recent direction, volatility, and data coverage. "
            "Not an official UNDP or UN assessment."
        )


def render_ai_section(
    country: str,
    indicator: str,
    unit: str,
    stats: dict,
    sdg_info: dict,
    risk: dict,
    trigger: bool,
) -> None:
    """Generate and/or display AI policy insights."""
    st.markdown(
        '<div class="panel-title">🤖 AI Policy Insight</div>',
        unsafe_allow_html=True,
    )

    if trigger:
        with st.spinner("Consulting Gemini as a UNDP policy analyst…"):
            result = generate_ai_insight(
                country=country,
                indicator=indicator,
                unit=unit,
                stats=stats,
                sdg_info=sdg_info,
                risk=risk,
            )

        if result["success"]:
            st.session_state.ai_insight_text = result["text"]
            st.session_state.ai_insight_meta = {
                "country": country,
                "indicator": indicator,
            }
            if result.get("incomplete"):
                st.toast("Insight generated but may be incomplete — try again", icon="⚠️")
            else:
                st.toast("AI insight generated successfully", icon="✨")
        else:
            st.session_state.ai_insight_text = ""
            err_type = result.get("error_type")
            if err_type == "quota":
                st.error(result["error"])
                st.toast("API quota exceeded", icon="⚠️")
            elif err_type == "missing_key":
                st.warning(result["error"])
            else:
                st.error(result["error"])

    text = st.session_state.ai_insight_text
    meta = st.session_state.ai_insight_meta

    # Invalidate insight if selection changed
    if text and meta:
        if meta.get("country") != country or meta.get("indicator") != indicator:
            st.info(
                "Selection changed. Click **✨ AI Insight** in the sidebar to "
                "generate a fresh brief for the current country and indicator."
            )
            return

    if text:
        if len(text.strip()) < 120:
            st.warning(
                "The previous AI reply looked truncated. Click **✨ AI Insight** "
                "again to regenerate a full brief."
            )
        html_body = format_insight_html(text)
        st.markdown(
            f"""
            <div class="ai-insight">
                <div class="ai-header">✨ UNDP-style Policy Brief</div>
                {html_body}
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander("View raw AI text", expanded=False):
            st.markdown(text)
    else:
        st.markdown(
            """
            <div class="panel">
                <p style="margin:0;opacity:0.75;">
                    Click <b>✨ AI Insight</b> in the sidebar to generate a cautious,
                    evidence-based policy brief grounded in the statistics above.
                    Requires <code>GEMINI_API_KEY</code> in Streamlit secrets.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_downloads(
    df,
    country: str,
    indicator: str,
    stats: dict,
    sdg_info: dict,
    unit: str,
    chart_fig,
    prepare: bool,
    data_quality: dict | None = None,
    scenario: dict | None = None,
    equity_info: dict | None = None,
) -> None:
    """Render CSV and SDG Progress Note PDF downloads."""
    st.markdown(
        '<div class="panel-title">📥 Download SDG Progress Note</div>',
        unsafe_allow_html=True,
    )

    if not prepare and "report_ready" not in st.session_state:
        st.caption("Click **📥 Prepare Report** in the sidebar to enable downloads.")
        return

    if prepare:
        st.session_state.report_ready = True
        st.toast("Progress note ready for download", icon="📥")

    export_df = df.copy()
    export_df["Country_Selected"] = country
    export_df["Indicator_Selected"] = indicator

    csv_bytes = dataframe_to_csv_bytes(export_df)
    equity_gap = (equity_info or {}).get("gap")
    equity_dimension = (equity_info or {}).get("dimension", "")

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="📄 Download CSV",
            data=csv_bytes,
            file_name=f"AI4SDG_{country}_{indicator.replace(' ', '_')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col2:
        try:
            pdf_bytes = generate_pdf_report(
                country=country,
                indicator=indicator,
                stats={
                    **stats,
                    "risk_score": st.session_state.get("last_risk_score"),
                },
                sdg_info=sdg_info,
                ai_insight=st.session_state.ai_insight_text or "",
                chart_fig=chart_fig,
                unit=unit,
                data_quality=data_quality,
                scenario=scenario,
                equity_gap=equity_gap,
                equity_dimension=equity_dimension,
            )
            st.download_button(
                label="📑 Download SDG Progress Note (PDF)",
                data=pdf_bytes,
                file_name=(
                    f"SDG_Progress_Note_{country}_{indicator.replace(' ', '_')}.pdf"
                ),
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as exc:
            st.warning(
                f"PDF generation unavailable ({exc}). CSV download still works. "
                "Install reportlab and kaleido for full PDF support."
            )


def render_footer() -> None:
    """Application footer."""
    st.markdown(
        """
        <div class="app-footer">
            <strong>AI4SDG Insights</strong> · AI-powered Sustainable Development Analytics<br/>
            Data courtesy of the
            <a href="https://data.worldbank.org/" target="_blank">World Bank Open Data</a>
            · AI analysis powered by Google Gemini<br/>
            Built for portfolio &amp; educational use · Not an official UN or UNDP product<br/>
            Indicators mapped to the
            <a href="https://sdgs.un.org/goals" target="_blank">UN Sustainable Development Goals</a>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    """Application entry point."""
    init_session_state()
    ctx = render_sidebar()

    country = ctx["country"]
    indicator = ctx["indicator"]
    unit = get_unit(indicator)
    sdg_info = get_sdg_info(indicator)
    accent = sdg_info.get("color", "#009EDB")

    # Inject theme CSS after sidebar so dark_mode + SDG accent are known
    st.markdown(
        inject_custom_css(ctx["dark_mode"], accent=accent),
        unsafe_allow_html=True,
    )

    render_header(sdg_info=sdg_info, country=country, indicator=indicator)

    # ---- Load primary series ----
    with st.spinner(f"Loading {indicator} data for {country}…"):
        df, error = load_country_indicator(
            country,
            indicator,
            start_year=ctx["start_year"],
            end_year=ctx["end_year"],
        )

    if error and df.empty:
        st.error(error)
        st.info(
            "Try another indicator, widen the year range, or click **Refresh** "
            "after checking your network connection."
        )
        render_footer()
        return

    if error:
        st.warning(error)

    stats = compute_statistics(df)
    risk = compute_sdg_risk_score(df, indicator, stats)
    st.session_state.last_risk_score = risk.get("risk_score")
    quality = compute_data_quality(
        df,
        start_year=ctx["start_year"],
        end_year=ctx["end_year"],
        indicator_name=indicator,
    )

    render_context_strip(country, indicator, quality, unit)

    # ---- SDG mapping ----
    render_sdg_badge(indicator)

    # ---- KPI cards + sparkline ----
    st.markdown(
        f"**{country}** · **{indicator}**"
        + (f" · _{unit}_" if unit else "")
    )
    k1, k2 = st.columns([3.2, 1])
    with k1:
        render_kpi_cards(stats, unit)
    with k2:
        st.caption("Recent trend")
        spark = build_sparkline(
            df.tail(15),
            color=accent,
            dark_mode=ctx["dark_mode"],
        )
        st.plotly_chart(spark, use_container_width=True, config={"displayModeBar": False})
    st.markdown("")

    # ---- Data integrity ----
    render_data_quality(quality)

    # ---- Risk score ----
    render_risk_score(risk, ctx["dark_mode"])

    # ---- Trend chart + forecast ----
    forecast_df = None
    r_sq = None
    if st.session_state.show_forecast:
        forecast_df, r_sq = forecast_linear(df, periods=5)

    chart_title = f"{indicator} — {country}"
    y_label = f"{indicator}" + (f" ({unit})" if unit else "")
    fig = build_line_chart(
        df=df,
        title=chart_title,
        y_label=y_label,
        color=COUNTRY_COLORS.get(country, accent),
        dark_mode=ctx["dark_mode"],
        forecast_df=forecast_df if st.session_state.show_forecast else None,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": True,
            "displaylogo": False,
            "modeBarButtonsToAdd": ["downloadImage"],
            "toImageButtonOptions": {
                "format": "png",
                "filename": f"AI4SDG_{country}_{indicator}",
                "height": 500,
                "width": 900,
                "scale": 2,
            },
        },
    )

    if forecast_df is not None and not forecast_df.empty and r_sq is not None:
        st.caption(
            f"Dashed line: linear regression forecast (next 5 years). "
            f"Model R² = {r_sq:.3f}. Forecasts are illustrative only and "
            "assume continuation of the historical linear trend."
        )

    # ---- Equity lens ----
    equity_info = render_equity_section(
        country=country,
        indicator=indicator,
        start_year=ctx["start_year"],
        end_year=ctx["end_year"],
        dark_mode=ctx["dark_mode"],
    )

    # ---- 2030 scenario ----
    scenario = render_scenario_section(
        df=df,
        indicator=indicator,
        country=country,
        unit=unit,
        growth_adj=ctx.get("growth_adj", 0),
        dark_mode=ctx["dark_mode"],
    )

    # ---- Country office briefing ----
    st.markdown("---")
    briefing = build_country_office_briefing(
        country=country,
        indicator=indicator,
        unit=unit,
        stats=stats,
        sdg_info=sdg_info,
        quality=quality,
        equity_gap=(equity_info or {}).get("gap"),
        scenario=scenario,
    )
    render_country_office_briefing(briefing)

    # ---- Country comparison ----
    st.markdown("---")
    st.markdown(
        '<div class="panel-title">🌐 South Asia Peer Review</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        f"Comparing **{indicator}** across Pakistan, India, and Bangladesh — "
        "shared regional development context, different trajectories."
    )

    with st.spinner("Loading comparison data…"):
        comparison = load_comparison_data(
            get_country_list(),
            indicator,
            start_year=ctx["start_year"],
            end_year=ctx["end_year"],
        )

    # Highlight if any series missing
    missing = [c for c, d in comparison.items() if d is None or d.empty]
    if missing:
        st.warning(
            "Limited or missing data for: " + ", ".join(missing)
        )

    comp_fig = build_comparison_chart(
        data_by_country=comparison,
        title=f"{indicator} — South Asia Peer Review",
        y_label=y_label,
        dark_mode=ctx["dark_mode"],
    )
    st.plotly_chart(
        comp_fig,
        use_container_width=True,
        config={"displayModeBar": True, "displaylogo": False},
    )

    # ---- Analytics expander ----
    with st.expander("📈 Summary Statistics", expanded=False):
        left, right = st.columns([1.2, 1])
        with left:
            st.dataframe(
                summary_table(stats),
                use_container_width=True,
                hide_index=True,
            )
        with right:
            st.markdown("**Interpretation notes**")
            st.markdown(
                f"""
                - **Latest value** reflects the most recent non-missing observation
                  ({stats.get('latest_year', 'N/A')}).
                - **Growth %** compares the latest value to the previous available year.
                - **Overall growth** spans {stats.get('first_year', '—')} to
                  {stats.get('last_year', '—')}.
                - World Bank series may contain gaps; missing years are excluded
                  from calculations.
                """
            )
            if forecast_df is not None and not forecast_df.empty:
                st.markdown("**Forecast preview**")
                st.dataframe(
                    forecast_df.assign(
                        Value=forecast_df["Value"].map(lambda v: format_number(v))
                    ),
                    use_container_width=True,
                    hide_index=True,
                )

    # ---- AI insights ----
    st.markdown("---")
    render_ai_section(
        country=country,
        indicator=indicator,
        unit=unit,
        stats=stats,
        sdg_info=sdg_info,
        risk=risk,
        trigger=ctx["generate_ai"],
    )

    # ---- Downloads ----
    st.markdown("---")
    render_downloads(
        df=df,
        country=country,
        indicator=indicator,
        stats=stats,
        sdg_info=sdg_info,
        unit=unit,
        chart_fig=fig,
        prepare=ctx["download_report"],
        data_quality=quality,
        scenario=scenario,
        equity_info=equity_info,
    )

    render_footer()


if __name__ == "__main__":
    main()
