from __future__ import annotations

from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if SRC_DIR.exists() and str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import streamlit as st
from dotenv import load_dotenv

from research_assistant.graph import build_research_graph
from research_assistant.models import ResearchReport


load_dotenv()

st.set_page_config(
    page_title="AI Research Assistant",
    layout="wide",
)


@st.cache_resource
def get_graph():
    return build_research_graph()


def secret_or_default(name: str, default: str = "") -> str:
    try:
        return st.secrets.get(name, default)
    except FileNotFoundError:
        return default


def render_report(report: ResearchReport) -> None:
    st.subheader(report.title)
    st.markdown("#### Executive Summary")
    st.write(report.executive_summary)

    st.markdown("#### Findings")
    for finding in report.findings:
        with st.expander(finding.heading, expanded=True):
            st.write(finding.summary)
            if finding.source_urls:
                st.caption("Sources: " + ", ".join(finding.source_urls))

    if report.limitations:
        st.markdown("#### Limitations")
        for limitation in report.limitations:
            st.write(f"- {limitation}")

    if report.sources:
        st.markdown("#### Source List")
        for index, source in enumerate(report.sources, start=1):
            st.write(f"{index}. [{source.title}]({source.url})")


with st.sidebar:
    st.header("Settings")
    offline_demo = st.toggle("Offline demo mode", value=True)
    openai_model = st.text_input("OpenAI model", value=secret_or_default("OPENAI_MODEL", "gpt-4.1-mini"))
    openai_api_key = st.text_input(
        "OpenAI API key",
        value=secret_or_default("OPENAI_API_KEY"),
        type="password",
        disabled=offline_demo,
    )
    tavily_api_key = st.text_input(
        "Tavily API key",
        value=secret_or_default("TAVILY_API_KEY"),
        type="password",
        disabled=offline_demo,
    )

st.title("AI Research Assistant")
st.caption("Planner Agent -> Web Search Agent -> Summarizer Agent -> Report Generator Agent")

topic = st.text_input(
    "Research topic",
    placeholder="Example: impact of AI agents on software engineering",
)

col_a, col_b = st.columns([1, 3])
with col_a:
    run = st.button("Generate PDF report", type="primary", use_container_width=True)
with col_b:
    st.write("")

if run:
    if not topic.strip():
        st.error("Enter a research topic first.")
    elif not offline_demo and (not openai_api_key or not tavily_api_key):
        st.error("Live mode needs both OpenAI and Tavily API keys. Use offline demo mode to test without keys.")
    else:
        output_path = Path("reports") / f"{'-'.join(topic.lower().split())[:60]}.pdf"
        with st.status("Running agents...", expanded=True) as status:
            st.write("Planner Agent is creating research questions.")
            st.write("Web Search Agent is collecting sources.")
            st.write("Summarizer Agent is synthesizing findings.")
            st.write("Report Generator Agent is writing the PDF.")
            result = get_graph().invoke(
                {
                    "topic": topic.strip(),
                    "output_path": str(output_path),
                    "offline_demo": offline_demo,
                    "openai_api_key": openai_api_key,
                    "tavily_api_key": tavily_api_key,
                    "openai_model": openai_model,
                }
            )
            status.update(label="Report generated", state="complete")

        report = result["report"]
        pdf_path = Path(result["output_path"])
        st.success(f"Generated {pdf_path}")
        render_report(report)

        st.download_button(
            label="Download PDF",
            data=pdf_path.read_bytes(),
            file_name=pdf_path.name,
            mime="application/pdf",
            use_container_width=True,
        )
