"""임원용 한 장 보고서의 형식과 검사 규칙.

문장 안의 숫자는 {F01} 같은 근거 ID로만 쓴다. 검사를 통과하면 코드가 ID를 실제 값으로 바꾼다.
"""
import re

BRIEF_SCHEMA = {
    "type": "object",
    "properties": {
        "conclusion": {"type": "string", "description": "결론 한 문장. 숫자는 근거 ID로."},
        "evidence": {
            "type": "array",
            "description": "결론을 받치는 근거 정확히 3개",
            "items": {
                "type": "object",
                "properties": {
                    "fact_id": {"type": "string"},
                    "meaning": {"type": "string", "description": "이 숫자가 결론에 왜 중요한지 한 문장"},
                },
                "required": ["fact_id", "meaning"],
                "additionalProperties": False,
            },
        },
        "options": {
            "type": "array",
            "description": "임원이 고를 선택지 2개 또는 3개",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "condition": {"type": "string", "description": "이 선택지가 맞는 조건. 본전 기준이 있으면 근거 ID로."},
                },
                "required": ["name", "condition"],
                "additionalProperties": False,
            },
        },
        "check_before_deciding": {
            "type": "array",
            "description": "결정 전에 사람이 확인할 가정",
            "items": {"type": "string"},
        },
        "decision_question": {"type": "string", "description": "임원에게 묻는 질문 한 문장"},
    },
    "required": ["conclusion", "evidence", "options", "check_before_deciding", "decision_question"],
    "additionalProperties": False,
}

PLACEHOLDER = re.compile(r"\{(F\d{2})\}")
DIGIT = re.compile(r"[0-9]")


def _texts(brief: dict) -> list[tuple[str, str]]:
    out = [("결론", brief["conclusion"]), ("질문", brief["decision_question"])]
    out += [(f"근거 {i+1}", e["meaning"]) for i, e in enumerate(brief["evidence"])]
    for i, o in enumerate(brief["options"]):
        out += [(f"선택지 {i+1} 이름", o["name"]), (f"선택지 {i+1} 조건", o["condition"])]
    return out


def validate(brief: dict, fact_ids: set[str], given_assumptions: list[str] = ()) -> list[str]:
    """문제 목록을 돌려준다. 비어 있으면 통과.

    확인할 가정은 입력에 적힌 문장을 그대로 옮긴 경우에만 숫자를 허용한다.
    """
    errors = []
    for i, a in enumerate(brief["check_before_deciding"]):
        if a not in given_assumptions and DIGIT.search(PLACEHOLDER.sub("", a)):
            errors.append(f"확인할 가정 {i+1}: 입력에 없는 숫자를 썼다 ({a})")
    if len(brief["evidence"]) != 3:
        errors.append(f"근거는 3개여야 하는데 {len(brief['evidence'])}개다")
    if not 2 <= len(brief["options"]) <= 3:
        errors.append(f"선택지는 2개나 3개여야 하는데 {len(brief['options'])}개다")
    used = [e["fact_id"] for e in brief["evidence"]]
    if len(set(used)) != len(used):
        errors.append("같은 근거를 두 번 썼다")
    for fid in used:
        if fid not in fact_ids:
            errors.append(f"근거 목록에 없는 ID {fid}")
    for where, text in _texts(brief):
        for fid in PLACEHOLDER.findall(text):
            if fid not in fact_ids:
                errors.append(f"{where}: 근거 목록에 없는 ID {fid}")
        if DIGIT.search(PLACEHOLDER.sub("", text)):
            errors.append(f"{where}: 근거 ID 없이 숫자를 직접 썼다 ({text})")
    return errors


def fill(text: str, facts_by_id: dict) -> str:
    return PLACEHOLDER.sub(lambda m: facts_by_id[m.group(1)].text(), text)
