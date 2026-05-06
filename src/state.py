"""GraphState and supporting Pydantic models — the single source of truth that
flows between agent nodes."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

RequestType = Literal["informational", "action", "incident", "unclear"]
Severity = Literal["low", "medium", "high"]
Category = Literal[
    "software_license",
    "hardware",
    "access",
    "account",
    "email",
    "printer",
    "av",
    "new_hire",
    "other",
]


class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserContext(BaseModel):
    """Identity + minimal profile passed in by the UI."""

    user_id: str = "demo.user"
    display_name: str = "Demo User"
    email: str = "demo.user@company.com"
    department: str = "Engineering"
    office: str = "SF"


class Intent(BaseModel):
    request_type: RequestType = "unclear"
    category: Category = "other"
    system: str | None = None
    severity: Severity = "low"
    confidence: float = 0.0
    # True when the user is reporting that previously suggested self-service
    # steps did not work. Forces routing to escalation regardless of category.
    follow_up_after_failed_help: bool = False


class RetrievedDoc(BaseModel):
    source_file: str
    chunk_index: int
    snippet: str
    score: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class Action(BaseModel):
    """A planned (and possibly executed) MCP tool call."""

    tool_name: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    status: Literal["PLANNED", "RUNNING", "SUCCESS", "FAILED", "SKIPPED"] = "PLANNED"
    result_summary: str | None = None
    error: str | None = None


class ToolResult(BaseModel):
    tool_name: str
    success: bool
    payload: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TraceEvent(BaseModel):
    """Append-only observability log. One per node entry/exit."""

    node: str
    phase: Literal["enter", "exit"]
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    duration_ms: int | None = None
    detail: str | None = None


class GraphState(BaseModel):
    # Conversation
    messages: list[Message] = Field(default_factory=list)
    user: UserContext = Field(default_factory=UserContext)

    # Intake outputs
    intent: Intent = Field(default_factory=Intent)
    entities: dict[str, Any] = Field(default_factory=dict)

    # Knowledge outputs
    rag_query: str | None = None
    retrieved_docs: list[RetrievedDoc] = Field(default_factory=list)
    knowledge_answer: str | None = None
    knowledge_unknown: bool = False  # True when LLM emitted the "I don't know" sentinel

    # Workflow outputs
    actions: list[Action] = Field(default_factory=list)
    tool_results: list[ToolResult] = Field(default_factory=list)

    # Set by Workflow when no concrete actions can be planned for the user's
    # request — signals the router to fall back to the Knowledge agent (the
    # request might still be answerable from documentation) rather than
    # immediately escalating to a human.
    workflow_no_plan: bool = False

    # Escalation outputs
    escalation_required: bool = False
    escalation_reason: str | None = None
    escalation_ticket_id: str | None = None
    escalation_summary: str | None = None

    # Final user-facing reply (set by Knowledge, Workflow, or Escalation depending on path)
    final_answer: str | None = None

    # Observability
    trace: list[TraceEvent] = Field(default_factory=list)

    def latest_user_message(self) -> Message | None:
        for m in reversed(self.messages):
            if m.role == "user":
                return m
        return None
