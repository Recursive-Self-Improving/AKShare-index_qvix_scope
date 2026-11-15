# 数库新闻情绪：迁移、同指标和替代研究

研究时间 2026-11-15。AC6–8 的研究证据，不修改图表、生产采集或目标账本。旧结论只证明特定环境中原服务不可可靠获取及有限档案查询未找到完整历史，**不能推论新闻情绪产品或迁移服务不存在**。这里区分实测、公开文档宣称和付费数据待验证；不把任何替代指标标成数库原指数。

## 直接结论与行动

1. AKShare 的旧接口是**删除，不是已知改名**。截至此次查询，未找到数库官方公开迁移 URL、参数或可调用的同指标接口；不能断言不存在。先联系数库/FactSet 或机构订阅，明确询问旧 `/inews/senti/index?period=YEAR` 的日度**市场指数原序列**、迁移地址、历史、授权和延续性。数库新闻分析系统和 SmarTag 是真实产品线，不证明含此指数。
2. 同一指标目前只有 AKShare 旧文档中实际印出的 10 条，详见 [既有证据](sentiment-recovery.md)；其 241 行是文档的展示描述，不是已恢复的 241 条。新搜索字段名、历史指数与第三方代码仅发现封装/引用，未获得可认证的额外历史数据；旧档案负结果及超时不能证明不存在。向原厂、大学现有订阅者和保留原始响应的研究者寻求带来源、采集时间、版本和再分发授权的历史；核对重叠日期与版本但重合并不能单独证明真实性。
3. 如果接受**不同口径**：优先试用米筐 `rqdatac.news.get_stock_news`（明确公开签名、逐股新闻情绪和历史查询），或通联/CnOpenData 的按公司日度 `SENTIMENT_INDEX`（直接具备日度粒度）；同时询数库 SmarTag 是否有市场级原指标。经权限、样本和授权确认后再决定；这些都不是自动等价替换。对于七指数，需另外定义全市场或逐指数历史成分股、权重、停牌/无新闻的缺失、去重和收盘前后新闻归属；不能将未来成分股回填或把缺失当零。记录发布时间与数据入库/修订时间以避免前视偏差。

## 原接口、迁移和同一历史

