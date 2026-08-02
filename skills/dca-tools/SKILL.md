---
name: dca-tools
description: |-
  510580 ETF 双周定投工具集。封装 tools/ 目录下的 Python 函数为可调用工具，
  支持查持仓、算份额、查价格、查估值、止盈判断、记录买入、定投日历等操作。
  触发词：定投、持仓、份额、PE、估值、止盈、510580、中证500、买入记录
---

# DCA 定投工具集

项目路径：D:\ws\dca-proj
工具源码：tools/ 目录（calculator.py、recorder.py、portfolio.py、scheduler.py、profit_taker.py、inspector.py、analyzer.py）
数据文件：D:\ws\dca-proj\portfolio.xlsx（持仓记录 Sheet1 + 定投日历 Sheet3）、tools/profit_taker_state.json（止盈状态）

## 路径注意事项

调用任何工具前，需要确保 Python 路径正确：

```python
import sys
sys.path.insert(0, r"D:\ws\dca-proj\tools")
sys.path.insert(0, r"D:\ws\dca-proj")
```

portfolio.xlsx 位于项目根目录（D:\ws\dca-proj\portfolio.xlsx）。
各模块通过 recorder.EXCEL_PATH 定位，main.py / inspector.py 启动时自动 patch 为绝对路径。

## 工具概览

| 工具名 | 功能 | 对应模块 |
|--------|------|---------|
| dca_calculate | 弹性股数法计算买入方案 | tools/calculator.py |
| dca_portfolio | 查看当前持仓状态 | tools/portfolio.py |
| dca_price | 获取实时价格 | tools/portfolio.py |
| dca_pe | PE 估值查询 | tools/portfolio.py |
| dca_records | 历史买入流水 | tools/recorder.py |
| dca_record_purchase | 记录一次买入（写操作） | tools/recorder.py |
| dca_profit_check | 三档止盈判断 | tools/profit_taker.py |
| dca_schedule | 生成定投日历 | tools/scheduler.py |
| dca_inspect | 每周巡检纯函数（五检查点） | tools/inspector.py |
| dca_analyzer | 回测 + 成本曲线 | tools/analyzer.py |

---

## 工具详细说明

### dca_calculate

**作用**：用弹性股数法计算给定金额能买多少手 ETF（1手=100份），返回实际花费和滚存零头。

**调用方式**：

```python
from calculator import calculate_shares

result = calculate_shares(500, 3.924)
```

**参数说明**：

| 参数 | 类型 | 含义 |
|------|------|------|
| amount | float | 本期定投金额（元），如 500 |
| price | float | 当前 ETF 单价（元/份），如 3.924 |

**返回值**：dict

| 键 | 类型 | 含义 |
|----|------|------|
| hands | int | 买入多少手（1手=100份） |
| shares | int | 买入多少份 |
| cost | float | 实际花费（元） |
| remainder | float | 剩余滚存（元），下期一并投入 |
| unit_price | float | 单价（回显） |
| amount | float | 原始定投金额（回显） |

**示例**：

```python
calculate_shares(500, 3.924)
# → {"hands": 1, "shares": 100, "cost": 392.4, "remainder": 107.6, "unit_price": 3.924, "amount": 500}
```

**注意**：price 必须大于 0，否则抛出 ValueError。

---

### dca_portfolio

**作用**：读取所有历史买入记录，计算当前持仓状态（总份额、均价、市值、浮盈亏）。

**调用方式**：

```python
from portfolio import analyze

result = analyze()
```

**参数说明**：无参数。

**返回值**：dict

| 键 | 类型 | 含义 |
|----|------|------|
| records_count | int | 累计买入次数 |
| total_shares | float | 累计份额（份） |
| total_invest | float | 累计投入（元） |
| avg_cost | float | 平均成本（元/份） |
| latest_price | float | 最新价格（元/份，新浪接口） |
| market_value | float | 当前市值（元） |
| pnl_value | float | 浮盈/浮亏（元，正为盈） |
| pnl_pct | float | 浮盈/浮亏（%） |

