# Repository guidance

## Lessons

- Use `uv sync --frozen` with Python 3.14 and this lock. AKShare 1.20.53 is the last approved version with `index_news_sentiment_scope`; 1.20.54 removed it. The installed JavaScript decoder imports `py_mini_racer`, but its distribution metadata name is `mini-racer` (not `py-mini-racer`).
- Capture `requests` response-hook `.content` before application decoding, including redirect responses; these are HTTP-decompressed bytes, not wire bytes. Request read/connect timeouts alone are not wall-clock bounds: acquisition uses one 45-second subprocess per source.
- Historical AKShare documentation puts the sentiment anchor immediately before its own `###` title. Splitting at the first heading yields an empty excerpt; bound the exact example using its explicit final dataframe row-count/fence, then transcribe only printed dated rows.
- Sina first observation is not official index inception. Store authoritative base/release dates and per-row pre-release/pre-base flags. In particular, vendor 沪深300 history starts before both official base and release; its reconstruction method remains unknown. 科创综指 includes dividends and is not the 科创50 price index.
- Keep provider failures nonzero and documentation examples separate. A successful offline report/hash check cannot establish genuine sentiment availability or browser interaction correctness. Never edit the orchestrator's goal ledger from an implementation slice.
- AKShare 1.20.53's sentiment wrapper raises a pandas column-projection KeyError for a valid HTTP200 `[]`. Keep the actual invocation/capture; recognize only that empty projection and strictly decode the captured body before treating it as observed empty success. Coverage of merged sentiment must be derived from all successful revisions, separately from the latest response; never rewrite an immutable acquisition manifest to migrate derived accounting.
