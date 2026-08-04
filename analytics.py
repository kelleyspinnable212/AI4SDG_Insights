"""
Analytics module for AI4SDG Insights.

Computes summary statistics, growth, trends, forecasts, and SDG risk scores.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from utils import trend_label


def compute_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute core analytics for an indicator time series.

    Expected columns: Year, Value.
    """
    empty: Dict[str, Any] = {
        "latest_value": None,
        "previous_value": None,
        "latest_year": None,
        "previous_year": None,
        "growth_pct": None,
        "trend": "Insufficient data",
        "average": None,
        "minimum": None,
        "maximum": None,
        "std_dev": None,
        "count": 0,
        "first_year": None,
        "last_year": None,
        "overall_growth_pct": None,
    }

    if df is None or df.empty or "Value" not in df.columns:
        return empty

    clean = df.dropna(subset=["Value"]).sort_values("Year").reset_index(drop=True)
    if clean.empty:
        return empty

    values = clean["Value"].astype(float)
    years = clean["Year"].astype(int)

    latest_value = float(values.iloc[-1])
    latest_year = int(years.iloc[-1])
    previous_value = float(values.iloc[-2]) if len(values) >= 2 else None
    previous_year = int(years.iloc[-2]) if len(years) >= 2 else None

    growth_pct = None
    if previous_value is not None and previous_value != 0:
        growth_pct = ((latest_value - previous_value) / abs(previous_value)) * 100.0

    first_value = float(values.iloc[0])
    overall_growth_pct = None
    if first_value != 0 and len(values) >= 2:
        overall_growth_pct = ((latest_value - first_value) / abs(first_value)) * 100.0

    return {
        "latest_value": latest_value,
        "previous_value": previous_value,
        "latest_year": latest_year,
        "previous_year": previous_year,
        "growth_pct": growth_pct,
        "trend": trend_label(growth_pct),
        "average": float(values.mean()),
        "minimum": float(values.min()),
        "maximum": float(values.max()),
        "std_dev": float(values.std(ddof=0)) if len(values) > 1 else 0.0,
        "count": int(len(values)),
        "first_year": int(years.iloc[0]),
        "last_year": latest_year,
        "overall_growth_pct": overall_growth_pct,
    }


def forecast_linear(
    df: pd.DataFrame,
    periods: int = 5,
) -> Tuple[pd.DataFrame, Optional[float]]:
    """
    Forecast the next `periods` years using ordinary least squares regression.

    Returns (forecast_df with Year/Value, r_squared) or (empty df, None).
    """
    empty = pd.DataFrame(columns=["Year", "Value"])

    if df is None or df.empty or len(df.dropna(subset=["Value"])) < 3:
        return empty, None

    clean = df.dropna(subset=["Value"]).sort_values("Year").reset_index(drop=True)
    X = clean[["Year"]].values.astype(float)
    y = clean["Value"].values.astype(float)

    model = LinearRegression()
    model.fit(X, y)
    r_squared = float(model.score(X, y))

    last_year = int(clean["Year"].iloc[-1])
    future_years = np.arange(last_year + 1, last_year + 1 + periods).reshape(-1, 1)
    predictions = model.predict(future_years)

    forecast_df = pd.DataFrame(
        {
            "Year": future_years.flatten().astype(int),
            "Value": predictions.astype(float),
        }
    )
    return forecast_df, r_squared


# Indicators where a decrease is generally desirable for development outcomes
LOWER_IS_BETTER = {"Unemployment", "CO₂ Emissions"}


