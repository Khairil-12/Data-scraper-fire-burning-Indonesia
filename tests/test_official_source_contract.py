from pathlib import Path

DECISION_PATH = Path(__file__).resolve().parents[1] / "docs/official-source-decision.md"


def test_official_sources_are_documented_and_evaluated():
    assert DECISION_PATH.exists(), "docs/official-source-decision.md must exist"
    content = DECISION_PATH.read_text(encoding="utf-8")
    required_candidates = [
        "SIPONGI / KLHK",
        "BNPB",
        "BPBD",
        "Manggala Agni",
        "BMKG",
    ]
    for candidate in required_candidates:
        assert candidate in content, f"Candidate {candidate} must be evaluated"
    assert "REJECTED" in content
