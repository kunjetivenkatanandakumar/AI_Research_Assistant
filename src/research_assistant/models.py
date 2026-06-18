from __future__ import annotations

from typing import TypedDict

from pydantic import BaseModel, Field, HttpUrl


class ResearchQuestion(BaseModel):
    question: str = Field(..., description="A focused research question.")
    rationale: str = Field(..., description="Why this question matters for the report.")


class Source(BaseModel):
    title: str
    url: HttpUrl | str
    content: str
    score: float | None = None


class Finding(BaseModel):
    heading: str
    summary: str
    source_urls: list[str] = Field(default_factory=list)


class ResearchReport(BaseModel):
    title: str
    executive_summary: str
    findings: list[Finding]
    limitations: list[str] = Field(default_factory=list)
    sources: list[Source] = Field(default_factory=list)


class ResearchState(TypedDict, total=False):
    topic: str
    questions: list[ResearchQuestion]
    sources: list[Source]
    report: ResearchReport
    output_path: str
    offline_demo: bool
    openai_api_key: str
    tavily_api_key: str
    openai_model: str
