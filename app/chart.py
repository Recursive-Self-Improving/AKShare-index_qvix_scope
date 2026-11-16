"""Eight independent date/dual-axis panels in one offline, self-contained page."""
import argparse
import html
import json
from pathlib import Path

from plotly.offline import get_plotlyjs

from app.core import INDICES, MAPPINGS, PUBLICATION, QVIX_FEEDS, histories, load_manifest, trace_points
from app.identities import IDENTITIES

INDEX_COLOR, QVIX_COLOR, QVIX_ALT_COLOR = "#3366cc", "#e08a1e", "#9b51b0"


def panels(root, manifest):
    data = histories(root, manifest)
    calendar = [r["date"] for r in data.get("sh000001", [])]
    qtraces = {}
    for feed in QVIX_FEEDS:
        rows = data.get(feed, [])
        qtraces[feed] = ([r["date"] for r in rows], [r["close"] for r in rows])
    result = []
    for code, name in INDICES.items():
        rows = data.get(code, [])
        observed_dates = {r["date"] for r in rows}
        x, y = trace_points(rows, "close", calendar)
        traces = [{"name": f"{name} 收盘", "type": "scatter", "mode": "lines", "x": x, "y": y,
                   "yaxis": "y", "connectgaps": False, "line": {"color": INDEX_COLOR, "width": 1.5}}]
        for position, feed in enumerate(MAPPINGS[code]):
            sx, sy = qtraces[feed]
            traces.append({"name": QVIX_FEEDS[feed]["label"], "type": "scatter", "mode": "lines",
                           "x": sx, "y": sy, "yaxis": "y2", "connectgaps": False,
                           "line": {"color": QVIX_COLOR if position == 0 else QVIX_ALT_COLOR,
                                    "dash": "solid" if position == 0 else "dot", "width": 1.2},
                           "opacity": 0.9})
        state = manifest["feeds"][code]
        snapshot = state.get("snapshot")
        layout = {
            "height": 420, "font": {"family": "inherit", "size": 12},
            "margin": {"l": 60, "r": 60, "t": 36, "b": 30}, "dragmode": "zoom",
            "xaxis": {"type": "date", "showgrid": False,
                      "rangeslider": {"visible": True, "thickness": 0.06},
                      "rangeselector": {"x": 1, "xanchor": "right", "y": 1.02, "yanchor": "bottom",
                                        "buttons": [
                                            {"count": 1, "label": "1年", "step": "year", "stepmode": "backward"},
                                            {"count": 5, "label": "5年", "step": "year", "stepmode": "backward"},
                                            {"label": "全部", "step": "all"}]}},
            "yaxis": {"title": {"text": "指数点位"}, "autorange": True, "fixedrange": False, "zeroline": False},
            "yaxis2": {"title": {"text": "QVIX（%）"}, "overlaying": "y", "side": "right",
                       "autorange": True, "fixedrange": False, "showgrid": False, "zeroline": False},
            # Legend on the left, range buttons on the right of the same top band.
            "legend": {"orientation": "h", "x": 0, "xanchor": "left", "y": 1.02, "yanchor": "bottom",
                       "bgcolor": "rgba(0,0,0,0)"},
            "hovermode": "x unified", "paper_bgcolor": "rgba(0,0,0,0)", "plot_bgcolor": "rgba(0,0,0,0)"}
        result.append({"code": code, "name": name, "data": traces, "layout": layout,
                       "status": {"attempt": state["attempt"]["status"],
                                  "attempted_at": state["attempt"]["attempted_at"],
                                  "stale_reuse": state["stale_reuse"],
                                  "snapshot_status": snapshot["status"] if snapshot else "unavailable",
                                  "range": snapshot["range"] if snapshot else None,
                                  "rows": len(rows), "successful_at": snapshot["successful_at"] if snapshot else None,
                                  "relative_gaps": [d for d in calendar if rows and
                                                    rows[0]["date"] <= d <= rows[-1]["date"]
                                                    and d not in observed_dates],
                                  "calendar_stale": manifest["feeds"]["sh000001"]["stale_reuse"],
                                  "publication_date": PUBLICATION.get(code),
                                  "base_date": IDENTITIES[code]["base_date"],
                                  "official_name": IDENTITIES[code]["official_name"],
                                  "citation": IDENTITIES[code]["citation"],
                                  "retrospective_rows": snapshot.get("retrospective_count") if snapshot else None}})
    return result


