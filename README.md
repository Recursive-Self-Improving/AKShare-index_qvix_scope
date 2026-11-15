# 七指数与新闻情绪历史对照

这是**部分覆盖**的数据制品，不是完整情绪历史/成功实时双序列。七个新浪指数已实际采集；ChinaScope 当前情绪接口的真实 AKShare 调用失败，真实范围未知。另有十个 **AKShare 文档示例（documentation example, not live/full history）**，仅以孤立标记显示，不连接缺失的一年，不代表其余231行已恢复。

## 运行（Python 3.14，uv）

```sh
uv sync --frozen
uv run python -m compileall -q app
uv run ruff check .
uv run pytest -q
# 刷新/回填：一次完整源历史抓取，按请求窗口本地筛选，无分页猜测
uv run python -m app.fetch --start 2000-01-01
# --end YYYY-MM-DD 可固定结束日；默认本机当前日期
uv run python -m app.chart --input data --output report.html
uv run python -m app.verify --input data --report report.html
```

`fetch` 任意必需源失败即返回非零（目前情绪失败返回1），但保留七指数成功结果、失败证据和运行清单；**不能把非零说成抓取通过**。之后单独运行 chart/verify 仍可检查部分制品。无后台服务、无调度器、无自动重试。首次运行已包含数据，可不联网直接 chart/verify。`report.html` 内嵌一次 Plotly 和所有数组，直接离线打开，不读取相邻CSV或CDN。

七个独立图分别为上证指数 sh000001、上证50 sh000016、沪深300 sh000300、创业板指 sz399006、创业板50 sz399673、科创综指 sh000680、科创50 sh000688。各自日期范围和左右刻度独立；拖动框选缩放、滚轮缩放、底部范围滑条、1年/5年/全部按钮、双击或“重置本图”恢复。右轴为情绪，示例点与真实源情绪（若以后成功）有不同图例。当前没有成功提供方情绪曲线。

## 原始数据、状态与不可变修订

- `data/latest.json` 是唯一原子替换的运行入口；它与 `data/runs/<UTC+uuid>/manifest.json` 相同。每次运行创建新的目录，不覆盖旧快照。
- 每个源的 `response-N.body` 是 `requests.Response.content` 的**HTTP解压后、应用解码前**的精确正文，不是套接字压缩线缆字节；包括已收到的重定向正文。`transport.json` 记录逐跳请求URL（含查询）、URL、状态、头、编码、时间、SHA256。TLS失败后不存在的最终正文不会被伪造。
- `result.json` 记录实际调用、版本、窗口、结果和错误；成功快照有原始正文和CSV的SHA256、观察范围/行数、独立成功时间。情绪真正调用固定 AKShare 1.20.53 的 `index_news_sentiment_scope()`，只提供 `period=YEAR`，没有日期/分页参数；不能由名称推断当前可取一年或全部历史。该版本对HTTP200空数组的空DataFrame列投影会抛KeyError；仅识别该特定调用栈/状态且严格重解码确认为`[]`时，保存零行成功快照，不放宽其他错误。
- 各请求连接/读超时5/12秒；每源子进程墙钟45秒，串行八源，无重试。超时杀死工作进程，已写正文保留；没有可用正文的错误只保存错误。成功前校验HTML/畸形响应、日期顺序/重复/格式和数值有限性，原始解码重放与CSV一致后才原子发布清单。中断前一成功入口不变；孤立的未发布运行可留作取证。
- `feeds.*.attempt` 是本次状态；`snapshot` 是最近成功身份，`revisions` 保留全部成功身份；`stale_reuse` 明确陈旧复用。失败不能刷新成功时间。`success` 的零行响应与没有成功快照不同，非有限值不转零。CSV空字段表示源明确null，而0是数值0。
- 指数CSV为 `date,close,pre_release,pre_base`；标记1表示严格早于官方发布日期/基日。保留完整源正文，即使CSV只筛选2000年以后。指数使用最近成功完整快照；真实情绪使用按成功采集顺序的 **latest-successful-by-date** 合并策略：相同日期新成功覆盖，旧日期若未再出现仍保留。所有原始修订保留；合并结果**不是历史时点数据库**。
- 真情绪CSV为 `date,sentiment,market_close`。源 `marketClose` 只作为该源字段保存，绝不替换独立采集的沪深300。文档示例CSV也相同，但单独目录和明确来源分类，绝不提升实时采集状态。

