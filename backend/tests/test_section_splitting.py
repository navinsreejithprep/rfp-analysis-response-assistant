"""split_into_sections is pure Python (no LLM call) — see app/graph/nodes.py.
Exercises its heading-detection and safety-net fallback directly.
"""

from pathlib import Path

from app.graph.nodes import MAX_SECTION_CHARS, split_into_sections

SAMPLE_RFP_PATH = Path(__file__).resolve().parent.parent / "data" / "sample_rfp" / "sample_rfp.md"


def test_splits_on_markdown_h2_headings():
    text = (
        "# RFP Title\n\nSome preamble.\n\n"
        "## 1. Background\nBackground text.\n\n"
        "## 2. Functional Requirements\nReq A. Req B.\n\n"
        "## 3. Technical Requirements\nReq C.\n"
    )
    sections = split_into_sections(text)
    assert len(sections) == 3
    assert "Background text" in sections[0]
    assert "RFP Title" in sections[0]  # preamble before first ## heading stays attached
    assert "Req A" in sections[1]
    assert "Req C" in sections[2]


def test_falls_back_to_plain_numbered_headings_without_markdown():
    text = (
        "1. BACKGROUND\nSome background.\n\n"
        "2. TECHNICAL REQUIREMENTS\nThe vendor must do X.\n\n"
        "3. COMMERCIAL TERMS\nPricing details.\n"
    )
    sections = split_into_sections(text)
    assert len(sections) == 3
    assert "background" in sections[0].lower()
    assert "vendor must do X" in sections[1]
    assert "Pricing details" in sections[2]


def test_no_detectable_headings_returns_single_section():
    text = "This RFP has no section headings at all, just prose. " * 5
    sections = split_into_sections(text)
    assert len(sections) == 1
    assert sections[0] == text


def test_oversized_section_gets_further_chunked_by_safety_net():
    huge = "word " * (MAX_SECTION_CHARS // 4)  # well over MAX_SECTION_CHARS, no headings
    sections = split_into_sections(huge)
    assert len(sections) > 1
    assert all(len(s) <= MAX_SECTION_CHARS for s in sections)


def test_decimal_sub_items_are_not_mistaken_for_section_headings():
    # "2.1", "2.2" style requirement numbering must not itself split into
    # per-requirement sections when there's no Markdown structure.
    text = "2.1 The vendor shall do A.\n2.2 The vendor shall do B.\n2.3 The vendor shall do C.\n"
    sections = split_into_sections(text)
    assert len(sections) == 1


def test_sample_rfp_splits_into_its_eight_numbered_sections():
    text = SAMPLE_RFP_PATH.read_text(encoding="utf-8")
    sections = split_into_sections(text)
    assert len(sections) == 8
    assert "Functional Requirements" in sections[1]
    assert "Experience & Credentials" in sections[7]
