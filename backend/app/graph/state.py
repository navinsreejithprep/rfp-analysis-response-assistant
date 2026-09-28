"""LangGraph state definition.

State is a plain TypedDict rather than Pydantic: LangGraph merges node
return values into this dict key-by-key between steps, and a TypedDict keeps
that merge mechanism obvious (no validation-on-every-partial-update surprises).
Every field that actually needs a schema (Requirement, CapabilityAssessment,
etc.) is still a validated Pydantic model *inside* this dict — see
app/models/schemas.py — it's just serialized to a plain dict while it lives
in graph state.
"""

from __future__ import annotations

from typing import Any, Optional, TypedDict


class TraceEventDict(TypedDict):
    node: str
    summary: str


class GraphState(TypedDict, total=False):
    job_id: str
    rfp_text: str

    # Knowledge base document names available for retrieval (for display only)
    knowledge_base_documents: list[str]

    # Populated by extract_requirements / classify_requirements
    requirements: list[dict[str, Any]]

    # Iteration cursor: which requirement in `requirements` is being processed
    current_index: int
    revision_count: int

    # Scratch space for the requirement currently in flight
    current_evidence: list[dict[str, Any]]
    current_assessment: Optional[dict[str, Any]]
    current_gap: Optional[dict[str, Any]]
    current_response: Optional[dict[str, Any]]
    current_validation: Optional[dict[str, Any]]
    current_trace: list[TraceEventDict]

    # Finished RequirementResult dicts, one per requirement
    results: list[dict[str, Any]]

    # Set by validate_response, read by the route_after_validation conditional
    # edge. Must be declared here: LangGraph only persists state keys that are
    # part of the schema — an undeclared key returned by a node is silently
    # dropped during the merge, which is exactly the bug this field's absence
    # caused the first time around (see README "Limitations" / git history).
    next_action: str  # "revise" | "next_requirement" | "done"

    # Set by final_output
    final_analysis: Optional[dict[str, Any]]

    # Workflow bookkeeping surfaced to the API for progress display
    status: str  # "running" | "completed" | "error"
    current_node: str
    error: Optional[str]
