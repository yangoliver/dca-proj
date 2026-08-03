---
name: monthly-report
description: |-
  生成月度汇报第一节"持仓现状"的数字内容。读取 data/portfolio.xlsx 持仓数据，
  获取实时价格，计算市值和盈亏，输出 Markdown 格式到 Day10/report/月度汇报文件。
  触发词：写月度汇报、生成月报、月报
---

# 月度汇报 Skill

## 功能定位

**只做一件事**：读取持仓数据，生成月度汇报第一节"持仓现状"的完整数字，输出为 Markdown。

**不做的事**：
- 不填写第二～六节（反思、纪律、计划）——这些由用户自己写
- 不给投资建议
- 不写主观判断

---

## 依赖

本 Skill 依赖 **dca-tools Skill** 提供的工具函数：
- `recorder.get_all_records()` — 读取 Sheet1 买入记录
- `portfolio.get_price_now()` — 获取实时价格
- `config.ETF_CODE` / `config.ETF_NAME` — ETF 配置

当 `tools/` 接口变化时，只需更新 dca-tools SKILL.md，本 Skill 自动继承。

---

## 数据来源

| 字段 | 来源 |
|------|------|
| 累计投入、累计份额、持仓均价 | 读 `data/portfolio.xlsx` Sheet1 |
| 当前价格 | 新浪接口（510580） |
| 当前市值、浮盈亏 | Skill 计算 |
| 各期买入记录 | 读 Sheet1 |
| 定投日历 | 读 Sheet3 |

---

## 执行步骤

### 1. 设置 Python 路径

```python
import sys, os

PROJECT_ROOT = r"<项目根>"  # 替换为 dca-proj 在本机的实际克隆路径
sys.path.insert(0, os.path.join(PROJECT_ROOT, "tools"))
sys.path.insert(0, PROJECT_ROOT)
```

### 2. 获取持仓数据与实时价格

通过 dca-tools Skill 提供的函数获取（详见 dca-tools SKILL.md）：
- `records = get_all_records()` — 返回 Sheet1 所有买入记录
- `latest_price = get_price_now()` — 返回当前价格（float）

从 `records` 最后一条记录获取 `total_shares`（累计份额）和 `total_invest`（累计投入）。

### 3. 计算持仓指标

从 `records` 最后一条记录获取：
- `total_shares`：累计份额
- `total_invest`：累计投入

计算：
- `avg_cost` = total_invest / total_shares
- `market_value` = total_shares * latest_price
- `pnl_value` = market_value - total_invest
- `pnl_pct` = (pnl_value / total_invest) * 100

### 4. 读取定投日历（Sheet3）

```python
import openpyxl

excel_path = os.path.join(PROJECT_ROOT, "data", "portfolio.xlsx")
wb = openpyxl.load_workbook(excel_path)
ws = wb["Sheet3"] if "Sheet3" in wb.sheetnames else None

schedule_data = []
if ws:
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row and row[0] is not None:
            schedule_data.append({
                "期数": int(row[0]),
                "计划日期": str(row[1]),
                "状态": str(row[4]) if row[4] else "⏳待执行",
                "实际日期": str(row[5]) if row[5] else "",
            })
wb.close()
```

### 5. 生成 Markdown 输出

输出格式如下（替换实际数字）：

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
| 1 | YYYY-MM-DD | ¥N.NNN | N | ¥N.NN | ¥N.NN | ¥N.NN | N | ... |
| 2 | YYYY-MM-DD | ¥N.NNN | N | ¥N.NN | ¥N.NN | ¥N.NN | N | ... |

### 1.3 定投日历执行情况

| 期数 | 计划日期 | 状态 | 实际日期 |
|------|----------|------|----------|
| 1 | YYYY-MM-DD | ✅已完成 | YYYY-MM-DD |
| 2 | YYYY-MM-DD | ⏳待执行 | - |
```

### 6. 写入文件

目标文件：`Day10/report/月度汇报_2026年7-8月.md`

**写入方式**：
1. 读取模板文件，找到 `<!-- 月度汇报 Skill 输出开始（粘贴区） -->` 和 `<!-- 月度汇报 Skill 输出结束 -->` 标记
2. 将生成的 Markdown 内容插入到标记之间
3. 如果标记不存在，则在 `## 一、持仓现状` 标题后插入

---

## 注意事项

1. **路径处理**：所有路径使用 `os.path.join()` 拼接，不硬编码绝对路径
2. **价格获取失败**：如果 `get_price_now()` 返回 None，提示用户检查网络，使用 0 或上次价格
3. **空记录处理**：如果 `records` 为空，输出"暂无持仓记录"
4. **数字格式**：
   - 金额保留 2 位小数
   - 价格保留 3-4 位小数
   - 百分比保留 2 位小数
5. **只填第一节**：不要触碰第二～六节的内容

---

## 触发示例

用户说："写月度汇报" 或 "生成月报"

执行：
1. 读取持仓数据
2. 获取实时价格
3. 计算各项指标
4. 生成 Markdown
5. 写入 Day10/report/月度汇报_2026年7-8月.md
6. 告诉用户"第一节已生成，请继续填写第二～六节"
