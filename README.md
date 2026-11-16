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
保留卡片、浅/深色、导航、独立缩放、重置、滑条和1年/5年/全部控制。
一次内嵌Plotly JS，无CDN或伴随文件读取；直接用浏览器打开 `report.html`，无需Python运行时、安装依赖或启动服务器。
[独立代码/数据复核](docs/reviews/matched-qvix-implementation-review-round2.md)与[最终浏览器复核](docs/reviews/matched-qvix-browser-review-round2.md)均PASS；M-R1、M-R2、F-B1均已关闭。

## 运行（Python 3.14，固定锁）

```sh
uv sync --frozen
uv run python -m compileall -q app
uv run ruff check .
uv run pytest -q
uv run python -m app.fetch --start 2000-01-01
# partial/失败退出1；不要用 && 跳过仍可运行的离线命令
uv run python -m app.chart --input data --output report.html
uv run python -m app.verify --input data --report report.html
```

`--end YYYY-MM-DD` 默认当天。先严格验证完整响应，再按包含边界的窗口选行。
八个指数串行独立子进程，各45秒墙钟；随后一个共享QVIX组子进程，总共45秒，
不是每个QVIX另45秒。请求connect/read为5/12秒；无重试、调度、后台服务或推送。
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
- 图例保持原高度、改为左对齐，为右上角hover工具栏留出横向空间；保留全部控制与面板尺寸。
  最终浏览器复核已通过八面板全部19个图例文字中心的普通点击检查；父任务全量联合测试108项通过。
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
每panel逐feed可见尝试、快照身份/时间/状态、源/close范围、冲突/无效/零/缺口/源外及比较来源；
一个干净兄弟不能隐藏另一个警告，详情可展开。

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
