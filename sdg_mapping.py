"""
SDG Mapping Module
Maps World Bank development indicators to UN Sustainable Development Goals.
"""

from typing import Dict, Any, List, Optional


# Display name -> World Bank indicator code
INDICATOR_CODES: Dict[str, str] = {
    "Population": "SP.POP.TOTL",
    "GDP": "NY.GDP.MKTP.CD",
    "Life Expectancy": "SP.DYN.LE00.IN",
    "Internet Users": "IT.NET.USER.ZS",
    "Unemployment": "SL.UEM.TOTL.ZS",
    "CO₂ Emissions": "EN.GHG.CO2.MT.CE.AR5",
    "Access to Electricity": "EG.ELC.ACCS.ZS",
    "Primary School Enrollment": "SE.PRM.ENRR",
}

# Country display name -> ISO Alpha-2 / World Bank country code
COUNTRY_CODES: Dict[str, str] = {
    "Pakistan": "PK",
    "India": "IN",
    "Bangladesh": "BD",
}

# Full SDG metadata keyed by indicator display name
SDG_MAPPING: Dict[str, Dict[str, Any]] = {
    "Population": {
        "sdg_number": 11,
        "sdg_code": "SDG 11",
        "goal_title": "Sustainable Cities and Communities",
        "description": (
            "Make cities and human settlements inclusive, safe, resilient and "
            "sustainable. Population trends inform urban planning, housing "
            "demand, and service delivery capacity."
        ),
        "icon": "🏙️",
        "color": "#FD9D24",
    },
    "GDP": {
        "sdg_number": 8,
        "sdg_code": "SDG 8",
        "goal_title": "Decent Work and Economic Growth",
        "description": (
            "Promote sustained, inclusive and sustainable economic growth, "
            "full and productive employment and decent work for all. GDP is a "
            "core measure of economic capacity and development trajectory."
        ),
        "icon": "📈",
        "color": "#A21942",
    },
    "Life Expectancy": {
        "sdg_number": 3,
        "sdg_code": "SDG 3",
        "goal_title": "Good Health and Well-Being",
        "description": (
            "Ensure healthy lives and promote well-being for all at all ages. "
            "Life expectancy reflects health system performance, nutrition, "
            "and broader social determinants of health."
        ),
        "icon": "❤️",
        "color": "#4C9F38",
    },
    "Internet Users": {
        "sdg_number": 9,
        "sdg_code": "SDG 9",
        "goal_title": "Industry, Innovation and Infrastructure",
        "description": (
            "Build resilient infrastructure, promote inclusive and sustainable "
            "industrialization and foster innovation. Internet access underpins "
            "digital inclusion, education, and economic opportunity."
        ),
        "icon": "🏗️",
        "color": "#FD6925",
    },
    "Unemployment": {
        "sdg_number": 8,
        "sdg_code": "SDG 8",
        "goal_title": "Decent Work and Economic Growth",
        "description": (
            "Promote sustained, inclusive and sustainable economic growth, "
            "full and productive employment and decent work for all. "
            "Unemployment rates highlight labour market resilience and "
            "inclusion gaps."
        ),
        "icon": "💼",
        "color": "#A21942",
    },
    "CO₂ Emissions": {
        "sdg_number": 13,
        "sdg_code": "SDG 13",
        "goal_title": "Climate Action",
        "description": (
            "Take urgent action to combat climate change and its impacts. "
            "CO₂ emissions track progress toward low-carbon development and "
            "national climate commitments."
        ),
        "icon": "🌍",
        "color": "#3F7E44",
    },
    "Access to Electricity": {
        "sdg_number": 7,
        "sdg_code": "SDG 7",
        "goal_title": "Affordable and Clean Energy",
        "description": (
            "Ensure access to affordable, reliable, sustainable and modern "
            "energy for all. Electricity access is foundational for health, "
            "education, and productive livelihoods."
        ),
        "icon": "⚡",
        "color": "#FCC30B",
    },
    "Primary School Enrollment": {
        "sdg_number": 4,
        "sdg_code": "SDG 4",
        "goal_title": "Quality Education",
        "description": (
            "Ensure inclusive and equitable quality education and promote "
            "lifelong learning opportunities for all. Primary enrollment is a "
            "foundational indicator of educational access."
        ),
        "icon": "📚",
        "color": "#C5192D",
    },
}

