from pathlib import Path

import pytest


@pytest.fixture
def project_root():
    """Return the actual Lincoln project root."""
    return Path(__file__).resolve().parents[1]


@pytest.fixture
def tmp_project(tmp_path):
    """Create a minimal temporary project skeleton for validator tests."""
    root = tmp_path / "lincoln"
    (root / "designs" / "checkout-redesign").mkdir(parents=True)
    (root / "requirements" / "2026-06-27-stakeholder").mkdir(parents=True)
    (root / "openspec" / "changes" / "add-csv-export").mkdir(parents=True)
    return root


@pytest.fixture
def design_id():
    return "checkout-redesign"


@pytest.fixture
def session_id():
    return "2026-06-27-stakeholder"
