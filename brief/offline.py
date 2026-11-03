"""API 키 없이 돌아가는 규칙 기반 초안.

모델 모드와 같은 형식을 만들기 때문에 같은 검사와 같은 출력 화면을 그대로 쓴다.
"""
from .facts import Fact


def draft(facts: list[Fact], assumptions: list[str]) -> dict:
    rates = [f for f in facts if f.unit == "%" and f.kind == "change"]
    rates.sort(key=lambda f: abs(f.value), reverse=True)
    npv = next((f for f in facts if f.kind == "npv"), None)
    breakeven = next((f for f in facts if f.kind == "breakeven"), None)
    cash = next((f for f in facts if f.kind == "level" and "연간 현금흐름" in f.label), None)
    worst = [f for f in facts if f.kind == "sensitivity"]

    picks = rates[:2] + ([npv] if npv else rates[2:3])
    evidence = [
        {"fact_id": f.id, "meaning": f"{f.label.replace(' 증감률', '')}은 전기 대비 {['가장', '두 번째로'][i]} 크게 움직인 항목이다"}
        for i, f in enumerate(picks[:2])
    ]
    if npv:
        evidence.append({"fact_id": npv.id, "meaning": "투자안의 현재가치가 본전에 얼마나 가까운지 보여 준다"})
    elif len(picks) > 2:
        evidence.append({"fact_id": picks[2].id, "meaning": "세 번째로 크게 움직인 항목이다"})

    if npv and breakeven and cash:
        thin = worst and any(w.value < 0 for w in worst)
        conclusion = (
            f"투자안 NPV가 {{{npv.id}}}에 그쳐 가정이 조금만 나빠져도 손실로 바뀌므로 조건부로 검토한다"
            if thin else f"투자안 NPV가 {{{npv.id}}}이고 가정이 나빠져도 본전 위에 있어 진행을 검토한다"
        )
        options = [
            {"name": "지금 진행", "condition": f"연간 현금흐름이 {{{breakeven.id}}} 아래로 내려가지 않는다는 근거가 있을 때"},
            {"name": "조건부 보류", "condition": f"연간 현금흐름 가정({{{cash.id}}})을 실제 자료로 다시 확인한 뒤 결정"},
            {"name": "중단", "condition": f"할인율이 오르면 NPV가 {{{worst[0].id}}}까지 떨어지는 위험을 감당할 수 없을 때"} if worst else
            {"name": "중단", "condition": "다른 투자안의 기대 수익이 더 높을 때"},
        ]
        question = "현금흐름 가정을 다시 확인할 때까지 결정을 미룰지 정해 주십시오"
    else:
        top = picks[0]
        conclusion = f"{top.label.replace(' 증감률', '')} 변동({{{top.id}}})의 원인 확인이 먼저다"
        options = [
            {"name": "원인 분석 지시", "condition": "변동이 일회성인지 구조적인지 아직 모를 때"},
            {"name": "현 계획 유지", "condition": "변동이 일회성으로 확인될 때"},
        ]
        question = "원인 분석을 어느 부서에 맡길지 정해 주십시오"

    return {
        "conclusion": conclusion,
        "evidence": evidence,
        "options": options,
        "check_before_deciding": list(assumptions) or ["입력 자료의 출처와 기준일"],
        "decision_question": question,
    }