WORDS = {"success": "成功", "partial": "部分成功", "failure": "失败"}
QVIX_ISSUES = [("缺口", "holes"), ("冲突", "conflict"), ("无效字段", "invalid_fields"),
               ("零值行", "zero_rows"), ("源外", "source_only"), ("包络异常", "envelope_rows"),
               ("内部空白", "blank_internal"), ("尾部空白", "blank_tail")]


def stamp(value):
    """ISO UTC timestamp to a readable minute-precision label."""
    return value[:16].replace("T", " ") + " UTC" if value else "未知"


def span(pair):
    return f"{pair[0]} → {pair[1]}" if pair else "范围未知"


def word(status):
    return WORDS.get(status, status)


def short(feed):
    return QVIX_FEEDS[feed]["label"].replace(" 收盘（%）", "")


def stale_note(attempt, successful_at):
    return f"陈旧：本次获取{word(attempt)}，沿用 {stamp(successful_at)} 快照"


def index_line(s):
    """Visible index disclosure: always the range, then only what deviates from normal."""
    if s["snapshot_status"] == "unavailable":
        parts = [f"无可用快照（本次获取{word(s['attempt'])} @ {stamp(s['attempted_at'])}）"]
    else:
        parts = [f"新浪收盘 {span(s['range'])}", f"{s['rows']} 行"]
        if s["snapshot_status"] != "success":
            parts.append(f"快照{word(s['snapshot_status'])}")
        if s["stale_reuse"]:
            parts.append(stale_note(s["attempt"], s["successful_at"]))
        if s["relative_gaps"]:
            parts.append(f"较上证缺 {len(s['relative_gaps'])} 日")
    if s["retrospective_rows"] is None:
        parts.append("发布前回溯行数未知")
    elif s["retrospective_rows"]:
        parts.append(f"发布前回溯 {s['retrospective_rows']} 行")
    if s["calendar_stale"]:
        parts.append("上证日历陈旧")
    return " · ".join(parts)


def qvix_issues(full, selected):
    """Non-zero quality counts; the window count is added only when it differs."""
    parts = []
    for label, key in QVIX_ISSUES:
        whole, window = full[key], selected[key]
        if whole is None:
            parts.append(f"{label} 未知")
        elif whole or window:
            parts.append(f"{label} {whole}" + (f"（窗口内 {window}）" if window != whole else ""))
    return parts


def qvix_line(feed, state):
    """Visible feed-local disclosure; a clean sibling never masks this feed's warnings."""
    snap = state["snapshot"]
    if not snap:
        attempt = state["attempt"]
        return f"{short(feed)} · 无可用快照（本次获取{word(attempt['status'])} @ {stamp(attempt['attempted_at'])}）"
    q = snap["accounting"]
    full, selected, comp = q["full"], q["selected"], q["comparator"]
    issues = qvix_issues(full, selected)
    parts = [short(feed), "有质量异常" if snap["status"] != "success" else "需留意" if issues else "无质量异常"]
    if full["range"] != full["close_range"]:
        parts.append(f"源 {span(full['range'])}")
    parts.append(f"收盘 {span(full['close_range'])}")
    if (selected["range"], selected["close_range"]) != (full["range"], full["close_range"]):
        parts.append(f"窗口内收盘 {span(selected['close_range'])}")
    if state["stale_reuse"]:
        parts.append(stale_note(state["attempt"]["status"], snap["successful_at"]))
    parts += issues
    if comp is None:
        parts.append("比较日历未知")
    elif comp["stale_reuse"]:
        parts.append(f"比较日历 {comp['feed']} 陈旧")
    return " · ".join(parts)


