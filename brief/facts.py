"""입력 파일에서 숫자를 계산해 근거 목록(facts)을 만든다.

숫자는 전부 여기서 코드로 계산한다. 모델은 숫자를 만들지 않고 근거 ID만 고른다.
"""
import csv
import json
from dataclasses import dataclass, asdict


@dataclass
class Fact:
    id: str
    label: str
    value: float
    unit: str
    source: str
    kind: str = "level"  # level, change, ratio, npv, breakeven, sensitivity

    def text(self) -> str:
        sign = "+" if self.kind == "change" else ""
        digits = 2 if self.kind in ("npv", "breakeven", "sensitivity") else 1
        s = f"{self.value:{sign},.{digits}f}"
        if "." in s:
            s = s.rstrip("0").rstrip(".")
        return f"{s}{self.unit}"


def _num(s: str) -> float:
    return float(s.replace(",", "").strip())


def load_financials(path: str) -> list[dict]:
    with open(path, encoding="utf-8-sig") as f:
        return [
            {**r, "당기": _num(r["당기"]), "전기": _num(r["전기"])}
            for r in csv.DictReader(f)
        ]


def annuity(rate: float, years: int) -> float:
    return sum(1 / (1 + rate) ** t for t in range(1, years + 1))


def npv(initial: float, cash: float, rate: float, years: int) -> float:
    return -initial + cash * annuity(rate, years)


def build_facts(fin_path: str, inv_path: str | None = None) -> tuple[list[Fact], list[str]]:
    rows = load_financials(fin_path)
    facts: list[Fact] = []
    n = 0

    def add(**kw) -> None:
        nonlocal n
        n += 1
        facts.append(Fact(id=f"F{n:02d}", **kw))

    by_name = {r["항목"]: r for r in rows}
    for r in rows:
        cur, prev, unit, src = r["당기"], r["전기"], r["단위"], r["출처"]
        add(label=f"{r['항목']} 당기", value=cur, unit=unit, source=src)
        add(label=f"{r['항목']} 전기 대비 증감", value=cur - prev, unit=unit, source=src, kind="change")
        if prev > 0:
            add(label=f"{r['항목']} 증감률", value=(cur / prev - 1) * 100, unit="%", source=src, kind="change")

    if "매출액" in by_name and "영업이익" in by_name:
        s, o = by_name["매출액"], by_name["영업이익"]
        m_cur = o["당기"] / s["당기"] * 100
        m_prev = o["전기"] / s["전기"] * 100
        add(label="영업이익률 당기", value=m_cur, unit="%", source="영업이익 나누기 매출액", kind="ratio")
        add(label="영업이익률 전기 대비", value=m_cur - m_prev, unit="%p", source="영업이익 나누기 매출액", kind="change")

    assumptions: list[str] = []
    if inv_path:
        with open(inv_path, encoding="utf-8") as f:
            inv = json.load(f)
        i0, cf, r, y, u = inv["초기투자"], inv["연간현금흐름"], inv["할인율"], inv["기간"], inv["단위"]
        src = inv["출처"]
        name = inv["이름"]
        add(label=f"{name} 초기투자", value=i0, unit=u, source=src)
        add(label=f"{name} 연간 현금흐름 가정", value=cf, unit=u, source=src)
        add(label=f"{name} NPV(할인율 {r*100:.0f}%)", value=npv(i0, cf, r, y), unit=u, source=src, kind="npv")
        add(label=f"{name} 본전 연간 현금흐름", value=i0 / annuity(r, y), unit=u, source=src, kind="breakeven")
        add(label=f"{name} NPV(할인율 {(r+0.02)*100:.0f}%)", value=npv(i0, cf, r + 0.02, y), unit=u, source=src, kind="sensitivity")
        add(label=f"{name} NPV(현금흐름 10% 감소)", value=npv(i0, cf * 0.9, r, y), unit=u, source=src, kind="sensitivity")
        assumptions = inv.get("확인할가정", [])

    return facts, assumptions


def facts_table(facts: list[Fact]) -> str:
    return "\n".join(f"{f.id} | {f.label} | {f.text()} | 출처: {f.source}" for f in facts)


def to_json(facts: list[Fact]) -> list[dict]:
    return [{**asdict(f), "text": f.text()} for f in facts]
