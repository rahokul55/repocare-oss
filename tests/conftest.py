from pathlib import Path

import pytest


@pytest.fixture
def write_junit(tmp_path):
    def make(xml: str, name: str = "report.xml") -> Path:
        destination = tmp_path / name
        destination.write_text(xml, encoding="utf-8")
        return destination

    return make