def qvix_clean(state):
    """Green only for a fresh success snapshot whose line lists nothing."""
    snap = state["snapshot"]
    if not snap or snap["status"] != "success" or state["stale_reuse"]:
        return False
    q = snap["accounting"]
    return not qvix_issues(q["full"], q["selected"]) and q["comparator"] is not None and \
        not q["comparator"]["stale_reuse"]


def index_clean(s):
    return (s["snapshot_status"] == "success" and not s["stale_reuse"] and not s["calendar_stale"]
            and not s["relative_gaps"] and s["retrospective_rows"] is not None)


def cell(value, warn=False):
    return f'<td class="{"num warn" if warn else "num"}">{html.escape(str(value))}</td>'


def quality_table(manifest):
    head = "".join(f"<th>{h}</th>" for h in
                   ["QVIX", "状态", "收盘范围", *[label for label, _ in QVIX_ISSUES], "比较指数", "快照 ID"])
    rows = []
    for feed in QVIX_FEEDS:
        state = manifest["feeds"][feed]
        snap = state["snapshot"]
        name = html.escape(short(feed))
        if not snap:
            rows.append(f'<tr><th scope="row">{name}</th><td colspan="{len(QVIX_ISSUES) + 4}">'
                        f'无可用快照 · 本次获取{html.escape(word(state["attempt"]["status"]))}</td></tr>')
            continue
        full, comp = snap["accounting"]["full"], snap["accounting"]["comparator"]
        status = word(snap["status"]) + ("（陈旧）" if state["stale_reuse"] else "")
        counts = "".join(cell("未知" if full[key] is None else full[key], full[key] is None or bool(full[key]))
                         for _, key in QVIX_ISSUES)
        compared = (f'{comp["feed"]}{"（陈旧）" if comp["stale_reuse"] else ""}' if comp else "未知")
        rows.append(f'<tr><th scope="row">{name}</th><td>{html.escape(status)}</td>'
                    f'<td>{html.escape(span(full["close_range"]))}</td>{counts}'
                    f'<td class="mono">{html.escape(compared)}</td>'
                    f'<td class="mono">{html.escape(snap["origin"]["sha256"][:12])}</td></tr>')
    return f'<div class="scroll"><table class="grid"><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'


def summary(manifest, items):
    """Header facts derived from the manifest; counts, not claims of correctness."""
    indices = [manifest["feeds"][code] for code in INDICES]
    feeds = [manifest["feeds"][feed] for feed in QVIX_FEEDS]
    ends = [p["status"]["range"][1] for p in items if p["status"]["range"]]
    fresh_index = sum(1 for s in indices if s["snapshot"] and s["snapshot"]["status"] == "success"
                      and not s["stale_reuse"])
    clean = sum(1 for s in feeds if qvix_clean(s))
    fetched = max((s["attempt"]["attempted_at"] for s in indices + feeds if s["attempt"].get("attempted_at")),
                  default=None)
    facts = [("指数", f"{fresh_index} / {len(indices)}", "本次获取成功", fresh_index < len(indices)),
             ("QVIX 质量", f"{len(feeds) - clean} / {len(feeds)}", "条需留意，见各图下方", clean < len(feeds)),
             ("数据截至", max(ends) if ends else "未知", "最新观察日", False),
             ("获取时间", stamp(fetched)[:16], "UTC", False)]
    return "".join(f'<div class="stat{" warn" if warn else ""}"><span>{label}</span><b>{html.escape(value)}</b>'
                   f'<small>{html.escape(note)}</small></div>' for label, value, note, warn in facts)


