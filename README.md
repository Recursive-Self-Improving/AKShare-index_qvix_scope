# 七指数与50ETF QVIX历史对照

本地非商业实验：七个真实新浪指数历史，与同一条 AKShare
`index_option_50etf_qvix()` **每日收盘**曲线对照，独立右轴 `50ETF QVIX 收盘（%）`。
不是新闻情绪，不是七个标的各自的波动率。50ETF为QVIX标的，不代表其余六指数。

## 运行（Python 3.14，固定锁）

```sh
uv sync --frozen
uv run python -m compileall -q app
uv run ruff check .
uv run pytest -q
uv run python -m app.fetch --start 2000-01-01 --end 2026-11-15
# fetch partial/失败返回1；不要用 && 跳过下面仍可运行的离线命令
uv run python -m app.chart --input data --output report.html
uv run python -m app.verify --input data --report report.html
```

省略 `--end` 使用当天日期。完整历史端点无分页/日期参数，先抓取并严格验证全响应，
再按请求窗口选行。串行八源，每源独立子进程45秒墙钟界限，请求连接/读超时5/12秒，
无重试、后台服务、调度或推送。七个指数：上证指数 sh000001、上证50 sh000016、
沪深300 sh000300、创业板指 sz399006、创业板50 sz399673、科创综指 sh000680、科创50 sh000688。

`report.html` 内嵌一次Plotly JS和数据，无CDN/邻接文件读取。七图独立日期范围和左右轴，
框选/滚轮缩放、底部滑条、1年/5年/全部按钮、双击/本图重置。当前交付的
[独立浏览器round2复核](docs/reviews/qvix-browser-review-round2.md) PASS：七图经heavy-gate隔离、离线真实鼠标交互通过，最终report哈希一致；
[独立实施/数据round2复核](docs/reviews/qvix-implementation-review-round2.md) PASS。
编排器最终联合检查45项测试及raw制品验证通过；真实fetch仍为fresh partial、退出非零，源质量问题未解决。

## 真实运行与质量

新运行 `runs/2026-11-15T21-47-32.121889+00-00-3b7821e3`：七指数 success，
QVIX **fresh partial**，fetch实际退出1，不是clean success。QVIX观察范围
2015-02-09—2026-11-13：2849源行、2848日期、2847无歧义日期；一个冲突日期
2026-11-02（15.92与15.90均不选）、13相对缺失日期、4源外日期、8包络异常源行。
计数由源数据重算，不是生产常量；详见 [实施证据](docs/qvix-implementation-evidence.md)。
2000只是请求下界；2015是最早观察，不是官方创设/首发证明，更早可用性未知。

`data/latest.json` 与其 `manifest_path` 不可变清单一致，schema=`qvix-comparison-v3`；
只含七指数加 `qvix_50etf`。活动命令拒绝旧schema，不包含情绪decoder或隐式迁移。
失败时可复用已验证的原始整快照/时间并标stale；缺少transport/origin不能绕过验证。

本轮是**离线格式迁移，不是新fetch**：新增
`data/derived/qvix-v3-round1/manifest.json`，operation=`format-migration`，
保留原run、attempted_at、successful_at和finished_at；`derived_at`仅指派生视图生成时间。
`previous`和每个snapshot的`origin`以路径/SHA256引用上述真实run的原manifest。
所有原始manifest/result/raw/transport/CSV/quality/timestamp保持不变，包括21-47-32运行。
QVIX的显式`derivation`只更新schema和经全raw比较日历重算的紧凑accounting；
继续引用原quality侧车及其hash，不复制候选表、不伪造新观测。验证器核对原始成员身份/时间、
侧车全部候选/序号、原CSV和重算摘要。一次性迁移脚本不作为运行时或CLI保留。
详见 [修正证据](docs/qvix-fix-evidence-round1.md)。

- `response-N.body`：响应钩子在应用解码前保存的 `Response.content`，
  **HTTP解压后正文，不是wire bytes**。`transport.json`保存请求/实际URL、状态、头、时间、
  编码和SHA256，包括重定向正文。当前策略拒绝重定向；失败证据仍保留。
- `result.json`：真实wrapper调用、固定版本、尝试/完成时间、窗口、错误和结果。
- 指数 `observations.csv`：`date,close,pre_release,pre_base`。
- QVIX `wrapper.csv`：全源顺序的固定AKShare输出，可从GBK正文隔离缓存离线逐字节重放。
  `observations.csv`：`date,open,high,low,close,quality`，排序且日期唯一。