# Units / formatting hints for indicators
INDICATOR_UNITS: Dict[str, str] = {
    "Population": "people",
    "GDP": "current US$",
    "Life Expectancy": "years",
    "Internet Users": "% of population",
    "Unemployment": "% of labour force",
    "CO₂ Emissions": "Mt CO₂e",
    "Access to Electricity": "% of population",
    "Primary School Enrollment": "% gross",
}

# Leave-no-one-behind (LNOB) equity lenses — disaggregated World Bank series
EQUITY_LENSES: Dict[str, Dict[str, Any]] = {
    "Access to Electricity": {
        "dimension": "Urban–Rural",
        "sdg_link": "SDG 7 — leave no one behind on energy access",
        "narrative": (
            "Urban–rural electricity gaps highlight who may still be excluded "
            "from modern energy services despite national progress."
        ),
        "series": [
            {"label": "Urban", "code": "EG.ELC.ACCS.UR.ZS", "color": "#009EDB"},
            {"label": "Rural", "code": "EG.ELC.ACCS.RU.ZS", "color": "#2E7D32"},
        ],
    },
    "Unemployment": {
        "dimension": "Gender",
        "sdg_link": "SDG 8 / SDG 5 — inclusive labour markets",
        "narrative": (
            "Male–female unemployment differences can signal unequal labour-market "
            "access and care-economy constraints."
        ),
        "series": [
            {"label": "Male", "code": "SL.UEM.TOTL.MA.ZS", "color": "#00689D"},
            {"label": "Female", "code": "SL.UEM.TOTL.FE.ZS", "color": "#C5192D"},
        ],
    },
    "Life Expectancy": {
        "dimension": "Gender",
        "sdg_link": "SDG 3 — healthy lives for all",
        "narrative": (
            "Gender gaps in life expectancy can reflect differences in health risks, "
            "access to care, and social determinants."
        ),
        "series": [
            {"label": "Male", "code": "SP.DYN.LE00.MA.IN", "color": "#00689D"},
            {"label": "Female", "code": "SP.DYN.LE00.FE.IN", "color": "#C5192D"},
        ],
    },
    "Primary School Enrollment": {
        "dimension": "Gender",
        "sdg_link": "SDG 4 — inclusive quality education",
        "narrative": (
            "Enrollment gaps between boys and girls are a core equity signal for "
            "educational inclusion."
        ),
        "series": [
            {"label": "Male", "code": "SE.PRM.ENRR.MA", "color": "#00689D"},
            {"label": "Female", "code": "SE.PRM.ENRR.FE", "color": "#C5192D"},
        ],
    },
    "Population": {
        "dimension": "Urban–Rural share",
        "sdg_link": "SDG 11 — sustainable cities and communities",
        "narrative": (
            "Urban and rural population shares shape service delivery pressures "
            "and territorial development priorities."
        ),
        "series": [
            {
                "label": "Urban (% of total)",
                "code": "SP.URB.TOTL.IN.ZS",
                "color": "#009EDB",
            },
            {
                "label": "Rural (% of total)",
                "code": "SP.RUR.TOTL.ZS",
                "color": "#2E7D32",
            },
        ],
    },
}

