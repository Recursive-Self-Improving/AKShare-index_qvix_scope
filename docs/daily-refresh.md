# 每小时刷新与 Pages 运维

[返回 README](../README.md)

## 调度与数据窗口

工作流 [daily-refresh.yml](../.github/workflows/daily-refresh.yml) 在默认分支运行：
`15 * * * *`（每小时第15分钟，UTC）与手动 **Run workflow**，不接受其他分支或日期输入。
实际准备开始时冻结一次 UTC 日期，选择 **2000-01-01 至 UTC 当天（含）**，跨午夜不重算；
延迟运行采用实际开始日，不补造名义 cron 日期。各源保留窗口内实际观察到的最新交易日，
不以周一至周五推算交易日，不补周末/节假日，也不要求不同源的最新日期一致。
调度与手动运行都使用当天截止，盘中运行不保证当天数据或收盘值已齐。
每次完整替换能接收30天以前的修订；这些 wrapper 无上游窗口参数，30天选行会截断图表，
不会减少下载。不是滚动合并，不把旧价格拼回新鲜 null。

### 上游发布时间

2026-11-17 01:19 UTC 对源端点的有界 HEAD 观察（各20秒上限）：
- [QVIX 日线 CSV](https://1.optbbs.com/d/csv/d/k.csv)：HTTP200，
  `Last-Modified: Mon, 16 Nov 2026 09:37:06 GMT`（北京时间17:37）。
- [新浪深证100日线](https://finance.sina.com.cn/realstock/company/sz399330/hisdata/klc_kl.js?d=2020_2_4)：
  HTTP200，`Last-Modified: Mon, 16 Nov 2026 10:24:55 GMT`（北京时间18:24）。

`Last-Modified` 不是首次发布时间，也不证明修改涉及哪条记录；这些观察不能保证09:00 UTC数据已齐。
源站曾在[2020年公告](https://www.optbbs.com/thread-11908257-1-1.html)称QVIX日K通常15:30左右更新，
但这不是当前七条QVIX与八个新浪指数的统一发布承诺。每小时触发不是可用性SLA。
应看各快照实际覆盖日期与质量，不能以当天请求成功或新获取时间冒充当天行情。

### 未自动运行的排查

2026-11-17 检查公开API时，默认分支为 `master`、工作流状态 `active`、运行记录数为0；
默认分支已包含定时配置。尚无运行记录可解释具体漏触发原因，不能归因于获取脚本报错。
[GitHub说明](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)
调度在高负载时可能延迟或丢失，整点尤其拥挤；改为非整点只是降低风险，不是修复已证实的根因。
修改须进入默认分支才生效；需要补跑时从默认分支使用 **Run workflow**，不要重跑旧发布任务。

## 启用前的外部设置

- 将工作流合并到实际默认分支；允许 Actions、所固定的 actions、Python3.14.4、uv0.13.6，
  并提供 runner 分钟数/磁盘/制品配额。`uv sync --frozen --no-dev` 不改变锁，不安装开发依赖。
  顶层 actions 均固定经上游 tag 核对的完整 SHA；不是传递依赖锁或供应链安全认证。
  `ubuntu-24.04` 托管镜像/Git 仍会更新。
- 允许短期 `GITHUB_TOKEN` 直接更新默认分支，且分支保护/ruleset须兼容；不修改保护、不用PAT，
  不绕过必须PR/签名的规则。默认权限为空；prepare只读，独立publisher仅contents-write；
  不持久化checkout凭据。获取/安装/渲染只在只读job；writer仅运行标准库/Git与固定Actions工具。
- Git持久化**不等于网站部署**。要只部署图表，在仓库 **Settings → Pages → Build and deployment → Source**
  选择 **GitHub Actions**，允许默认分支部署到 `github-pages` 环境。显式部署只含 `index.html`，不提供仓库中的 `data/`、`docs/` 路径。
  未设置 `PUBLISH_PAGES` 时，本工作流根据事件的 `repository.has_pages` 决定是否部署；
  `false` 仅关闭这里的部署，`true` 明确要求部署。该变量不会切换 Pages 来源，也不会关闭独立的分支构建。
- 部署/公开仓库前确认原始、派生及HTML内嵌数据再分发授权；当前实验声明不是许可证。
  GitHub runner连通性、token/分支策略、通知、真实调度和部署须在托管环境另行验证。

## 安全发布

`app.daily` 先独立验证现有 `data/current/` 和 `index.html`，再在空的临时目录运行一次真实 fetch，
渲染并独立校验候选。必须是本次调用时间内的新采集：15 个新鲜成员，均属于自己的固定证据路径，窗口正确，所有选中日期不超过截止日。
基线和候选的相对路径相同，必须分别从各自的数据根读取原始响应。比较重叠请求窗口中的指数 raw 日期和 QVIX 公共 raw 日期；丢失任何旧日期均拒绝自动发布，
包括首/中/尾和等计数替换。比较不使用有限close集合，新鲜空白/冲突可按已有规则取代旧价格。
任何fatal、stale、未知/缺失、校验/执行错误均阻止整个更新；旧公开页面可能因此落后。

**定时运行的去重发生在上述校验及日期保留检查之后**：

- 比较8份新浪、7条QVIX所用的完整响应内容哈希（QVIX共用源）、源地址/编码、调用/版本、各序列的CSV和状态。
  QVIX 还比较 wrapper 输出、全量/窗口质量统计及比较指数的数据身份和陈旧状态。采集时钟和 HTTP 响应头变化本身不代表行情变化。
- 即使最后交易日、行数、收盘曲线不动，历史源字节修订也会触发发布。跨UTC日仅延长截止日、没有新选中行或质量变化时，不为日期另建快照。
- 数据一致时，用当前渲染器重建**原快照**，与已提交的 `index.html` 逐字节比较，避免漏掉模板更新。两者也一致才记 `unchanged`：保留原文件、窗口和获取时间，不生成候选包、不推送、不部署。
- 最新检查时间看 Actions 运行与摘要；页面显示上次发布的快照时间。`unchanged` 是相对事件基线的结果，**不是对线上页面的健康检查**。手动 **Run workflow** 会重新获取、校验并请求发布，即使内容相同；不能跳过质量或旧日期保护。

候选包只含完整的 `data/current/` 和根 `index.html`；清单是 `data/current/manifest.json`，没有第二份指针或前驱目录。
独立 `app/daily_transfer.py` 在新 runner 校验同一次 Actions run/attempt 的制品 ID、receipt SHA256 及各文件的
path/size/hash，拒绝额外/缺失路径、link、可执行模式或其他代码路径，不执行制品。
从精确 event base 用一条提交替换快照和页面；旧快照中不再有的文件一起移除，`data/` 的其他内容不参与替换。验证新 commit 的**完整父列表恰为 [receipt base]**，
只推送该commit一次，使用显式 `--force-with-lease=refs/heads/<branch>:<base>` 原子比较并更新。
这不是普通non-force push；sole-parent约束保证接受的base→commit严格快进，不改写已有历史。
当前远端不是base（包括分叉、回退或删除）即拒绝；规则拒绝也不fallback，
不使用通用force、不rebase、不重试、不换base。无法检测base→其他值→base的ABA历史变化。
模糊push响应只有精确远端commit读回才可认定持久化，否则unknown/失败；读回不是第二次push。

## 质量状态与部署结果

需要发布时，新鲜 `success` 或通过独立验证的新鲜 QVIX `partial` 都可持久化并部署。`partial` 保留 null 和页面质量提示；
预期步骤完成后，`quality-status` 成功并发出 warning，摘要记录 `quality: partial`。`unchanged` 也保留质量警告，不宣称本次部署。
共享 QVIX 采集超时导致成员获取失败，不是可发布的 `partial`；`prepare` 拒绝发布，保留上一份完整快照和报告。
应部署却失败或跳过，工作流仍失败，不把“已提交”误报成“已上线”。
Pages仅打包精确已验证 `index.html`，部署前再次检查已持久化commit；
event代码SHA与数据commit分开记录。Git与Pages不跨服务原子，部署失败不回滚数据，
最后一刻检查后的外部竞争也不能由Git锁保证；所有自动site writer应共用并发组。

## 资源、诊断与通知

固定workflow并发组不取消运行中实例；pending可被替换、调度可能延迟/丢失，
公共仓库不活跃可能禁用调度，并非exactly-once队列或“未运行”告警。
prepare/persist/Pages/conclusion分别限30/5/10/2分钟，prepare内部25分钟deadline；
8 个指数各限 45 秒（连接 5 秒、读取空闲 12 秒）。7 条 QVIX 共用一次 CSV 请求：
连接 5 秒、读取空闲最多 300 秒，整个共享子进程（含下载和解析）总计最多 5 分钟，不是每条各 5 分钟。
仍然超时就停止发布，不重试、不把旧快照当作本次获取。
候选最多512文件/256MiB；receipt最多1MiB，单命令日志最多4MiB（超限截断并失败）。

| 本工作流结果 | 上传及保留 |
|---|---|
| 定时校验通过，无变化 | 仅 Actions 日志和摘要，**零制品**，不新增 Git 文件。 |
| 有变化或手动请求发布 | 上传一份经校验的 `candidate-*`（14天），成功时不另传诊断副本。启用 Pages 时另传只含 HTML 的部署制品（1天）。 |
| 准备失败 | 尽力上传 `diagnostics-*`（14天）：日志、outcome、本次候选证据（最多512文件/256MiB，超限有TRUNCATED标记）和已生成的候选HTML（最多256MiB）。不发布。 |

候选上传失败时诊断中可有日志和outcome；persist/部署失败看该job日志与已上传的候选，不另复制原始数据。强制取消、安装、runner或上传故障可能没有制品。

实测旧[刷新运行 #44235114468](https://github.com/Recursive-Self-Improving/AKShare-index_qvix_scope/actions/runs/44235114468)
的候选、诊断、Pages 压缩制品分别为3.44、3.43、1.80 MB；同一数据提交还有一次独立的
[pages build and deployment](https://github.com/Recursive-Self-Improving/AKShare-index_qvix_scope/actions/runs/44235293553)，制品37.55 MB。
后者不是本工作流上传的单页包；应检查 Pages 来源，不要仅调短制品保留期。

每次发布都复用同一组工作树路径，不再按小时累积整份目录。Git 保留已提交的旧版本并复用内容相同的 blob；这不等于 Git 历史不再增长。
新鲜 partial 的警告可在该次运行中查看；它不触发工作流失败通知。
失败通知依赖GitHub用户设置及调度创建/编辑/重新启用者；丢失/禁用的调度不一定产生通知。

### 查看旧版本

用 `git log -- data/current/manifest.json` 查固定布局下的历次发布。`git show <提交>:data/current/manifest.json` 读取当时的清单；要离线回放，请在同一提交取出应用、完整 `data/` 和 `index.html`，不要把旧清单与当前证据混用。

本次布局迁移沿用 2026-11-18 04:39 UTC 的实际采集，不重新抓取。原始响应、CSV 和采集时间不变；含路径的元数据及其哈希随路径更新。迁移前的文档按当时提交的 `data/runs/`、`data/derived/` 布局阅读。更早已有七个 run 在一次独立的历史清理中移除，回看那些版本需要清理前的备份。

## 故障恢复

下载诊断后处理源/完整性/权限问题，再从最新默认分支dispatch一次全历史刷新；
这是**新刷新**，不是部署重试，也不保证相同HTML字节。不要削弱丢日期保护；
合法撤回日期需人工审阅，不提供自动旁路。

### Pages 单独失败且 Git 已持久化

**本工作流没有deploy-only命令/dispatch。**
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

## 实施验证与边界

实施时的本地确定性验证：`uv run --frozen pytest -q tests/test_daily.py`。
使用留存/合成HTTP、真实worker/离线渲染与独立校验器、一次性本地bare remote，
没有真实provider请求、远端推送或部署；[精确命令/证据与限制](daily-refresh-implementation-evidence.md)。

2026-11-17 调度/当天截止调整后：`uv run --frozen pytest -q tests/test_daily.py` 为54通过，
含当天行纳入、未来行排除、UTC跨日冻结及真实离线准备/发布边界；
`uv run --frozen ruff check app/daily.py tests/test_daily.py` 与
`actionlint .github/workflows/daily-refresh.yml` 均通过。未验证托管调度触发或当天源可用性。

2026-11-18 在本地临时目录用新预算运行真实 `prepare`：QVIX 共享请求取得 930038 字节，
首条调用至收到完整响应耗时 46 秒，已超过旧进程上限。8 个指数成功，7 条 QVIX 均为本次获取的 `partial`，
独立验证通过，整次准备耗时 78 秒。未提交该次数据或部署到 Pages；这不是 GitHub runner 的耗时保证。

按变化发布的本地验证：`uv run --frozen --offline pytest -q tests/test_daily.py`，70项通过。
重复获取相同内容不出候选包；旧源字段修订（15份选中CSV均未变）、截止日纳入新行、仅渲染器变化及手动发布均生成可校验的候选。
`actionlint` 和变更Python文件的 `ruff check` 通过；未触发托管工作流、推送或部署。
