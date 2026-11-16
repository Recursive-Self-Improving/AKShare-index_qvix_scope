# 八指数与匹配 QVIX 历史对照

本地非商业实验；真实新浪指数收盘（左轴）与指定 AKShare 1.20.53
期权隐含波动率每日收盘（右轴，%）对照。不是新闻情绪、已实现波动率或预测证据。

| 顺序 / 指数 | 独立 QVIX 曲线（wrapper 后缀） |
|---|---|
| sh000001 上证指数 | 50index + 50etf |
| sh000016 上证50 | 50index + 50etf |
| sz399330 深证100 | 100etf |
| sh000300 沪深300 | 300index + 300etf |
| sz399006 创业板指 | cyb |
| sz399673 创业板50 | cyb |
| sh000680 科创综指 | kcb |
| sh000688 科创50 | kcb |

每条调用 `index_option_<后缀>_qvix()`；不替换端点、不加入500/1000。
前三条双QVIX面板（第1、2、4图）各三条可独立图例切换曲线；其余各两条。
同feed跨面板使用完全相同数组及固定比较日历，不随所在面板改变。
2026-11-16重新设计：顶部摘要、吸顶导航、图表在前、状态行在图下、质量表与读图须知置底；
保留浅/深色、独立缩放、重置、滑条、图例切换和1年/5年/全部控制（隐藏Plotly工具栏）。
一次内嵌Plotly JS，无CDN或伴随文件读取；直接用浏览器打开 `index.html`，无需Python运行时、安装依赖或启动服务器。
[独立代码/数据复核](docs/reviews/matched-qvix-implementation-review-round2.md)与[最终浏览器复核](docs/reviews/matched-qvix-browser-review-round2.md)均PASS；M-R1、M-R2、F-B1均已关闭。

## 运行（Python 3.14，固定锁）

