"""Eight independent date/dual-axis panels, preserving the offline card layout."""
import argparse
import html
import json
from pathlib import Path

from plotly.offline import get_plotlyjs

from app.core import INDICES, MAPPINGS, PUBLICATION, QVIX_FEEDS, histories, load_manifest, trace_points
from app.identities import IDENTITIES

INDEX_COLOR, QVIX_COLOR = "#2f5fd0", "#d9822b"


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
                   "yaxis": "y", "connectgaps": False, "line": {"color": INDEX_COLOR, "width": 1.4}}]
        for position, feed in enumerate(MAPPINGS[code]):
            sx, sy = qtraces[feed]
            traces.append({"name": QVIX_FEEDS[feed]["label"], "type": "scatter", "mode": "lines",
                           "x": sx, "y": sy, "yaxis": "y2", "connectgaps": False,
                           "line": {"color": QVIX_COLOR if position == 0 else "#9b51b0",
                                    "dash": "solid" if position == 0 else "dash", "width": 1.2},
                           "opacity": 0.85})
        state = manifest["feeds"][code]
        snapshot = state.get("snapshot")
        layout = {
            "height": 460, "font": {"family": "inherit", "size": 12},
            "margin": {"l": 64, "r": 64, "t": 40, "b": 40}, "dragmode": "zoom",
            "xaxis": {"type": "date", "rangeslider": {"visible": True, "thickness": 0.07},
                      "rangeselector": {"x": 0, "y": 1.06, "buttons": [
                          {"count": 1, "label": "1年", "step": "year", "stepmode": "backward"},
                          {"count": 5, "label": "5年", "step": "year", "stepmode": "backward"},
                          {"label": "全部", "step": "all"}]}},
            "yaxis": {"title": {"text": "收盘点位"}, "autorange": True, "fixedrange": False},
            "yaxis2": {"title": {"text": "QVIX（%）"}, "overlaying": "y", "side": "right",
                       "autorange": True, "fixedrange": False, "showgrid": False},
            # Keep the legend row left of Plotly's upper-right hover modebar.
            "legend": {"orientation": "h", "x": 0, "xanchor": "left", "y": 1.17, "yanchor": "bottom"},
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


def stamp(value):
    """ISO UTC timestamp to a readable second-precision label."""
    return value[:19].replace("T", " ") + " UTC" if value else "未知"


def span(pair):
    return f"{pair[0]} → {pair[1]}" if pair else "范围未知"


def count(values):
    return "未知" if values is None else str(values)


def index_line(s):
    """Compact visible disclosure of one index feed's snapshot state."""
    if s["snapshot_status"] == "unavailable":
        text = f"无可用快照 · 本次尝试 {s['attempt']} @ {stamp(s['attempted_at'])} · 范围未知"
    else:
        fresh = "陈旧（沿用旧快照）" if s["stale_reuse"] else "新鲜"
        text = (f"快照 {s['snapshot_status']} · {fresh} @ {stamp(s['successful_at'])} · "
                f"本次尝试 {s['attempt']} · {span(s['range'])} · {s['rows']} 行 · "
                f"相对上证缺口 {len(s['relative_gaps'])} 日")
    retro = "未知" if s["retrospective_rows"] is None else s["retrospective_rows"]
    text += f" · 发布前回溯 {retro} 行"
    if s["calendar_stale"]:
        text += " · 上证日历陈旧"
    return text


def qvix_line(feed, state):
    """Visible feed-local material quality; never masked by a clean sibling."""
    snap = state["snapshot"]
    head = f"{QVIX_FEEDS[feed]['label']} · 本次尝试 {state['attempt']['status']} @ {stamp(state['attempt']['attempted_at'])} · "
    if not snap:
        return head + "无可用快照，范围未知"
    q = snap["accounting"]
    c, full, comp = q["selected"], q["full"], q["comparator"]
    provenance = (f"{comp['feed']} {comp['raw_sha256'][:12]} @ {stamp(comp['successful_at'])}"
                  f"（{'陈旧' if comp['stale_reuse'] else '新鲜'}）" if comp else "未知")
    return (head + f"快照 {snap['status']} · {'陈旧' if state['stale_reuse'] else '新鲜'} @ "
            f"{stamp(snap['successful_at'])} · 身份 {snap['origin']['sha256'][:12]} · "
            f"全源 {span(full['range'])} / 收盘 {span(full['close_range'])} · "
            f"选中 {span(c['range'])} / 收盘 {span(c['close_range'])} · "
            f"全量/选中 缺口 {count(full['holes'])}/{count(c['holes'])} · "
            f"冲突 {full['conflict']}/{c['conflict']} · 无效字段 {full['invalid_fields']}/{c['invalid_fields']} · "
            f"零值行 {full['zero_rows']}/{c['zero_rows']} · 源外 {count(full['source_only'])}/{count(c['source_only'])} · "
            f"包络异常 {full['envelope_rows']}/{c['envelope_rows']} · "
            f"空白内部/尾部 {full['blank_internal']}/{full['blank_tail']} · 比较日历 {provenance}")


def tile(label, value, tone=""):
    return (f'<div class="tile {tone}"><span>{html.escape(label)}</span>'
            f'<b>{html.escape(str(value))}</b></div>')


def qvix_card(feed, state, window):
    snap = state["snapshot"]
    heading = html.escape(QVIX_FEEDS[feed]["label"])
    if not snap:
        return f'<details class="card"><summary>{heading} · 无可用快照</summary></details>'
    q = snap["accounting"]
    tiles = "".join(tile(label, count(q["full"][key]), "warn" if q["full"][key] else "")
                    for label, key in [("收盘日期", "finite_close_dates"), ("缺口日期", "holes"),
                                       ("冲突日期", "conflict"), ("无效字段", "invalid_fields"),
                                       ("零值行", "zero_rows"), ("源外日期", "source_only")])
    rows = [("请求窗口", span(window)), ("共享来源", snap.get("shared", {}).get("path", "派生历史")),
            ("候选证据", snap["quality"] + " · " + snap["quality_sha256"]),
            ("完整质量", json.dumps(q["full"], ensure_ascii=False)),
            ("选中质量", json.dumps(q["selected"], ensure_ascii=False)),
            ("比较日历", json.dumps(q["comparator"], ensure_ascii=False)),
            ("源顺序", "有序" if q["ordered"] else "乱序；排序不是修复")]
    table = "".join(f"<tr><th>{html.escape(k)}</th><td>{html.escape(v)}</td></tr>" for k, v in rows)
    return (f'<details class="card"><summary>{heading} · {snap["status"]} · 质量详情</summary>'
            f'<div class="tiles">{tiles}</div><table class="facts">{table}</table></details>')


CSS = """
:root{--bg:#f5f6f8;--card:#fff;--ink:#1c2430;--muted:#667085;--line:#e3e7ee;--chip:#eef2f7;
--warn:#b54708;--warn-bg:#fff4e5;--ok:#027a48;--ok-bg:#ecfdf3;--accent:#2f5fd0;--qvix:#d9822b;--grid:#e9edf3}
@media (prefers-color-scheme:dark){:root{--bg:#0f1318;--card:#171c23;--ink:#e6e9ee;--muted:#98a2b3;
--line:#2a313b;--chip:#222a35;--warn:#f5a54a;--warn-bg:#2d2113;--ok:#47cd89;--ok-bg:#12261c;--grid:#252c36}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.6 -apple-system,BlinkMacSystemFont,
"PingFang SC","Noto Sans CJK SC","Microsoft YaHei",sans-serif}
main{max-width:1180px;margin:0 auto;padding:32px 16px 64px}
header h1{font-size:26px;margin:0 0 4px;letter-spacing:.2px}
header p{margin:0;color:var(--muted)}
.legend{display:inline-flex;gap:14px;margin-left:6px}
.legend i{display:inline-block;width:16px;height:3px;border-radius:2px;vertical-align:middle;margin-right:5px}
nav{display:flex;flex-wrap:wrap;gap:8px;margin:18px 0 22px}
nav a{padding:5px 12px;border-radius:999px;background:var(--card);border:1px solid var(--line);
color:var(--ink);text-decoration:none;font-size:13px}
nav a:hover{border-color:var(--accent);color:var(--accent)}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px 22px;margin:0 0 18px;
box-shadow:0 1px 2px rgba(16,24,40,.04)}
.card h2{font-size:18px;margin:0 0 12px;display:flex;align-items:baseline;gap:10px;flex-wrap:wrap}
.card h2 small{font-size:12.5px;font-weight:400;color:var(--muted)}
.code{font:12px ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--muted);background:var(--chip);
padding:2px 7px;border-radius:6px}
.tiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(128px,1fr));gap:10px;margin-bottom:14px}
.tile{background:var(--chip);border-radius:10px;padding:10px 12px}
.tile span{display:block;font-size:12px;color:var(--muted)}
.tile b{font-size:19px;font-weight:600}
.tile.warn{background:var(--warn-bg)}.tile.warn b{color:var(--warn)}
.tile.ok{background:var(--ok-bg)}.tile.ok b{color:var(--ok)}
.facts{width:100%;border-collapse:collapse;font-size:13px}
.facts th{width:88px;text-align:left;font-weight:500;color:var(--muted);vertical-align:top;padding:5px 12px 5px 0}
.facts td{padding:5px 0;overflow-wrap:anywhere}
.facts tr+tr{border-top:1px solid var(--line)}
.lead.bad{color:var(--warn)}
.meta{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:12.5px;color:var(--muted);margin:-4px 0 6px}
.meta a{color:var(--accent);text-decoration:none}
p.index-status,p.quality{margin:0 0 4px;font-size:12.5px;color:var(--muted);overflow-wrap:anywhere}
p.quality{color:var(--warn)}
.panel-head{display:flex;justify-content:space-between;align-items:flex-start;gap:12px}
button{font:inherit;font-size:12.5px;padding:5px 12px;border-radius:8px;border:1px solid var(--line);
background:var(--card);color:var(--ink);cursor:pointer;white-space:nowrap}
button:hover{border-color:var(--accent);color:var(--accent)}
.plot{margin-top:6px;min-height:460px}
details.card summary{cursor:pointer;font-weight:600;font-size:15px}
details.card ul{margin:10px 0 0;padding-left:20px}details.card li{margin:4px 0}
a{color:var(--accent)}
"""

NOTES = [
    "QVIX 是期权隐含波动率代理，<b>不是新闻情绪</b>、指数点位或已实现波动率；期限、年化、截止及修订时间未知。",
    "上证指数/上证50→50股指+50ETF；深证100→100ETF；沪深300→300股指+300ETF；创业板指/50→创业板；科创综指/50→科创板。"
    "宽基/子集、ETF跟踪及衍生品流动性不同，未证明提供方具体ETF合约代码。断线含空白、无效收盘、缺口和冲突；冲突全OHLC为空，不修复、不插值、不外推；零值保留且不保证经济有效。",
    "横轴是观察日期，不是发布时间；不能据此推导滞后、预测或因果。整快照可被修订，非 point-in-time。",
    "新浪首个观察日 ≠ 指数发布日；发布前的行是回溯数据，重建方法未知。科创综指含股息，不同于科创50价格指数。",
    "来源：指数为新浪，QVIX 为期权论坛 optbbs（经 AKShare，HTTP 获取）。提供方提示数据可能有误；"
    "再分发许可未确认，仅供本地非商业实验，分发前请核对"
    '<a href="https://1.optbbs.com/s/vix.shtml?50ETF">提供方条款</a>。',
]


def build(root, output):
    manifest = load_manifest(root)
    payload = {"run": manifest["run"], "panels": panels(root, manifest),
               "qvix_status": {f: manifest["feeds"][f] for f in QVIX_FEEDS}, "window": manifest["window"]}
    encoded = json.dumps(payload, ensure_ascii=False, allow_nan=False).replace("<", "\\u003c")
    nav = "".join(f'<a href="#panel-section-{p["code"]}">{html.escape(p["name"])}</a>' for p in payload["panels"])
    sections = "".join(
        f'<section class="card" id="panel-section-{p["code"]}"><div class="panel-head"><div>'
        f'<h2>{html.escape(p["name"])} <span class="code">{p["code"]}</span>'
        f'<small>{html.escape(p["status"]["official_name"])}</small></h2>'
        f'<div class="meta"><span>基日 {p["status"]["base_date"]}</span>'
        f'<span>发布 {p["status"]["publication_date"]}</span>'
        f'<a href="{html.escape(p["status"]["citation"])}">官方资料 ↗</a></div>'
        f'<p class="index-status" id="index-status-{p["code"]}">{html.escape(index_line(p["status"]))}</p>'
        + "".join(f'<p class="quality" id="qvix-status-{p["code"]}-{f}">'
                  f'{html.escape(qvix_line(f, manifest["feeds"][f]))}</p>' for f in MAPPINGS[p["code"]])
        + '</div>'
        f'<button onclick="resetPanel({i})">重置</button></div>'
        f'<div class="plot" id="panel-{i}"></div></section>'
        for i, p in enumerate(payload["panels"]))
    page = ('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>八指数与匹配 QVIX</title><style>{CSS}</style></head><body><main>'
            '<header><h1>八指数历史 × 匹配 QVIX</h1>'
            f'<p>观察区间 {html.escape(span(manifest["window"]))}<span class="legend">'
            f'<span><i style="background:{INDEX_COLOR}"></i>指数收盘（左轴）</span>'
            f'<span><i style="background:{QVIX_COLOR}"></i>QVIX（右轴）</span></span></p></header>'
            f'<nav>{nav}</nav>' + "".join(qvix_card(f, manifest["feeds"][f], manifest["window"]) for f in QVIX_FEEDS) +
            '<details class="card"><summary>读图须知</summary><ul>' +
            "".join(f"<li>{n}</li>" for n in NOTES) + '</ul></details>' + sections)
    page += '<script>' + get_plotlyjs() + '</script>'
    page += '<script id="report-data" type="application/json">' + encoded + '</script>'
    page += '''<script>
const report=JSON.parse(document.getElementById('report-data').textContent);
const css=getComputedStyle(document.documentElement);
const ink=css.getPropertyValue('--ink').trim(), grid=css.getPropertyValue('--grid').trim(),
      card=css.getPropertyValue('--card').trim();
report.panels.forEach((p,i)=>{
 const l=p.layout;
 l.font.color=ink; l.font.family=getComputedStyle(document.body).fontFamily;
 l.xaxis.gridcolor=l.yaxis.gridcolor=grid; l.xaxis.rangeslider.bgcolor=card;
 l.xaxis.rangeselector.bgcolor=grid; l.xaxis.rangeselector.activecolor=card;
 l.yaxis.title.font={color:p.data[0].line.color}; l.yaxis2.title.font={color:p.data[1].line.color};
 l.hoverlabel={bgcolor:card,font:{color:ink}};
 Plotly.newPlot('panel-'+i,p.data,l,
  {responsive:true,displaylogo:false,scrollZoom:true,modeBarButtonsToAdd:['resetScale2d']});
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
