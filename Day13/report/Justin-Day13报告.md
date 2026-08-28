# Day 13 报告

> **学生**：Justin ｜ **出资人**：Oliver ｜ **日期**：2026-08-22 ｜ 协作助手：QoderWork

---

## 一、盘点现状

> 本章对应指南第一章：运行检查命令，把实际输出填入下表，并做出判断。

### 1.1 执行记录

执行指南中的检查命令，把实际输出抄在下面：

```bash
# 1. config.py 硬编码
$ grep -n "ETF_CODE\|ETF_NAME" tools/config.py
# 输出：
# 32:DEFAULT_ETF = "510580"
# 33:ETF_CODE = DEFAULT_ETF
# 34:ETF_NAME = ETF_LIST[DEFAULT_ETF]["name"]
# 改造前：ETF_CODE = "510580" / ETF_NAME = "易方达中证500ETF" 硬编码

# 2. Excel sheet
$ python -c "import openpyxl; wb=openpyxl.load_workbook('data/portfolio.xlsx'); print(wb.sheetnames)"
# 改造前输出：['Sheet1', 'Sheet3']
# 改造后输出：['510580_买入记录', '510580_定投日历', '510300_买入记录', '510300_定投日历']

# 3. 引用 ETF 的工具
$ grep -l "from config import.*ETF" tools/*.py
# 输出：tools/dashboard.py, tools/inspector.py, tools/main.py,
#       tools/portfolio.py, tools/profit_taker.py, tools/recorder.py, tools/scheduler.py

# 4. SKILL 触发词
$ grep -n "510580\|中证500" skills/dca-tools/SKILL.md
# 输出：多处引用 510580 和中证500（已在改造后更新为双ETF描述）

# 5. 现有定时任务（Windows 使用 QoderWork Cron，非 crontab）
$ QoderWork cron list
# 输出：3个定投相关任务：每日定投巡检(09:00)、510580止盈检查(09:05工作日)、双周定投提醒(14天间隔)
```

### 1.2 盘点结论

根据实际输出，填入下表，并判断是否需要修改：

| 文件 | 找到的硬编码 | 需要修改？| 修改方案 |
|------|------------|---------|---------|
| tools/config.py | ETF_CODE/ETF_NAME 硬编码为 510580 | 是 | 新增 ETF_LIST 字典 + get_etf_config() + sheet_name() |
| tools/calculator.py | 无 ETF 特定代码（纯数学） | 否 | 不改 |
| tools/portfolio.py | get_price_now 硬编码 sh510580；get_pe_data 硬编码中证500 | 是 | 加 etf_code 参数，INDEX_CODE_MAP 路由 |
| tools/recorder.py | 硬编码 Sheet1 / Sheet3 | 是 | 用 config.sheet_name() 动态生成 |
| tools/profit_taker.py | 单文件 profit_taker_state.json | 是 | 按 ETF 分文件 + 自动迁移 |
| tools/scheduler.py | 硬编码 Sheet3 | 是 | 用 config.sheet_name() 动态生成 |
| tools/inspector.py | 硬编码 Sheet3；无 ETF 参数 | 是 | 加 etf_code 参数，动态 sheet |
| tools/main.py | 无 ETF 切换能力 | 是 | 加 current_etf 全局 + 选项7切换 |
| tools/analyzer.py | plot_cost_curve 标题硬编码 | 是 | 加 etf_code 参数，动态标题 |
| tools/dashboard.py | 标题硬编码 510580 | 是 | 加 etf_code 参数，动态标题 |
| tools/fee_compare.py | 无 ETF 特定代码 | 否 | 不改 |
| tools/smile_curve_analyzer.py | 无 ETF 特定代码 | 否 | 不改 |
| data/portfolio.xlsx | Sheet1/Sheet3 命名 | 是 | 重命名+新建 510300 sheets |
| skills/dca-tools/SKILL.md | 函数签名无 etf_code 参数 | 是 | 更新所有函数签名和说明 |
| Cron（QoderWork） | 3个任务只覆盖 510580 | 是 | 合并为双ETF统一巡检 |

