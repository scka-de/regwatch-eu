from datetime import date

from regwatch.models import ClassifiedChange, RawChange, make_change_id


def test_raw_change_creation():
    rc = RawChange(
        title="EBA publishes DORA guidelines",
        date=date(2026, 3, 15),
        url="https://www.eba.europa.eu/example",
        source="eba",
    )
    assert rc.title == "EBA publishes DORA guidelines"
    assert rc.source == "eba"
    assert rc.description == ""
    assert rc.celex_id == ""
    assert rc.eurovoc_codes == []


def test_raw_change_with_all_fields():
    rc = RawChange(
        title="Commission Delegated Regulation on DORA",
        date=date(2026, 3, 10),
        url="http://publications.europa.eu/resource/cellar/abc123",
        source="eurlex",
        description="Full text of the regulation",
        celex_id="32022R2554",
        eurovoc_codes=["2441", "3236"],
    )
    assert rc.celex_id == "32022R2554"
    assert rc.eurovoc_codes == ["2441", "3236"]


def test_classified_change_creation():
    cc = ClassifiedChange(
        id="abc123",
        title="EBA publishes DORA guidelines",
        date=date(2026, 3, 15),
        url="https://www.eba.europa.eu/example",
        source="eba",
        regulation="dora",
        type="guideline",
        urgency="medium",
        summary=None,
    )
    assert cc.regulation == "dora"
    assert cc.type == "guideline"
    assert cc.summary is None


def test_classified_change_id_from_url():
    id1 = make_change_id("https://example.com/doc1")
    id2 = make_change_id("https://example.com/doc2")
    id_same = make_change_id("https://example.com/doc1")
    assert id1 != id2
    assert id1 == id_same
    assert len(id1) == 64
