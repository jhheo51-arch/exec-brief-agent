"""검사를 통과한 보고서를 한 장짜리 HTML과 Markdown으로 만든다."""
import html

from .facts import Fact
from .schema import fill

CSS = """
@page { size: A4 landscape; margin: 0 }
* { box-sizing: border-box; margin: 0 }
body { font-family: Pretendard, 'Malgun Gothic', sans-serif; color: #262626; background: #fff }
.sheet { width: 297mm; height: 210mm; padding: 14mm 16mm; display: flex; flex-direction: column; gap: 6mm }
.top { display: flex; justify-content: space-between; align-items: baseline; border-bottom: 2px solid #262626; padding-bottom: 3mm }
.top h1 { font-size: 13pt; font-weight: 700 } .top span { font-size: 9pt; color: #666 }
.conclusion { background: #1c69d4; color: #fff; padding: 6mm 7mm; font-size: 17pt; font-weight: 700; line-height: 1.4 }
.label { font-size: 9pt; font-weight: 700; color: #1c69d4; margin-bottom: 2mm }
.ev { display: grid; grid-template-columns: repeat(3, 1fr); gap: 4mm }
.ev div { background: #f2f2f2; padding: 5mm }
.ev b { display: block; font-size: 20pt; margin-bottom: 1.5mm }
.ev small { display: block; font-size: 8pt; color: #666; margin-bottom: 2mm }
.ev p { font-size: 10pt; line-height: 1.45 }
.row { display: grid; grid-template-columns: 1.6fr 1fr; gap: 6mm; flex: 1 }
table { width: 100%; border-collapse: collapse; font-size: 10pt }
td { border-top: 1px solid #e6e6e6; padding: 2.4mm 2mm; vertical-align: top; line-height: 1.4 }
td:first-child { font-weight: 700; width: 28mm }
ul { padding-left: 4mm; font-size: 10pt; line-height: 1.6 }
.ask { background: #dde8f9; padding: 4mm 6mm; font-size: 12pt; font-weight: 700 }
.foot { font-size: 7.5pt; color: #666 }
"""


def to_html(brief: dict, facts: list[Fact], title: str, mode: str) -> str:
    by_id = {f.id: f for f in facts}
    e = lambda s: html.escape(fill(s, by_id))
    ev = "".join(
        f"<div><b>{html.escape(by_id[x['fact_id']].text())}</b>"
        f"<small>{html.escape(by_id[x['fact_id']].label)} | {html.escape(by_id[x['fact_id']].source)}</small>"
        f"<p>{e(x['meaning'])}</p></div>"
        for x in brief["evidence"]
    )
    opts = "".join(f"<tr><td>{e(o['name'])}</td><td>{e(o['condition'])}</td></tr>" for o in brief["options"])
    checks = "".join(f"<li>{html.escape(c)}</li>" for c in brief["check_before_deciding"])
    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(title)}</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css">
<style>{CSS}</style></head><body><div class="sheet">
<div class="top"><h1>{html.escape(title)}</h1><span>임원 보고 한 장 | 작성 방식 {mode}</span></div>
<div><div class="label">결론</div><div class="conclusion">{e(brief['conclusion'])}</div></div>
<div><div class="label">근거 숫자 3개</div><div class="ev">{ev}</div></div>
<div class="row"><div><div class="label">선택지와 조건</div><table>{opts}</table></div>
<div><div class="label">결정 전에 확인할 가정</div><ul>{checks}</ul></div></div>
<div class="ask">{e(brief['decision_question'])}</div>
<div class="foot">모든 숫자는 입력 파일에서 코드로 계산했고, 문장은 근거 ID로만 숫자를 불렀습니다. 결정은 보고받는 사람이 합니다.</div>
</div></body></html>"""


def to_markdown(brief: dict, facts: list[Fact], title: str) -> str:
    by_id = {f.id: f for f in facts}
    lines = [f"# {title}", "", f"**결론** {fill(brief['conclusion'], by_id)}", "", "## 근거 숫자 3개"]
    for x in brief["evidence"]:
        f = by_id[x["fact_id"]]
        lines.append(f"- **{f.text()}** {f.label} ({f.source}): {fill(x['meaning'], by_id)}")
    lines += ["", "## 선택지와 조건"] + [f"- **{fill(o['name'], by_id)}** {fill(o['condition'], by_id)}" for o in brief["options"]]
    lines += ["", "## 결정 전에 확인할 가정"] + [f"- {c}" for c in brief["check_before_deciding"]]
    lines += ["", f"**질문** {fill(brief['decision_question'], by_id)}", ""]
    return "\n".join(lines)
