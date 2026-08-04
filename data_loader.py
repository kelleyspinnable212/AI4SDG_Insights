"""
World Bank Open Data loader for AI4SDG Insights.

Fetches indicator time series via the World Bank API, cleans the data,
and caches responses for performance.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import pandas as pd
import requests
import streamlit as st

from sdg_mapping import get_country_code, get_wb_code

WB_API_BASE = "https://api.worldbank.org/v2"
DEFAULT_TIMEOUT = 25
MAX_PER_PAGE = 1000


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_indicator_data(
    country_code: str,
    indicator_code: str,
    start_year: int = 1990,
    end_year: int = 2024,
) -> pd.DataFrame:
    """
    Fetch a single country-indicator time series from the World Bank API.

    Returns a cleaned DataFrame with columns: Year, Value, Country, Indicator.
    Empty DataFrame on failure or no data.
    """
    url = (
        f"{WB_API_BASE}/country/{country_code}/indicator/{indicator_code}"
        f"?format=json&per_page={MAX_PER_PAGE}"
        f"&date={start_year}:{end_year}"
    )

    try:
        response = requests.get(url, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        payload = response.json()
    except requests.exceptions.Timeout:
        return pd.DataFrame(columns=["Year", "Value", "Country", "Indicator"])
    except requests.exceptions.RequestException:
        return pd.DataFrame(columns=["Year", "Value", "Country", "Indicator"])
    except ValueError:
        # JSON decode error
        return pd.DataFrame(columns=["Year", "Value", "Country", "Indicator"])

    if not isinstance(payload, list) or len(payload) < 2:
        return pd.DataFrame(columns=["Year", "Value", "Country", "Indicator"])

    records = payload[1]
    if not records:
        return pd.DataFrame(columns=["Year", "Value", "Country", "Indicator"])

    rows: List[Dict] = []
    for item in records:
        if item is None:
            continue
        year_raw = item.get("date")
        value = item.get("value")
        if year_raw is None or value is None:
            continue
        try:
            year = int(year_raw)
        except (TypeError, ValueError):
            continue
        rows.append(
            {
                "Year": year,
                "Value": float(value),
                "Country": item.get("country", {}).get("value", country_code),
                "Indicator": item.get("indicator", {}).get("value", indicator_code),
            }
        )

    if not rows:
        return pd.DataFrame(columns=["Year", "Value", "Country", "Indicator"])

    df = pd.DataFrame(rows)
    df = df.dropna(subset=["Value"])
    df["Year"] = df["Year"].astype(int)
    df = df.sort_values("Year").reset_index(drop=True)
    return df


def load_country_indicator(
    country_name: str,
    indicator_name: str,
    start_year: int = 1990,
    end_year: int = 2024,
) -> Tuple[pd.DataFrame, Optional[str]]:
    """
    High-level loader using display names.

    Returns (dataframe, error_message). error_message is None on success.
    """
    country_code = get_country_code(country_name)
    indicator_code = get_wb_code(indicator_name)

    if not country_code:
        return (
            pd.DataFrame(columns=["Year", "Value", "Country", "Indicator"]),
            f"Unknown country: {country_name}",
        )
    if not indicator_code:
        return (
            pd.DataFrame(columns=["Year", "Value", "Country", "Indicator"]),
            f"Unknown indicator: {indicator_name}",
        )

    df = fetch_indicator_data(country_code, indicator_code, start_year, end_year)

    if df.empty:
        return (
            df,
            (
                f"No data returned for {indicator_name} in {country_name}. "
                "The World Bank API may be unavailable or the series has gaps."
            ),
        )
    return df, None


def load_comparison_data(
    countries: List[str],
    indicator_name: str,
    start_year: int = 1990,
    end_year: int = 2024,
) -> Dict[str, pd.DataFrame]:
    """
    Load the same indicator for multiple countries.

    Returns a dict keyed by country display name.
    """
    result: Dict[str, pd.DataFrame] = {}
    for country in countries:
        df, _ = load_country_indicator(country, indicator_name, start_year, end_year)
        result[country] = df
    return result


def load_equity_series(
    country_name: str,
    series_defs: List[Dict],
    start_year: int = 1990,
    end_year: int = 2024,
) -> Dict[str, pd.DataFrame]:
    """
    Load disaggregated equity series for a country.

    series_defs: list of dicts with keys label, code (and optional color).
    """
    country_code = get_country_code(country_name)
    result: Dict[str, pd.DataFrame] = {}
    if not country_code:
        return result

    for item in series_defs:
        label = item.get("label", item.get("code", "Series"))
        code = item.get("code")
        if not code:
            continue
        df = fetch_indicator_data(country_code, code, start_year, end_year)
        result[label] = df
    return result


def clear_data_cache() -> None:
    """Clear Streamlit cached World Bank responses."""
    fetch_indicator_data.clear()