CSS = """
:root{color-scheme:light;--bg:#f6f7f9;--card:#fff;--ink:#141a23;--soft:#3d4757;--muted:#6b7585;
--line:#e4e7ec;--chip:#f0f2f5;--accent:#3366cc;--qvix:#e08a1e;--warn:#b54708;--warn-bg:#fef3e6;
--ok:#067647;--grid:#eceef2;--shadow:0 1px 2px rgba(16,24,40,.05),0 1px 3px rgba(16,24,40,.04)}
@media (prefers-color-scheme:dark){:root{color-scheme:dark;--bg:#0d1117;--card:#151b23;--ink:#e8ecf1;
--soft:#c3cad5;--muted:#8b95a5;--line:#262e39;--chip:#1e2530;--accent:#6b97f0;--warn:#f0a050;
--warn-bg:#2a1f12;--ok:#4cc38a;--grid:#212833;--shadow:none}}
*{box-sizing:border-box}
html{scroll-behavior:smooth;scroll-padding-top:64px}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.65 -apple-system,BlinkMacSystemFont,
"Segoe UI","PingFang SC","Hiragino Sans GB","Noto Sans CJK SC","Microsoft YaHei",sans-serif;
-webkit-font-smoothing:antialiased}
main{max-width:1120px;margin:0 auto;padding:44px 16px 72px}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
.mono,.code{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
.top h1{font-size:28px;line-height:1.25;margin:0 0 8px;letter-spacing:-.01em;font-weight:700}
.top p{margin:0;color:var(--soft);max-width:720px}
.key{display:flex;flex-wrap:wrap;gap:6px 18px;margin-top:12px;font-size:13px;color:var(--muted)}
.key i{display:inline-block;width:18px;height:3px;border-radius:2px;vertical-align:middle;margin-right:6px}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:24px 0 14px}
.stat{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 16px;box-shadow:var(--shadow)}
.stat span{display:block;font-size:12px;color:var(--muted)}
.stat b{display:block;font-size:20px;font-weight:650;letter-spacing:-.01em;margin:2px 0}
.stat small{font-size:12px;color:var(--muted)}
.stat.warn b{color:var(--warn)}
.callout{background:var(--warn-bg);border-radius:10px;padding:10px 14px;font-size:13px;color:var(--soft);margin:0}
.callout b{color:var(--warn)}
nav{position:sticky;top:0;z-index:10;display:flex;gap:6px;overflow-x:auto;margin:20px -16px 8px;
padding:10px 16px;background:color-mix(in srgb,var(--bg) 88%,transparent);backdrop-filter:blur(8px);
-webkit-backdrop-filter:blur(8px);scrollbar-width:none}
nav a{flex:none;padding:5px 12px;border-radius:999px;background:var(--card);border:1px solid var(--line);
color:var(--soft);font-size:13px}
nav a:hover{border-color:var(--accent);color:var(--accent);text-decoration:none}
.panel{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px 20px 14px;
margin:0 0 16px;box-shadow:var(--shadow)}
.panel-head{display:flex;justify-content:space-between;align-items:flex-start;gap:12px}
.panel h2{font-size:18px;margin:0;display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.code{font-size:12px;font-weight:500;color:var(--muted);background:var(--chip);padding:1px 7px;border-radius:6px}
.sub{font-size:12.5px;color:var(--muted);margin-top:2px}
button{font:inherit;font-size:12.5px;padding:4px 12px;border-radius:8px;border:1px solid var(--line);
background:var(--card);color:var(--soft);cursor:pointer;white-space:nowrap}
button:hover{border-color:var(--accent);color:var(--accent)}
.plot{min-height:420px;margin:4px -6px 0;overflow:hidden}
.status{border-top:1px solid var(--line);margin-top:6px;padding-top:10px}
.status p{position:relative;margin:0 0 3px;padding-left:16px;font-size:12.5px;color:var(--muted);overflow-wrap:anywhere}
.status p::before{content:"";position:absolute;left:2px;top:.62em;width:7px;height:7px;border-radius:50%;background:var(--ok)}
.status p.index-status.ok::before{background:var(--accent)}
.status p.warn{color:var(--soft)}.status p.warn::before{background:var(--warn)}
h3{font-size:17px;margin:40px 0 6px}
.lead{color:var(--muted);font-size:13px;margin:0 0 12px}
.scroll{overflow-x:auto;background:var(--card);border:1px solid var(--line);border-radius:12px;box-shadow:var(--shadow)}
.grid{width:100%;border-collapse:collapse;font-size:12px;white-space:nowrap}
.grid th,.grid td{padding:8px 9px;text-align:left;border-bottom:1px solid var(--line)}
.grid thead th{font-weight:500;color:var(--muted);background:var(--chip)}
.grid tbody tr:last-child>*{border-bottom:0}
.grid td.num{text-align:right;color:var(--muted)}.grid td.warn{color:var(--warn);font-weight:600}
.notes{margin:0;padding-left:20px;color:var(--soft);font-size:13.5px}
.notes li{margin:6px 0}
footer{margin-top:40px;font-size:12px;color:var(--muted)}
@media (max-width:720px){.stats{grid-template-columns:repeat(2,1fr)}.top h1{font-size:23px}
.stat b{font-size:17px}.panel{padding:14px 12px 10px}.plot{min-height:380px;margin:4px 0 0}}
"""

