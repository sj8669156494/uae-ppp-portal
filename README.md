---
title: UAE PPP Backend
emoji: 🏗️
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# UAE PPP Intelligence Portal

An AI-powered portal for discovering, tracking, and searching UAE Public-Private Partnership and infrastructure projects.

## What it does

- **Automatically collects** PPP project data from UAE government websites, news, and procurement portals
- **Structures and cleans** raw data into a consistent schema with deduplication
- **AI-powered search** — ask in plain English: "Show me road projects in Dubai under execution"
- **Persistent conversation** — refine queries across turns: "now only above AED 5 billion"
- **Domain guardrails** — stays strictly on UAE PPP/infrastructure topic
- **Monitoring** — every query logged with latency, filters, and result counts

## Quick start

```bash
# 1. Clone / navigate to project
cd uae-ppp-portal

# 2. Add your OpenAI API key to .env
cp .env.example .env
# Edit .env: OPENAI_API_KEY=sk-proj-...

# 3. One-command setup (creates conda env, seeds DB, installs frontend)
bash scripts/setup.sh

# 4. Start everything
bash scripts/run_dev.sh

# 5. Open browser
open http://localhost:5173
```

## Architecture

```
Public Websites (ADIO, WAM, Dubai DOF, RTA, News)
        │
   [Scrapers: httpx + BeautifulSoup + Playwright]
        │
   [LLM Extraction: Claude API]     [Deduplication: rapidfuzz]
        │
   SQLite / PostgreSQL Database
        │
   FastAPI Backend (port 8000)
        │
   ┌────┴────────────┐
React Frontend    LangGraph AI Agent
(port 5173)       (NL → filters → SQL → results)
```

## Tech stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + Python 3.11 |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Scraping | Playwright + BeautifulSoup + httpx |
| AI Agent | OpenAI gpt-4o-mini (NL → filters → results) |
| Frontend | React 18 + Vite + TailwindCSS |
| Scheduling | APScheduler (daily 6am) |
| Monitoring | structlog (JSON logs) |
| Environment | Conda (uae-ppp) |

## Demo queries

```
"Show me road projects in Dubai"
"Which water projects are still in tendering?"
"Only projects above AED 10 billion"
"Now only the ones under execution"
"Who won FIFA?" → [guardrail blocks this]
```

## Data sources

| Source | Type | Refresh |
|--------|------|---------|
| ADIO (Abu Dhabi Investment Office) | Government portal | Monthly |
| WAM (UAE Media Office) | Government news | Daily |
| Dubai DOF PPP Portal | Government portal | Weekly |
| RTA Dubai | Government portal | Weekly |
| Gulf News / The National | News RSS | Daily |

## Running tests

```bash
conda activate uae-ppp
pytest tests/ -v
```
