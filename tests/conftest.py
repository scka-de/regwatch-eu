import pytest


@pytest.fixture
def regwatch_instance(tmp_path):
    from regwatch import RegWatch

    return RegWatch(cache_dir=str(tmp_path / ".regwatch"))