NOTES = [
    "<b>QVIX 是期权隐含波动率（%），不是新闻情绪</b>，也不是指数点位或已实现波动率；期限、年化、截止与修订方式均未知。",
    "QVIX 与指数的匹配只是近似代理：上证指数、上证50 → 50股指 + 50ETF；深证100 → 深证100ETF；"
    "沪深300 → 300股指 + 300ETF；创业板指、创业板50 → 创业板；科创综指、科创50 → 科创板。具体期权合约未经确认。",
    "曲线断开处是空白、无效收盘、缺口或冲突日：不修复、不插值、不外推；零值按原样保留，不保证经济含义。",
    "横轴是观察日期，不是发布时间；整份快照可能被修订，不是 point-in-time 数据，不能据此推断滞后、预测或因果。",
    "新浪首个观察日不等于指数发布日，发布前的行是回溯数据，重建方法未知。科创综指含股息，与科创50价格指数不同。",
    "来源：指数为新浪，QVIX 为期权论坛 optbbs，均经 AKShare 1.20.53 通过 HTTP 获取。提供方提示数据可能有误；"
    "再分发许可未确认，仅供本地非商业实验，分发前请核对"
    '<a href="https://1.optbbs.com/s/vix.shtml?50ETF">提供方条款</a>。',
]


def panel_section(i, p, manifest):
    s = p["status"]
    lines = [f'<p class="index-status {"ok" if index_clean(s) else "warn"}" id="index-status-{p["code"]}">{html.escape(index_line(s))}</p>']
    for feed in MAPPINGS[p["code"]]:
        state = manifest["feeds"][feed]
        tone = "ok" if qvix_clean(state) else "warn"
        lines.append(f'<p class="quality {tone}" id="qvix-status-{p["code"]}-{feed}">'
                     f'{html.escape(qvix_line(feed, state))}</p>')
    return (f'<section class="panel" id="panel-section-{p["code"]}"><header class="panel-head"><div>'
            f'<h2>{html.escape(p["name"])} <span class="code">{p["code"]}</span></h2>'
            f'<div class="sub">{html.escape(s["official_name"])} · 基日 {s["base_date"]} · '
            f'发布 {s["publication_date"]} · <a href="{html.escape(s["citation"])}">官方资料 ↗</a></div></div>'
            f'<button onclick="resetPanel({i})">重置缩放</button></header>'
            f'<div class="plot" id="panel-{i}"></div><div class="status">{"".join(lines)}</div></section>')


