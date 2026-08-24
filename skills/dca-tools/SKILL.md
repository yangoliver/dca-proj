---
name: dca-tools
description: |-
  510580/510300 ETF 双周定投工具集。封装 tools/ 目录下的 Python 函数为可调用工具，
  支持查持仓、算份额、查价格、查估值、止盈判断、记录买入、定投日历、周巡检、回测等操作。
  触发词：定投、持仓、份额、PE、估值、止盈、510580、510300、中证500、沪深300、买入记录、周巡检、微笑曲线
---

# DCA 定投工具集

> 本技能把 `dca-proj` 仓库的 `tools/` Python 工具暴露给 QClaw，让助手能直接查实盘、算方案、做止盈判断与周巡检。

## 项目根（本机默认）

```python
PROJECT_ROOT = r"<PROJECT_ROOT>"   # 仓库移动后改此常量即可
```

> 仓库本身用相对路径（见 `recorder.EXCEL_PATH`/`config.py`），可 Fork 到别处；这里只是本机默认的调用入口。

## 标准调用引导（每次用工具前先跑这段）

```python
import sys, os
PROJECT_ROOT = r"<PROJECT_ROOT>"
for p in (os.path.join(PROJECT_ROOT, "tools"), PROJECT_ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)
import config  # ETF_CODE / DCA_AMOUNT(500) / DCA_INTERVAL_DAYS(14)
```

数据文件：`<PROJECT_ROOT>/data/portfolio.xlsx`（按 ETF 分 sheet：`{code}_买入记录` + `{code}_定投日历`，如 `510580_买入记录`）、`tools/profit_taker_state_{etf_code}.json`（每 ETF 独立止盈状态）。
运行时（`main.py`/`inspector.py`）会自动把 `recorder.EXCEL_PATH` patch 为绝对路径，无需手动设置。

### 双 ETF 架构要点

- `config.ETF_LIST` 定义所有支持的 ETF（代码→名称/指数/首期/金额）
- `config.DEFAULT_ETF = "510580"` — 不传参数时默认
- `config.get_etf_config(etf_code)` — 获取指定 ETF 的配置 dict
- `config.sheet_name(etf_code, "buy"|"schedule")` — 返回动态 sheet 名
- **所有数据函数均接受 `etf_code` 参数**（默认 510580），不传则操作默认 ETF
- PE 估值自动路由：510580→中证500(000905)，510300→沪深300(000300)

## 工具概览

| 工具名 | 功能 | 对应模块 |
|--------|------|---------|
| dca_calculate | 弹性股数法计算买入方案 | tools/calculator.py |
| dca_portfolio | 查看当前持仓状态（实时价+浮盈亏） | tools/portfolio.py |
| dca_price | 获取实时价格（新浪，超时10s） | tools/portfolio.py |
| dca_pe | PE 估值查询（乐咕乐股/akshare） | tools/portfolio.py |
| dca_records | 历史买入流水 | tools/recorder.py |
| dca_record_purchase | 记录一次买入（⚠️写操作，须用户确认） | tools/recorder.py |
| dca_profit_check | 三档止盈判断 | tools/profit_taker.py |
| dca_schedule | 生成定投日历（每14天一期） | tools/scheduler.py |
| dca_inspect | 每周巡检纯函数（五检查点，可 Cron） | tools/inspector.py |
| dca_analyzer | 回测 + 成本曲线 | tools/analyzer.py |
| dca_smile | 微笑曲线分析 | tools/smile_curve_analyzer.py |

---

## 工具详细说明

### dca_calculate

**作用**：用弹性股数法计算给定金额能买多少手 ETF（1手=100份），返回实际花费和滚存零头。

```python
from calculator import calculate_shares
calculate_shares(500, 3.924)
# → {"hands": 1, "shares": 100, "cost": 392.4, "remainder": 107.6, "unit_price": 3.924, "amount": 500}
```

| 参数 | 类型 | 含义 |
|------|------|------|
| amount | float | 本期定投金额（元），如 500 |
| price | float | 当前 ETF 单价（元/份），如 3.924 |

返回值：`hands`(手) / `shares`(份) / `cost`(花费) / `remainder`(滚存零头) / `unit_price` / `amount`。
注意：price 必须 > 0，否则 ValueError。

---

### dca_portfolio

**作用**：读取所有历史买入记录，计算当前持仓（总份额、均价、市值、浮盈亏）。

```python
from portfolio import analyze
analyze()                        # 默认 510580
analyze(etf_code="510300")       # 指定 ETF
# → {"records_count": 3, "total_shares": 300, "total_invest": 1220, "avg_cost": 4.0667,
#    "latest_price": 4.262, "market_value": 1278.6, "pnl_value": 58.6, "pnl_pct": 4.8}
```

参数：`etf_code: str = "510580"`。内部调 `get_price_now(etf_code)` 需网络；持仓为空返回 `{}`。

---

### dca_price

