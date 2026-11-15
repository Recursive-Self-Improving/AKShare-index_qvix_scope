"""Seven independent date/dual-axis panels; embedded JS and arrays, no companion fetch."""
import argparse
import html
import json
from pathlib import Path

from plotly.offline import get_plotlyjs

from app.core import INDICES, PUBLICATION, QVIX, comparator_history, histories, load_manifest, trace_points
from app.identities import IDENTITIES

QVIX_LABEL = "50ETF QVIX 收盘（%）"


def panels(root, manifest):
    data = histories(root, manifest)
    calendar = [r["date"] for r in data.get("sh000001", [])]
    genuine = data.get(QVIX, [])
    qsnap = manifest["feeds"][QVIX]["snapshot"]
    comparator = qsnap["accounting"]["comparator"] if qsnap else None
    qcalendar = comparator_history(root, comparator)
    qbounds = ([max(qsnap["window"][0], qsnap["source_range"][0]),
                min(qsnap["window"][1], qsnap["source_range"][1])] if qsnap else None)
    result = []
    for code, name in INDICES.items():
        rows = data.get(code, [])
        observed_dates = {r["date"] for r in rows}
        x, y = trace_points(rows, "close", calendar)
        traces = [{"name": f"{name} 收盘", "type": "scatter", "mode": "lines", "x": x, "y": y,
                   "yaxis": "y", "connectgaps": False, "line": {"color": "#1769aa", "width": 1}}]
        sx, sy = trace_points(genuine, "close", qcalendar, qbounds)
        traces.append({"name": QVIX_LABEL, "type": "scatter", "mode": "lines",
                       "x": sx, "y": sy, "yaxis": "y2", "connectgaps": False,
                       "line": {"color": "#b04a00", "width": 1}})
        state = manifest["feeds"][code]
        snapshot = state.get("snapshot")
        layout = {
            "title": {"text": f"{name} · {code}", "x": 0.04}, "height": 660,
            "font": {"family": "Noto Sans CJK SC, Microsoft YaHei, sans-serif", "size": 14},
            "margin": {"l": 90, "r": 100, "t": 200, "b": 125}, "dragmode": "zoom",
            "xaxis": {"type": "date", "title": {"text": "观察日期（非发布时间）"},
                      "rangeslider": {"visible": True, "thickness": 0.09},
                      "rangeselector": {"buttons": [
                          {"count": 1, "label": "1年", "step": "year", "stepmode": "backward"},
                          {"count": 5, "label": "5年", "step": "year", "stepmode": "backward"},
                          {"label": "全部", "step": "all"}]}},
            "yaxis": {"title": {"text": f"{name} 收盘点位"}, "autorange": True, "fixedrange": False},
            "yaxis2": {"title": {"text": QVIX_LABEL}, "overlaying": "y", "side": "right",
                       "autorange": True, "fixedrange": False, "showgrid": False},
            "legend": {"orientation": "v", "x": 0, "xanchor": "left",
                       "y": 1.18, "yanchor": "bottom", "font": {"size": 13}},
            "hovermode": "closest", "paper_bgcolor": "white", "plot_bgcolor": "white"}
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

def quality_summary(state, window):
    snap = state["snapshot"]
    text = (f"QVIX 尝试 {state['attempt']['status']} @ {state['attempt']['attempted_at']}；"
            f"请求 {window}；")
    if not snap:
        return text + "unavailable 无可用快照，范围未知，非零值。"
    q = snap["accounting"]
    c = q["selected"]
    return (text + f"快照 {snap['status']} / {'stale 陈旧' if state['stale_reuse'] else 'fresh 新鲜'} "
            f"@ {snap['successful_at']}；源范围 {q['full']['range']}；选中 {c['range']} / {c['dates']}日期；"
            f"缺失源日期 {len(c['missing']) if c['missing'] is not None else 'unknown'}（无源行，以null断线）；"
            f"冲突日期 {c['conflicts']}（全部OHLC为null，不选任一候选）；"
            f"源外日期 {len(c['source_only']) if c['source_only'] is not None else 'unknown'}；"
            f"包络异常源行 {c['envelope_rows']}；精确重复 {c['exact_duplicates']}；"
            f"源有序 {q['ordered']}；全响应质量计数 {q['full']}；"
            f"比较日历身份 {q['comparator']}（非官方独立日历；陈旧/未知不能声称完整）。")


