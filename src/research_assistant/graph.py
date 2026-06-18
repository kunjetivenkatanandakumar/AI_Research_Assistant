from __future__ import annotations

import os
from pathlib import Path

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field
from tavily import TavilyClient

from research_assistant.llm import OpenAIJsonClient
from research_assistant.models import Finding, ResearchQuestion, ResearchReport, ResearchState, Source
from research_assistant.pdf import build_pdf


class Plan(BaseModel):
    questions: list[ResearchQuestion] = Field(min_length=3, max_length=6)


class Findings(BaseModel):
    findings: list[Finding] = Field(min_length=3)
    executive_summary: str
    limitations: list[str] = Field(default_factory=list)


def _openai_api_key(state: ResearchState) -> str | None:
    return state.get("openai_api_key") or os.getenv("OPENAI_API_KEY")


def _tavily_api_key(state: ResearchState) -> str | None:
    return state.get("tavily_api_key") or os.getenv("TAVILY_API_KEY")


def _openai_model(state: ResearchState) -> str | None:
    return state.get("openai_model") or os.getenv("OPENAI_MODEL")


def planner_agent(state: ResearchState) -> ResearchState:
    topic = state["topic"]
    openai_api_key = _openai_api_key(state)
    if state.get("offline_demo") or not openai_api_key:
        questions = [
            ResearchQuestion(question=f"What is the current state of {topic}?", rationale="Establishes baseline context."),
            ResearchQuestion(question=f"What are the main benefits of {topic}?", rationale="Identifies positive impact."),
            ResearchQuestion(question=f"What are the risks and limitations of {topic}?", rationale="Balances the analysis."),
            ResearchQuestion(question=f"What trends will shape {topic} next?", rationale="Adds forward-looking insight."),
        ]
        return {"questions": questions}

    client = OpenAIJsonClient(model=_openai_model(state), api_key=openai_api_key)
    plan = client.parse_json(
        prompt=(
            "Create 3 to 6 focused research questions for a concise research report.\n"
            f"Topic: {topic}\n"
            "Return JSON only."
        ),
        schema=Plan,
    )
    return {"questions": plan.questions}


def web_search_agent(state: ResearchState) -> ResearchState:
    topic = state["topic"]
    questions = state["questions"]
    tavily_api_key = _tavily_api_key(state)
    if state.get("offline_demo") or not tavily_api_key:
        sources = [
            Source(
                title="Offline demo source",
                url="https://example.com/offline-demo",
                content=f"Demo research note for {question.question}",
                score=1.0,
            )
            for question in questions
        ]
        return {"sources": sources}

    client = TavilyClient(api_key=tavily_api_key)
    sources: list[Source] = []
    seen_urls: set[str] = set()
    for question in questions:
        response = client.search(
            query=question.question,
            search_depth="advanced",
            max_results=4,
            include_raw_content=False,
        )
        for item in response.get("results", []):
            url = item.get("url", "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            sources.append(
                Source(
                    title=item.get("title", "Untitled source"),
                    url=url,
                    content=item.get("content", ""),
                    score=item.get("score"),
                )
            )
    return {"sources": sources}


def summarizer_agent(state: ResearchState) -> ResearchState:
    topic = state["topic"]
    sources = state["sources"]
    openai_api_key = _openai_api_key(state)

    if state.get("offline_demo") or not openai_api_key:
        findings = [
            Finding(
                heading="Research direction",
                summary=f"{topic} should be evaluated through adoption, benefits, risk, and near-term trend lenses.",
                source_urls=[str(source.url) for source in sources[:2]],
            ),
            Finding(
                heading="Evidence quality",
                summary="The demo run uses placeholder sources. Add API keys to replace this with live web evidence.",
                source_urls=[str(source.url) for source in sources[2:4]],
            ),
            Finding(
                heading="Next steps",
                summary="Use the generated questions to deepen the search and compare claims across independent sources.",
                source_urls=[str(source.url) for source in sources[4:6]],
            ),
        ]
        report = ResearchReport(
            title=f"Research Report: {topic}",
            executive_summary=f"This demo report outlines a research structure for {topic}.",
            findings=findings,
            limitations=["Offline demo mode does not perform live search or model synthesis."],
            sources=sources,
        )
        return {"report": report}

    evidence = "\n\n".join(
        f"Title: {source.title}\nURL: {source.url}\nSnippet: {source.content}" for source in sources
    )
    client = OpenAIJsonClient(model=_openai_model(state), api_key=openai_api_key)
    findings = client.parse_json(
        prompt=(
            "Synthesize the evidence into findings for a PDF research report.\n"
            "Use source URLs from the evidence when making claims.\n"
            f"Topic: {topic}\n\nEvidence:\n{evidence}\n\nReturn JSON only."
        ),
        schema=Findings,
    )
    report = ResearchReport(
        title=f"Research Report: {topic}",
        executive_summary=findings.executive_summary,
        findings=findings.findings,
        limitations=findings.limitations,
        sources=sources,
    )
    return {"report": report}


def report_generator_agent(state: ResearchState) -> ResearchState:
    topic_slug = "-".join(state["topic"].lower().split())[:60]
    output_path = state.get("output_path") or str(Path("reports") / f"{topic_slug}.pdf")
    return {"output_path": build_pdf(state["report"], output_path)}


def build_research_graph():
    graph = StateGraph(ResearchState)
    graph.add_node("planner", planner_agent)
    graph.add_node("web_search", web_search_agent)
    graph.add_node("summarizer", summarizer_agent)
    graph.add_node("report_generator", report_generator_agent)
    graph.add_edge(START, "planner")
    graph.add_edge("planner", "web_search")
    graph.add_edge("web_search", "summarizer")
    graph.add_edge("summarizer", "report_generator")
    graph.add_edge("report_generator", END)
    return graph.compile()
