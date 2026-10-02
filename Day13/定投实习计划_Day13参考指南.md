# P2 - Day 13 参考指南：双ETF定投系统改造

> **本指南定位**：教练式指南，AI 助手提问、给方向、帮你核对自检，**不替你做判断、不替你 push**。

> **核心目标**：现有工具/skills/Excel/定时任务 全部只支持510580，需要扩展为同时支持510580和510300双ETF并行运营。今天完成基础设施改造。

---

## 一、盘点现状：找出硬编码点

> 开始之前，先把所有写死510580的地方全部找出来。

**Step 1：运行检查命令**

```bash
# 1. config.py — 全局配置
grep -n "ETF_CODE\|ETF_NAME" tools/config.py

# 2. Excel — 看所有 sheet 名称和表头
python3 -c "
import openpyxl
wb = openpyxl.load_workbook('data/portfolio.xlsx')
for s in wb.sheetnames:
    ws = wb[s]
    print(s, [c.value for c in ws[1]])
"

# 3. tools — 哪些文件引用了 ETF_CODE / ETF_NAME
grep -l "from config import.*ETF" tools/*.py

# 4. SKILL — 触发词和工具描述
grep -n "510580\|中证500" skills/dca-tools/SKILL.md

# 5. 定时任务 — 现有定时任务
crontab -l
```

**Step 2：对照实际输出，填入下表**

根据上面的输出，填入下表，并判断每个文件是否需要修改：

| 文件 | 找到的硬编码 | 是否需要修改？| 你的修改方案 |
|------|------------|-------------|-------------|
| tools/config.py | ETF_CODE="510580", ETF_NAME="易方达中证500ETF" | ___ | ___ |
| tools/calculator.py | 无ETF引用 | ___ | ___ |
| tools/portfolio.py | ETF_CODE/ETF_NAME导入，打印语句写死"510580" | ___ | ___ |
| tools/recorder.py | ETF_CODE/ETF_NAME写入Excel | ___ | ___ |
| tools/profit_taker.py | ETF_CODE/ETF_NAME导入，打印语句 | ___ | ___ |
| tools/scheduler.py | DCA_AMOUNT/INTERVAL导入 | ___ | ___ |
| tools/inspector.py | 未显示ETF引用（手动确认） | ___ | ___ |
| tools/main.py | ETF_CODE/ETF_NAME导入，打印语句 | ___ | ___ |
| tools/analyzer.py | 图表标题写死"510580 定投实盘" | ___ | ___ |
| tools/dashboard.py | 图表标题写死"510580 定投实盘" | ___ | ___ |
| tools/fee_compare.py | ETFS列表含510580 | ___ | ___ |
| tools/smile_curve_analyzer.py | 文件不存在 | ___ | ___ |
| data/portfolio.xlsx | 现状：Sheet1有标的列含2笔510580真实记录；Sheet3无标的列含510580日历21行 | ___ | ___ |
| skills/dca-tools/SKILL.md | 触发词写死510580 | ___ | ___ |
| 定时任务 | 现有任务有几条？是否区分ETF？ | ___ | ___ |

> 判断标准：只要文件里有510580这个具体代码，且没有etf_code参数的地方，都需要改。

---

## 二、制定改造计划

> 根据第一章的盘点结果，和 AI 助手一起讨论改造方案。

**几个关键问题需要你判断**：

1. **config.py 的改造方式**：改成 ETF_LIST 列表是最佳方案吗？还是你有其他想法？

2. **calculator.py**：你说它"无ETF引用"，真的不需要改吗？

3. **定时任务 的合并**：两套ETF的定时推送是合并成一个定时任务还是分开两个？

4. **改造顺序**：先改 config.py（基础），还是先改各个工具（需要等 config 改完才能跑）？还是交叉进行？

5. **Excel 的处理**：Oliver 已给出方案（见第三章四），你判断这个方案是否合理？

把讨论结论记在下面，然后按顺序执行：

```
Excel改造方案判断：同意 / 不同意（你的调整：___）

改造顺序（你的决定）：
___

其他备注：
___
```

---

## 三、执行改造

按第二章确定的顺序执行。每一项改造后，运行一次确认510580历史流程未损坏，再继续下一项。

