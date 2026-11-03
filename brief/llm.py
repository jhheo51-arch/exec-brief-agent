"""Claude가 근거 목록을 읽고 보고서 문장을 쓴다.

모델은 숫자를 직접 쓰지 못하고 근거 ID만 고른다. 검사에 걸리면 문제 목록을 돌려주고 한 번 더 쓰게 한다.
"""
import json

import anthropic

from .facts import Fact, facts_table
from .schema import BRIEF_SCHEMA, validate

MODEL = "claude-opus-5-5"

SYSTEM = """너는 기획조정 부서에서 임원 보고서를 쓰는 담당자다.
임원이 이 한 장만 읽고 바로 결정할 수 있게 쓴다.

규칙
1. 숫자는 직접 쓰지 않는다. 숫자가 필요하면 근거 목록의 ID를 {F03}처럼 중괄호로 쓴다.
2. 근거는 결론을 가장 잘 받치는 것 정확히 3개를 고른다.
3. 선택지는 2개나 3개이고, 각 선택지가 맞는 조건을 쓴다. 본전 기준이 있으면 그 ID를 쓴다.
4. 확인할 가정에는 입력에 적힌 가정 문장을 그대로 옮기고, 근거 목록에서 보이는 위험이 있으면 숫자 없이 덧붙인다.
5. 결정은 사람이 한다. 추천은 해도 되지만 질문으로 끝낸다.
6. 가운데 점, 화살표, 해시태그를 쓰지 않는다. 문장은 짧게 쓴다."""


def write_brief(facts: list[Fact], assumptions: list[str], goal: str, client: anthropic.Anthropic | None = None) -> tuple[dict, list[str]]:
    client = client or anthropic.Anthropic()
    ids = {f.id for f in facts}
    messages = [{
        "role": "user",
        "content": (
            f"보고 목적: {goal}\n\n근거 목록\n{facts_table(facts)}\n\n"
            "확인할 가정(입력)\n" + "\n".join(f"- {a}" for a in assumptions)
        ),
    }]

    for attempt in range(2):
        response = client.beta.messages.create(
            model=MODEL,
            max_tokens=16000,
            system=SYSTEM,
            messages=messages,
            output_config={"effort": "medium", "format": {"type": "json_schema", "schema": BRIEF_SCHEMA}},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
        if response.stop_reason == "refusal":
            raise RuntimeError(f"모델이 응답을 거절했다: {response.stop_details}")
        if response.stop_reason == "max_tokens":
            raise RuntimeError("응답이 max_tokens에서 끊겼다")

        text = next(b.text for b in response.content if b.type == "text")
        brief = json.loads(text)
        errors = validate(brief, ids, assumptions)
        if not errors:
            return brief, []
        messages += [
            {"role": "assistant", "content": response.content},
            {"role": "user", "content": "검사에서 아래 문제가 나왔다. 고쳐서 다시 써라.\n" + "\n".join(f"- {e}" for e in errors)},
        ]
    return brief, errors
