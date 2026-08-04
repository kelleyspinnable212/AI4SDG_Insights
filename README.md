# 🌍 AI4SDG Insights

**AI-powered Sustainable Development Analytics Platform**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Streamlit%20Cloud-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://hijabf-ai4sdg-insights-app-ak34e9.streamlit.app/)
[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Built%20with-Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Live app:** [https://hijabf-ai4sdg-insights-app-ak34e9.streamlit.app/](https://hijabf-ai4sdg-insights-app-ak34e9.streamlit.app/)

A production-quality Streamlit dashboard that combines **World Bank Open Data** with **Google Gemini AI** to explore development indicators, compare countries, and generate cautious UNDP-style policy insights.

Designed as a polished portfolio project with a professional UN / UNDP visual language — blue-and-white palette, card layouts, and modular architecture.

---

## Project Overview

AI4SDG Insights helps analysts and students:

- Explore Sustainable Development-related indicators for **Pakistan**, **India**, and **Bangladesh**
- View KPI cards, interactive Plotly charts, and summary statistics
- Map each indicator to a related **UN Sustainable Development Goal (SDG)**
- Generate grounded **AI policy briefs** via Gemini (executive summary, why it matters, challenges, recommended actions)
- Overlay a **5-year linear forecast** and a heuristic **SDG risk score**
- Download **CSV** and professionally formatted **PDF** reports

---

## Features

| Area | Capabilities |
|------|----------------|
| **Data** | Live World Bank API, 1-hour cache, missing-value cleaning, graceful failure handling |
| **Indicators** | Population, GDP, Life Expectancy, Internet Users, Unemployment, CO₂ Emissions, Access to Electricity, Primary School Enrollment |
| **Analytics** | Latest value, YoY growth, polarity-aware trend, average / min / max, overall growth |
| **Visuals** | Interactive Plotly charts (hover, zoom, pan, image download), multi-country comparison |
| **SDG Mapping** | Dedicated module linking indicators to SDG number, title, description, and icon |
| **AI Insights** | Gemini policy analyst prompt; quota-aware error handling; ~180-word briefs |
| **Forecast** | Optional 5-year OLS forecast with dashed overlay and R² |
| **Risk Score** | Heuristic 0–100 SDG risk score with confidence and factors |
| **Export** | CSV + SDG Progress Note PDF (limitations, equity, 2030 scenario, AI notes) |
| **Equity (LNOB)** | Urban–rural / gender disaggregation where World Bank series exist |
| **Data integrity** | Coverage %, missing years, freshness, “what this cannot tell us” |
| **2030 scenarios** | Bounded baseline vs adjusted growth paths to Agenda 2030 |
| **UX** | Wide layout, dark/light mode, sidebar search, toasts, spinners, footer |

---

## Project Structure

```
AI4SDG_Insights/
├── app.py                 # Streamlit UI entry point
├── data_loader.py         # World Bank API client + caching
├── analytics.py           # Statistics, forecast, risk score
├── ai_insights.py         # Gemini policy insight generation
├── sdg_mapping.py         # Indicator ↔ SDG metadata
├── utils.py               # Theming, charts, PDF/CSV helpers
├── requirements.txt
├── LICENSE
├── README.md
└── .streamlit/
    └── secrets.toml.example
```

---

## Requirements

- Python **3.9+** (3.10 or 3.11 recommended)
- Internet access for World Bank API and Gemini
- A Google AI Studio / Gemini API key (for AI insights)

Python packages are listed in `requirements.txt`.

---

## Installation

```bash
# 1. Navigate to the project
cd AI4SDG_Insights

# 2. Create and activate a virtual environment (recommended)
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

### Configure Gemini API key

1. Obtain an API key from [Google AI Studio](https://aistudio.google.com/apikey).
2. Create Streamlit secrets:

```bash
# Windows
copy .streamlit\secrets.toml.example .streamlit\secrets.toml

# macOS / Linux
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

3. Edit `.streamlit/secrets.toml`:

```toml
GEMINI_API_KEY = "your-actual-api-key"
```

> Never commit real API keys. The app reads the key only from `st.secrets["GEMINI_API_KEY"]`.

---

## How to Run

```bash
streamlit run app.py
```

The app opens in your browser (typically `http://localhost:8501`).

### Sidebar workflow

1. Choose **country** and **indicator** (optionally search)
2. Adjust the **year range**
3. Toggle **forecast** and **dark mode** as needed
4. Click **✨ AI Insight** for a policy brief
5. Click **📥 Prepare Report**, then download CSV / PDF

---

## Deployment

**Already live on Streamlit Community Cloud:**  
[https://hijabf-ai4sdg-insights-app-ak34e9.streamlit.app/](https://hijabf-ai4sdg-insights-app-ak34e9.streamlit.app/)

To redeploy or fork:

1. Push to GitHub (public).
2. Open [share.streamlit.io](https://share.streamlit.io/) → **New app** → Main file: `app.py`.
3. In **App settings → Secrets**, add:

```toml
GEMINI_API_KEY = "your-actual-api-key"
```

World Bank charts work without a key. Only **AI Insight** needs `GEMINI_API_KEY`.

---

## Screenshots

| View | Description |
|------|-------------|
| <img width="1421" height="862" alt="Main dashboard" src="https://github.com/user-attachments/assets/580a1867-205d-42cd-a6ec-a77f80e264e7" /> | Main dashboard — KPI cards + trend chart (light mode) |
| <img width="1296" height="688" alt="Country comparison" src="https://github.com/user-attachments/assets/5e4d6173-ca48-4e86-adc1-2b215411a6b5" /> | Pakistan / India / Bangladesh comparison |
| <img width="1368" height="920" alt="AI policy brief" src="https://github.com/user-attachments/assets/93c94136-3f97-4d63-850c-84ad6c7e918b" /> | Gemini policy brief panel |
| <img width="1827" height="805" alt="Dark mode" src="https://github.com/user-attachments/assets/8dc930c9-ddd4-4001-bacc-5439e7257c96" /> | Dark mode theme |

---

## Data Source

All time series are fetched from the [World Bank Open Data API](https://data.worldbank.org/):

| Indicator | World Bank Code |
|-----------|-----------------|
| Population | `SP.POP.TOTL` |
| GDP | `NY.GDP.MKTP.CD` |
| Life Expectancy | `SP.DYN.LE00.IN` |
| Internet Users | `IT.NET.USER.ZS` |
| Unemployment | `SL.UEM.TOTL.ZS` |
| CO₂ Emissions | `EN.GHG.CO2.MT.CE.AR5` |
| Access to Electricity | `EG.ELC.ACCS.ZS` |
| Primary School Enrollment | `SE.PRM.ENRR` |

---

## SDG Mapping (examples)

| Indicator | SDG | Goal |
|-----------|-----|------|
| Internet Users | SDG 9 | Industry, Innovation and Infrastructure |
| Population | SDG 11 | Sustainable Cities and Communities |
| Life Expectancy | SDG 3 | Good Health and Well-Being |
| GDP | SDG 8 | Decent Work and Economic Growth |
| Access to Electricity | SDG 7 | Affordable and Clean Energy |
| CO₂ Emissions | SDG 13 | Climate Action |
| Primary School Enrollment | SDG 4 | Quality Education |

---

## Design Notes

- Wide Streamlit layout with Montserrat / Source Sans typography
- UN-inspired blue & white palette with soft shadows and rounded cards
- Business logic separated from UI (`data_loader`, `analytics`, `ai_insights`)
- PEP 8-oriented modular Python; no notebook / Colab patterns
- Polarity-aware trend labels (rising unemployment is a watch signal, not “improving”)

---

## Future Improvements

- Expand country coverage beyond South Asia (ASEAN, Sub-Saharan Africa, etc.)
- Add multi-indicator correlation and radar charts
- Support additional Gemini models and streaming responses
- Persist user preferences (theme, last selection) via query params
- Multilingual UI (EN / UR / BN / HI)
- Official UNDP colour tokens and SDG icon assets
- Unit tests and CI for data cleaning / analytics

---

## Disclaimer

AI4SDG Insights is an **educational / portfolio** application. It is **not** an official United Nations or UNDP product. AI-generated text is illustrative and must be validated against official statistics and national planning frameworks before any policy use.

---

## License

MIT — feel free to adapt for learning and portfolio showcases.