- `quality.json`：全响应每日期全部候选OHLC、源数据行序号（一开始）、包络/冲突/源外标记，
  全响应与选中窗口的行数/日期/候选/重复/冲突/异常/缺口/范围，比较日历身份、哈希和陈旧状态。
  新清单/result只保存制品引用与紧凑摘要，完整候选/序号表只在不可变侧车保存一次。
  历史v2清单的旧重复内容保留原样，不再复制到新清单或HTML。
  JSON禁止NaN，冲突CSV四个OHLC全部为空（不是零）。

先严格验证全部原始日期、必需列、有限OHLC，再检查wrapper转换/重放；
窗口外畸形数据也失败。按固定解码有限OHLC四元组比较，等值重复可折叠但保留全部发生序号；
收盘相同但其他OHLC不同仍冲突。排序/精确重复仅为notice；冲突、包络异常、相对缺失、
源外日期或未知/陈旧比较日历使结果partial，仍发布可用的新整快照且退出非零。
包络异常和源外值保留不修复；冲突不任取候选、不从旧修订填值。

fatal错误保留之前整快照并标stale/原时间；首次失败则unavailable。
新partial替换旧clean；后续修正也是新整快照，**从不逐日合并**。
清单验证或原子替换失败保持原latest入口。旧不可变修订全部保留，非point-in-time数据库。
活动state只含attempt、snapshot、stale_reuse，不累积revisions；每次新清单用previous
路径/hash引用上一清单，旧原始/侧车/清单仍可审计。HTML仅含当前显示数组、状态和紧凑来源引用。

图中七条QVIX数组相同，使用其质量快照绑定的上证指数**全raw历史重放**日历，
不是已按请求窗口裁剪的指数CSV；全响应质量在全比较历史上计算。
选中缺口是全响应观察边界内缺口与请求窗口的交集，包括窗口边缘和没有QVIX源行的窗口。
图在请求窗口与全源观察范围的交集内插入这些null；冲突也是null，`connectgaps=false`。
源外日期不删，不补周末、不外推。无可验证比较源则覆盖为unknown，不能冒充源外日期。
相对比较不是官方独立交易日历，共同遗漏无法检测，陈旧/未知日历不能证明clean coverage。
每图可见说明区分别解释缺失与冲突及计数，显示本次尝试和快照身份/时间/范围/状态及官方引用。

## 核查与限制

`verify` 离线检查active/不可变清单、当前引用整快照及其原始获取成员身份、时间和
raw/transport/wrapper/CSV/sidecar哈希；不随历史增长重放所有旧版本。
清缓存重放固定wrapper并禁网；独立从原始字段分组/重算候选、序号、规范CSV、sidecar、
计数/范围和已验证全比较历史。除实际嵌入数组/null/轴/JSON状态，还逐panel解析实际HTML
可见指数披露和QVIX状态/时间/范围/质量；删除或矛盾即失败，不以JSON payload代替可见披露。
不使用渲染器/生产分组函数产生预期值。通过不代表源质量clean或数值经济正确。

提供方为 [期权论坛 optbbs](https://1.optbbs.com/s/vix.shtml?50ETF)，经固定AKShare 1.20.53。
固定wrapper使用HTTP；研究中后续HTTPS文件字节相同，只证明那次同源传输字节一致，
不追认HTTP认证，不是独立正确性证明。哈希仅证明留存字节一致。
提供方具体期限、年化约定、close计算/截止、发布时间、修订和历史重建未知；
不能借用另一官方指数的30天定义。日期不等于可交易可得时间，无安全交易滞后、预测/因果承诺。
指数官方基日/发布日期与引用见 [身份研究](docs/research/index-identities.md)；
发布前记录带标记，新浪重建未知。科创综指含股息，与科创50价格指数不同。

提供方提示数据可能有错、商业使用需授权；**raw/派生数据及嵌入值HTML的再分发许可未确认**。
仅本地非商业实验；发布/分发前需核对实际条款，不声称无限制再分发授权。
参见 [可行性](docs/research/qvix-feasibility.md)、
[生效质量计划](docs/research/qvix-quality-plan.md)、[计划审阅](docs/reviews/qvix-plan-review.md)。

## 历史证据（不再是活动运行时）

保留全部旧 `data/runs/`、`data/documentation-example/`（含原文和LICENSE）、
研究及reviews；原始字节/清单不改。移除活动情绪wrapper、空投影workaround、逐日合并、
示例导入/图形/校验分支、`app/sample.py`及废弃测试，不加兼容shim。
`docs/reviews/browser-evidence-round2/fixture.py`等归档脚本要求历史代码与数据：
使用单独历史checkout的 `c9943caf13` 及该提交冻结环境复现，不能用新active运行时运行。
不要把历史样例或旧审阅通过当作当前QVIX浏览器验证。