def build(root, output):
    manifest = load_manifest(root)
    payload = {"run": manifest["run"], "panels": panels(root, manifest),
               "qvix_status": {f: manifest["feeds"][f] for f in QVIX_FEEDS}, "window": manifest["window"]}
    encoded = json.dumps(payload, ensure_ascii=False, allow_nan=False).replace("<", "\\u003c")
    nav = "".join(f'<a href="#panel-section-{p["code"]}">{html.escape(p["name"])}</a>' for p in payload["panels"])
    sections = "".join(panel_section(i, p, manifest) for i, p in enumerate(payload["panels"]))
    page = ('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>A股指数与 QVIX</title><style>{CSS}</style></head><body><main>'
            '<header class="top"><h1>A股八大指数 × 期权隐含波动率</h1>'
            '<p>每张图左轴为新浪指数日收盘，右轴为对应期权的 QVIX 日收盘（%）。拖动框选可缩放，下方滑条可平移，点图例可隐藏曲线。</p>'
            '<div class="key">'
            f'<span><i style="background:{INDEX_COLOR}"></i>指数收盘 · 左轴</span>'
            f'<span><i style="background:{QVIX_COLOR}"></i>QVIX · 右轴</span>'
            f'<span><i style="background:{QVIX_ALT_COLOR}"></i>第二条 QVIX · 右轴</span>'
            f'<span>观察区间 {html.escape(span(manifest["window"]))}</span></div></header>'
            f'<div class="stats">{summary(manifest, payload["panels"])}</div>'
            '<p class="callout"><b>注意：</b>QVIX 衡量期权市场预期波动，不是新闻情绪；数据仅供本地非商业实验。'
            '<a href="#notes">读图须知 ↓</a></p>'
            f'<nav>{nav}</nav>{sections}'
            '<h3 id="quality">QVIX 数据质量</h3>'
            '<p class="lead">全量历史计数，非零项标为橙色。缺口 = QVIX 区间内比较指数有交易而 QVIX 无有效收盘；'
            '源外 = QVIX 有数据而比较指数无交易；包络异常 = 当日最高/最低价未包住开盘与收盘。各项可重叠，不能相加。</p>'
            + quality_table(manifest) +
            '<h3 id="notes">读图须知</h3><ul class="notes">' + "".join(f"<li>{n}</li>" for n in NOTES) + '</ul>'
            '<footer>离线单文件页面：图表库与数据均已内嵌，无需联网。</footer>')
    page += '<script>' + get_plotlyjs() + '</script>'
    page += '<script id="report-data" type="application/json">' + encoded + '</script>'
    page += '''<script>
const report=JSON.parse(document.getElementById('report-data').textContent);
const css=getComputedStyle(document.documentElement);
const v=n=>css.getPropertyValue(n).trim();
const ink=v('--soft'), muted=v('--muted'), grid=v('--grid'), card=v('--card'), line=v('--line'), chip=v('--chip');
report.panels.forEach((p,i)=>{
 const l=p.layout;
 l.font.color=ink; l.font.family=getComputedStyle(document.body).fontFamily;
 l.yaxis.gridcolor=grid; l.xaxis.linecolor=l.yaxis.linecolor=l.yaxis2.linecolor=line;
 l.xaxis.rangeslider.bgcolor=chip; l.xaxis.rangeslider.bordercolor=line;
 l.xaxis.rangeselector.bgcolor=chip; l.xaxis.rangeselector.activecolor=line;
 l.xaxis.rangeselector.font={color:ink,size:11};
 l.yaxis.title.font={color:p.data[0].line.color,size:11}; l.yaxis2.title.font={color:p.data[1].line.color,size:11};
 l.xaxis.tickfont=l.yaxis.tickfont=l.yaxis2.tickfont={color:muted,size:11};
 l.hoverlabel={bgcolor:card,bordercolor:line,font:{color:ink}};
 if(innerWidth<640){l.margin={l:44,r:44,t:92,b:24}; Object.assign(l.xaxis.rangeselector,{x:0,xanchor:'left',y:1.24});}
 Plotly.newPlot('panel-'+i,p.data,l,{responsive:true,displaylogo:false,displayModeBar:false,scrollZoom:true});
});
function resetPanel(i){Plotly.relayout('panel-'+i,{'xaxis.autorange':true,'yaxis.autorange':true,'yaxis2.autorange':true});}
</script></main></body></html>'''
    Path(output).write_text(page)
    print(f"Wrote {output}: eight panels; seven independently disclosed QVIX feeds")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data")
    parser.add_argument("--output", default="index.html")
    args = parser.parse_args()
    build(args.input, args.output)


if __name__ == "__main__":
    main()
