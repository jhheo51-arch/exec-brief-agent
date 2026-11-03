from pathlib import Path

from brief.facts import build_facts
from brief.offline import draft
from brief.schema import fill, validate

ROOT = Path(__file__).resolve().parents[1]


def sample():
    facts, assumptions = build_facts(ROOT / "samples/financials.csv", ROOT / "samples/investment.json")
    return facts, assumptions, {f.id for f in facts}


def test_offline_draft_passes():
    facts, assumptions, ids = sample()
    assert validate(draft(facts, assumptions), ids, assumptions) == []


def test_number_outside_placeholder_fails():
    facts, assumptions, ids = sample()
    brief = draft(facts, assumptions)
    brief["conclusion"] = "NPV가 0.39억 원이라 조건부로 검토한다"
    assert validate(brief, ids, assumptions)


def test_unknown_id_fails():
    facts, assumptions, ids = sample()
    brief = draft(facts, assumptions)
    brief["evidence"][0]["fact_id"] = "F99"
    assert validate(brief, ids, assumptions)


def test_evidence_count_must_be_three():
    facts, assumptions, ids = sample()
    brief = draft(facts, assumptions)
    brief["evidence"] = brief["evidence"][:2]
    assert validate(brief, ids, assumptions)


def test_fill_uses_computed_value():
    facts, _, _ = sample()
    npv = next(f for f in facts if f.kind == "npv")
    assert fill(f"NPV는 {{{npv.id}}}", {f.id: f for f in facts}) == f"NPV는 {npv.text()}"
