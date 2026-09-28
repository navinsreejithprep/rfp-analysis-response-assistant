"""Wires the nodes in app/graph/nodes.py into the LangGraph StateGraph.

    START -> ingest_rfp -> extract_requirements -> classify_requirements -> retrieve_evidence
    retrieve_evidence -> assess_capability -> identify_gaps -> draft_response -> validate_response
    validate_response --[revise]--------------> draft_response          (bounded by MAX_REVISIONS)
    validate_response --[next_requirement]----> retrieve_evidence       (advance to requirement i+1)
    validate_response --[done]----------------> final_output -> END

The per-requirement loop and the revision loop are both ordinary conditional
edges driven by `state["next_action"]`, computed deterministically in
validate_response — no sub-graphs needed to get real branching behavior.
"""

from __future__ import annotations

from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from app.graph import nodes
from app.graph.state import GraphState


@lru_cache(maxsize=1)
def build_graph():
    graph = StateGraph(GraphState)

    graph.add_node("ingest_rfp", nodes.ingest_rfp)
    graph.add_node("extract_requirements", nodes.extract_requirements)
    graph.add_node("classify_requirements", nodes.classify_requirements)
    graph.add_node("retrieve_evidence", nodes.retrieve_evidence)
    graph.add_node("assess_capability", nodes.assess_capability)
    graph.add_node("identify_gaps", nodes.identify_gaps)
    graph.add_node("draft_response", nodes.draft_response)
    graph.add_node("validate_response", nodes.validate_response)
    graph.add_node("final_output", nodes.final_output)

    graph.add_edge(START, "ingest_rfp")
    graph.add_edge("ingest_rfp", "extract_requirements")
    graph.add_edge("extract_requirements", "classify_requirements")
    graph.add_edge("classify_requirements", "retrieve_evidence")
    graph.add_edge("retrieve_evidence", "assess_capability")
    graph.add_edge("assess_capability", "identify_gaps")
    graph.add_edge("identify_gaps", "draft_response")
    graph.add_edge("draft_response", "validate_response")

    graph.add_conditional_edges(
        "validate_response",
        nodes.route_after_validation,
        {
            "draft_response": "draft_response",
            "retrieve_evidence": "retrieve_evidence",
            "final_output": "final_output",
        },
    )
    graph.add_edge("final_output", END)

    return graph.compile()
