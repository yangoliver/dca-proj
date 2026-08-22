---
name: monthly-report
description: |-
  生成月度汇报第一节"持仓现状"的数字内容。读取 data/portfolio.xlsx 持仓数据，
  获取实时价格，计算市值和盈亏，输出 Markdown 格式。依赖 dca-tools 提供的工具函数。
  触发词：写月度汇报、生成月报、月报、持仓现状
---

# 月度汇报 Skill

## 功能定位

**只做一件事**：读取持仓数据，生成月度汇报第一节"持仓现状"的完整数字，输出为 Markdown。

**不做的事**：
- 不填写第二～六节（反思、纪律、计划）——由用户自己写
- 不给投资建议、不写主观判断

## 依赖

依赖 **dca-tools Skill** 提供的工具函数（确保 dca-tools 已加载）：
- `recorder.get_all_records(etf_code=...)` — 读 `{code}_买入记录` sheet
- `portfolio.get_price_now(etf_code=...)` — 新浪实时价
- `config.ETF_CODE` / `config.ETF_NAME` / `config.get_etf_config()` / `config.sheet_name()` — ETF 配置

tools/ 接口变化时只更新 dca-tools SKILL.md，本 Skill 自动继承。

## 项目根（本机默认）

```python
PROJECT_ROOT = r"<PROJECT_ROOT>"
```

## 执行步骤

### 1. 设置 Python 路径

```python
import sys, os
PROJECT_ROOT = r"<PROJECT_ROOT>"
for p in (os.path.join(PROJECT_ROOT, "tools"), PROJECT_ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)
```

### 2. 取持仓与实时价

```python
from recorder import get_all_records
from portfolio import get_price_now
records = get_all_records(etf_code="510580")  # {code}_买入记录 所有买入记录
latest_price = get_price_now(etf_code="510580")  # 当前价（float，失败为 None）
```

从 `records[-1]` 取 `total_shares`（累计份额）与 `total_invest`（累计投入）。

### 3. 计算指标

- `avg_cost = total_invest / total_shares`
- `market_value = total_shares * latest_price`
- `pnl_value = market_value - total_invest`
- `pnl_pct = (pnl_value / total_invest) * 100`

### 4. 读定投日历（{code}_定投日历）

```python
import openpyxl
from config import sheet_name
excel_path = os.path.join(PROJECT_ROOT, "data", "portfolio.xlsx")
ws = openpyxl.load_workbook(excel_path)[sheet_name("510580", "schedule")]
schedule_data = [{"期数": row[0], "计划日期": row[1], "状态": row[4] or "⏳待执行",
                  "实际日期": row[5] or ""} for row in ws.iter_rows(min_row=2, values_only=True) if row and row[0] is not None]
```

### 5. 生成 Markdown（替换实际数字）

```markdown
## 一、持仓现状

**数据截止日期**：YYYY-MM-DD

### 1.1 持仓概览

| 指标 | 数值 |
|------|------|
| 标的 | 易方达中证500ETF（510580） |
| 累计买入次数 | N 次 |
| 累计份额 | N 份 |
| 累计投入 | ¥N.NN |
| 持仓均价 | ¥N.NNNN /份 |
| 当前价格 | ¥N.NNN /份 |
| 当前市值 | ¥N.NN |
| 浮盈/浮亏 | ¥N.NN（+N.NN%） |

### 1.2 各期买入记录

| 期数 | 日期 | 价格 | 份额 | 花费 | 手续费 | 累计投入 | 累计份额 | 备注 |
|------|------|------|------|------|--------|----------|----------|------|
| 1 | ... | ... | ... | ... | ... | ... | ... | ... |

### 1.3 定投日历执行情况

| 期数 | 计划日期 | 状态 | 实际日期 |
|------|----------|------|----------|
| 1 | ... | ✅已完成 | ... |
```

### 6. 写入文件

目标月报文件由用户指定（通常是最新 Day 的 `report/` 下月度汇报 md，如 `Day12/report/月度汇报_YYYY年M-M月.md`）。
写入方式：
1. 读模板，找 `<!-- 月度汇报 Skill 输出开始（粘贴区） -->` 与 `<!-- 月度汇报 Skill 输出结束 -->` 标记
2. 将 Markdown 插入标记之间；若无标记，在 `## 一、持仓现状` 后插入
3. 提示用户"第一节已生成，请继续填写第二～六节"

## 注意事项

1. 路径用 `os.path.join()`，不硬编码绝对路径（本 Skill 内的 `PROJECT_ROOT` 常量除外）
2. `get_price_now()` 返回 None → 提示检查网络，用上次价格或 0
3. `records` 为空 → 输出"暂无持仓记录"
4. 金额 2 位小数，价格 3-4 位，百分比 2 位
5. **只填第一节**，不碰第二～六节