[AKShare 1.20.54 官方更新日志](https://akshare.akfamily.xyz/changelog.html#v1-20-54)单独列出 `index_news_sentiment_scope`：原因“网站证书失效且请求超时”，并未像该节其他项目一样给出替代名。[官方 issue #6245](https://github.com/akfamily/akshare/issues/6245) 2025 年报告 JSONDecodeError，2025-12 评论旧名 AttributeError；它没有提供迁移方案，不能据此断言今天上游的全球可用性。旧包装字段、重定向、TLS/超时及 Arquivo、Wayback、Common Crawl 有界查询详见 [feasibility](endpoint-feasibility.md) 和 [recovery](sentiment-recovery.md)，本次未为确认而重复这些失败。第三方 [Rust wrapper](https://docs.rs/akshare/latest/src/akshare/index/scope.rs.html) 是旧实现的独立封装而非历史响应或迁移证明。

[FactSet 对 ChinaScope SmarTag 的产品说明](https://insight.factset.com/resources/at-a-glance-chinascope-smartag)（明确标注资料截至 2020-01）称每篇及关联公司有正、中、负情绪，覆盖 A 股，事件驱动、每日交付；文章来自 2017 起爬虫及 2008–2016 采购来源。**这是产品所述文章来源时段，不是实测的市场指数历史、不保证现在仍可购买或回溯。**须联系 sales@factset.com 获取报价、授权、数据字典、交付方式及该原指数是否存在。[清华经管新闻分析系统介绍](https://www.sem.tsinghua.edu.cn/info/1154/36224.htm)称院内订购并限制有线 IP；是机构访问线索，非开放 API 证明。历史说明与当前供货情况均需核实。

## 最接近：真正新闻情绪（不是原指标）

按公开可操作程度及数据相似性排序，非质量或价格排名；下列范围均为厂商/手册宣称，除明确写明外未实测返回数据。

| 顺位与来源 | 实际接口/字段、频率和历史 | 访问、授权和对七指数的适配 |
|---|---|---|
| 1. [米筐 RQData](https://assets.ricequant.com/doc/rqdata/python/alternative-data#rqdata-API-news-overview) | `rqdatac.news.get_stock_news(order_book_ids, start_date=None, end_date=None, fields=None)`；单独安装并导入 `rqdatac_news`，先 `rqdatac.init()`。文章时间、代码、news_id、标题、来源，以及文章/公司正中负标签与权重和公司相关度；文档称 2017 起、正式数据盘中每半小时更新。文档样例 2021-03-01，并非本次运行；实际首末日期及完整性未知。 | 账户及该数据权限/报价和再分发条款待厂商确认；未持凭据、未调用。原始粒度为文章×股票，不是单条全市场日指数；可在授权下自定义聚合并可按成分股做各指数新闻情绪。 |
| 2. [CnOpenData/通联 中国上市公司新闻舆情](https://www.cnopendata.com/en/data/m/recent/news_a_share.html) | 逐篇 `SENTIMENT`, `SENTIMENT_SCORE`, `EFFECTIVE_TIME`；“中国公司新闻指数统计表”含 `NEWS_EFFECTIVE_DATE`, `TICKER_SYMBOL`, `NEWS_COUNT`, `CLAC_DIM_TYPE`, `HEAT_INDEX`, `SENTIMENT_INDEX`，文档称盘中、隔夜、当天公司指数，去重并过滤若干行业类别。页面给范围 **2016-01-01–2023-10-16**、年度更新；这是目录声称，非本次实测或全历史保证。 | 页面列商业版 API、学术版 CSV/Stata/Excel、试用及询价，具体 API 函数/认证/成本未公开确认；不假定当前更新至今。公司日度指数需按历史成分及权重再聚合，算法与数库不同。 |
| 3. [ChinaScope SmarTag](https://insight.factset.com/resources/at-a-glance-chinascope-smartag) | 同原厂，新闻/公司正中负得分，事件驱动、每日交付；来源年限见上。 | 机构授权和现行 API/价格未知。虽然是同厂，**无法证明同一市场指数或公式**，应先向供应商要求原数据或方法说明。 |
| 4. [UIBE 托管的 CNRDS CFND 产品手册](https://lib.uibe.edu.cn/docs/2019-12/20191230143850837733.pdf)；[山东大学托管手册](https://www.glxy.sdu.edu.cn/__local/8/63/D2/5C90CF36B67E763BAB84E161D3E_86A486B3_59A849.pdf?e=.pdf) | 中国上市公司财经新闻数据库，个股新闻情感分类及日度正中负计数；UIBE 托管手册印刷页 41–43 宣称网络新闻自 **2002**、报刊自 **1994**；山东大学托管手册印刷页 4–6 则宣称两者均自 **2004**。两份手册的历史目录陈述存在冲突，不能将任一范围视为已证实的当前覆盖。 | [高校访问说明](https://libdb.zju.edu.cn/s/lib/libtb/show/1990)为机构权限；手册版本先后、当前授权历史范围、逐证券覆盖及导出/API 可用性均须通过供应商或有权限的样本验证；价格及再分发条款待核实。可根据计数自行构造指标，不能冒称厂商连续分数或数库原指数。 |
| 5. [今日投资 `/data/news`](https://std.investoday.net/apidocs/api-reference/%E6%96%B0%E9%97%BB%E4%B8%8E%E8%B5%84%E8%AE%AF/%E6%96%B0%E9%97%BB%E4%B8%8E%E8%B5%84%E8%AE%AF) | `GET https://data-api.investoday.net/data/news`，`apiKey` 请求头，`beginTime` 最早可传 2020-01-01，`endTime`、`sentiment`、`newsType`、分页；响应列 `date`, `newsId`, `sentimentScore`, `sentiment`（1 利空至 5 利多）。页面描述可按证券筛选，但展示的参数表未确认证券参数名；最早允许参数不等于实际数据覆盖。 | 需 API key；费用、可用日期、数据授权、股票映射及更新频率未知，未持凭据实测。逐新闻聚合方法须另定。 |
| 6. [Wind Client API](https://www.wind.com.cn/mobile/ClientApi/zh.html) | 官方称可经 API 获取品种/组合新闻舆情和风险事件并做 AI 情感分析；没有公开具体情感函数、字段、频率、历史。 | 申请试用/联系销售；权限、价格、数据可提取性和授权待确认，不把产品宣传当可调用接口证明。 |

其他线索： [CSMAR 官方介绍](https://www.cicfconf.org/2025/files/CSMAR%20Intro%20EN.pdf)介绍 API，[高校 PDF](https://www.sbm.shisu.edu.cn/_upload/article/files/67/bb/3cff397249a9ab6ffbc72f3458c8/79b6c0f0-ea64-4b9e-bf02-72fd1172438e.pdf)投资者情绪库有综合/交易等指标；不能把它当已证实的新闻情绪接口。[Choice 用户指南](https://choice.eastmoney.com/choicewebfile/UserGuide.pdf)提供 AI 舆情日报线索；[iFinD 官方 FAQ](https://ftwc.51ifind.com/gwstatic/static/ds_web/quantapi-web/help-center/faq.html)确认 SDK/HTTP、账号区别及新闻通常夜间入库，但未证明可调用的新闻情绪字段。三者具体指标代码、历史、授权和价格均待询，不作排名同等替代。

## 公开可调用候选：实际结果与不等价代理

[实际命令及最小输出](alternative-evidence/runtime.txt)，调用以 `timeout` 设定整体时限，使用 AKShare 1.20.53，无凭据，2026-11-15 执行：

* [东方财富 `stock_news_em`](https://github.com/akfamily/akshare/blob/v1.20.53/docs/data/stock/stock.md)：`ak.stock_news_em(symbol="600519")` 10 条，返回新闻标题、内容、发布时间、来源、链接，时间跨度 **2026-11-10 15:34:00 至 2026-11-15 12:09:48**。不是情绪数据，没有得分；该单次结果不能证明完整历史、全市场覆盖或可再发布许可。可在获得授权后自行建立新闻 NLP 管线，但不等价于即用新闻情绪接口。
* [乐咕乐股 `stock_market_activity_legu`](https://github.com/akfamily/akshare/blob/v1.20.53/docs/data/stock/stock.md)：返回 12 项快照，统计时间 **2026-11-13 15:00:00**，上涨 744、下跌 4415、活跃度 14.24%。这是交易涨跌广度/活跃度，**非新闻情绪**；该调用无历史日期参数，单次快照不能满足长历史。
* [金十 `index_vix`](https://akshare-hh.readthedocs.io/en/latest/data/index/index.html) 是美股 CBOE 隐含波动率/恐慌代理，不是 A 股新闻。[CNN Fear & Greed](https://www.cnn.com/markets/fear-and-greed) 是美国市场多指标情绪，不是中国新闻。它们只适合作跨市场背景，不替代任何七个 A 股指数的新闻情绪。未进行运行测试；付费、覆盖和历史规则未核实。

实测不等于授权：AKShare 包的许可不是上游新闻及数据的再分发许可。发布网页/数据前须逐一确认上游、渠道和合同条款。联网结果仅是本机当时观测。付费产品无凭据不声称可用、历史完整或免费；本报告不能关闭原图表的真实情绪数据缺口。