**示例**：

```python
analyze()
# → {"records_count": 2, "total_shares": 200, "total_invest": 792.0, "avg_cost": 3.96,
#    "latest_price": 3.95, "market_value": 790.0, "pnl_value": -2.0, "pnl_pct": -0.25}
```

**注意**：内部会调用 get_price_now() 获取实时价格，需要网络。持仓为空时返回空 dict {}。

---

### dca_price

**作用**：通过新浪行情接口获取 510580 当前价格。

**调用方式**：

```python
from portfolio import get_price_now

price = get_price_now()
```

**参数说明**：无参数。

**返回值**：float 或 None

- 成功：当前价格（元/份），如 3.924
- 失败（网络异常等）：None

**示例**：

```python
get_price_now()
# → 3.924
```

**注意**：依赖网络，超时 10 秒。非交易时间返回最近收盘价。

---

### dca_pe

**作用**：用乐咕乐股 akshare 接口获取中证500指数当前 PE 估值和历史分位。

**调用方式**：

```python
from portfolio import get_pe_data

pe = get_pe_data()
```

**参数说明**：无参数。

**返回值**：dict

| 键 | 类型 | 含义 |
|----|------|------|
| pe_date | str | 数据日期 |
| index_point | float | 指数点位 |
| pe_ttm | float | 滚动 PE(TTM) |
| pe_static | float | 静态 PE |
| pb | float | 市净率 |
| pe_5y_pct | float | 近5年 PE 分位（%） |
| pe_5y_high | float | 近5年最高 PE |
| pe_5y_low | float | 近5年最低 PE |
| pe_10y_pct | float | 近10年 PE 分位（%） |
| pe_5y_high_date | str | 近5年最高 PE 日期 |
| pe_5y_low_date | str | 近5年最低 PE 日期 |

**示例**：

```python
get_pe_data()
# → {"pe_date": "2026-07-25", "index_point": 5823.1, "pe_ttm": 22.5, "pe_static": 23.1,
#    "pb": 1.85, "pe_5y_pct": 35.2, "pe_5y_high": 35.8, "pe_5y_low": 18.2, "pe_10y_pct": 28.7, ...}
```

**注意**：依赖 akshare 库和网络，获取失败返回空 dict {}。分位越低越便宜。

---

### dca_records

**作用**：读取 portfolio.xlsx 中所有历史买入记录。

**调用方式**：

```python
from recorder import get_all_records

records = get_all_records()
```

**参数说明**：无参数。

**返回值**：list[dict]，每条记录包含：

| 键 | 类型 | 含义 |
|----|------|------|
| 日期 | str | 买入日期 |
| 标的代码 | str | ETF 代码（510580） |
| 标的名称 | str | ETF 名称 |
| 买入价格 | float | 成交单价 |
| 买入份额 | int | 买入份额（份） |
| 实际花费 | float | 实际花费（元） |
| 手续费 | float | 手续费（元） |
| 累计投入 | float | 截至该笔的累计投入 |
| 累计份额 | int | 截至该笔的累计份额 |
| 备注 | str | 备注信息 |

**示例**：

```python
get_all_records()
# → [{"日期": "2026-07-20", "标的代码": "510580", "买入价格": 3.924, "买入份额": 100, ...},
#    {"日期": "2026-07-21", "买入价格": 3.885, "买入份额": 100, ...}]
```

**注意**：文件不存在或无数据时返回空列表 []。

---

### dca_record_purchase

**作用**：追加一条买入记录到 portfolio.xlsx。⚠️ **写操作，执行前必须获得用户确认。**

**调用方式**：

```python
from recorder import add_purchase

record = add_purchase(
    buy_date="2026-08-03",
    buy_price=3.95,
    shares=100,
    cost=395.0,
    fee=5.0,
    total_invest=1187.0,
    total_shares=300,
    remark="第3期定投"
)
```

