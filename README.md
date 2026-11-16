# 八指数与 QVIX 历史对照

将八个中国股票指数的日收盘价（左轴）与七条 QVIX 期权隐含波动率序列（右轴，%）放在同一时间轴上。
这是供本地非商业研究使用的历史对照工具，不是新闻情绪指标、已实现波动率或预测证据。

## 查看图表

下载仓库后，**用浏览器打开 [index.html](index.html)** 即可。
数据和 Plotly 均已内嵌，无需 Python、安装依赖或启动服务器。

支持浅／深色模式、缩放、时间滑条、图例切换，以及 1 年／5 年／全部范围选择。
各图下方显示数据状态，页底质量表汇总快照与比较指数信息。

> **数据质量提醒**：2026-11-16 的[获取记录](docs/matched-qvix-implementation-evidence.md)中，
> 八个指数获取成功，七条 QVIX 均为新鲜但有质量缺陷的 `partial` 数据；图表可用不代表历史完整。

## 对照范围

| 指数 | 代码 | 对照 QVIX |
|---|---|---|
| 上证指数 | sh000001 | 上证50股指、50ETF |
| 上证50 | sh000016 | 上证50股指、50ETF |
| 深证100 | sz399330 | 100ETF |
| 沪深300 | sh000300 | 沪深300股指、300ETF |
| 创业板指 | sz399006 | 创业板ETF |
| 创业板50 | sz399673 | 创业板ETF |
| 科创综指 | sh000680 | 科创板ETF |
| 科创50 | sh000688 | 科创板ETF |

