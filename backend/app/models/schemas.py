from typing import List, Optional
from pydantic import BaseModel, Field


class ClientConfig(BaseModel):
    domain: str
    risk_keywords: List[str] = Field(default_factory=list)
    policies: List[str] = Field(default_factory=list)


class AnalyzeRequest(BaseModel):
    input_type: str
    conversation: Optional[str] = None
    client_config: ClientConfig


class Metadata(BaseModel):
    input_type: str
    detected_languages: List[str] = Field(default_factory=list)


class Insights(BaseModel):
    summary: str = ""
    sentiment: str = ""
    primary_intents: List[str] = Field(default_factory=list)
    topics_entities: List[str] = Field(default_factory=list)


class RiskAnalysis(BaseModel):
    risk_detected: bool = False
    trigger_keywords: List[str] = Field(default_factory=list)


class AdvancedAnalysis(BaseModel):
    call_outcome: str = ""
    risk_score: float = 0.0


class AnalyzeResponse(BaseModel):
    metadata: Metadata
    insights: Insights
    risk_analysis: RiskAnalysis
    advanced_analysis: AdvancedAnalysis
