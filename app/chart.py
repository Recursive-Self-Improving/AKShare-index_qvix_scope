"""Seven independent date/dual-axis panels; embedded JS and arrays, no companion fetch."""
import argparse
import html
import json
from pathlib import Path

from plotly.offline import get_plotlyjs

from app.core import INDICES, PUBLICATION, histories, load_manifest, read_csv, selected_history, trace_points
from app.identities import IDENTITIES

SAMPLE_LABEL = "文档示例 documentation example, not live/full history"


def panels(root, manifest):
    data = histories(root, manifest)
    calendar = [r["date"] for r in data.get("sh000001", [])]
    genuine = data.get("sentiment", [])
    samples = read_csv(Path(root) / "documentation-example/documentation-example.csv")
    result = []
    for code, name in INDICES.items():
        rows = data.get(code, [])
        x, y = trace_points(rows, "close", calendar)
        traces = [{"name": f"{name} 收盘", "type": "scatter", "mode": "lines", "x": x, "y": y,
                   "yaxis": "y", "connectgaps": False, "line": {"color": "#1769aa", "width": 1}}]
        if genuine:
            sx, sy = trace_points(genuine, "sentiment", calendar)
            traces.append({"name": "真实 ChinaScope 情绪（最新成功版本，非时点）", "type": "scatter",
                           "mode": "lines+markers", "x": sx, "y": sy, "yaxis": "y2", "connectgaps": False})
        traces.append({"name": SAMPLE_LABEL, "type": "scatter", "mode": "markers",
                       "x": [r["date"] for r in samples], "y": [r["sentiment"] for r in samples],
                       "yaxis": "y2", "connectgaps": False,
                       "marker": {"symbol": "diamond-open", "size": 9, "color": "#b04a00"}})
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
            "yaxis2": {"title": {"text": "情绪指数（独立刻度）"}, "overlaying": "y", "side": "right",
                       "autorange": True, "fixedrange": False, "showgrid": False},
            "legend": {"orientation": "v", "x": 0, "xanchor": "left",
                       "y": 1.18, "yanchor": "bottom", "font": {"size": 12}},
            "hovermode": "closest", "paper_bgcolor": "white", "plot_bgcolor": "white"}
        result.append({"code": code, "name": name, "data": traces, "layout": layout,
                       "status": {"attempt": state["attempt"]["status"], "stale_reuse": state["stale_reuse"],
                                  "range": snapshot["range"] if snapshot else None,
                                  "rows": len(rows), "successful_at": snapshot["successful_at"] if snapshot else None,
                                  "publication_date": PUBLICATION.get(code),
                                  "base_date": IDENTITIES[code]["base_date"],
                                  "official_name": IDENTITIES[code]["official_name"],
                                  "citation": IDENTITIES[code]["citation"],
                                  "retrospective_rows": snapshot.get("retrospective_count") if snapshot else None}})
    return result


def build(root, output):
    manifest = load_manifest(root)
    payload = {"run": manifest["run"], "panels": panels(root, manifest),
               "sentiment_status": manifest["feeds"]["sentiment"],
               "selected_history": selected_history(root, manifest)}
    state = manifest["feeds"]["sentiment"]
    snap = state["snapshot"]
    status = f"当前情绪采集：{state['attempt']['status']}；尝试时间 {state['attempt']['attempted_at']}；"
    coverage = payload["selected_history"]["sentiment"]
    status += (f"最近响应成功时间 {snap['successful_at']}，最近响应范围 {snap['range']}，"
               f"最近响应行数 {snap['count']}，陈旧复用 {state['stale_reuse']}；"
               f"选中逐日合并历史范围 {coverage['range']}，行数 {coverage['count']}，"
               f"相对缺口 {len(coverage['relative_gaps'])}（非独立日历）") if snap else (
        "当前提供方不可用；真实情绪覆盖未知（不是零值、不是零历史）；无最近成功快照")
    encoded = json.dumps(payload, ensure_ascii=False, allow_nan=False).replace("<", "\\u003c")
    sections = "".join(
        f'<section><h2>{html.escape(p["name"])} · {p["code"]}</h2>'
        f'<p>{html.escape(json.dumps(p["status"], ensure_ascii=False))}</p>'
        f'<button onclick="resetPanel({i})">重置本图</button><div id="panel-{i}"></div></section>'
        for i, p in enumerate(payload["panels"]))
    page = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<title>七指数与情绪：部分覆盖</title><style>
body{font-family:"Noto Sans CJK SC","Microsoft YaHei",sans-serif;margin:24px;color:#182330}
.warning{border:3px solid #a44b00;background:#fff3dc;padding:18px;font-size:18px}
section{border-top:2px solid #adbccc;margin-top:30px;min-width:700px}button{padding:9px 18px}
p{overflow-wrap:anywhere}h2{font-size:23px}</style>
<h1>七指数历史与新闻情绪 — 部分对照，非完整实时双序列</h1>'''
    page += f'<div class="warning">{html.escape(status)}<br>'
    page += ("仅十个历史文档示例点：2023-10-31—2023-11-06 / 2024-10-25—2024-10-31；"
             "documentation example, not live/full history。缺失年不连线，未恢复其余231行。</div>"
             "<p>指数来源新浪；情绪真实来源 ChinaScope（若成功），示例来源 AKShare MIT 历史文档。"
             "观察日期不等于发布时间；示例原始获取/发布/修订时间未知。marketClose 独立保存在示例CSV，未代替沪深300。"
             "各图独立日期范围与双轴：拖动缩放、底部滑条、1年/5年/全部、本图重置或双击重置。</p>"
             "<p>日期缺口使用上证指数已观察交易日相对比较（非独立官方日历）；共同遗漏未知。周末不补值。"
             "官方基日/发布日与来源见各图；CSV逐行标记pre_release/pre_base。发布前仅为回溯数据，新浪重建方法未知。"
             "最新成功逐日合并保留不可变修订，但不是 point-in-time 数据，不能证明同日可交易、安全滞后或因果关系。</p>"
             '<p>科创综指包含股息，与科创50价格指数不同。名称、代码、基日/发布日期来源及运行快照时间见下表。</p>')
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