### 3.1 Excel 改造方案（Oliver 已确定）

**目标**：510580 和 510300 的买入记录与定投日历各独立 sheet。

**改造前现状**：
- Sheet1：有标的列，含 2 笔 510580 真实买入记录（2026-07-20、2026-08-03）
- Sheet3：无标的列，含 510580 定投日历（21行）

**改造后目标结构**：

| Sheet 名称 | 用途 |
|-----------|------|
| 510580_买入记录 | 510580 所有买入记录（保留现有 2 笔真实数据） |
| 510580_定投日历 | 510580 定投日历（保留现有日历数据） |
| 510300_买入记录 | 510300 现有持仓（建仓基线：12000 股 @ 4.8395，2026-08-24 录入，不参与微笑曲线） |
| 510300_定投日历 | 510300 双周 ¥500 定投计划（首期 2026-08-31，与 510580 同节奏，共 21 期） |

**迁移步骤**（按顺序执行）：

**Step 1**：重命名 Sheet1 → `510580_买入记录`

```python
import openpyxl
wb = openpyxl.load_workbook('data/portfolio.xlsx')
ws1 = wb['Sheet1']
ws1.title = '510580_买入记录'
wb.save('data/portfolio.xlsx')
print('Sheet1 → 510580_买入记录 完成')
```

**Step 2**：重命名 Sheet3 → `510580_定投日历`

```python
import openpyxl
wb = openpyxl.load_workbook('data/portfolio.xlsx')
ws3 = wb['Sheet3']
ws3.title = '510580_定投日历'
wb.save('data/portfolio.xlsx')
print('Sheet3 → 510580_定投日历 完成')
```

**Step 3**：`510300_买入记录` 写入建仓基线（sheet 已建，这里填现有持仓）

> ⚠️ 510300 **不是从零开始**——出资人账户已有 12000 股、成本价 4.8395 的原有持仓，必须作为建仓基线写入，不能留空。

```python
import openpyxl
wb = openpyxl.load_workbook('data/portfolio.xlsx')
ws = wb['510300_买入记录']
ws.append(['2026-08-24', '510300', '沪深300ETF华泰柏瑞', 4.8395, 12000,
           58074.0, 0, 58074.0, 12000, 0,
           '原有持仓·一次性投入建仓，不参与微笑曲线计算'])
wb.save('data/portfolio.xlsx')
print('510300_买入记录 建仓基线写入完成')
```

**Step 4**：`510300_定投日历` 写入双周定投计划（sheet 已建，这里填计划）

> 首期 2026-08-31（与 510580 同节奏，双周周一），每期 ¥500，共 21 期。云端巡检靠读此表判断定投日、出双周报。

```python
import openpyxl
from datetime import date, timedelta
wb = openpyxl.load_workbook('data/portfolio.xlsx')
ws = wb['510300_定投日历']
wk = ['周一','周二','周三','周四','周五','周六','周日']
start = date(2026, 8, 31)
for i in range(21):
    d = start + timedelta(days=14*i)
    ws.append([i+1, d.strftime('%Y-%m-%d'), wk[d.weekday()], 500,
               '待执行', None, None, None, None])
wb.save('data/portfolio.xlsx')
print('510300_定投日历 计划写入完成')
```

**验收**：打开 portfolio.xlsx，确认有 4 个 sheet；510580 历史数据完整保留，`510300_买入记录` 含建仓基线（12000 股 @ 4.8395）、`510300_定投日历` 含 21 期双周计划。

---

### 3.2 定时任务：本地 crontab → WorkBuddy 云端定时任务

**问题**：现有 crontab 跑在本地 Mac 上，Mac 休眠就断了。

**解决方案**：用 WorkBuddy 的**云端定时任务**（小程序「云端工作」里的自动化）——跑在云端，不依赖你的电脑。每次触发时从 GitHub 拉最新代码、安装 skill 与依赖后再巡检，确保云端始终有最新工具、最新 skill、最新数据。

**前置**

- 微信里能打开 **WorkBuddy 小程序**并正常对话（云端任务在小程序「云端工作」中创建和管理）。
- 本地 crontab 先别删，等云端任务验证通过后再清理（第四步）。

**第一步：确认仓库已改为公开**

