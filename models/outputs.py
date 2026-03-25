from pydantic import BaseModel, Field
from typing import Optional


class BoardBrief(BaseModel):
    startup_summary: str
    current_stage: str
    fundraising_goal: str
    assumptions: list[str] = Field(default_factory=list)
    clarification_questions: list[str] = Field(default_factory=list)
    evaluation_criteria: list[str] = Field(default_factory=list)


class InvestorReview(BaseModel):
    investor_id: str
    investor_name: str
    personality: str
    stance: str = Field(description="bullish, cautious, skeptical, or neutral")
    conviction_score: int = Field(ge=1, le=10)
    investment_thesis: str
    key_strengths: list[str] = Field(default_factory=list)
    key_concerns: list[str] = Field(default_factory=list)
    diligence_questions: list[str] = Field(default_factory=list)
    actionable_advice: list[str] = Field(default_factory=list)


class AgentRevisionInstruction(BaseModel):
    investor_id: str
    investor_name: str
    instruction: str


class BoardCritique(BaseModel):
    iteration: int
    convergence_assessment: str
    disagreements: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    revision_instructions: list[AgentRevisionInstruction] = Field(default_factory=list)
    should_stop: bool = False


class RouteOption(BaseModel):
    route_name: str
    why_this_route: str
    expected_tradeoffs: list[str] = Field(default_factory=list)


class ExecutiveBoardSummary(BaseModel):
    executive_summary: str
    funding_readiness_score: int = Field(ge=1, le=10)
    consensus_level: str
    advantages: list[str] = Field(default_factory=list)
    disadvantages: list[str] = Field(default_factory=list)
    key_risks: list[str] = Field(default_factory=list)
    optimal_route: RouteOption
    alternative_route: Optional[RouteOption] = None
    next_30_day_plan: list[str] = Field(default_factory=list)