---

## 二、制定改造计划

> 本章对应指南第二章：和 AI 助手讨论，根据盘点结论做出决策。

### 2.1 讨论记录

**与 AI 助手的讨论摘要**（把关键结论记下来）：

```
1. config.py 改造方式：同意 ETF_LIST 字典方案，保留 ETF_CODE/ETF_NAME 向后兼容
2. 参数传递策略：所有数据函数加 etf_code 参数（默认 "510580"），不传则操作默认 ETF
3. Excel sheet 命名：统一用 config.sheet_name(etf_code, "buy"|"schedule")
4. 止盈状态隔离：每 ETF 独立 JSON 文件 profit_taker_state_{code}.json，旧文件自动迁移
5. PE 路由：ETF→指数映射放 config（中证500→000905，沪深300→000300），portfolio.py 据此调 akshare
6. Cron 策略：合并每日巡检+止盈检查为 1 个双ETF任务（工作日9:00），双周提醒单独更新
7. 改造顺序：config→recorder→scheduler→portfolio→profit_taker→inspector→main/analyzer/dashboard
```

### 2.2 决策记录

把讨论结论记录下来：

| 问题 | 你的决策 |
|------|---------|
| 1. config.py 改造方式 | ETF_LIST 字典 + get_etf_config() + sheet_name()，保留旧变量向后兼容 |
| 2. calculator.py 是否需要改 | 不改，纯数学函数无 ETF 特定逻辑 |
| 3. Cron 合并还是分开两个 | 合并：每日巡检+止盈检查→1个双ETF任务（工作日9:00），双周提醒单独更新 |
| 4. 改造顺序 | config→recorder→scheduler→portfolio→profit_taker→inspector→main/analyzer/dashboard→验证→cron→SKILL |
| 5. Excel 改造方案（Oliver 方案） | 同意（重命名 Sheet1/Sheet3 + 新建 510300 sheets） |

---

## 三、执行改造

> 本章对应指南第三章：按第二章确定的顺序执行，每项完成后打勾。

### 3.1 Excel 改造（Oliver 已确定方案）

| 步骤 | 执行内容 | 执行结果 |
|------|---------|---------|
| Step 1 | 重命名 Sheet1 → `510580_买入记录` | ✅ 完成 |
| Step 2 | 重命名 Sheet3 → `510580_定投日历` | ✅ 完成 |
| Step 3 | 新建 `510300_买入记录` 并写入建仓基线（12000股@4.8395） | ✅ 完成 |
| Step 4 | 新建 `510300_定投日历` 并填入 21 期计划（首期 2026-08-31） | ✅ 完成 |

**验收**：打开 portfolio.xlsx，确认有 4 个 sheet，数据完整：

- `510580_买入记录`：3笔真实记录（2026-07-20、2026-08-03、2026-08-17）✓
- `510580_定投日历`：20行日历数据（3期已完成）✓
- `510300_买入记录`：1条建仓基线（12000股 @ 4.8395，原有持仓）✓
- `510300_定投日历`：21期双周 ¥500 计划（首期 2026-08-31）✓

验收结论：**通过**，4个sheet结构正确，510580历史数据完整，510300有建仓基线和定投计划。

### 3.2 其他改造

按第二章确定的顺序，逐项执行并记录：