**参数说明**：

| 参数 | 类型 | 含义 |
|------|------|------|
| buy_date | str | 买入日期，格式 YYYY-MM-DD |
| buy_price | float | 成交单价（元/份） |
| shares | int | 买入份额（份） |
| cost | float | 实际花费（元） |
| fee | float | 手续费（元） |
| total_invest | float | 累计投入（元） |
| total_shares | int | 累计份额（份） |
| remark | str | 备注（可选，默认空） |

**返回值**：dict — 本条记录内容（用于确认写入成功）。

**⚠️ 重要**：这是写操作，会修改 portfolio.xlsx。AI 必须在执行前向用户确认所有参数，尤其是 total_invest 和 total_shares 需要基于上一条记录累加计算。

---

### dca_profit_check

**作用**：输入当前价格，判断是否触发三档止盈条件，返回建议操作。

**调用方式**：

```python
from profit_taker import check

result = check(4.95)
```

**参数说明**：

| 参数 | 类型 | 含义 |
|------|------|------|
| current_price | float | 当前价格（元/份） |

**返回值**：dict

| 键 | 类型 | 含义 |
|----|------|------|
| action | str | 建议操作："继续持有"/"卖一半（第一档）"/"再卖一半（第二档）"/"移动止盈（第三档）"/"本轮已结束" |
| profit_pct | float | 当前浮盈（%） |
| state | int | 止盈状态（0=未止盈, 1=已卖一半, 2=已卖3/4, 3=本轮结束） |
| state_name | str | 状态中文名 |
| trigger | bool | 是否触发止盈 |
| sell_shares | float | 建议卖出份额（0=不卖） |
| sell_amount | float | 建议卖出金额（0=不卖） |
| message | str | 说明文字 |

**示例**：

```python
check(4.95)
# → {"action": "卖一半（第一档）", "profit_pct": 26.12, "state": 0, "state_name": "未止盈",
#    "trigger": true, "sell_shares": 50, "sell_amount": 247.5, "message": "浮盈 26.12% >= 25%，触发第一档..."}
```

**止盈规则（第三课三档）**：
- 第一档（state 0→1）：浮盈 ≥ 25% → 卖剩余一半
- 第二档（state 1→2）：第一档卖价再涨 10% → 卖剩余一半
- 第三档（state 2→3）：历史最高价曾达 +30%，且从最高点回撤 ≥ 10% → 清剩余全部，本轮结束
- 重置：state==3 时，下一次买入（add_purchase）自动 reset()，开启新一轮
- 卖出基数 = 总份额 - 累计已卖（从 state.json sell_records 求和）
- check() 唯一副作用：更新 highest_price（追踪必需），不做 reset/sell 动作

---

### dca_schedule

**作用**：从指定日期开始，每 14 天生成一期定投计划列表。

**调用方式**：

```python
from scheduler import generate_schedule

schedule = generate_schedule("2026-07-20", 20)
```

**参数说明**：

| 参数 | 类型 | 含义 |
|------|------|------|
| first_date | str | 第一期日期，格式 YYYY-MM-DD |
| count | int | 总期数 |

**返回值**：list[dict]，每项包含：

| 键 | 类型 | 含义 |
|----|------|------|
| no | int | 期数（从 1 起） |
| planned | str | 计划日期 YYYY-MM-DD |
| weekday | str | 星期几（如"周一"） |
| amount | float | 计划金额（来自 config.py） |
| status | str | 状态标记（"⏳待执行"） |
| actual | str | 实际日期（空字符串表示未执行） |

**示例**：

