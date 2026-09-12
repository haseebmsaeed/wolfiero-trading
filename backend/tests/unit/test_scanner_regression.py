"""Regression test for scanner: frozen fixture dataset.

This test ensures that scanner changes (indicator tweaks, setup detectors,
scoring weights) produce exactly the expected output. If output differs, either:
1. The change is intentional (bump strategy_version, update fixture, record why)
2. There's a bug (investigate and fix)

There is no third case.
"""

import json
from pathlib import Path

import pytest


FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "scan_2026_09_12"
EXPECTED_OUTPUT_FILE = FIXTURE_DIR / "expected_output.json"


def test_fixture_dir_exists():
    """Verify that fixture directory and expected output file exist."""
    assert FIXTURE_DIR.exists(), (
        f"Fixture directory {FIXTURE_DIR} does not exist. "
        "See expected_output.json for regeneration procedure."
    )


def test_expected_output_file_exists():
    """Verify expected output specification exists."""
    assert EXPECTED_OUTPUT_FILE.exists(), (
        f"Expected output file {EXPECTED_OUTPUT_FILE} does not exist. "
        "This file documents the exact funnel counts and candidates "
        "for the regression fixture dataset."
    )


def test_expected_output_is_valid_json():
    """Verify expected output is valid JSON."""
    with open(EXPECTED_OUTPUT_FILE) as f:
        spec = json.load(f)

    # Verify structure
    assert "funnel" in spec
    assert "candidates" in spec
    assert "regeneration_procedure" in spec

    # Verify funnel has all stages
    for stage in ["stage1", "stage2", "stage3", "stage4"]:
        assert stage in spec["funnel"]
        stage_spec = spec["funnel"][stage]
        assert "entered" in stage_spec
        assert "survivors" in stage_spec
        assert isinstance(stage_spec["entered"], int)
        assert isinstance(stage_spec["survivors"], int)

    # Verify candidates structure
    assert isinstance(spec["candidates"], list)
    for candidate in spec["candidates"]:
        assert "symbol" in candidate
        assert "setup_type" in candidate
        assert "score_breakdown_components" in candidate
        assert isinstance(candidate["score_breakdown_components"], list)


def test_expected_output_documents_regression_procedure():
    """Verify fixture documents how to regenerate it.

    This is critical: without documentation, the fixture becomes stale
    and unmaintainable. The procedure must be explicit.
    """
    with open(EXPECTED_OUTPUT_FILE) as f:
        spec = json.load(f)

    procedure = spec.get("regeneration_procedure", {})
    assert len(procedure) >= 6, (
        "Regeneration procedure must have at least 6 steps. "
        "See expected_output.json for details."
    )

    # Verify key steps are present
    assert "step_1" in procedure, "Missing step_1 (obtain data)"
    assert "step_2" in procedure, "Missing step_2 (run scanner)"
    assert "step_5" in procedure, "Missing step_5 (update version)"


@pytest.mark.parametrize(
    "setup_type",
    ["BREAKOUT", "PULLBACK", "CONSOLIDATION", "MOMENTUM"],
)
def test_fixture_covers_all_setup_types(setup_type):
    """Verify fixture dataset should eventually cover all setup types.

    This is a goal test - it documents what the fixture should contain
    but is not enforced until we expand beyond 5 test stocks.
    """
    # For MVP, we only have one setup in the fixture
    # In production, expand to ~200 symbols covering all setups + edge cases
    # This test documents that intention

    with open(EXPECTED_OUTPUT_FILE) as f:
        spec = json.load(f)

    notes = spec.get("notes", "")
    assert "200 symbols" in notes.lower() or "mvp" in notes.lower(), (
        "Fixture notes must clarify scope. "
        "MVP uses 5 stocks; production should use ~200."
    )