## 覆盖、缺口与身份

运行的每源观察范围、行数及状态在清单；具体本次结果在 [实施证据](docs/implementation-evidence.md)。从2000-01-01到检索日仅表示请求窗口，不表示每日都有数据。第一条供应商记录不是成立/基日或首发日期；更早区间可用性未知，不推断“成立前”。结束日至最后观察日的间隔也不自行判定为停市或遗漏。

`snapshot.range/count/successful_at` 始终只描述最近一次成功响应。新运行的 `feeds.*.selected_history` 描述实际选中/绘图历史：`range`、`count`、`relative_gaps`、`relative_extra_dates` 和 `calendar_snapshot`；情绪按所有成功修订逐日合并，指数取最近成功快照。没有成功快照时count为null；观察到空成功历史时为0。报告内嵌JSON的顶层 `selected_history` 对所有运行独立派生相同字段，情绪提示区分别显示最近响应与选中历史。相对缺口在选中历史首尾范围内使用同一运行选中上证指数快照日期比较。这是**非独立相对交易日比较**，不是官方交易日历；无法识别共同遗漏。曲线为这些已知缺失日期插入null，关闭跨null连接；不补周末/假日，不外推情绪。样例仅markers，不跨年连线。

迁移不重写旧采集证据：现存不可变manifest和latest入口保留原始字节，旧的源级 `relative_gaps/relative_extra_dates/calendar_snapshot` 仍按其原始最近响应语义检查；重新生成报告时派生新的选中历史元数据，不制造新采集或成功时间。下一次真实fetch才写入新字段。`verify` 分别检查旧清单语义、新清单选中历史和报告选中历史，不能用最近响应范围冒充合并历史；见 [修正证据](docs/fix-evidence-round1.md)。

官方全名、代码、基日、发布日期和权威链接见 [身份研究](docs/research/index-identities.md)、`data/identities.json` 和各快照身份元数据。沪深300供应商2002年历史早于2004-12-31基日和2005-04-08发布，科创综指2020年数据早于2025-01-20发布；这些是**发布前/回溯供应商记录**，重建方法未知，不是当时公开可交易信息。科创综指包括股息，与科创50价格指数不同。

## 文档样例许可与复核

`data/documentation-example/` 保存 AKShare 提交 `8fc02741a1807a2fa111d5baf119b19c5718ae79` 的完整文档、同提交 MIT LICENSE、逐字节哈希、摘录及仅十行的转录CSV。MIT许可检查在转录之前；保留版权和许可。其证明的是文档可再现，不是独立认证的提供方原始响应；不声称拥有ChinaScope完整历史的许可。

如需在全新空目录重建该历史示例：`uv run python -m app.sample`（已有不可变目录时拒绝覆盖；通常无需运行）。该命令两次HTTP请求均5/12秒超时；生产采集另有45秒墙钟限制。提供方原始获取、发布、修订时间未知。完整实时情绪与完整回填仍依赖提供方恢复合法TLS/API或获得真实、授权的历史快照；见 [有界恢复研究](docs/research/sentiment-recovery.md)。

## 核查边界与回测限制

`verify` 不联网：校验实际已保存正文/逐跳SHA、成功正文重新用固定AKShare解码并与CSV字节比较；检查每个成功响应范围/行数及独立重算的选中历史范围/行数/相对缺口/额外日期/比较快照身份；检查不可变文档哈希/摘录/十行转录；独立解析HTML JSON，逐一比较七图真实数组/显式null/情绪轴/示例标记与CSV，并核对运行和失败身份。不是只数HTML字符串或生成一个无关的预期图。

观察日期不等于发布时刻。日内可得性未知，文档示例的原始获取/发布/修订时刻未知，回溯指数与后续修订会引入前视偏差。日期对齐不证明当日可交易、预测力、因果关系或任何“安全滞后”。本项目不做回测和收益承诺。离线交互视觉检查由独立审阅者执行；本实现阶段只运行数据/制品离线验证，不声称浏览器已通过。
