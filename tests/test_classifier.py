from datetime import date

from regwatch.classifier import classify_regulation, classify_type, classify_urgency
from regwatch.models import RawChange
from regwatch.regulations import ALL_REGULATIONS


def test_classify_regulation_celex_direct_match():
    raw = RawChange(
        title="Some regulation",
        date=date(2026, 3, 15),
        url="http://example.com",
        source="eurlex",
        celex_id="32022R2554",
    )
    assert classify_regulation(raw, ALL_REGULATIONS) == "dora"


def test_classify_regulation_keyword_in_title():
    raw = RawChange(
        title="ESMA publishes DORA guidelines on ICT risk",
        date=date(2026, 3, 15),
        url="http://example.com",
        source="esma",
    )
    assert classify_regulation(raw, ALL_REGULATIONS) == "dora"


def test_classify_regulation_keyword_in_description():
    raw = RawChange(
        title="New regulatory technical standards",
        date=date(2026, 3, 15),
        url="http://example.com",
        source="eba",
        description="This document relates to Markets in Crypto-Assets regulation",
    )
    assert classify_regulation(raw, ALL_REGULATIONS) == "mica"


def test_classify_regulation_no_match():
    raw = RawChange(
        title="Something about fishing quotas",
        date=date(2026, 3, 15),
        url="http://example.com",
        source="eurlex",
    )
    assert classify_regulation(raw, ALL_REGULATIONS) is None


def test_classify_regulation_multiple_matches_highest_wins():
    raw = RawChange(
        title="DORA DORA DORA and also MiCA",
        date=date(2026, 3, 15),
        url="http://example.com",
        source="eurlex",
    )
    assert classify_regulation(raw, ALL_REGULATIONS) == "dora"


def test_classify_type_guideline():
    assert classify_type("EBA publishes final Guidelines on ICT risk") == "guideline"


def test_classify_type_consultation():
    assert classify_type("ESMA consults on post-trade risk reduction") == "consultation"


def test_classify_type_rts_its():
    assert (
        classify_type("EBA publishes final draft regulatory technical standards")
        == "rts_its"
    )


def test_classify_type_delegated_act():
    assert (
        classify_type("Commission Delegated Regulation on DORA") == "delegated_act"
    )


def test_classify_type_q_and_a():
    assert classify_type("New Q&As available") == "q_and_a"


def test_classify_type_opinion():
    assert classify_type("Opinion of the ECB on prudential matters") == "opinion"


def test_classify_type_fallback():
    assert classify_type("Some random document title") == "legislative_act"


def test_classify_urgency_deadline():
    assert (
        classify_urgency("This enters into force on 1 January", "legislative_act")
        == "high"
    )


def test_classify_urgency_consultation():
    assert classify_urgency("ESMA consults on something", "consultation") == "high"


def test_classify_urgency_q_and_a():
    assert classify_urgency("New Q&As", "q_and_a") == "low"


def test_classify_urgency_default():
    assert classify_urgency("Regular document", "guideline") == "medium"


def test_classify_regulation_empty_title_and_description():
    """Edge: empty strings should return None, not crash."""
    raw = RawChange(title="", date=date(2026, 3, 15), url="http://x.com", source="eurlex")
    assert classify_regulation(raw, ALL_REGULATIONS) is None


def test_classify_regulation_case_insensitive():
    """Edge: keywords should match regardless of case."""
    raw = RawChange(
        title="dora guidelines", date=date(2026, 3, 15),
        url="http://x.com", source="eurlex",
    )
    assert classify_regulation(raw, ALL_REGULATIONS) == "dora"
    raw2 = RawChange(
        title="DORA GUIDELINES", date=date(2026, 3, 15),
        url="http://x.com", source="eurlex",
    )
    assert classify_regulation(raw2, ALL_REGULATIONS) == "dora"


def test_classify_type_case_insensitive():
    """Edge: type patterns should match regardless of case."""
    assert classify_type("EBA PUBLISHES FINAL GUIDELINES") == "guideline"
    assert classify_type("New Consultation Paper") == "consultation"


def test_classify_regulation_word_boundary_short_keywords():
    """Edge: short keywords like DORA should NOT match 'Pandora', 'adorable'."""
    raw = RawChange(title="Pandora papers investigation", date=date(2026, 3, 15),
                    url="http://x.com", source="eurlex")
    result = classify_regulation(raw, ALL_REGULATIONS)
    assert result != "dora"  # Should NOT match "Pandora"


def test_classify_regulation_word_boundary_aml():
    """Edge: AML-like keywords should not match 'caml' or 'hamlet'."""
    raw = RawChange(title="The OCaml programming language", date=date(2026, 3, 15),
                    url="http://x.com", source="eurlex")
    result = classify_regulation(raw, ALL_REGULATIONS)
    assert result != "amld6"
