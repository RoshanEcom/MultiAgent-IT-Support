"""LangGraph wiring — turns the four agent nodes into a single state machine with
conditional routing.

Routing rules:
- intake → knowledge        if request_type == informational AND confidence >= 0.5
- intake → workflow         if request_type in {action, incident} AND confidence >= 0.5
- intake → escalation       otherwise (unclear OR low confidence)
- knowledge → escalation    if Knowledge agent emitted "I don't know"
- knowledge → END           if Knowledge agent answered
- workflow → escalation     if any action failed OR severity == high OR no actions planned
- workflow → END            if all actions succeeded and severity != high
- escalation → END          always
"""
from __future__ import annotations

from functools import lru_cache

from langgraph.graph import END, StateGraph

from src.agents.escalation import escalation_node
from src.agents.intake import intake_node
from src.agents.knowledge import knowledge_node
from src.agents.workflow import workflow_node
from src.state import GraphState

CONFIDENCE_THRESHOLD = 0.5


def route_from_intake(state: GraphState) -> str:
    intent = state.intent
    # Follow-up-after-failed-help short-circuits all other routing — the user has
    # already exhausted self-service, send them straight to a human.
    if intent.follow_up_after_failed_help:
        return "escalation"
    if intent.confidence < CONFIDENCE_THRESHOLD or intent.request_type == "unclear":
        return "escalation"
    if intent.request_type == "informational":
        return "knowledge"
    if intent.request_type in ("action", "incident"):
        return "workflow"
    return "escalation"


def route_from_knowledge(state: GraphState) -> str:
    if state.knowledge_unknown or state.escalation_required:
        return "escalation"
    return END


def route_from_workflow(state: GraphState) -> str:
    # If Workflow couldn't plan any actions, give Knowledge a chance — the
    # runbooks may have a self-service answer even when no automation applies.
    if state.workflow_no_plan:
        return "knowledge"
    if state.escalation_required:
        return "escalation"
    return END


@lru_cache(maxsize=1)
def build_app():
    graph = StateGraph(GraphState)

    graph.add_node("intake", intake_node)
    graph.add_node("knowledge", knowledge_node)
    graph.add_node("workflow", workflow_node)
    graph.add_node("escalation", escalation_node)

    graph.set_entry_point("intake")

    graph.add_conditional_edges(
        "intake",
        route_from_intake,
        {
            "knowledge": "knowledge",
            "workflow": "workflow",
            "escalation": "escalation",
        },
    )
    graph.add_conditional_edges(
        "knowledge",
        route_from_knowledge,
        {"escalation": "escalation", END: END},
    )
    graph.add_conditional_edges(
        "workflow",
        route_from_workflow,
        {"escalation": "escalation", "knowledge": "knowledge", END: END},
    )
    graph.add_edge("escalation", END)

    return graph.compile()
