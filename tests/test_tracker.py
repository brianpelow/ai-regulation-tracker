"""Tests for AI Regulation Tracker."""

from tracker.sources import RegulatoryItem, is_ai_relevant, is_horizon_item, AI_KEYWORDS
from tracker.synthesizer import _template_digest, ENGINEERING_IMPLICATIONS


def make_item(title: str, summary: str = "", agency: str = "OCC") -> RegulatoryItem:
    return RegulatoryItem(title=title, url="https://example.com", agency=agency, summary=summary)


def test_ai_relevant_detects_model_risk() -> None:
    item = make_item("OCC Issues Guidance on Model Risk Management for AI Systems")
    assert is_ai_relevant(item)


def test_ai_relevant_detects_algorithmic() -> None:
    item = make_item("CFPB Proposes Rule on Algorithmic Credit Decisioning")
    assert is_ai_relevant(item)


def test_ai_relevant_detects_llm() -> None:
    item = make_item("Federal Reserve Examines Large Language Model Use in Banking")
    assert is_ai_relevant(item)


def test_ai_relevant_rejects_unrelated() -> None:
    item = make_item("OCC Releases Annual Report on Community Bank Performance")
    assert not is_ai_relevant(item)


def test_ai_relevant_detects_generative_ai() -> None:
    item = make_item("SEC Issues Staff Bulletin on Generative AI Disclosures")
    assert is_ai_relevant(item)


def test_horizon_detects_proposed_rule() -> None:
    item = make_item("OCC Proposed Rule on AI Model Governance", "Comment period closes March 2026")
    assert is_horizon_item(item)


def test_horizon_detects_rfi() -> None:
    item = make_item("Federal Reserve Request for Information on AI in Banking")
    assert is_horizon_item(item)


def test_horizon_rejects_enforcement() -> None:
    item = make_item("OCC Issues Enforcement Action Against Bank for Model Failures")
    assert not is_horizon_item(item)


def test_template_digest_contains_issue_number() -> None:
    import datetime
    digest = _template_digest([], [], issue_number=7, today=datetime.date(2026, 5, 10))
    assert "Issue #7" in digest


def test_template_digest_contains_agency_items() -> None:
    import datetime
    items = [make_item("AI Governance Proposed Rule", agency="OCC")]
    digest = _template_digest(items, [], issue_number=1, today=datetime.date(2026, 5, 10))
    assert "OCC" in digest


def test_template_digest_contains_footer() -> None:
    import datetime
    digest = _template_digest([], [], issue_number=1, today=datetime.date(2026, 5, 10))
    assert "Brian Pelow" in digest


def test_template_digest_no_items_message() -> None:
    import datetime
    digest = _template_digest([], [], issue_number=1, today=datetime.date(2026, 5, 10))
    assert "No new AI-relevant" in digest


def test_engineering_implications_count() -> None:
    assert len(ENGINEERING_IMPLICATIONS) >= 7


def test_ai_keywords_coverage() -> None:
    assert "model risk" in [k.lower() for k in AI_KEYWORDS]
    assert "SR 11-7" in AI_KEYWORDS
    assert "generative AI" in AI_KEYWORDS