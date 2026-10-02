from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from config import MAX_X, MAX_Y

# Canonical mood values used throughout the simulation (UI-drawable).
MoodLiteral = Literal["angry", "anxious", "worried", "neutral", "hopeful", "excited"]

RoleLiteral = Literal[
    "worker",
    "business_owner",
    "politician",
    "student",
    "retiree",
    "activist",
    "farmer",
    "shopkeeper",
    "driver",
    "teacher",
    "municipal_employee",
    "tenant",
]


class NPC(BaseModel):
    id: str
    name: str
    category: str = ""
    role: RoleLiteral = "worker"
    gender: str
    bio: str
    persona: str
    mbti: str
    country: str
    profession: str
    interested_topics: list[str]
    income_level: Literal["low", "medium", "high"]
    political_leaning: float = Field(ge=-1, le=1)
    reputation: float = Field(default=0.5, ge=0, le=1)
    beliefs: list[str] = Field(default_factory=list)
    controversial_ideas: list[str] = Field(default_factory=list)
    x: int = Field(ge=0, le=MAX_X)
    y: int = Field(ge=0, le=MAX_Y)
    lang: Literal["de", "fr", "en"] = "en"
    life_story: str = ""
    expert_reflection: str = ""


class Relationship(BaseModel):
    source_id: str
    target_id: str
    affinity: float = Field(default=0.0, ge=-1, le=1)
    trust: float = Field(default=0.5, ge=0, le=1)


class SimEvent(BaseModel):
    round: int
    npc_id: str
    event_type: Literal["chat", "move", "protest", "price_change", "mood_shift"]
    message: str
    data: dict[str, Any] = Field(default_factory=dict)


SourceKind = Literal["pdf", "csv", "text", "book", "video"]
SourceStatus = Literal["ready"]
TrendDirection = Literal["up", "down", "flat", "unknown"]
ReportDirection = Literal["positive", "negative", "mixed"]
ReportSeverity = Literal["low", "medium", "high"]
ReportTrend = Literal["up", "down", "flat", "mixed"]


class IndicatorSnapshot(BaseModel):
    metric: str
    latest_value: float
    previous_value: float | None = None
    change: float | None = None
    trend: TrendDirection = "unknown"
    latest_period: str | None = None
    source_id: str
    unit: str | None = None


class ContextSourceResponse(BaseModel):
    id: str
    kind: SourceKind
    filename: str
    label: str
    status: SourceStatus = "ready"
    preview_text: str = ""
    summary: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class PolicyContextBundle(BaseModel):
    policy_text: str
    notes_text: str = ""
    trend_summary: str = ""
    source_summaries: list[str] = Field(default_factory=list)
    indicator_snapshots: list[IndicatorSnapshot] = Field(default_factory=list)


class PolicyInput(BaseModel):
    """Simulation input: policy PDF sources, optional CSV trend data, and notes."""

    primary_policy_source_id: str | None = None
    policy_source_ids: list[str] = Field(default_factory=list)
    notes_text: str = Field(default="", max_length=4000)
    trend_source_ids: list[str] = Field(default_factory=list)
    num_rounds: int = 3
    num_npcs: int = 5
    objective: str = Field(default="", max_length=500)
    map_id: str = Field(default="ccity")
    situation_kind: Literal["policy", "vote", "budget"] = "policy"

    @model_validator(mode="after")
    def require_policy_source(self) -> PolicyInput:
        has_files = bool(self.policy_source_ids) or bool(self.primary_policy_source_id)
        notes = (self.notes_text or "").strip()
        if not has_files and len(notes) < 40:
            raise ValueError(
                "Provide at least one policy source upload, or at least 40 characters in notes_text."
            )
        return self


class OrchestratorPlan(BaseModel):
    """Swarm orchestrator output: which NPCs initiate this round."""
    initiator_ids: list[str]
    rationale: str = ""


class RelationshipRecord(BaseModel):
    """A directed social relationship between two NPCs."""
    source_id: str
    target_id: str
    affinity: float = 0.5   # -1.0 (hostile) to 1.0 (close friend)
    trust: float = 0.5      # 0.0 (distrustful) to 1.0 (fully trusted)


class RelationshipsResponse(BaseModel):
    """Wrapper for the relationship generation LLM call."""
    relationships: list[RelationshipRecord]


# --- Structured output response models for LLM calls ---


class PolicyAnalysis(BaseModel):
    """Structured response from the policy parsing LLM call."""

    sectors: list[str]
    stakeholders: list[str]
    economic_impacts: list[str]
    controversy_level: Literal["low", "medium", "high"]


class NPCGenerationResponse(BaseModel):
    """Structured response from the NPC generation LLM call."""

    npcs: list[NPC]
    relationships: list[Relationship]


MemType = Literal["observation", "reflection", "plan"]


class NPCEvent(BaseModel):
    """A single event produced by an NPC during a simulation round."""

    event_type: Literal["chat", "move", "protest", "price_change", "mood_shift"]
    message: str
    # chat
    target_npc_id: str = ""
    dialogue: str = ""
    # move
    to_x: int | None = None
    to_y: int | None = None
    # mood_shift
    new_mood: str = ""
    used_source_ids: list[str] = Field(default_factory=list)
    grounded: bool = False

    @model_validator(mode="after")
    def canonicalize_mood(self) -> NPCEvent:
        if not self.new_mood:
            return self
        allowed = {"angry", "anxious", "worried", "neutral", "hopeful", "excited"}
        if self.new_mood not in allowed:
            self.new_mood = "neutral"
        return self


class NPCRoundResponse(BaseModel):
    """Simplified NPC round response — flat events, optional perception."""

    events: list[NPCEvent]
    perception: str = ""

    @model_validator(mode="before")
    @classmethod
    def normalize_shape(cls, data: Any) -> Any:
        # Some models return a single event dict instead of {"events": [...]}
        if isinstance(data, dict) and "event_type" in data:
            return {"events": [data]}
        return data


class ReflectionResponse(BaseModel):
    """Structured response from an NPC's reflection phase."""

    insights: list[str]


class ReportImpact(BaseModel):
    title: str
    description: str
    direction: ReportDirection
    severity: ReportSeverity


class ReportStat(BaseModel):
    label: str
    value: str
    trend: ReportTrend | None = None


class ChartSlice(BaseModel):
    label: str
    value: int = Field(ge=0)


class BarChartEntry(BaseModel):
    label: str
    value: int = Field(ge=0)


class PieChartData(BaseModel):
    title: str
    slices: list[ChartSlice]


class BarChartData(BaseModel):
    title: str
    bars: list[BarChartEntry]


class EconomicReportNarrative(BaseModel):
    headline: str
    summary: str
    livelihood_impact: str
    top_impacts: list[ReportImpact]
    notable_events: list[str]


class EconomicReportResponse(BaseModel):
    headline: str
    summary: str
    livelihood_impact: str
    top_impacts: list[ReportImpact]
    key_stats: list[ReportStat]
    pie_chart: PieChartData
    bar_chart: BarChartData
    notable_events: list[str]
