# Deployment & Local Setup Guide

This guide provides step-by-step instructions for a mentor, colleague, or developer to spin up the AI Pulse Data Engineering pipeline on their local machine from scratch.

## Prerequisites
1. **Python 3.12+**
2. **PostgreSQL 16** (or higher)
3. **Git**

---

## 1. PostgreSQL Setup

The pipeline requires a running PostgreSQL instance to store the data warehouse tables.

1. Download and install PostgreSQL from [postgresql.org](https://www.postgresql.org/download/).
2. During installation, set a password for the default `postgres` user.
3. Open `psql` (the command-line tool) or pgAdmin.
4. Create the project database:
   ```sql
   CREATE DATABASE ai_pulse_db;
   ```

---

## 2. Project Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/irfan-dot-shaik/AI-Pulse-GenAI-Industry-Trends-Warehouse.git
   cd AI-Pulse-GenAI-Industry-Trends-Warehouse
   ```

2. **Create a Python virtual environment:**
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## 3. Environment Variables Configuration

The project uses a `.env` file to securely manage database credentials and API keys.

1. Create a copy of the template file:
   ```bash
   # Windows
   copy .env.example .env
   
   # macOS/Linux
   cp .env.example .env
   ```

2. Open `.env` in a text editor and fill in your credentials:
   - `DATABASE_URL`: Typically `postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/ai_pulse_db`
   - `GNEWS_API_KEY`: Get a free key from [gnews.io](https://gnews.io).
   - `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET`: (Optional) Get from [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps). The pipeline will skip Reddit automatically if these are missing.

---

## 4. Running the Data Pipeline

The pipeline is entirely orchestrated via `main.py`. This script creates the database schema, fetches from all sources concurrently, validates, scores, and inserts the data.

```bash
python main.py
```

**Expected Output:**
You should see a clean log of the ingestion process taking under 30 seconds, finishing with a `PIPELINE RUN SUMMARY` indicating the number of articles inserted into the Raw and Staging layers.

---

## 5. Launching the Analytics Dashboard

Once the data is populated in the database, launch the Streamlit frontend.

```bash
streamlit run dashboard/app.py
```

Streamlit will start a local server and automatically open the dashboard in your default web browser (typically at `http://localhost:8501`).

---

## Troubleshooting

- **"Connection Refused" / SQLAlchemy Errors:** Verify that PostgreSQL is running as a background service and that your `DATABASE_URL` password in `.env` is correct.
- **"Module Not Found" Errors:** Ensure your virtual environment is activated (`(venv)` should appear in your terminal prompt) and that you ran `pip install -r requirements.txt`.
- **Streamlit charts look broken or throw TypeErrors:** Make sure you are on the `week3-multisource` branch where all Plotly deprecation fixes and kwargs deduplications have been resolved.
