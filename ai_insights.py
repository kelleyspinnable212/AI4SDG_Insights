"""
Gemini AI policy insights for AI4SDG Insights.

Generates cautious UNDP-style analytical briefs from World Bank statistics.
Never hardcodes API keys — reads from st.secrets["GEMINI_API_KEY"].
"""

from __future__ import annotations

import html
import re
from typing import Any, Dict, Optional

import pandas as pd
import streamlit as st

from utils import format_number, format_percent


SYSTEM_CONTEXT = (
    "You are a senior policy analyst advising the United Nations Development "
    "Programme (UNDP). Write in cautious, evidence-based language suitable for "
    "development practitioners. Do not invent statistics. Only reference the "
    "figures explicitly provided in the user prompt. Avoid absolute claims; "
    "use hedging language such as 'may', 'suggests', and 'could'. "
    "Always complete all required sections. Keep the full response under 200 words."
)


def _get_api_key() -> Optional[str]:
    """Safely retrieve Gemini API key from Streamlit secrets."""
    try:
        key = st.secrets.get("GEMINI_API_KEY", None)
        if key and str(key).strip():
            return str(key).strip()
    except Exception:
        pass
    return None


def _format_stat_for_prompt(value: Optional[float], unit: str = "") -> str:
    """
    Format a statistic clearly for the LLM.

    Uses full digit grouping plus a plain-language magnitude so the model
    does not truncate mid-number (e.g. writing '1' instead of '1.43 billion').
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "N/A"

    compact = format_number(value)
    if abs(value) >= 1_000_000_000:
        plain = f"{value / 1_000_000_000:.2f} billion"
        full = f"{value:,.0f}"
    elif abs(value) >= 1_000_000:
        plain = f"{value / 1_000_000:.2f} million"
        full = f"{value:,.0f}"
    elif abs(value) >= 1_000:
        plain = f"{value:,.2f}"
        full = f"{value:,.2f}"
    else:
        plain = f"{value:.2f}"
        full = plain

    unit_bit = f" {unit}" if unit else ""
    if full != plain and abs(value) >= 1_000_000:
        return f"{full}{unit_bit} (about {plain}; compact: {compact})"
    return f"{plain}{unit_bit} (compact: {compact})"


def _build_prompt(
    country: str,
    indicator: str,
    unit: str,
    stats: Dict[str, Any],
    sdg_info: Dict[str, Any],
    risk: Optional[Dict[str, Any]] = None,
) -> str:
    """Construct a grounded prompt with only provided statistics."""
    latest = _format_stat_for_prompt(stats.get("latest_value"), unit)
    prev = _format_stat_for_prompt(stats.get("previous_value"), unit)
    growth = format_percent(stats.get("growth_pct"))
    avg = _format_stat_for_prompt(stats.get("average"), unit)
    mn = _format_stat_for_prompt(stats.get("minimum"), unit)
    mx = _format_stat_for_prompt(stats.get("maximum"), unit)
    trend = stats.get("trend", "N/A")
    year = stats.get("latest_year", "N/A")
    first_year = stats.get("first_year", "N/A")

    risk_line = ""
    if risk and risk.get("risk_score") is not None:
        risk_line = (
            f"- Heuristic SDG risk score: {risk['risk_score']}/100 "
            f"({risk.get('risk_label', 'N/A')}; confidence: {risk.get('confidence', 'N/A')})"
        )

    return f"""
Analyse the following World Bank indicator data for {country}.

Indicator: {indicator}
Unit: {unit or 'as reported by World Bank'}
Related goal: {sdg_info.get('sdg_code', '')} — {sdg_info.get('goal_title', '')}
Goal description: {sdg_info.get('description', '')}

