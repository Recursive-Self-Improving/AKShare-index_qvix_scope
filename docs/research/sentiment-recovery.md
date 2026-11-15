# ChinaScope sentiment recovery research

Observed 2026-11-15 20:26–20:27 UTC. Scope: same-provider API/website, public archives, and historical AKShare documentation/source. No production code, ledger, or TLS bypass. Network outcomes are specific to this environment.

## Result: ten documented historical observations, not a complete backfill

AKShare's own historical documentation, [v1.20.53 at commit 8fc02741a1807a2fa111d5baf119b19c5718ae79](https://github.com/akfamily/akshare/blob/8fc02741a1807a2fa111d5baf119b19c5718ae79/docs/data/index/index.md), attributes the sample to 数库 A股新闻情绪指数 and prints ten dated rows: five from 2023-10-31 through 2023-11-06 and five from 2024-10-25 through 2024-10-31. [Exact excerpt](recovery-evidence/akshare-v1.20.53-sentiment-excerpt.txt) preserves the values and ellipsis. Example: 2023-10-31 sentiment 0.986883; 2024-10-31 1.007300. This is an **AKShare documentation example**, not provider response bytes or an independently authenticated original capture; its original fetch time, precise revision and publication timestamps are unknown. It is evidence of ten reported values, not proof of unaltered wire data. The example says 241 rows, but the other 231 rows are not present and cannot be recovered from the ellipsis. Do not fill the gap or treat all intermediate days as observed. The repeated CSI 300 figures in the first five rows further warrant treating the example as documentation evidence, not independently validated market closes.

Reproduction:

```sh
curl --max-time 20 -sS 'https://raw.githubusercontent.com/akfamily/akshare/v1.20.53/docs/data/index/index.md' -o /tmp/scope-old-doc.md
rg -n -A65 -B5 'index_news_sentiment_scope' /tmp/scope-old-doc.md
sha256sum /tmp/scope-old-doc.md
```

Observed full downloaded document SHA-256 `3e8d086441ec1d252d556050d5b5a1112bc2199112d90daddf267d3228c89785`. GitHub [tag reference](https://api.github.com/repos/akfamily/akshare/git/ref/tags/v1.20.53) resolves to commit above. Retrieve immutable raw URL by replacing `v1.20.53` in the command with that commit. The excerpt is verbatim documentation text, not a provider raw JSON response. Documentation states approximately one year; this is a historical claim, not an observed current backfill guarantee.

## Other bounded approaches

1. **Current provider and migration.** Search queries `"chinascope" "senti/index" sentiment index API` and `"chinascope.com.cn" 情绪 指数 API` found the old endpoint and third-party implementations, but no verified replacement API or official migration contract. `curl --max-time 12 -sS -w '\nHTTP %{http_code}\n' 'https://www.chinascope.com.cn/' -o /tmp/scope-home` returned curl 60, `SSL certificate OpenSSL verify result: unable to get local issuer certificate (20)`, HTTP 000. Thus current official site assets could not be inspected over authenticated TLS. An indexed provider [NLP whitepaper](https://qiniu.csfimg.com/url/csf/pdf/ChinaScope%C2%A0NLP%C2%A0White%C2%A0Paper.pdf) likewise failed fetch due to an expired certificate; no supported endpoint inferred from this. Previous old-path redirect and timeout results are in [endpoint feasibility](endpoint-feasibility.md), not repeated here. No production request should disable certificate validation.
2. **Public archives.** `curl --max-time 15 -sS 'https://arquivo.pt/textsearch?versionHistory=www.chinascope.com%2Finews%2Fsenti%2Findex&maxItems=10'` returned HTTP 200, `estimated_nr_results:0`, `response_items:[]`. `curl --max-time 15 -sS 'https://index.commoncrawl.org/CC-MAIN-2025-47-index?url=www.chinascope.com%2Finews%2Fsenti%2Findex%2A&output=json&filter=status%3A200'` returned HTTP 504 gateway timeout; separately `https://index.commoncrawl.org/collinfo.json` returned HTTP 200. The 504 is not a negative archive result, and one crawl/index plus one Arquivo lookup cannot prove no archive exists. The earlier Wayback CDX timeout is recorded in endpoint feasibility.
3. **Historical documentation/caches.** Web searches `"maIndex1" "tradeDate" sentiment chinascope`, `"index_news_sentiment_scope" csv 数据 日期 市场情绪指数`, and `"index_news_sentiment_scope" "市场情绪指数" "2024"` led to AKShare's example above. The search engine claimed the current main branch still contained that example; direct `curl --max-time 20 -sS https://raw.githubusercontent.com/akfamily/akshare/main/docs/data/index/index.md -o /tmp/scope-index-doc.md; rg -n -A70 -B4 'index_news_sentiment_scope' /tmp/scope-index-doc.md` produced no match. Historical tagged file, not search summary, is the evidence. A [third-party wrapper](https://docs.rs/akshare/latest/src/akshare/index/scope.rs.html) corroborates field mapping but does not establish successful access or an archive.

## Feasible contract and remaining blocker

A defensible partial historical import can transcribe only the ten explicit documentation rows, with source URL, commit, documentation-example provenance and unknown original capture/publication time; preserve the excerpt and report the unobserved interval as unknown. Do not label these bytes as raw provider JSON or represent the stated 241-row frame as recovered. Check redistribution/license before incorporating samples into a published dataset. Do not use the date alone to claim point-in-time availability.

No verified publicly reachable authenticated current API, full historic response, or supported historical pagination was obtained. Complete same-provider backfill and live refresh are externally blocked in this environment pending provider restoration/valid TLS and an actual history contract, or access to authentic retained responses or licensed provider history. This is not proof no alternative archive or provider service exists. The prior 1.20.53 invocation remains the actual AKShare invocation evidence, not the example above.