| 步骤 | 执行内容 | 执行结果 |
|------|---------|---------|
| 1 | config.py — 新增 ETF_LIST / DEFAULT_ETF / get_etf_config() / sheet_name() | ✅ |
| 2 | recorder.py — _load_workbook/get_all_records/add_purchase 全部加 etf_code 参数，用 sheet_name() | ✅ |
| 3 | scheduler.py — 所有函数加 etf_code 参数，_get_or_create_schedule_sheet 用动态名 | ✅ |
| 4 | portfolio.py — analyze/get_price_now/get_pe_data 加 etf_code，INDEX_CODE_MAP 路由 PE | ✅ |
| 5 | profit_taker.py — 每ETF独立状态文件，_migrate_if_needed 自动迁移旧文件 | ✅ |
| 6 | inspector.py — inspect_once 加 etf_code，_check_skip/_check_next_dca 用动态 sheet | ✅ |
| 7 | main.py — current_etf 全局变量 + 选项7切换 + 所有选项传 etf_code | ✅ |
| 8 | analyzer.py — plot_cost_curve 加 etf_code，CLI 加 --etf | ✅ |
| 9 | dashboard.py — generate_dashboard 加 etf_code，动态标题/文件名 | ✅ |
| 10 | SKILL.md — 更新所有函数签名，新增双ETF架构要点说明 | ✅ |
| 11 | monthly-report/SKILL.md — Sheet1/Sheet3→动态名，绝对路径→占位符 | ✅ |

### 3.3 定时任务改造

#### 3.3.1 仓库状态确认

访问 https://github.com/yangoliver/dca-proj，不登录能看到代码：**是**（公开仓库）

#### 3.3.2 Cron 改造记录（QoderWork Cron，非系统 crontab）

| 旧任务 | 操作 |
|--------|------|
| 每日定投巡检（09:00，仅510580） | ❌ 已删除 |
| 510580 止盈检查（09:05工作日，仅510580） | ❌ 已删除 |
| 双周定投提醒（14天间隔，仅510580） | ✅ 已更新为双ETF |

| 新任务 | 创建结果 | schedule |
|--------|---------|---------|
| 双ETF每日巡检（巡检+止盈，覆盖510580+510300） | ✅ 已创建 | 工作日 09:00 (Asia/Shanghai) |
| 双ETF双周定投提醒（更新原任务） | ✅ 已更新 | 每14天 |

**验收**：定时任务列表确认两个双ETF任务存在，巡检任务内含 config.ETF_LIST 遍历逻辑。

验收结论：**通过**

#### 3.3.3 本地 crontab

- 本地环境为 Windows，不使用系统 crontab，定时任务全部由 QoderWork Cron 管理
- 无需执行 `crontab -r`

---

## 四、验证结果

> 执行完每一项改造后立即验证，510580 历史流程未损坏再继续。

| 验证项 | 结果 | 如失败，原因分析 |
|--------|------|----------------|
| Excel 4 sheet 结构正确 | ✅ | — |
| config.ETF_LIST / get_etf_config / sheet_name 函数正确 | ✅ | — |
| recorder 读取 510580 记录（3条） | ✅ | — |
| recorder 读取 510300 记录（0条） | ✅ | — |
| portfolio.analyze(510580) 返回正确持仓（300份，¥1220，均价4.0667） | ✅ | — |
| profit_taker.check() 状态正常（未止盈） | ✅ | — |
| inspector.inspect_once(510580) 全流程通过（价格+PE+止盈+纪律） | ✅ | — |
| inspector.inspect_once(etf_code="510300") 全流程通过 | ✅ | 价格4.648，PE路由沪深300(000300)，分位89.7% |
| 510580 历史数据未被破坏 | ✅ | 3条记录完整，浮盈+1.19% |
| Cron 任务列表正确（2个双ETF任务） | ✅ | — |
| SKILL.md 已更新并同步 | ✅ | — |

---

## 五、提交前检查

- [x] 第一章盘点完成，所有文件检查命令已执行并记录
- [x] 第二章改造方案经讨论确认，5项决策已记录
- [x] 第三章 Excel 改造验收通过（4个sheet结构正确）
- [x] 第三章其他改造按计划执行完毕（10项全部完成）
- [x] 第三章定时任务验收通过（2个双ETF Cron 任务存在）
- [x] 第四章验证通过，510580 流程正常，510300 工具可调用
- [x] Day 13 报告填写完整，无空白必填项
- [x] PR 已发起（PR #26: https://github.com/yangoliver/dca-proj/pull/26）