```sh
uv sync --frozen
uv run python -m compileall -q app
uv run ruff check .
uv run pytest -q
uv run python -m app.fetch --start 2000-01-01
# partial/失败退出1；不要用 && 跳过仍可运行的离线命令
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

## V4与不可变证据

活动schema=`qvix-comparison-v4`：八指数+七QVIX，拒绝旧schema，无运行时v3兼容路径。
`latest.json`仅在独立离线验证后原子替换；清单验证/提升失败保留旧入口。
每个feed只有attempt、snapshot、stale_reuse，`previous`用路径/hash引用上个不可变清单。
历史runs、derived、研究和审阅均不修改；预编辑清单见
[`docs/matched-qvix-pre-edit.sha256`](docs/matched-qvix-pre-edit.sha256)。

本轮先显式新增 `data/derived/matched-qvix-v4/`，重算50ETF v4质量/CSV，
引用原始HTTP正文、transport、wrapper及源清单，保持原attempt/success/finish时间，
迁移时间单列derived_at；不是fetch。不重新解释或改写旧侧车。
原七指数沿用其已验证原始origin；深证100及其余六QVIX没有伪造prior。
随后新生产run整体替换可用结果；故新失败只能沿用自己原来的整快照，不能借用兄弟feed。

- 指数 `response-N.body` 是响应钩子应用解码前保留的 `Response.content`，
  HTTP解压后正文而非wire bytes。`transport.json`包括URL、状态、头、编码、时间/hash；
  重定向正文亦保留，当前策略拒绝重定向。`result.json`记录真实调用/版本/尝试和结果。
- 指数CSV为 `date,close,pre_release,pre_base`；官方日期不是新浪首次观察日。
  [399330官方留存摘录](docs/research/matched-qvix-evidence/cnindex-399330-excerpt.md)
  给出基日2002-12-31、发布2006-01-24；399004是另一个深证100R代码，不混用。
- QVIX组只存一份正文/transport，`group.json`绑定唯一group_id、获取时间、config hash，
  成员只存shared引用。七个实际wrapper共享真实加载缓存；加载失败即停，
  记录一个实际调用和其余not-invoked；wrapper局部失败不阻止后续兄弟。
- 各成员先持久化源顺序 `wrapper.csv`、规范CSV、单份 `quality.json`（全部候选、
  一开始的原始ordinal、坏字段原token、空白ordinal及完整日期集合），最后原子提交result。
  每个成员提交后才启动下一个。父进程在超时/崩溃/非零退出后独立验证并恢复已完成兄弟；
  不完整记录不成功，未完成成员分别fatal/自身prior stale。失败证据保留。
- 清单/HTML只含紧凑完整与选中计数/范围/引用；不复制候选payload或累积历史。
- 恢复/提升先验证不可变result的attempted_at、successful_at、finished_at及原始获取时间：
  必须是有效、含秒和UTC时区的ISO时间；缺失或不可用的完成记录只使自身失败/自身prior stale，
  直接提升拒绝且保留旧入口。派生v3仍须逐项保持原始时间，不能改用派生时间。
- HTML可见披露除逐panel/feed精确文本外，还校验现有容器祖先路径；
  hidden、内联style、额外/不允许的容器或披露内嵌标签均拒绝，JSON状态不能替代可见披露。
- 披露路径为 `html/body/main/section.panel/div.status/p`；QVIX行类须与状态一致
  （`quality ok`仅限新鲜success，否则`quality warn`）。图例居左、时间按钮居右同一上带。
  旧版浏览器复核（19个图例点击）针对重设计前页面，不覆盖当前版式。
  代码/浏览器PASS不改变七QVIX均fresh partial、fetch退出1的源质量状态，也不认证经济正确性。

## 稀疏、错误与日历

先验证全响应GBK、公共schema/一致宽度/规范真实日期；公共结构失败使全部成员无效。
缺少成员必需位置、numeric NaN/inf或wrapper/raw不符只使该feed fatal，
窗口外数据同样验证。非空非数值（包括电子表格错误与`22。27`）保留原token/字段/ordinal，
对应字段null，不修复；同一无歧义行的有限收盘仍保留并标partial。
零为有限源值，有可见notice，不自动当缺失，也不保证经济有效。
候选比较全OHLC及missing/invalid身份；不同候选使四个OHLC全null，即使close相同。
精确重复仅notice，包络异常保留值/partial；不选赢家、不拼接不同修订。

新鲜all-blank/all-error/all-conflict仍是证据快照并替换旧价格，partial且不stale；
只有fatal才沿用自身prior整快照并保持原时间。完整历史有价格但选中窗口没有时，
完整状态/范围不变，选中源与close范围分别为空；不以旧价格填空。
任一必需feed partial/fatal使fetch退出1，仍提升已验证的部分结果。

公共日期D、非空源日期N和无歧义有限close日期V分别决定公共、源S、close U范围。
空白行/空白独占日期分prefix/internal/tail，无N则单列no-source；
碰撞空白ordinal不删除已有候选。prefix不降级，内部/尾部空白和无全量close使partial。
固定比较源：50index/50etf→sh000001；100etf→sz399330；
300index/300etf→sh000300；cyb→sz399006；kcb→sh000688。
绑定原始origin/hash/time、全raw hash与原陈旧标记，不使用窗口裁剪CSV。
比较源缺失是unknown而非空集，缺失或陈旧不能宣称clean coverage。

在S内，比较日历缺口恰为 `(C ∩ S) \\ V`，分成互斥absent、blank、conflict、
invalid-close、missing-close；source-only为N中不属C的日期，另计blank-source-only。
选中集合均为全量集合与窗口交集，包括没有源行但存在缺口的窗口。
trace为N、内部/尾部空白（无N则全部空白）及已知holes的排序并集再选窗口，
不属V处显式null，`connectgaps=false`；因此保留源外错误/空白尾部，不合成日网格。
全量/选中行数与日期数分开；质量标签可重叠，不能相加当总缺陷数。
不是官方交易日历，共同遗漏无法发现，无响应后外推或官方完整性声明。
每panel逐feed可见状态、源/close范围、全部非零质量计数（窗口内不同时附注）、
陈旧/失败、未知值及比较日历陈旧/未知；零计数和新鲜时间省略，快照ID与比较指数见页底质量表。
顶部摘要卡片（`#summary`）与页底质量表（`#quality-table`）同样由verify独立重建并逐格比对
（文字、颜色类、属性），且须位于固定可见路径，隐藏/内联style/额外包裹均拒绝。
一个干净兄弟不能隐藏另一个警告。

## 独立校验与使用限制

verify核对原始获取身份、原时间、成员/共享body/transport/config/hash、固定wrapper离线禁网重放、
独立原始字段分组/日期集合/候选/CSV/质量摘要，以及真实HTML的各feed数组、null、轴、状态、
可见披露。它不以renderer或normalizer当oracle。通过不代表经济正确或浏览器交互通过。

上证综指比上证50宽；创业板50不是创业板指；科创综指含股息而科创50是价格指数。
ETF跟踪误差、衍生品流动性及股指/ETF不同均有影响。
[提供方](https://1.optbbs.com/s/vix.shtml?100ETF)命名不证明准确合约代码；
[深交所期权手册](https://investor.szse.cn/institute/rules/t20230309_599162.html)列出的ETF代码，
不能直接当作optbbs实际使用合约。期限、年化、计算截止、发布/修订/重建方法未知。
日期不是可交易获知时间；非point-in-time，无安全lag/因果/预测承诺。
固定wrapper走HTTP；早先HTTPS字节一致不追认HTTP认证，也不证明源值正确。
提供方提示可能出错，商业需授权；raw/派生数据及内嵌值HTML的再分发许可未确认。
仅供本地非商业实验，分发前核对实际许可。

历史情绪、文档样本及七图50ETF审阅仅为旧证据，不能当作本轮八图验收。
历史归档脚本需要对应历史checkout；活动运行时不保留情绪、旧单feed或兼容shim。
