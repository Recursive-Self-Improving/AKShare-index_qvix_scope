# Independent alternatives evidence review

## Verdict: Fix — one material evidence qualification

Research-only review, 2026-11-15. Reviewed `../research/sentiment-alternatives.md`, all of `../research/alternative-evidence/` (currently `runtime.txt`), prior endpoint-feasibility and sentiment-recovery reports, and ledger AC6–8. No implementation review is required for unchanged code. No production, chart, ledger, or acquisition edits; no commits, endpoint-error retries, project tests, or browser launches.

The central recommendation is supported. One historical-depth comparison needs correction before this report receives an unconditional PASS. No architectural Replan or source replacement is needed.

## F1 — Fix: disclose conflicting CFND manuals; remove unsupported chronology

**Location:** `docs/research/sentiment-alternatives.md:26`.

The first linked [UIBE-hosted CNRDS manual](https://lib.uibe.edu.cn/docs/2019-12/20191230143850837733.pdf), printed pp. 41–43, supports article sentiment `1/-1/0`, company-level positive/neutral/negative counts by natural day and trading-time interval, and declared starts of **2002 for online news and 1994 for newspaper news**. These are catalogue claims, not returned coverage.

However, the second manual, labelled “较新手册”, [hosted by Shandong University](https://www.glxy.sdu.edu.cn/__local/8/63/D2/5C90CF36B67E763BAB84E161D3E_86A486B3_59A849.pdf?e=.pdf), printed pp. 4–6, instead lists **2004 for both modules**. The inspected text does not establish that this second manual is newer. The research presents the wider history without disclosing the conflict in its own citations. Historical depth matters particularly for a requested 2000-onward comparison.

**Required correction:** attribute 2002/1994 specifically to the UIBE-hosted manual; explicitly record the other manual's 2004/2004 claim; replace “较新” with a neutral host/source label unless a publication date is established. State that edition chronology, currently licensed history, per-security coverage and export/API availability require vendor or entitled-sample confirmation. Do not silently choose either range as current coverage. Acceptance requires only this research clarification, not a licensed runtime call or production change.

## Primary-source checks

| Candidate | Independently checked support | Qualification/access classification |
|---|---|---|
| [RQData news documentation](https://assets.ricequant.com/doc/rqdata/python/alternative-data#rqdata-API-news-overview) | Explicitly says 2017 onward and formal data updated every half hour intraday. Signature `news.get_stock_news(order_book_ids, start_date=None, end_date=None, fields=None)`; example imports `rqdatac_news`, initializes `rqdatac`, and calls `rqdatac.news.get_stock_news`. Return fields include article and company sentiment indicators and positive/neutral/negative weights, company relevance, news ID, stock ID, publication time and source. The printed example is dated 2021-03-01. | Strongest explicit Python interface candidate, not evidence of actual returned historical coverage in this project. Account, product entitlement, cost and redistribution terms unverified; no entitled call made. Article×company observations, not the original market index. |
| [CnOpenData/通联 catalogue](https://www.cnopendata.com/en/data/m/recent/news_a_share.html) | Confirms joint database, `SENTIMENT`, `SENTIMENT_SCORE`, `EFFECTIVE_TIME`; company index table has `NEWS_EFFECTIVE_DATE`, `TICKER_SYMBOL`, `NEWS_COUNT`, `CLAC_DIM_TYPE`, `HEAT_INDEX`, `SENTIMENT_INDEX`. Describes intraday/overnight/current-day company aggregation, deduplication and category filtering. Declares 2016-01-01–2023-10-16 and annual updates. | Daily statistical grain is distinct from annual catalogue delivery/update cadence. Commercial API access and academic CSV/Stata/Excel are advertised; no concrete callable API signature/authentication contract or sample rows are shown. Licensed/sales-gated, not proven current-to-2026 coverage. |
| CNRDS CFND manuals above | Real article sentiment classification and daily company counts, not merely generic investor mood. | Institution/entitlement-gated; history disagreement is F1. [Zhejiang University access notice](https://libdb.zju.edu.cn/s/lib/libtb/show/1990) specifies campus IP, personal registration, off-campus WebVPN and trial restrictions; it does not grant the reviewer full CFND history. Publicly readable manuals are not publicly callable data. |
| [FactSet ChinaScope SmarTag](https://insight.factset.com/resources/at-a-glance-chinascope-smartag) | Article- and company-level positive/neutral/negative sentiment; event-driven data, daily delivery. History describes crawler articles from 2017 and purchased sources from 2008–2016. Explicitly says details are as of January 2020; sales contact offered. | Historical product documentation, not proof of present purchasing availability, an API migration, or preservation of `maIndex1`/the old market-index formula. Same supplier does not establish same metric. Sales/contract access and actual history remain unknown. |
| [Investoday news API](https://std.investoday.net/apidocs/api-reference/%E6%96%B0%E9%97%BB%E4%B8%8E%E8%B5%84%E8%AE%AF/%E6%96%B0%E9%97%BB%E4%B8%8E%E8%B5%84%E8%AE%AF) | Documents `GET https://data-api.investoday.net/data/news`, required `apiKey` header, pagination, `beginTime` minimum 2020-01-01 00:00:00, `endTime`, and sentiment filter 1 bearish through 5 bullish. Printed response includes `sentimentScore` and `sentiment`. | API-key-gated, uncalled. Minimum permitted query date is not a measured data start; printed response is a documentation example. Securities filtering is described but its parameter name is absent from the displayed parameter table, correctly flagged in the research. Frequency, price, mapping and rights remain unresolved. |

These sources support the statement that similar news-sentiment products **do exist**, predominantly through account, institutional or commercial access. They do not establish that every listed product is currently purchasable, that any subscription includes unrestricted API use, or that redistribution is permitted.

## AC6–7: original migration and identical history

The [AKShare removal changelog](https://akshare.akfamily.xyz/changelog.html#v1-20-54) explicitly lists removal for certificate failure/timeouts, not a rename or substitute for `index_news_sentiment_scope`. Prior research distinguishes redirects/HTML, TLS errors, timeouts, an actual empty archive search, and documentation samples. Those outcomes must not become a claim of global nonexistence or zero historical observations.

An additional bounded search for `"chinascope" "senti/index" API migration` produced wrapper/product/documentation leads, not an official migration contract. Search summaries can cite stale main-branch documentation; they are not evidence of a working endpoint. This review found no positive migration or identical-history evidence that overturns the prior bounded conclusion. It did not repeat failed source/archive requests.

Acceptable conclusion: **No verified migrated endpoint or publicly obtainable authentic full same-metric history was found in the bounded searches.** Not acceptable: “the original never migrated”, “the metric no longer exists”, or “news sentiment is unavailable”. The ten explicitly printed historical AKShare rows remain documentation-example evidence, not 241 recovered observations or live provider response bytes.

## AC8: runtime evidence is more than HTTP200

`../research/alternative-evidence/runtime.txt:3–28` records three exit-0 subprocess invocations across **two distinct public interfaces**, not two licensed sentiment feeds:

- `stock_news_em(symbol="600519")`: first invocation reports 10 rows and six named news columns. A second invocation computes extrema over all returned timestamps: 2026-11-10 15:34:00–2026-11-15 12:09:48, with all ten timestamps listed. This supports the stated observed news batch/range, not only transport success. It proves neither sentiment scores nor complete history. News text was intentionally omitted; the file is a summarized execution transcript, not raw-response/hash archival evidence.
- `stock_market_activity_legu()`: reports 12 rows, `item/value` columns, actual breadth counts (744 up, 4415 down), activity 14.24%, and timestamp 2026-11-13 15:00:00. This supports a parsed breadth snapshot, not news sentiment or historical retrieval.

The opening statement that each subprocess had a 35-second limit is imprecise: the explicit second news command uses 25 seconds. All displayed commands are wall-clock bounded; this harmless summary inconsistency does not invalidate the two-interface result. Prefer “at most 35 seconds” when editing that evidence header.

No new runtime calls were needed for this evidence review. Retained output supports the limited observation claims; no independent re-execution or provider-authenticity guarantee is implied. Public reachability, no credentials and zero observed charge do not establish a redistribution license. VIX/CNN are explicitly untested, US-market proxies and are not counted among the successful probes.

## Corrected recommendation for the user

The original metric's migration has **not been verified**; no publicly obtainable identical full series was found within bounded searches. Ask ChinaScope/FactSet specifically for the old daily market series, continuity/formula, delivery endpoint, historical sample and license. Similar products exist: prioritize an entitled RQData news sample or CnOpenData/通联 company-day sample if a different methodology is acceptable. CFND is another genuine candidate, but its published history is edition-dependent and must be confirmed (F1). The successful credential-free probes provide raw news or market breadth, not equivalent sentiment.

Do not silently replace the chart's source. Any new aggregate requires explicit methodology, historical constituent/weight treatment, missing-news handling, publication/ingestion/revision timing, and licensed access. AC6–8 research does not unblock original AC1/AC3 genuine data acquisition or prove original-series nonexistence.
