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
    # Code-owned stance on the question: -1 (against) .. +1 (for). Seeded once by an Apertus
    # elicitation, then moved only by the Python opinion dynamics (never rewritten by the LLM).
    stance: float = Field(default=0.0, ge=-1, le=1)
    stance_reason: str = ""
    impact: str = ""


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
    # 30 000: the balanced bilingual Linden sample is ~4 500 characters and a pasted booklet section more; the old cap of 4 000 made
    # the UI fail silently with HTTP 422 (found by the live screenshot run). Whole documents go through the PDF upload path.
    notes_text: str = Field(default="", max_length=30000)
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
    # Whom does the measure favour politically? -1 = left/progressive voters, +1 = right/conservative.
    ideological_valence: float = Field(default=0.0, ge=-1, le=1)

    @classmethod
    def prompt_example(cls) -> dict[str, Any]:
        return {
            "sectors": ["Retail", "Construction"],
            "stakeholders": ["Tenants pay more tax", "Shop owners hope for demand"],
            "economic_impacts": ["Household tax burden rises", "School construction orders local firms"],
            "controversy_level": "medium",
            "ideological_valence": -0.4,
        }


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

    @model_validator(mode="before")
    @classmethod
    def null_to_default(cls, data: Any) -> Any:
        """The model emits null for string/list fields it has nothing to say for."""
        if isinstance(data, dict):
            data = dict(data)
            for k in ("message", "target_npc_id", "dialogue", "new_mood"):
                if data.get(k) is None:
                    data[k] = ""
            ids = data.get("used_source_ids")
            if ids is None:
                data["used_source_ids"] = []
            elif isinstance(ids, (str, int)):
                data["used_source_ids"] = [str(ids)]
            elif isinstance(ids, list):  # the 8B writes [1, 2] for ["P1", "P2"]
                data["used_source_ids"] = [str(x) for x in ids]
            for k in ("to_x", "to_y"):
                if data.get(k) in ("", "null"):
                    data[k] = None
        return data

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

    @classmethod
    def prompt_example(cls, lang: str = "en") -> dict[str, Any]:
        """Three-event example with <instruction> placeholders in the resident's language.

        Research E2/E2b: the example *is* the behaviour policy. Placeholder defaults ("...", 0)
        are echoed and leave the 8B at one chat per turn; a filled example is parroted (8B: 53 %
        of dialogue). Instruction placeholders gave 0 % parroting, 2.0 events/turn on the 70B
        (with `move` kept) and 1.8 on the 8B (from 1.0). The types shown are NOT binding."""
        t = {
            "de": ("<was du tust, ein Satz>", "<id aus der Nearby-Liste>", "<deine genauen Worte, auf Deutsch>",
                   "<P1, P2 ...>", "<wie sich deine Stimmung ändert und warum>", "<wohin und warum>",
                   "<was du in dieser Runde bemerkst>"),
            "fr": ("<ce que tu fais, une phrase>", "<id de la liste Nearby>", "<tes mots exacts, en français>",
                   "<P1, P2 ...>", "<comment ton humeur change et pourquoi>", "<où et pourquoi>",
                   "<ce que tu remarques ce tour>"),
            "en": ("<what you do, one sentence>", "<id from the Nearby list>", "<your exact words>",
                   "<P1, P2 ...>", "<how your mood changes and why>", "<where and why>",
                   "<what you notice this round>"),
        }[lang if lang in ("de", "fr") else "en"]
        mood = "<angry|anxious|worried|neutral|hopeful|excited>"
        base = {"target_npc_id": "", "dialogue": "", "to_x": None, "to_y": None, "new_mood": "", "used_source_ids": []}
        return {
            "events": [
                {**base, "event_type": "chat", "message": t[0], "target_npc_id": t[1], "dialogue": t[2], "used_source_ids": [t[3]]},
                {**base, "event_type": "mood_shift", "message": t[4], "new_mood": mood},
                {**base, "event_type": "move", "message": t[5], "to_x": 0, "to_y": 0},
            ],
            "perception": t[6],
        }

    @model_validator(mode="before")
    @classmethod
    def normalize_shape(cls, data: Any) -> Any:
        # Some models return a single event dict instead of {"events": [...]}
        if isinstance(data, dict) and "event_type" in data:
            return {"events": [data]}
        return data


class ImpactResponse(BaseModel):
    """How the measure touches one resident, plus the best argument each way (resident's language).

    The stance is NOT asked for: Apertus answers "yes" for every persona (research E11)."""

    impact: Literal["benefit", "harm", "mixed", "none"] = "mixed"
    support_reason: str = ""
    oppose_reason: str = ""


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
    stance_summary: dict[str, Any] | None = None