Verified statistics (use ONLY these numbers; write large figures in full words
such as '1.43 billion', never stop mid-number):
- Latest value ({year}): {latest}
- Previous value: {prev}
- Year-over-year growth: {growth}
- Trend label: {trend}
- Series average ({first_year} to {year}): {avg}
- Minimum: {mn}
- Maximum: {mx}
- Observations: {stats.get('count', 0)}
{risk_line}

OUTPUT RULES (mandatory):
- Write ALL five labelled sections below. Do not stop after the first section.
- Use these exact plain headings (no markdown # symbols):
Executive Summary:
Why it Matters:
Potential Challenge:
Recommended Action:
Confidence:
- 2 to 3 short sentences per section (Confidence: one sentence only).
- Total length about 150 to 180 words.
- Finish the Confidence sentence completely.
""".strip()


def _extract_response_text(response: Any) -> str:
    """Pull text from a Gemini response, including multi-part candidates."""
    try:
        text = getattr(response, "text", None)
        if text and str(text).strip():
            return str(text).strip()
    except Exception:
        pass

    parts: list[str] = []
    try:
        for candidate in getattr(response, "candidates", None) or []:
            content = getattr(candidate, "content", None)
            for part in getattr(content, "parts", None) or []:
                piece = getattr(part, "text", None)
                if piece:
                    parts.append(str(piece))
    except Exception:
        pass

    return "\n".join(parts).strip()


def _is_incomplete_insight(text: str) -> bool:
    """Heuristic: true if the model clearly stopped before finishing sections."""
    if not text or len(text.strip()) < 120:
        return True
    lower = text.lower()
    required = ["executive summary", "why it matters", "potential challenge", "recommended action"]
    hits = sum(1 for s in required if s in lower)
    return hits < 3


def generate_ai_insight(
    country: str,
    indicator: str,
    unit: str,
    stats: Dict[str, Any],
    sdg_info: Dict[str, Any],
    risk: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Call Gemini to generate a policy insight brief.

    Returns dict with keys:
        success (bool), text (str), error (str|None), error_type (str|None)
    """
    api_key = _get_api_key()
    if not api_key:
        return {
            "success": False,
            "text": "",
            "error": (
                "Gemini API key not found. Add GEMINI_API_KEY to "
                ".streamlit/secrets.toml to enable AI insights."
            ),
            "error_type": "missing_key",
        }

    if not stats or stats.get("latest_value") is None:
        return {
            "success": False,
            "text": "",
            "error": "Insufficient statistics to generate a grounded AI insight.",
            "error_type": "no_data",
        }

    prompt = _build_prompt(country, indicator, unit, stats, sdg_info, risk)

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)

        model_names = [
            "gemini-flash-lite-latest",
            "gemini-flash-latest",
            "gemini-2.0-flash-lite",
            "gemini-2.0-flash",
            "gemini-2.5-flash",
            "gemini-pro-latest",
        ]

        last_error: Optional[Exception] = None
        quota_hits = 0
        response_text = None

        def _is_quota_error(exc: Exception) -> bool:
            err_str = str(exc).lower()
            return any(
                token in err_str
                for token in (
                    "quota",
                    "429",
                    "rate limit",
                    "resource exhausted",
                    "resourceexhausted",
                )
            )

        # Higher budget: some Flash models reserve tokens for internal reasoning
        generation_config = {
            "temperature": 0.3,
            "max_output_tokens": 2048,
            "top_p": 0.9,
        }

        for model_name in model_names:
            try:
                model = genai.GenerativeModel(
                    model_name,
                    system_instruction=SYSTEM_CONTEXT,
                )
                response = model.generate_content(
                    prompt,
                    generation_config=generation_config,
                )
                response_text = _extract_response_text(response)

                # Retry once on the same model if the reply was truncated
                if response_text and _is_incomplete_insight(response_text):
                    retry = model.generate_content(
                        prompt
                        + "\n\nIMPORTANT: Your previous draft was incomplete. "
                        "Rewrite the FULL brief with all five headings now.",
                        generation_config=generation_config,
                    )
                    retry_text = _extract_response_text(retry)
                    if retry_text and (
                        not _is_incomplete_insight(retry_text)
                        or len(retry_text) > len(response_text)
                    ):
                        response_text = retry_text

                if response_text:
                    break
            except Exception as exc:
                last_error = exc
                if _is_quota_error(exc):
                    quota_hits += 1
                continue

        if not response_text:
            if last_error:
                if quota_hits > 0 and quota_hits >= len(model_names) - 1:
                    return {
                        "success": False,
                        "text": "",
                        "error": (
                            "Gemini free-tier quota is exhausted for available "
                            "models. Wait a few minutes and try again, or enable "
                            "billing in Google AI Studio: "
                            "https://aistudio.google.com/"
                        ),
                        "error_type": "quota",
                    }
                return {
                    "success": False,
                    "text": "",
                    "error": f"AI generation failed: {last_error}",
                    "error_type": "api_error",
                }
            return {
                "success": False,
                "text": "",
                "error": "Gemini returned an empty response.",
                "error_type": "empty",
            }

        return {
            "success": True,
            "text": response_text.strip(),
            "error": None,
            "error_type": None,
            "incomplete": _is_incomplete_insight(response_text),
        }

    except ImportError:
        return {
            "success": False,
            "text": "",
            "error": (
                "google-generativeai package is not installed. "
                "Run: pip install google-generativeai"
            ),
            "error_type": "import_error",
        }
    except Exception as exc:
        err_str = str(exc).lower()
        if any(
            token in err_str
            for token in (
                "quota",
                "429",
                "rate limit",
                "resource exhausted",
                "resourceexhausted",
            )
        ):
            return {
                "success": False,
                "text": "",
                "error": (
                    "Gemini API quota or rate limit reached. "
                    "Please wait and try again later."
                ),
                "error_type": "quota",
            }
        return {
            "success": False,
            "text": "",
            "error": f"Unexpected AI error: {exc}",
            "error_type": "unknown",
        }