```python
from portfolio import get_price_now
get_price_now()                    # → 4.262（默认510580）
get_price_now(etf_code="510300")   # → 沪深300ETF价格
```
新浪接口，超时 10s，非交易时间返回最近收盘价。

---

### dca_pe

```python
from portfolio import get_pe_data
pe = get_pe_data()                    # 默认510580→中证500
pe = get_pe_data(etf_code="510300")   # 510300→沪深300
# dict：pe_ttm / pe_5y_pct / pe_10y_pct / pb / index_name / index_code ...
```
乐咕乐股 akshare 接口，依赖 akshare 库与网络，失败返回 `{}`。**分位越低越便宜，但 PE 只作提醒，不触发买卖。**

---

### dca_records

```python
from recorder import get_all_records
get_all_records()                        # 默认510580
get_all_records(etf_code="510300")       # 510300记录
# list[dict]，每条含 日期/标的代码/买入价格/买入份额/实际花费/手续费/累计投入/累计份额/备注
```
文件不存在或无数据返回 `[]`。

---

### dca_record_purchase ⚠️ 写操作

```python
from recorder import add_purchase
add_purchase(
    buy_date="2026-08-17", buy_price=4.262, shares=100, cost=426.2, fee=5.0,
    total_invest=1220.0, total_shares=300, remark="第3期定投",
    etf_code="510580"    # 指定ETF（默认510580）
)
```
**执行前必须向用户确认所有参数**，尤其 `total_invest`/`total_shares` 需基于上一条记录累加。会修改 `portfolio.xlsx`。

---

### dca_profit_check

```python
from profit_taker import check
check(4.95)                           # 默认510580
check(4.95, etf_code="510300")        # 指定ETF
# → {"action": "卖一半（第一档）", "profit_pct": 26.12, "state": 0, "state_name": "未止盈",
#    "trigger": True, "sell_shares": 50, "sell_amount": 247.5, "message": "..."}
```

**三档止盈（第三课）**：
- 第一档（state 0→1）：浮盈 ≥ 25% → 卖剩余一半
- 第二档（state 1→2）：第一档卖价再涨 10% → 卖剩余一半
- 第三档（state 2→3）：历史最高价曾达 +30% 且从最高点回撤 ≥ 10% → 清剩余全部，本轮结束
- 重置：state==3 时下次 `add_purchase` 自动 `reset(etf_code)` 开新一轮
- 每 ETF 独立状态文件：`profit_taker_state_{etf_code}.json`
- 卖出基数 = 总份额 - 累计已卖（state.json `sell_records` 求和）
- `check()` 唯一副作用：更新 `highest_price`（追踪必需），**不做 reset/卖出**

---

### dca_schedule

```python
from scheduler import generate_schedule
generate_schedule("2026-07-20", 20)                        # 默认510580
generate_schedule("2026-08-03", 20, etf_code="510300")     # 指定ETF
# list[dict]，每14天一期，金额读 config.ETF_LIST[etf_code]["amount"]
```

---

### dca_inspect

```python
from inspector import inspect_once
inspect_once()                        # 默认510580
inspect_once(etf_code="510300")       # 指定ETF
# → {"etf_code": "510580", "etf_name": "易方达中证500ETF",
#    "price": 4.262, "pnl_pct": 4.8, "profit_action": "继续持有", "profit_trigger": False,
#    "pe_pct": ..., "pe_alert": "pe_normal", "warning_20": False, "skip_alert": "ok",
#    "should_push": True, "push_reasons": [...], "summary": "[510580]巡检：..."}
```
纯函数，无副作用（不改 xlsx，仅 `check()` 更新 highest_price 属观测）。五检查点：准备/建仓/持有PE(只提醒不卖)/止盈/纪律(浮亏≥20%或漏投预警)。**Cron 可直接调用，不替用户下单，只给结论。** 遍历 `config.ETF_LIST` 即可巡检所有 ETF。

---

### dca_analyzer

```python
from analyzer import backtest_dca, plot_cost_curve
backtest_dca("2022-01-01", "2025-01-01", amount=500, interval_days=14)  # 回测 dict
plot_cost_curve()                               # 默认510580实盘曲线
plot_cost_curve(etf_code="510300")              # 510300实盘曲线
# → tools/output/cost_curve.png
```
依赖 akshare（回测）+ matplotlib（画图）。

---

### dca_smile

```python
from smile_curve_analyzer import analyze_smile
analyze_smile("510580")   # 峰值→谷底→恢复 的微笑曲线量化
```
量化历史最大跌幅、填坑所需金额、定投 vs 一次性成本差。

---

## 使用纪律（务必遵守）

1. **到点就买，不择时**：定投日到了就执行，不因涨跌犹豫。
2. **PE 只提醒不触发**：PE 近5年分位 >70% 或 <30% 提醒，但绝不据此买卖。
3. **写操作必确认**：`add_purchase` 前把全部参数念给用户确认。
4. **巡检不下单**：`inspect_once()` 只给结论，不自动交易。
5. **止盈看收益率**：触发操作只看目标收益率（三档），不看估值。
