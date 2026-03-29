"""Extended classifier tests for urgency patterns and EuroVoc scoring."""

from datetime import date

from regwatch.classifier import classify_regulation, classify_urgency
from regwatch.models import RawChange
from regwatch.regulations.base import Regulation


def test_classify_urgency_deadline_pattern():
    assert classify_urgency("Response deadline: 15 March 2026", "legislative_act") == "high"


def test_classify_urgency_final_draft_pattern():
    assert classify_urgency("Final draft RTS on ICT risk", "rts_its") == "high"


def test_classify_urgency_opinion_is_low():
    assert classify_urgency("Opinion on supervisory approach", "opinion") == "low"


def test_classify_urgency_enters_into_force():
    result = classify_urgency("Regulation enters into force on 1 January", "legislative_act")
    assert result == "high"


def test_classify_regulation_eurovoc_match():
    """EuroVoc codes should be weighted 2x in scoring."""
    reg = Regulation(
        id="test_reg",
        name="Test",
        keywords=["obscure keyword nobody uses"],
        eurovoc_codes=["1234"],
    )
    raw = RawChange(
        title="Unrelated title",
        date=date(2026, 3, 15),
        url="http://example.com/1",
        source="eurlex",
        eurovoc_codes=["1234"],
    )
    result = classify_regulation(raw, [reg])
    assert result == "test_reg"


def test_classify_regulation_source_tags():
    """Source-specific tags should contribute to scoring."""
    reg = Regulation(
        id="tagged_reg",
        name="Tagged",
        keywords=[],
        esma_tags=["digital resilience"],
    )
    raw = RawChange(
        title="ESMA publishes digital resilience guidelines",
        date=date(2026, 3, 15),
        url="http://example.com/2",
        source="esma",
    )
    result = classify_regulation(raw, [reg])
    assert result == "tagged_reg"


def test_classify_regulation_llm_fallback_called():
    """When deterministic layers fail, LLM fallback is called."""
    reg = Regulation(id="x", name="X", keywords=["zzzzzzz"])
    raw = RawChange(
        title="Ambiguous document",
        date=date(2026, 3, 15),
        url="http://example.com/3",
        source="eurlex",
    )
    def fake_llm(title, desc):
        return "mica"

    result = classify_regulation(raw, [reg], llm_classify=fake_llm)
    assert result == "mica"


def test_classify_regulation_llm_not_called_when_deterministic_matches():
    """LLM fallback should NOT be called when deterministic layers match."""
    reg = Regulation(id="dora", name="DORA", keywords=["DORA"])
    raw = RawChange(
        title="DORA implementation update",
        date=date(2026, 3, 15),
        url="http://example.com/4",
        source="eurlex",
    )
    calls = []

    def fake_llm(title, desc):
        calls.append(1)
        return "mica"

    result = classify_regulation(raw, [reg], llm_classify=fake_llm)
    assert result == "dora"
    assert len(calls) == 0
