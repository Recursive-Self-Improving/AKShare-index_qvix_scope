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
- Git持久化**不等于网站部署**。`GITHUB_TOKEN` 推送不会触发branch Pages构建。
  要部署网站，先启用 Pages（推荐 Source = **GitHub Actions**），允许默认分支部署到 `github-pages` 环境。
  未设置仓库变量 `PUBLISH_PAGES` 时，根据事件的 `repository.has_pages` 决定是否部署；
  `false` 仅更新仓库，`true` 明确要求部署。工作流不会创建站点或绕过审批。`Pages: disabled` 不代表网站已更新。
- 部署/公开仓库前确认原始、派生及HTML内嵌数据再分发授权；当前实验声明不是许可证。
  GitHub runner连通性、token/分支策略、通知、真实调度和部署须在托管环境另行验证。

## 安全发布

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

## 质量状态与部署结果

新鲜 `success` 或通过独立验证的新鲜 QVIX `partial` 都可持久化并部署。`partial` 保留 null 和页面质量提示；
预期的发布步骤完成后，`quality-status` 成功并发出 warning，摘要记录 `quality: partial`。
若共享 QVIX 采集超时、只能沿用旧快照，则不是这种 partial：`prepare` 拒绝发布，网站保留上一份报告。
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
always诊断仅保存本次新增证据（最多512文件/256MiB，超限有TRUNCATED标记）、
候选HTML（最多256MiB）、阶段日志与outcome，申请保留14天；Pages制品1天。
强制取消/安装/runner故障可能没有诊断，上传失败仍为失败，不保证制品永久可用。

接受的不可变证据持续增长，不自动清理；
实施时每次发布约新增10MB；若每天24次均发布，约新增240MB/日，需预算Git历史、clone和制品存储。
新鲜 partial 的警告可在该次运行中查看；它不触发工作流失败通知。
失败通知依赖GitHub用户设置及调度创建/编辑/重新启用者；丢失/禁用的调度不一定产生通知。

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
