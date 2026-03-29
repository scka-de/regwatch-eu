from regwatch.registry import get_regulations, get_sources


def test_get_regulations_returns_all_five():
    regs = get_regulations()
    ids = [r.id for r in regs]
    assert "dora" in ids and "mica" in ids and "ai_act" in ids and "psd3" in ids and "amld6" in ids
    assert len(regs) == 5


def test_get_sources_returns_all_three():
    sources = get_sources()
    ids = [s.id for s in sources]
    assert "eurlex" in ids and "esma" in ids and "eba" in ids
    assert len(sources) == 3
