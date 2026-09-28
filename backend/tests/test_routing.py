from app.graph.nodes import route_after_validation


def test_routes_to_draft_response_on_revise():
    assert route_after_validation({"next_action": "revise"}) == "draft_response"


def test_routes_to_retrieve_evidence_for_next_requirement():
    assert route_after_validation({"next_action": "next_requirement"}) == "retrieve_evidence"


def test_routes_to_final_output_when_done():
    assert route_after_validation({"next_action": "done"}) == "final_output"