```python
generate_schedule("2026-07-20", 3)
# → [{"no": 1, "planned": "2026-07-20", "weekday": "周一", "amount": 500, "status": "⏳待执行", "actual": ""},
#    {"no": 2, "planned": "2026-08-03", "weekday": "周一", "amount": 500, "status": "⏳待执行", "actual": ""},
#    {"no": 3, "planned": "2026-08-17", "weekday": "周一", "amount": 500, "status": "⏳待执行", "actual": ""}]
```

**注意**：间隔天数和金额从 config.py 读取（DCA_INTERVAL_DAYS=14, DCA_AMOUNT=500）。

---

### dca_inspect

**作用**：每周巡检纯函数，一次跑出五个检查点结论（准备/建仓/持有PE/止盈/纪律），可被 Cron 定时调用。

**调用方式**：

```python
from inspector import inspect_once

result = inspect_once()
```

**参数说明**：无参数（内部读 portfolio.xlsx + 获取实时价格 + 读 state.json）。

**返回值**：dict

| 键 | 类型 | 含义 |
|----|------|------|
| price | float | 当前价 |
| pnl_pct | float | 浮盈亏比(%) |
| profit_action | str | 止盈判断结论 |
| profit_trigger | bool | 是否触发止盈 |
| pe_pct | float | PE 分位(%) |
| pe_alert | str | PE 结论（pe_high/pe_low/pe_normal） |
| warning_20 | bool | 浮亏≥20%? |
| skip_alert | str | 别跳投结论（ok/warn_skip） |
| summary | str | 一段话总结（可直接推微信） |

**五个检查点**：
- B-① 准备：返回 ok（不需定时检查）
- B-② 建仓：已有 Day7 双周 Cron，跳过
- B-③ 持有：PE>70% → pe_high，<30% → pe_low，区间 → pe_normal（只提醒不卖出）
- B-④ 止盈：调 profit_taker.check()，触发时返回 sell_tier + 建议份数
- B-⑤ 纪律：浮亏≥20% → warning_20=True；定投日已过未买 → warn_skip

**示例**：

```python
inspect_once()
# → {"price": 3.95, "pnl_pct": -2.5, "profit_action": "继续持有",
#    "profit_trigger": false, "pe_pct": 35.2, "pe_alert": "pe_normal: 估值中性(35.2%)",
#    "warning_20": false, "skip_alert": "ok",
#    "summary": "本周巡检：当前价 3.950 元。浮盈亏 -2.50%。pe_normal...。不替你下单，只给结论。"}
```

**注意**：纯函数，无 input()，无业务副作用（不改 xlsx）。check() 更新 highest_price 属观测追踪。

**Cron 提示词（每周一 9:00）**：
> 调用 dca-tools Skill 执行周巡检。运行 inspector.inspect_once() 获取五个检查点结论。把 summary 字段推送到微信。如果有止盈触发或浮亏预警，额外加粗提醒。不替我下单，只给结论。如果全部正常，推"本周无异常，继续持有"。

---

### dca_analyzer

**作用**：定投回测 + 实盘成本曲线（方案A·③持有能力归位），独立实现，不依赖 Day5/code/。

**调用方式**：

```python
from analyzer import backtest_dca, plot_cost_curve

# 回测
result = backtest_dca("2022-01-01", "2025-01-01", amount=500, interval_days=14)

# 实盘曲线
path = plot_cost_curve()
```

**backtest_dca 参数**：

| 参数 | 类型 | 含义 |
|------|------|------|
| start | str | 回测起始日 YYYY-MM-DD |
| end | str | 回测结束日 YYYY-MM-DD |
| amount | float | 每期投入金额（默认500） |
| interval_days | int | 定投间隔天数（默认14） |

**backtest_dca 返回值**：dict（periods, total_invest, avg_cost, final_value, return_pct, max_drawdown, schedule）

**plot_cost_curve**：无参数，读 portfolio.xlsx 真实记录画图，输出 tools/output/cost_curve.png。

**注意**：依赖 akshare（回测）和 matplotlib（画图）。回测用中证500指数日线数据模拟，不限手数。