def format_insight_html(text: str) -> str:
    """
    Convert Gemini response into structured HTML for the UI.

    Escapes content so Streamlit does not strip partial markdown.
    """
    if not text:
        return ""

    sections = [
        "Executive Summary",
        "Why it Matters",
        "Potential Challenge",
        "Recommended Action",
        "Confidence",
    ]

    # Normalise markdown heading markers before parsing
    normalised = text.replace("\r\n", "\n")
    normalised = re.sub(r"^#{1,6}\s*", "", normalised, flags=re.MULTILINE)
    normalised = re.sub(r"\*\*([^*]+)\*\*", r"\1", normalised)

    html_parts: list[str] = []
    current_paras: list[str] = []

    def flush_paras() -> None:
        nonlocal current_paras
        if current_paras:
            para = " ".join(current_paras).strip()
            if para:
                html_parts.append(f"<p>{html.escape(para)}</p>")
            current_paras = []

    for raw in normalised.split("\n"):
        line = raw.strip()
        if not line:
            flush_paras()
            continue

        # Strip leading numbering: "1.", "1)", "-", etc.
        stripped = re.sub(r"^[\d]+[\.\)\-:\s]+", "", line).strip()
        stripped = stripped.lstrip("-• ").strip()

        matched = False
        for section in sections:
            pattern = re.compile(
                rf"^{re.escape(section)}\s*:?\s*(.*)$",
                re.IGNORECASE,
            )
            m = pattern.match(stripped)
            if m:
                flush_paras()
                html_parts.append(f"<h4>{html.escape(section)}</h4>")
                remainder = (m.group(1) or "").strip(" :-")
                if remainder:
                    current_paras.append(remainder)
                matched = True
                break

        if not matched:
            current_paras.append(line)

    flush_paras()
    if not html_parts:
        return f"<p>{html.escape(text)}</p>"
    return "\n".join(html_parts)