def compute_sdg_risk_score(
    df: pd.DataFrame,
    indicator_name: str,
    stats: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Compute a heuristic SDG risk score (0–100, higher = more concern).

    Factors:
    - Direction of recent growth relative to whether higher/lower is better
    - Volatility (coefficient of variation)
    - Data coverage gaps
    """
    if stats is None:
        stats = compute_statistics(df)

    if not stats or stats.get("count", 0) < 2:
        return {
            "risk_score": None,
            "risk_label": "Insufficient data",
            "confidence": "Low",
            "factors": ["Not enough observations to assess risk."],
        }

    lower_better = indicator_name in LOWER_IS_BETTER
    growth = stats.get("growth_pct")
    factors: List[str] = []

    # Direction component (0–40)
    direction_score = 20.0
    if growth is not None:
        if lower_better:
            # Rising unemployment / emissions = higher risk
            if growth > 2:
                direction_score = 38.0
                factors.append("Recent increase may warrant closer monitoring.")
            elif growth > 0:
                direction_score = 28.0
                factors.append("Slight recent increase observed.")
            elif growth < -2:
                direction_score = 8.0
                factors.append("Recent decline aligns with favourable direction.")
            else:
                direction_score = 15.0
                factors.append("Recent change is relatively modest.")
        else:
            # Falling population access / GDP / etc. = higher risk
            if growth < -2:
                direction_score = 38.0
                factors.append("Recent decline may warrant closer monitoring.")
            elif growth < 0:
                direction_score = 28.0
                factors.append("Slight recent decline observed.")
            elif growth > 2:
                direction_score = 8.0
                factors.append("Recent improvement aligns with favourable direction.")
            else:
                direction_score = 15.0
                factors.append("Recent change is relatively modest.")

    # Volatility component (0–35)
    avg = stats.get("average") or 0
    std = stats.get("std_dev") or 0
    cv = (std / abs(avg)) if avg else 0
    if cv > 0.4:
        vol_score = 32.0
        factors.append("High historical volatility increases uncertainty.")
    elif cv > 0.2:
        vol_score = 20.0
        factors.append("Moderate historical volatility.")
    else:
        vol_score = 8.0
        factors.append("Relatively stable historical pattern.")

    # Coverage component (0–25)
    count = stats.get("count", 0)
    span = (stats.get("last_year") or 0) - (stats.get("first_year") or 0) + 1
    coverage_ratio = count / span if span > 0 else 0
    if coverage_ratio < 0.5:
        cov_score = 22.0
        factors.append("Sparse data coverage reduces confidence.")
    elif coverage_ratio < 0.8:
        cov_score = 12.0
        factors.append("Partial data coverage across the period.")
    else:
        cov_score = 5.0
        factors.append("Good data coverage across the period.")

    risk = min(100.0, max(0.0, direction_score + vol_score + cov_score))

    if risk < 35:
        label = "Low Risk"
    elif risk < 65:
        label = "Moderate Risk"
    else:
        label = "Elevated Risk"

    # Confidence based on sample size and R-style coverage
    if count >= 20 and coverage_ratio >= 0.8:
        confidence = "High"
    elif count >= 10:
        confidence = "Moderate"
    else:
        confidence = "Low"

    return {
        "risk_score": round(risk, 1),
        "risk_label": label,
        "confidence": confidence,
        "factors": factors,
    }


def summary_table(stats: Dict[str, Any]) -> pd.DataFrame:
    """Convert statistics dict into a two-column display DataFrame."""
    from utils import format_number, format_percent

    rows = [
        ("Observations", str(stats.get("count", 0))),
        ("Period", f"{stats.get('first_year', '—')} – {stats.get('last_year', '—')}"),
        ("Latest Value", format_number(stats.get("latest_value"))),
        ("Latest Year", str(stats.get("latest_year", "N/A"))),
        ("Previous Value", format_number(stats.get("previous_value"))),
        ("YoY Growth %", format_percent(stats.get("growth_pct"))),
        ("Overall Growth %", format_percent(stats.get("overall_growth_pct"))),
        ("Trend", str(stats.get("trend", "N/A"))),
        ("Average", format_number(stats.get("average"))),
        ("Minimum", format_number(stats.get("minimum"))),
        ("Maximum", format_number(stats.get("maximum"))),
        ("Std. Deviation", format_number(stats.get("std_dev"))),
    ]
    return pd.DataFrame(rows, columns=["Metric", "Value"])


def compute_data_quality(
    df: pd.DataFrame,
    start_year: int,
    end_year: int,
    indicator_name: str,
    limitations: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Assess data integrity for the selected window.

    Returns coverage, gap years, staleness, and limitation notes.
    """
    from sdg_mapping import get_indicator_limitations

    expected = list(range(int(start_year), int(end_year) + 1))
    empty = {
        "coverage_pct": 0.0,
        "observed_years": 0,
        "expected_years": len(expected),
        "missing_years": expected,
        "gap_count": len(expected),
        "latest_year": None,
        "years_since_update": None,
        "staleness_label": "No data",
        "quality_label": "Insufficient",
        "limitations": limitations or get_indicator_limitations(indicator_name),
    }

    if df is None or df.empty:
        return empty

    clean = df.dropna(subset=["Value"]).copy()
    if clean.empty:
        return empty

    observed = sorted({int(y) for y in clean["Year"].tolist()})
    observed_in_window = [y for y in observed if start_year <= y <= end_year]
    missing = [y for y in expected if y not in observed_in_window]
    coverage = (
        (len(observed_in_window) / len(expected)) * 100.0 if expected else 0.0
    )
    latest_year = max(observed_in_window) if observed_in_window else max(observed)
    # Reference "today" year for portfolio tooling (user_info date context may vary)
    reference_year = 2026
    years_since = reference_year - int(latest_year)

    if years_since <= 2:
        staleness = "Recent"
    elif years_since <= 5:
        staleness = "Moderately dated"
    else:
        staleness = "Stale"

    if coverage >= 85 and years_since <= 3:
        quality = "Strong"
    elif coverage >= 60 and years_since <= 6:
        quality = "Adequate"
    else:
        quality = "Limited"

    return {
        "coverage_pct": round(coverage, 1),
        "observed_years": len(observed_in_window),
        "expected_years": len(expected),
        "missing_years": missing,
        "gap_count": len(missing),
        "latest_year": int(latest_year),
        "years_since_update": int(years_since),
        "staleness_label": staleness,
        "quality_label": quality,
        "limitations": limitations or get_indicator_limitations(indicator_name),
    }


# Soft bounds so linear scenarios do not print impossible values (e.g. 105% access).
INDICATOR_VALUE_BOUNDS: Dict[str, tuple[Optional[float], Optional[float]]] = {
    "Internet Users": (0.0, 100.0),
    "Unemployment": (0.0, 100.0),
    "Access to Electricity": (0.0, 100.0),
    "Primary School Enrollment": (0.0, 150.0),  # gross enrollment can exceed 100
    "Life Expectancy": (20.0, 100.0),
    "Population": (0.0, None),
    "GDP": (0.0, None),
    "CO₂ Emissions": (0.0, None),
}


def _clamp_series(
    values: np.ndarray,
    lo: Optional[float],
    hi: Optional[float],
) -> tuple[np.ndarray, bool]:
    """Clamp array to [lo, hi]; return (clamped, whether any value changed)."""
    out = values.astype(float).copy()
    capped = False
    if lo is not None:
        mask = out < lo
        if mask.any():
            out[mask] = lo
            capped = True
    if hi is not None:
        mask = out > hi
        if mask.any():
            out[mask] = hi
            capped = True
    return out, capped


def project_to_2030(
    df: pd.DataFrame,
    growth_adjustment_pct: float = 0.0,
    target_year: int = 2030,
    indicator_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Project indicator values to a target year under baseline and adjusted paths.

    growth_adjustment_pct shifts the implied annual growth rate
    (e.g. -20 means 20% slower than the historical linear trend).
    Percentage-style indicators are clamped to plausible bounds.
    """
    empty = {
        "baseline_df": pd.DataFrame(columns=["Year", "Value"]),
        "adjusted_df": pd.DataFrame(columns=["Year", "Value"]),
        "baseline_2030": None,
        "adjusted_2030": None,
        "latest_value": None,
        "latest_year": None,
        "r_squared": None,
        "implied_annual_change": None,
        "was_capped": False,
        "note": "Insufficient history for a 2030 projection.",
    }

    if df is None or df.empty or len(df.dropna(subset=["Value"])) < 3:
        return empty

    clean = df.dropna(subset=["Value"]).sort_values("Year").reset_index(drop=True)
    X = clean[["Year"]].values.astype(float)
    y = clean["Value"].values.astype(float)

    model = LinearRegression()
    model.fit(X, y)
    r_squared = float(model.score(X, y))

    latest_year = int(clean["Year"].iloc[-1])
    latest_value = float(clean["Value"].iloc[-1])
    if latest_year >= target_year:
        return {
            **empty,
            "latest_value": latest_value,
            "latest_year": latest_year,
            "r_squared": r_squared,
            "baseline_2030": latest_value,
            "adjusted_2030": latest_value,
            "note": f"Series already reaches {latest_year}; no forward projection needed.",
        }

    future_years = np.arange(latest_year + 1, target_year + 1)
    baseline_vals = model.predict(future_years.reshape(-1, 1)).astype(float)

    # Approximate annual change from linear slope
    annual_change = float(model.coef_[0])
    factor = 1.0 + (growth_adjustment_pct / 100.0)
    adjusted_annual = annual_change * factor

    adjusted_vals = []
    cursor = latest_value
    for _ in future_years:
        cursor = cursor + adjusted_annual
        adjusted_vals.append(cursor)
    adjusted_arr = np.array(adjusted_vals, dtype=float)

    lo, hi = INDICATOR_VALUE_BOUNDS.get(indicator_name or "", (None, None))
    baseline_vals, capped_b = _clamp_series(baseline_vals, lo, hi)
    adjusted_arr, capped_a = _clamp_series(adjusted_arr, lo, hi)
    was_capped = capped_b or capped_a

    baseline_df = pd.DataFrame({"Year": future_years.astype(int), "Value": baseline_vals})
    adjusted_df = pd.DataFrame(
        {"Year": future_years.astype(int), "Value": adjusted_arr}
    )

    note = (
        "Illustrative linear scenario only — not a forecast commitment. "
        "Structural breaks, policy shifts, and shocks are not modelled."
    )
    if was_capped:
        bound_txt = []
        if lo is not None:
            bound_txt.append(str(lo))
        if hi is not None:
            bound_txt.append(str(hi))
        note += (
            f" Values were capped to a plausible range ({'–'.join(bound_txt)}) "
            "so the path does not exceed natural limits (e.g. 100% access)."
        )

    return {
        "baseline_df": baseline_df,
        "adjusted_df": adjusted_df,
        "baseline_2030": float(baseline_vals[-1]),
        "adjusted_2030": float(adjusted_arr[-1]),
        "latest_value": latest_value,
        "latest_year": latest_year,
        "r_squared": r_squared,
        "implied_annual_change": annual_change,
        "adjusted_annual_change": adjusted_annual,
        "was_capped": was_capped,
        "note": note,
    }


def compute_equity_gap(
    series_map: Dict[str, pd.DataFrame],
) -> Dict[str, Any]:
    """
    Compare latest overlapping values across equity groups.

    series_map: label -> DataFrame(Year, Value)
    """
    latest_by_label: Dict[str, Dict[str, Any]] = {}
    for label, sdf in series_map.items():
        if sdf is None or sdf.empty:
            continue
        clean = sdf.dropna(subset=["Value"]).sort_values("Year")
        if clean.empty:
            continue
        latest_by_label[label] = {
            "value": float(clean["Value"].iloc[-1]),
            "year": int(clean["Year"].iloc[-1]),
        }

    if len(latest_by_label) < 2:
        return {
            "available": False,
            "gap": None,
            "gap_pct": None,
            "lead_group": None,
            "lag_group": None,
            "latest_by_label": latest_by_label,
            "common_year": None,
        }

    # Prefer same-year comparison when possible
    year_sets = []
    for label, sdf in series_map.items():
        if sdf is None or sdf.empty:
            continue
        year_sets.append(set(sdf.dropna(subset=["Value"])["Year"].astype(int)))
    common_years = set.intersection(*year_sets) if year_sets else set()
    common_year = max(common_years) if common_years else None

    values_for_gap: Dict[str, float] = {}
    if common_year is not None:
        for label, sdf in series_map.items():
            row = sdf.loc[sdf["Year"] == common_year, "Value"]
            if not row.empty:
                values_for_gap[label] = float(row.iloc[0])
    else:
        values_for_gap = {k: v["value"] for k, v in latest_by_label.items()}

    if len(values_for_gap) < 2:
        return {
            "available": False,
            "gap": None,
            "gap_pct": None,
            "lead_group": None,
            "lag_group": None,
            "latest_by_label": latest_by_label,
            "common_year": common_year,
        }

    lead = max(values_for_gap, key=values_for_gap.get)
    lag = min(values_for_gap, key=values_for_gap.get)
    gap = values_for_gap[lead] - values_for_gap[lag]
    base = values_for_gap[lag]
    gap_pct = ((gap / abs(base)) * 100.0) if base else None

    return {
        "available": True,
        "gap": gap,
        "gap_pct": gap_pct,
        "lead_group": lead,
        "lag_group": lag,
        "values": values_for_gap,
        "latest_by_label": latest_by_label,
        "common_year": common_year,
    }


def _briefing_direction_phrase(indicator: str, growth: Optional[float]) -> str:
    """Neutral / polarity-aware wording (never call rising unemployment 'improving')."""
    if growth is None or (isinstance(growth, float) and pd.isna(growth)):
        return "direction unclear from YoY change"
    lower_better = indicator in LOWER_IS_BETTER
    if abs(growth) < 0.5:
        return "broadly stable versus the prior year"
    if growth > 0:
        if lower_better:
            return "rising — a concern for this indicator"
        return "rising versus the prior year"
    if lower_better:
        return "falling — a favourable direction for this indicator"
    return "falling versus the prior year"


def build_country_office_briefing(
    country: str,
    indicator: str,
    unit: str,
    stats: Dict[str, Any],
    sdg_info: Dict[str, Any],
    quality: Optional[Dict[str, Any]] = None,
    equity_gap: Optional[Dict[str, Any]] = None,
    scenario: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    """
    Build a four-bullet country-office style briefing from verified stats.

    No generative AI — deterministic and grounded in provided numbers only.
    """
    from utils import format_number, format_percent

    latest = format_number(stats.get("latest_value"))
    year = stats.get("latest_year", "N/A")
    growth = format_percent(stats.get("growth_pct"))
    direction = _briefing_direction_phrase(indicator, stats.get("growth_pct"))
    unit_bit = f" {unit}" if unit else ""

    situation = (
        f"In {year}, {country}'s {indicator.lower()} stood at {latest}{unit_bit}, "
        f"with a year-over-year change of {growth} ({direction})."
    )

    drivers = (
        f"This indicator maps to {sdg_info.get('sdg_code', 'the SDGs')} — "
        f"{sdg_info.get('goal_title', 'Sustainable Development')}. "
        f"Across {stats.get('first_year', '—')}–{stats.get('last_year', '—')}, "
        f"values ranged from {format_number(stats.get('minimum'))} to "
        f"{format_number(stats.get('maximum'))}{unit_bit}."
    )

    if equity_gap and equity_gap.get("available"):
        risk = (
            f"Equity lens: {equity_gap.get('lead_group')} leads "
            f"{equity_gap.get('lag_group')} by {format_number(equity_gap.get('gap'))}"
            + (
                f" ({format_percent(equity_gap.get('gap_pct'))})."
                if equity_gap.get("gap_pct") is not None
                else "."
            )
            + " Disparities may warrant leave-no-one-behind targeting."
        )
    elif quality:
        coverage = quality.get("coverage_pct")
        coverage_txt = f"{coverage:.0f}%" if isinstance(coverage, (int, float)) else "N/A"
        risk = (
            f"Data quality is labelled {quality.get('quality_label', 'N/A')} "
            f"({coverage_txt} coverage; "
            f"{quality.get('staleness_label', 'N/A')}). "
            "Gaps and national averages can hide excluded groups."
        )
    else:
        risk = (
            "National aggregates can mask subnational and group-based disparities; "
            "triangulate with household surveys and administrative data."
        )

    if scenario and scenario.get("baseline_2030") is not None:
        cap_note = (
            " Path values are bounded to a plausible range for this indicator."
            if scenario.get("was_capped")
            else ""
        )
        ask = (
            f"For planning discussions: a linear baseline path points to about "
            f"{format_number(scenario.get('baseline_2030'))}{unit_bit} by 2030 "
            f"(adjusted path: {format_number(scenario.get('adjusted_2030'))}{unit_bit})."
            f"{cap_note} Treat as illustrative only and stress-test against policy shifts."
        )
    else:
        ask = (
            "Ask: which population groups are not captured in the national average, "
            "and what complementary indicators would confirm progress toward the related SDG?"
        )

    return {
        "Situation": situation,
        "Why it matters": drivers,
        "Risk / watchpoint": risk,
        "Ask for next step": ask,
    }