# What each national aggregate cannot tell you (analyst integrity notes)
INDICATOR_LIMITATIONS: Dict[str, List[str]] = {
    "Population": [
        "National totals mask internal migration, informal settlements, and subnational disparities.",
        "Census and intercensal estimates may revise historical figures over time.",
    ],
    "GDP": [
        "GDP does not measure distribution, unpaid care work, or environmental depletion.",
        "Informal economy coverage varies; welfare outcomes may diverge from GDP growth.",
    ],
    "Life Expectancy": [
        "Averages hide inequality by income, geography, disability, and minority status.",
        "Does not capture morbidity, quality of care, or healthy life years.",
    ],
    "Internet Users": [
        "Access does not equal meaningful use, affordability, digital skills, or safety online.",
        "Survey definitions and reference periods can differ across countries and years.",
    ],
    "Unemployment": [
        "Standard rates may understate underemployment, discouraged workers, and informal work.",
        "Gender and youth gaps require complementary labour-force indicators.",
    ],
    "CO₂ Emissions": [
        "Production-based accounting can differ from consumption-based footprints.",
        "Does not alone show adaptation needs, loss and damage, or just-transition impacts.",
    ],
    "Access to Electricity": [
        "Connection rates do not guarantee reliability, affordability, or clean generation mix.",
        "Urban–rural and last-mile gaps may remain even when national coverage looks high.",
    ],
    "Primary School Enrollment": [
        "Enrollment is not completion, learning outcomes, or inclusive quality.",
        "Gross rates can exceed 100% due to over-age enrollment and repetition.",
    ],
}


def get_indicator_list() -> List[str]:
    """Return ordered list of indicator display names."""
    return list(INDICATOR_CODES.keys())


def get_country_list() -> List[str]:
    """Return ordered list of country display names."""
    return list(COUNTRY_CODES.keys())


def get_wb_code(indicator_name: str) -> Optional[str]:
    """Return World Bank indicator code for a display name."""
    return INDICATOR_CODES.get(indicator_name)


def get_country_code(country_name: str) -> Optional[str]:
    """Return ISO/World Bank country code for a display name."""
    return COUNTRY_CODES.get(country_name)


def get_sdg_info(indicator_name: str) -> Dict[str, Any]:
    """
    Return SDG metadata for an indicator.

    Falls back to a generic SDG 17 entry if the indicator is unknown.
    """
    if indicator_name in SDG_MAPPING:
        return SDG_MAPPING[indicator_name].copy()
    return {
        "sdg_number": 17,
        "sdg_code": "SDG 17",
        "goal_title": "Partnerships for the Goals",
        "description": "Strengthen the means of implementation and revitalize "
        "the Global Partnership for Sustainable Development.",
        "icon": "🤝",
        "color": "#19486A",
    }


def get_unit(indicator_name: str) -> str:
    """Return unit label for an indicator."""
    return INDICATOR_UNITS.get(indicator_name, "")


def search_indicators(query: str) -> List[str]:
    """
    Filter indicators by case-insensitive substring match on name,
    SDG code, or goal title.
    """
    if not query or not query.strip():
        return get_indicator_list()

    q = query.strip().lower()
    results: List[str] = []
    for name in get_indicator_list():
        info = get_sdg_info(name)
        haystack = " ".join(
            [
                name.lower(),
                info.get("sdg_code", "").lower(),
                info.get("goal_title", "").lower(),
                info.get("description", "").lower(),
            ]
        )
        if q in haystack:
            results.append(name)
    return results


def get_equity_lens(indicator_name: str) -> Optional[Dict[str, Any]]:
    """Return leave-no-one-behind equity lens metadata, if available."""
    lens = EQUITY_LENSES.get(indicator_name)
    return lens.copy() if lens else None


def get_indicator_limitations(indicator_name: str) -> List[str]:
    """Return analyst notes on what the indicator cannot tell us."""
    return list(
        INDICATOR_LIMITATIONS.get(
            indicator_name,
            [
                "National aggregates can mask subnational and group-based disparities.",
                "Validate findings with official statistics and qualitative context.",
            ],
        )
    )
