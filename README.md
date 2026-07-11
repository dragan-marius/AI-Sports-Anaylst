# ⚽ AI Sports Analyst

Dragan Marius

## 🚀 Overview

AI Sports Analyst is a full-stack web application that predicts football match outcomes using a statistical model, then hands the raw numbers to an LLM agent to turn them into a readable, journalist-style analysis. The system started as a single-script LangChain + SQLite prototype and was rebuilt into a proper client-server architecture: a **Django REST backend** for the statistics and AI orchestration, and a **React frontend** for the UI.

The project targets football matches from the 2026 World Cup dataset stored locally in SQLite.

## 🏗️ Architecture

**Backend (Django + DRF)**
- `sports_project/` — Django project configuration (settings, URL routing, CORS setup for the React frontend).
- `api/` — the single Django app exposing one endpoint, `POST /api/predict/`, which takes two team names and returns the AI-generated analysis.
- `api/predictor.py` — the statistical engine (see below). Pure Python, no ML framework, queries `world_cup.db` directly via `sqlite3`.
- `api/views.py` — wires the predictor's output into a LangChain **tool**, exposes it to a Gemini-backed agent (`langchain_google_genai` + `create_agent`), and returns the agent's final text response.

**Frontend (React, no build step)**
- `index.html` — a single-file React app loaded via CDN (`react`, `react-dom`, Babel Standalone for in-browser JSX) and `axios` for the HTTP call. No `npm`/webpack pipeline; this keeps the frontend framework-free to run, at the cost of not being a "real" React SPA project.

## 🧮 Prediction Model

The core of `predictor.py` is a **Poisson-based expected goals (xG) model**, with two statistical corrections layered on top:

1. **Empirical Bayesian shrinkage**: a team's scoring/conceding average is pulled toward the tournament-wide average, weighted by how many matches that team has played (`pondere_medie`). This prevents a team with only 1-2 matches played from producing wildly overconfident xG values — the model "trusts" a team's own stats more as its sample size grows.
2. **Dixon-Coles low-score correction (τ)**: raw independent-Poisson models overestimate the probability of 0-0 and 1-1 draws, since real match scores are negatively correlated at low totals. A correction factor (`calcul_corectie_tau`, parameterized by `rho`) adjusts probabilities specifically for the 0-0, 1-0, 0-1 and 1-1 scorelines.

From the corrected score-probability matrix, the system derives:
- 1X2 odds (home win / draw / away win), with a fixed bookmaker margin applied.
- Over/Under odds for goal lines 0.5 through 7.5, computed from the cumulative scoreline probabilities.

**Known limitation**: xG values are clamped to a `[0.4, 3.0]` range to avoid unstable outputs for teams with very small or very lopsided sample sizes, rather than being fully derived from a larger, more robust dataset. This is a pragmatic guardrail, not a substitute for more historical data.

## 🤖 AI Layer

- The `predict_math_prompt` function is registered as a LangChain `@tool`, so the Gemini agent (`gemini-2.5-flash`) is instructed to *always* call it before answering — the model never invents odds on its own.
- A fixed system prompt constrains the agent to: use the tool, explain the reasoning behind the odds using xG, and close with a clear prediction and a suggested "value bet."
- This separates concerns cleanly: **the math is deterministic and auditable** (pure Python, testable independently), while the LLM is only responsible for turning numbers into natural-language explanation — it can't quietly change the odds it's asked to explain.

## ⚙️ Technologies Used

- **Backend**: Django, Django REST Framework, django-cors-headers
- **AI/Agent**: LangChain, LangGraph, `langchain-google-genai` (Gemini 2.5 Flash)
- **Data**: SQLite (`world_cup.db`)
- **Frontend**: React 18 (CDN), Babel Standalone, Axios
- **Config**: `python-dotenv` for API key management

## 💻 Running Locally

**Backend**
```bash
python -m venv venv
source venv/bin/activate       # venv\Scripts\activate on Windows
pip install -r requirements.txt

# create a .env file in the project root:
# GEMINI_API_KEY=your_key_here

python manage.py migrate
python manage.py runserver
```

**Frontend**

Simply open `index.html` in a browser once the Django server is running on `http://127.0.0.1:8000`. No build step required.

## 📁 What's Not Included

`app.py` in the repository root is an earlier Streamlit-based prototype, kept for historical reference — the logic it contained (LangChain tool + Gemini agent) was migrated into `api/views.py`. It is not part of the current Django/React architecture and is not required to run the app.