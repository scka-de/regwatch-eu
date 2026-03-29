from regwatch.regulations.ai_act import ai_act
from regwatch.regulations.amld6 import amld6
from regwatch.regulations.dora import dora
from regwatch.regulations.mica import mica
from regwatch.regulations.psd3 import psd3


def test_dora_regulation():
    assert dora.id == "dora"
    assert "32022R2554" in dora.celex_ids
    assert any("DORA" in kw for kw in dora.keywords)


def test_mica_regulation():
    assert mica.id == "mica"
    assert "32023R1114" in mica.celex_ids


def test_ai_act_regulation():
    assert ai_act.id == "ai_act"
    assert "32024R1689" in ai_act.celex_ids


def test_psd3_regulation():
    assert psd3.id == "psd3"
    assert any("PSD3" in kw for kw in psd3.keywords)


def test_amld6_regulation():
    assert amld6.id == "amld6"
    assert any("AMLD" in kw for kw in amld6.keywords)


def test_all_regulations_have_required_fields():
    for reg in [dora, mica, ai_act, psd3, amld6]:
        assert reg.id
        assert reg.name
        assert len(reg.keywords) > 0