def build(root, output):
    manifest = load_manifest(root)
    payload = {"run": manifest["run"], "panels": panels(root, manifest),
               "qvix_status": manifest["feeds"][QVIX], "window": manifest["window"]}
    state = manifest["feeds"][QVIX]
    status = quality_summary(state, manifest["window"])
    encoded = json.dumps(payload, ensure_ascii=False, allow_nan=False).replace("<", "\\u003c")
    sections = "".join(
        f'<section id="panel-section-{p["code"]}"><h2>{html.escape(p["name"])} · {p["code"]}</h2>'
        f'<p class="index-status" id="index-status-{p["code"]}">{html.escape(json.dumps(p["status"], ensure_ascii=False))}</p>'
        f'<p class="quality" id="qvix-status-{p["code"]}">{html.escape(status)}</p>'
        f'<button onclick="resetPanel({i})">重置本图</button><div id="panel-{i}"></div></section>'
        for i, p in enumerate(payload["panels"]))
    page = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<title>七指数与50ETF QVIX</title><style>
body{font-family:"Noto Sans CJK SC","Microsoft YaHei",sans-serif;margin:24px;color:#182330}
.warning{border:3px solid #a44b00;background:#fff3dc;padding:18px;font-size:18px}
section{border-top:2px solid #adbccc;margin-top:30px;min-width:700px}button{padding:9px 18px}
p{overflow-wrap:anywhere}h2{font-size:23px}</style>
<h1>七指数历史与50ETF QVIX — 真实来源，显式部分质量</h1>'''
    page += f'<div class="warning">{html.escape(status)}<br>'
    page += ("</div><p>指数来源新浪；50ETF QVIX 来源期权论坛 optbbs，经 AKShare "
             "index_option_50etf_qvix。波动率不是新闻情绪；50ETF是其标的，不是其余六指数的波动率。"
             "右轴百分数读数，绘制每日close。各图独立拖动/滚轮缩放、滑条、1年/5年/全部及重置。</p>"
             "<p>缺失源日期与冲突日期均画断线null；冲突的全部OHLC置空，候选留在quality.json，"
             "null通常不能悬停。源外日期和OHLC包络异常保留原值，不插值、不补周末、不外推。"
             "上证指数快照只是非独立相对日历，共同遗漏未知。</p>"
             "<p>首次观察2015年不表示2000年已有值，也不证明正式创设日期。提供方期限、年化约定、"
             "收盘计算/截止、发布时间、修订和重建方法未知。观察日期不是可交易时间，不能推导安全滞后、"
             "预测或因果。整快照修订非point-in-time；发布前指数记录标记pre_release/pre_base，"
             "新浪回溯重建未知。科创综指包括股息，不同于科创50价格指数。</p>"
             "<p>固定wrapper使用HTTP；后续同源HTTPS字节匹配不追认原HTTP认证，也非独立准确性证明。"
             "哈希只证明留存字节一致。提供方提示可能有错、商业使用需授权；原始数据、派生数据及"
             "嵌入值HTML的再分发许可未确认。仅本地非商业实验，分发前核对"
             '<a href="https://1.optbbs.com/s/vix.shtml?50ETF">提供方条款</a>。</p>')
    page += sections + '<script>' + get_plotlyjs() + '</script>'
    page += '<script id="report-data" type="application/json">' + encoded + '</script>'
    page += '''<script>
const report=JSON.parse(document.getElementById('report-data').textContent);
report.panels.forEach((p,i)=>Plotly.newPlot('panel-'+i,p.data,p.layout,
 {responsive:true,displaylogo:false,scrollZoom:true,modeBarButtonsToAdd:['resetScale2d']}));
function resetPanel(i){Plotly.relayout('panel-'+i,{'xaxis.autorange':true,'yaxis.autorange':true,'yaxis2.autorange':true});}
</script></html>'''
    Path(output).write_text(page)
    print(f"Wrote {output}: seven panels; {status}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data")
    parser.add_argument("--output", default="report.html")
    args = parser.parse_args()
    build(args.input, args.output)


if __name__ == "__main__":
    main()