仓库已改为 public（已确认：不登录访问返回 200）。

> ⚠️ 公开后 `data/portfolio.xlsx`（含真实买入记录）会完全暴露。如介意，可只跟踪脱敏数据，或改用带 token 的私有 clone（提示词里的 clone 地址换成 `https://<token>@github.com/yangoliver/dca-proj.git`）。

**第二步：设计定时任务节奏**

- **止盈 / 巡检**：每个交易日都要覆盖（止盈信号不能漏）——定时规则设为**每周一至周五 9:00**（交易日近似为工作日；WorkBuddy 按「每天 / 每周 / 每月」设规则，不支持 cron 表达式，在创建界面按周勾选即可）。
- **双周报**：必须在**定投日当天**生成。做法：巡检任务每个工作日跑，命中「定投日」（读定投日历）才额外出双周报——无需单独的双周任务，也不会提前/延后。
- **一个任务覆盖双 ETF**：`dca_inspect` 遍历 `config.ETF_LIST`，一次跑完 510580 + 510300，不必拆两个任务。

**第三步：创建云端定时任务（完整提示词）**

打开 WorkBuddy 小程序的「云端工作」，把下面这段**完整复制**发给它，让它创建**一个**定时任务：

```
请帮我创建一个云端定时任务「每日定投巡检（双ETF）」，每周一至周五 9:00（Asia/Shanghai）触发。每次触发严格按顺序执行：

1. rm -rf /tmp/dca-proj && git clone https://github.com/yangoliver/dca-proj.git /tmp/dca-proj（固定目录，避免每次新建临时目录堆积）
2. cd /tmp/dca-proj
3. 安装 dca-tools skill（将 skills/dca-tools 复制到技能目录）
4. 分析依赖——读取 skills/dca-tools/SKILL.md 和仓库根的 requirements.txt，列出所需 Python 包（如 akshare / openpyxl / pandas 等）
5. 安装依赖——pip install <第4步列出的包>
6. 加载 dca-tools skill，调用 dca_inspect 遍历 config.ETF_LIST，返回五个检查点结论（准备/建仓/持有PE/止盈/纪律）
7. 读取 data/portfolio.xlsx 的「定投日历」，判断今天是否为定投日；若是，额外调用月度汇报 skill 生成双周报
8. 巡检不下单，只给结论与操作建议（由管理人在中信APP手动执行，不在云端自动下单）

巡检结论推送到我的微信。
```

**验收**：任务创建成功后，问 WorkBuddy「列出我当前的定时任务」，确认：任务存在、触发节奏为每周一至周五 9:00、提示词里包含仓库地址、推送渠道为微信。再手动触发一次，确认能收到巡检结论推送。

**如果云端跑不起来（兜底方案）**

云端环境能否 git clone + pip install 以实际表现为准。如果实测不通，按顺序退到：

1. **桌面端定时任务**：在桌面端 WorkBuddy 创建同样的自动化（本地执行，能直接用你已配好的 Python 环境）——代价是电脑需保持运行、不能休眠。
2. **保留本地 crontab 过渡**：维持现状，同时关闭 Mac 自动休眠作为临时措施，待云端能力确认后再切换。

**第四步：删除本地 crontab（确认云端任务正常后）**

```bash
crontab -r
```

---

## 四、收尾：写报告 + PR

把 `Day13/report/报告模板.md` → `<你的署名>-Day13报告.md`，按实际情况填写。

按 AGENTS.md 走 PR：Fork → 分支 → commit → push → PR。

---

## 今日任务清单

- [ ] 运行第一章检查命令，填完硬编码盘点表
- [ ] 和 AI 助手讨论改造方案，确定顺序
- [ ] Excel 改造：迁移510580已有数据，新建各ETF独立sheet
- [ ] 按改造计划逐项执行，每项验证后再继续
- [ ] 确认仓库已改为公开（不登录能访问即为公开）
- [ ] 用 WorkBuddy 云端定时任务替换本地 crontab（每日交易日巡检双ETF + 定投日出双周报，每次从GitHub拉代码并装依赖）
- [ ] 验证 510580/510300 流程均正常
- [ ] Day 13 报告填写完整
- [ ] PR 已发起
