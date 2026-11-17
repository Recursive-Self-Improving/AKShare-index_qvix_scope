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

## 手动更新

手动更新或重建图表需要 **Python 3.14** 和 **uv**。在仓库根目录执行：

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

只想用现有数据重建图表，可以跳过 `fetch`。
`verify` 核对原始证据、派生数据与 HTML 的一致性，不认证源值正确性或浏览器交互。

## 自动更新与 Pages

[Daily verified refresh](.github/workflows/daily-refresh.yml) 按每天 **11:15 UTC（北京时间 19:15）** 调度，
也可在 Actions 页面从默认分支 **Run workflow**。每次获取完整源历史，图表窗口为
**2000-01-01 至实际准备开始时的 UTC 当天（含）**，不是滚动 30 天合并。
各源保留窗口内实际返回的最新交易日，不补周末／节假日；当天是否已齐取决于上游发布，
不能把请求成功当成当天数据已齐。选择晚间并避开整点是留出缓冲，不是准点或数据完整性保证。

启用前：

1. 确认再分发许可，允许 Actions 运行及 `GITHUB_TOKEN` 更新默认分支；分支规则须兼容，不绕过保护。
2. 需要自动部署时，在 Settings → Pages 选择 **GitHub Actions**，配置 `github-pages` 环境及默认分支授权／审批。
3. 将仓库变量 **`PUBLISH_PAGES` 设为 `true`**（小写）。未启用时只更新仓库，不部署网站。

自动发布比手动 `fetch` 更严格：

- 新鲜 QVIX `partial` 通过校验后可以发布，但最后的质量检查仍为红色；**红色不一定表示没有更新**。
- 任一获取失败、陈旧快照、旧日期丢失或校验失败，会阻止整次自动更新，保留此前公开版本。
- 数据提交与 Pages 部署不是原子操作；部署失败不回滚数据，也不能靠重跑旧任务恢复部署。

调度可能延迟或漏跑；本地验证不代表托管运行已验证。
完整配置、诊断与恢复步骤见[自动更新运维指南](docs/daily-refresh.md)。

## 使用限制

- **不补齐历史**：缺口不插值，冲突候选不选赢家。比较日历来自新浪而非官方交易日历，无法发现共同遗漏。
- **指标不能混同**：科创综指含股息，科创50是价格指数；ETF 跟踪误差及衍生品流动性也会影响比较。
  QVIX 的准确合约、期限、年化及发布／修订方法未确认。
- **不是无前视偏差的数据集**：历史日期不等于可交易获知时间，部分指数含正式发布前的回溯值，不能据此作因果或预测承诺。
- **校验不等于来源认证**：固定 QVIX 接口使用 HTTP；留存与哈希校验不能证明源值真实或经济上正确。
- **分发前核对许可**：原始数据、派生数据及内嵌数据的 HTML 再分发许可未确认；商业使用需提供方授权。

## 开发检查

安装依赖后，开发检查与数据获取分开运行：

```sh
uv run python -m compileall -q app
uv run ruff check .
uv run pytest -q
```

## 详细文档

- [设计与数据规则](docs/research/matched-qvix-plan.md)：数据映射、质量分类、比较日历和证据约束。
- [获取与迁移记录](docs/matched-qvix-implementation-evidence.md)：实际运行、源质量与不可变证据。
- [代码与数据复核](docs/reviews/matched-qvix-implementation-review-round2.md) · [浏览器复核（重设计前页面）](docs/reviews/matched-qvix-browser-review-round2.md)。
- [指数身份与官方日期](docs/research/index-identities.md) · [深证100补充依据](docs/research/matched-qvix-evidence/cnindex-399330-excerpt.md)。
