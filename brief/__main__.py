"""사용법
python -m brief --fin samples/financials.csv --inv samples/investment.json --out out/sample
python -m brief ... --llm   (ANTHROPIC_API_KEY 또는 ant auth login 필요)
"""
import argparse
import json
import sys
from pathlib import Path

from .facts import build_facts, to_json
from .offline import draft
from .render import to_html, to_markdown
from .schema import validate


def main() -> None:
    p = argparse.ArgumentParser(description="재무표와 투자 가정으로 임원용 한 장 보고서를 만든다")
    p.add_argument("--fin", required=True, help="항목,당기,전기,단위,출처 열이 있는 CSV")
    p.add_argument("--inv", help="투자안 가정 JSON")
    p.add_argument("--goal", default="이번 분기 실적 변화와 투자안 진행 여부를 한 장으로 보고한다")
    p.add_argument("--title", default="실적 점검과 투자안 검토")
    p.add_argument("--out", default="out/brief")
    p.add_argument("--llm", action="store_true", help="Claude로 문장을 쓴다. 없으면 규칙 기반 초안")
    a = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    facts, assumptions = build_facts(a.fin, a.inv)
    ids = {f.id for f in facts}

    if a.llm:
        from .llm import write_brief
        brief, errors = write_brief(facts, assumptions, a.goal)
        mode = "Claude"
    else:
        brief = draft(facts, assumptions)
        errors = validate(brief, ids, assumptions)
        mode = "규칙 기반"

    if errors:
        raise SystemExit("검사를 통과하지 못했다\n" + "\n".join(errors))

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.with_suffix(".html").write_text(to_html(brief, facts, a.title, mode), encoding="utf-8")
    out.with_suffix(".md").write_text(to_markdown(brief, facts, a.title), encoding="utf-8")
    out.with_suffix(".json").write_text(
        json.dumps({"brief": brief, "facts": to_json(facts)}, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"{mode} 보고서 저장: {out.with_suffix('.html')}")


if __name__ == "__main__":
    main()