数据通过固定版本 AKShare 1.20.53 获取：指数来自新浪，QVIX 来自 [optbbs](https://1.optbbs.com/s/vix.shtml?100ETF)。
同一 QVIX 在不同图中使用相同数据；名称沿用提供方，对照不表示期权标的与图中指数完全一致。

## 更新数据

仅更新或重建图表时需要 **Python 3.14** 和 **uv**。在仓库根目录执行：

```sh
uv sync --frozen
uv run python -m app.fetch --start 2000-01-01
```

可加 `--end YYYY-MM-DD`，默认当天；起止日期均包含。
请求从 2000 年开始不表示源数据覆盖至该年，也不会补造早期历史。

**`fetch` 遇到 `partial` 或失败会退出 `1`**，但仍会保存并尝试提升经验证的部分结果。
失败的数据源仅在有自身历史快照时沿用旧数据，并标记为陈旧。
检查获取结果后，单独执行以下离线命令；不要用 `&&` 把它们接在 `fetch` 后：

```sh
uv run python -m app.chart --input data --output index.html
uv run python -m app.verify --input data --report index.html
```

## 每日 GitHub Actions 与 Pages

工作流 [daily-refresh.yml](.github/workflows/daily-refresh.yml) 在默认分支运行：
`5 0 * * *`（UTC）与手动 **Run workflow**，不接受其他分支或日期输入。
实际准备开始时冻结一次 UTC 日期，选择 **2000-01-01 至 UTC 昨天**，跨午夜不重算；
延迟运行采用实际开始日，不补造名义 cron 日期。周末/节假日只保留源观察，不补交易行。
完整源每日替换能接收30天以前的修订；这些 wrapper 无上游窗口参数，30天选行会截断图表，
不会减少下载。不是滚动合并，不把旧价格拼回新鲜 null。

### 启用前的外部设置

- 将工作流合并到实际默认分支；允许 Actions、所固定的 actions、Python3.14.4、uv0.13.6，
  并提供 runner 分钟数/磁盘/制品配额。`uv sync --frozen --no-dev` 不改变锁，不安装开发依赖。
  顶层 actions 均固定经上游 tag 核对的完整 SHA；不是传递依赖锁或供应链安全认证。
  `ubuntu-24.04` 托管镜像/Git 仍会更新。
- 允许短期 `GITHUB_TOKEN` 直接更新默认分支，且分支保护/ruleset须兼容；不修改保护、不用PAT，
  不绕过必须PR/签名的规则。默认权限为空；prepare只读，独立publisher仅contents-write；
  不持久化checkout凭据。获取/安装/渲染只在只读job；writer仅运行标准库/Git与固定Actions工具。
- Git持久化**不等于网站部署**。`GITHUB_TOKEN` 推送不会触发branch Pages构建。
  自动部署需 Settings → Pages → Source = **GitHub Actions**，配置 `github-pages` 环境、
  默认分支授权/审批，再设置仓库变量 **`PUBLISH_PAGES=true`**（精确小写）。
  未启用时明确为 `Pages: disabled`，不声称网站已更新；外部部署设置仍未完成。
- 部署/公开仓库前确认原始、派生及HTML内嵌数据再分发授权；当前实验声明不是许可证。
  GitHub runner连通性、token/分支策略、通知、真实调度和部署须在托管环境另行验证。

### 安全发布与结果

`app.daily` 先独立验证现有 `data/` + `index.html`，普通复制到私有临时目录后运行一次真实fetch，
渲染并再次执行 `app.verify`。必须是本次时间界内的新完整acquisition、正确previous、
15个新鲜成员与固定窗口；全部选中CSV/图日期不得超过cutoff。
比较重叠请求窗口中的指数raw日期、QVIX公共raw日期集合；丢失任何旧日期均拒绝自动发布，
包括首/中/尾和等计数替换。比较不使用有限close集合，新鲜空白/冲突可按已有规则取代旧价格。
任何fatal、stale、未知/缺失、校验/执行错误均阻止整个更新；旧公开页面可能因此落后。

只允许新增本run子树、替换 `data/latest.json` 与根 `index.html`；不得删除或改写旧证据。
独立 `app/daily_transfer.py` 在新runner校验同run/attempt制品ID、receipt SHA256及每个文件的
path/size/hash，拒绝额外/缺失路径、link、可执行模式或其他代码路径，不执行制品。
从精确event base一次提交数据、证据、指针和页面；验证新commit的**完整父列表恰为[receipt base]**，
只推送该commit一次，使用显式 `--force-with-lease=refs/heads/<branch>:<base>` 原子比较并更新。
这不是普通non-force push；sole-parent约束保证接受的base→commit严格快进，不改写已有历史。
当前远端不是base（包括分叉、回退或删除）即拒绝；规则拒绝也不fallback，
不使用通用force、不rebase、不重试、不换base。无法检测base→其他值→base的ABA历史变化。
模糊push响应只有精确远端commit读回才可认定持久化，否则unknown/失败；读回不是第二次push。

新鲜success或独立验证的QVIX partial可持久化；partial保持null/警告，先持久化和可选部署，
最后 `quality-status` **红色退出1**，不以绿色掩盖质量。全部success才可绿色。
Pages仅打包精确已验证 `index.html`，部署前再次检查已持久化commit；
event代码SHA与数据commit分开记录。Git与Pages不跨服务原子，部署失败不回滚数据，
最后一刻检查后的外部竞争也不能由Git锁保证；所有自动site writer应共用并发组。

固定workflow并发组不取消运行中实例；pending可被替换、调度可能延迟/丢失，
公共仓库不活跃可能禁用调度，并非exactly-once队列或“未运行”告警。
prepare/persist/Pages/conclusion分别限30/5/10/2分钟，prepare内部25分钟deadline；
原有8×45秒+共享45秒源预算不变，无provider重试、浏览器或后台服务。
候选最多512文件/256MiB；receipt最多1MiB，单命令日志最多4MiB（超限截断并失败）。
always诊断仅保存本次新增证据（最多512文件/256MiB，超限有TRUNCATED标记）、
候选HTML（最多256MiB）、阶段日志与outcome，申请保留14天；Pages制品1天。
强制取消/安装/runner故障可能没有诊断，上传失败仍为失败，不保证制品永久可用。

恢复：下载诊断后处理源/完整性/权限问题，再从最新默认分支dispatch一次全历史刷新；
这是**新刷新**，不是部署重试，也不保证相同HTML字节。不要削弱丢日期保护；
合法撤回日期需人工审阅，不提供自动旁路。

**Pages单独失败且Git已持久化：本工作流没有deploy-only命令/dispatch。**
失败job重跑会增加run_attempt，旧prepare制品不再符合receipt同attempt身份；
全部job重跑仍沿用旧event SHA，持久化后已不是当前base。因此两种rerun均不支持此恢复，
不得修改旧receipt的attempt/hash来绕过检查，也不要把重新获取近似页面当作精确恢复。
精确字节部署是**本工作流之外的授权人工/外部运维步骤**，不是这里提供的可执行恢复命令：

1. 有仓库和部署权限的操作者从原run/attempt的persist输出确认完整data commit SHA，
   核对repository、默认branch、event base及run/attempt与原receipt和prepare输出SHA256一致；
   确认当前远端默认分支仍指向该data commit，过期则停止并人工决定目标。
2. 从该commit读取根 `index.html`（不重渲染、不fetch），核对其SHA256与原已验证receipt
   的 `files["index.html"]["sha256"]` 一致；只将这一个文件交给获授权的外部部署流程。
3. 核对Pages Source=GitHub Actions、实际目标站点/环境、默认分支授权、pages-write/OIDC权限及审批；
   部署前再核对远端commit和制品hash，部署后从目标站点读取HTML核对同一SHA256。
   保存commit/run/attempt/hash与部署记录；部署不能绕过原授权、审批或再分发许可。

外部流程的实现和托管执行未由本地测试认证；Git与Pages仍不原子，不能保证最后检查后无竞争。
接受的不可变证据持续增长，不自动清理；
当前约10MB新增run/日的量级需预算Git历史、clone和制品存储。
通知依赖GitHub用户设置及调度创建/编辑/重新启用者；预期partial会告警，可能造成告警疲劳，
不要把该质量job设为代码合并必需check。丢失/禁用的调度不一定产生通知。

本地确定性验证：`uv run --frozen pytest -q tests/test_daily.py`。
使用留存/合成HTTP、真实worker/离线渲染与独立校验器、一次性本地bare remote，
没有真实provider请求、远端推送或部署；[精确命令/证据与限制](docs/daily-refresh-implementation-evidence.md)。

`--end YYYY-MM-DD` 默认当天。先严格验证完整响应，再按包含边界的窗口选行。
八个指数串行独立子进程，各45秒墙钟；随后一个共享QVIX组子进程，总共45秒，
不是每个QVIX另45秒。请求connect/read为5/12秒；fetch命令本身无重试、调度或推送。
请求自2000开始不表示当时已有源数据；不回填首次真实返回之前的历史。
真实运行及完整gate输出见 [本轮实施证据](docs/matched-qvix-implementation-evidence.md)。
本轮一次生产获取：八指数success，七QVIX均fresh partial，fetch退出1，非clean quality。

## 开发与部署

安装依赖后，开发检查与数据获取分开运行：

```sh
uv run python -m compileall -q app
uv run ruff check .
uv run pytest -q
```

**GitHub Pages**：先核对再分发许可，再提交并推送根目录的 `index.html`。
在 Settings → Pages 中选择 **Deploy from a branch → master → / (root)** 并保存。
发布页面也会公开其中的全部内嵌数据。

## 详细文档

- [设计与数据规则](docs/research/matched-qvix-plan.md)：数据映射、质量分类、比较日历和证据约束。
- [获取与迁移记录](docs/matched-qvix-implementation-evidence.md)：实际运行、源质量与不可变证据。
- [代码与数据复核](docs/reviews/matched-qvix-implementation-review-round2.md) · [浏览器复核（重设计前页面）](docs/reviews/matched-qvix-browser-review-round2.md)。
- [指数身份与官方日期](docs/research/index-identities.md) · [深证100补充依据](docs/research/matched-qvix-evidence/cnindex-399330-excerpt.md)。
