# AI Research Assistant

Agent workflow that researches a topic and automatically generates a PDF report.

## Agents

- Planner Agent: expands the user topic into focused research questions.
- Web Search Agent: searches the web with Tavily and collects source snippets.
- Summarizer Agent: synthesizes findings with citations.
- Report Generator Agent: creates a structured PDF research report.

## Tools

- LangGraph for orchestration.
- OpenAI API for planning, synthesis, and report drafting.
- Tavily Search for web research.
- Streamlit for the browser UI.
- ReportLab for PDF generation.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
Copy-Item .env.example .env
```

Add your keys to `.env`:

```text
OPENAI_API_KEY=...
TAVILY_API_KEY=...
```

## Run

Streamlit app:

```powershell
streamlit run streamlit_app.py
```

CLI:

```powershell
research-assistant "impact of AI agents on software engineering" --output reports/ai-agents.pdf
```

You can run without API keys using the deterministic demo mode:

```powershell
research-assistant "impact of AI agents on software engineering" --offline-demo
```

PDFs are written to `reports/` by default.

## Deploy To Streamlit Community Cloud

1. Push this project to GitHub.
2. In Streamlit Community Cloud, create a new app from the repository.
3. Set the main file path to `streamlit_app.py`.
4. Add secrets:

```toml
OPENAI_API_KEY = "..."
TAVILY_API_KEY = "..."
OPENAI_MODEL = "gpt-4.1-mini"
```

5. Deploy the app. You can leave offline demo mode enabled to test without API calls.
