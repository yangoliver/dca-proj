# P2 - Day 13 参考指南：双ETF定投系统改造

> **本指南定位**：教练式指南，AI 助手提问、给方向、帮你核对自检，**不替你做判断、不替你 push**。

> **核心目标**：现有工具/skills/Excel/Cron 全部只支持510580，需要扩展为同时支持510580和510300双ETF并行运营。今天完成基础设施改造。

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

# 5. Cron — 现有定时任务
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
| Cron | 现有任务有几条？是否区分ETF？ | ___ | ___ |

> 判断标准：只要文件里有510580这个具体代码，且没有etf_code参数的地方，都需要改。

---

## 二、制定改造计划

> 根据第一章的盘点结果，和 AI 助手一起讨论改造方案。

**几个关键问题需要你判断**：

1. **config.py 的改造方式**：改成 ETF_LIST 列表是最佳方案吗？还是你有其他想法？

2. **calculator.py**：你说它"无ETF引用"，真的不需要改吗？

3. **Cron 的合并**：两套ETF的定时推送是合并成一个Cron还是分开两个？

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
| 510300_买入记录 | 510300 买入记录（空表，等待首笔） |
| 510300_定投日历 | 510300 定投日历（空表，等待设置） |

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

**Step 3**：新建 `510300_买入记录` sheet（空表）

```python
import openpyxl
wb = openpyxl.load_workbook('data/portfolio.xlsx')
ws = wb.create_sheet('510300_买入记录')
headers = ['日期', '标的代码', '标的名称', '买入价格', '买入份额', '实际花费', '手续费', '累计投入', '累计份额', '累计滚存', '备注']
for col, h in enumerate(headers, 1):
    ws.cell(row=1, column=col, value=h)
wb.save('data/portfolio.xlsx')
print('510300_买入记录 新建完成')
```

**Step 4**：新建 `510300_定投日历` sheet（空表）

```python
import openpyxl
wb = openpyxl.load_workbook('data/portfolio.xlsx')
ws = wb.create_sheet('510300_定投日历')
headers = ['期数', '计划日期', '星期', '计划金额', '状态', '实际日期', '实际价格', '实际份额', '备注']
for col, h in enumerate(headers, 1):
    ws.cell(row=1, column=col, value=h)
wb.save('data/portfolio.xlsx')
print('510300_定投日历 新建完成')
```

**验收**：打开 portfolio.xlsx，确认有 4 个 sheet，且 510580 的历史数据完整保留。

---

### 3.2 定时任务：本地 crontab → QClaw 云端 Cron

**前置：创建云端 QClaw**

1. 在手机应用商店下载 **QClaw App**。
2. 在 App 上创建一个**云端 QClaw**（云端 isolated 实例，不依赖本地电脑）。
3. 后续所有提示词都在**这个云端 QClaw 的对话里**录入（本节的提示词都是发给它，不是本地终端）。

**问题**：现有 crontab 跑在本地 Mac 上，Mac 休眠就断了。

**解决方案**：用 QClaw 云端 Cron。每次触发时从 GitHub 拉最新代码，安装 skill 与依赖后再巡检，确保云端始终有最新工具、最新 skill、最新数据。

**第一步：确认仓库已改为公开**

仓库已改为 public（已确认：不登录访问返回 200）。

> ⚠️ 公开后 `data/portfolio.xlsx`（含真实买入记录）会完全暴露。如介意，可只跟踪脱敏数据，或改用带 token 的私有 clone（第四步 JSON 的 clone 地址换成 `https://<token>@github.com/yangoliver/dca-proj.git`）。

**第二步：设计定时任务节奏**

- **止盈 / 巡检**：每个交易日都要覆盖（止盈信号不能漏），cron `0 9 * * 1-5`（周一至周五 9:00，交易日近似为工作日）。
- **双周报**：必须在**定投日当天**生成。做法：巡检任务每天跑，命中「定投日」（读定投日历）才额外出双周报——无需单独的双周 cron，也不会提前/延后。
- **一个任务覆盖双 ETF**：`dca_inspect` 遍历 `config.ETF_LIST`，一次跑完 510580 + 510300，不必拆两个任务。

**第三步：创建云端 Cron（完整提示词）**

把下面这段**完整复制**发给你的云端 QClaw，让它创建**一个**每日定时任务：

```
请帮我创建一个定投巡检的云端定时任务，覆盖 510580 和 510300 双 ETF。每次触发从 GitHub 拉最新代码并安装依赖后巡检。

仓库：https://github.com/yangoliver/dca-proj

任务 - 每日定投巡检（双ETF）：
- 触发时间：每个交易日 9:00（上海时区），cron 表达式 0 9 * * 1-5
- 完整参数如下（直接用 cron 工具创建，不要改字段名）：

技术要求：
0. agentId：用你当前会话的 agentId（取 sessionKey 第二段或 workspace 目录名），不可省略、不可填 "main"
1. sessionTarget: "isolated"（跑在云端，不依赖我的电脑）
2. schedule: {"kind": "cron", "expr": "0 9 * * 1-5", "tz": "Asia/Shanghai"}
3. delivery: {"mode": "announce", "channel": "wechat-access"}
4. payload.kind: "agentTurn"
5. payload.message 里必须包含以下步骤（严格按顺序）：
   第一步：rm -rf /tmp/dca-proj && git clone https://github.com/yangoliver/dca-proj.git /tmp/dca-proj（固定目录，避免每次新建临时目录堆积）
   第二步：cd /tmp/dca-proj
   第三步：安装 dca-tools skill 到 QClaw（将 skills/dca-tools 复制到 QClaw 的 skills 目录，或按 QClaw 的 skill 安装方式注册）
   第四步：分析 skill 依赖——读取 skills/dca-tools/SKILL.md 和仓库根的 requirements.txt，列出所需 Python 包（如 akshare / openpyxl / pandas 等）
   第五步：安装依赖——pip install <第四步列出的包>
   第六步：加载 dca-tools skill，调用 dca_inspect 遍历 config.ETF_LIST，返回五个检查点结论（准备/建仓/持有PE/止盈/纪律）
   第七步：读取 data/portfolio.xlsx 的「定投日历」，判断今天是否为定投日；若是，额外调用月度汇报 skill 生成双周报
   第八步：巡检不下单，只给结论与操作建议（由管理人在中信APP手动执行，不在云端自动下单）
6. message 里写清楚不要回复 HEARTBEAT_OK
```

**第四步：如果 QClaw 听不懂，直接给 JSON 参数**

把下面这段发给你的云端 QClaw：

```
用 cron 工具（action=add）创建一个定时任务，参数如下，直接调用不要改：

{
  "action": "add",
  "job": {
    "name": "每日定投巡检（双ETF）",
    "agentId": "<你的agentId>",
    "schedule": {"kind": "cron", "expr": "0 9 * * 1-5", "tz": "Asia/Shanghai"},
    "sessionTarget": "isolated",
    "payload": {
      "kind": "agentTurn",
      "message": "【定投巡检任务】请严格按顺序执行：\n1. rm -rf /tmp/dca-proj && git clone https://github.com/yangoliver/dca-proj.git /tmp/dca-proj\n2. cd /tmp/dca-proj\n3. 安装 dca-tools skill 到 QClaw（将 skills/dca-tools 复制到 skills 目录或按 QClaw 安装方式注册）\n4. 分析依赖：读 skills/dca-tools/SKILL.md 与 requirements.txt，列出所需 Python 包\n5. pip install <第四步列出的包>\n6. 加载 dca-tools skill，调用 dca_inspect 遍历 config.ETF_LIST，返回五检查点（准备/建仓/持有PE/止盈/纪律）\n7. 读 data/portfolio.xlsx 的「定投日历」判断今天是否为定投日；若是，调用月度汇报 skill 生成双周报\n8. 巡检不下单，只给结论与操作建议（由管理人在中信APP手动执行，不在云端自动下单）\n不要回复 HEARTBEAT_OK。"
    },
    "delivery": {"mode": "announce", "channel": "wechat-access"}
  }
}
```

**验收**：任务创建成功后，问 QClaw「列出我当前的定时任务」，确认：任务存在、sessionTarget 为 isolated、cron 为 `0 9 * * 1-5`、仓库地址在 message 里、agentId 已填。

**第五步：删除本地 crontab（确认云端任务正常后）**

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
- [ ] 用 QClaw 云端 Cron 替换本地 crontab（每日交易日巡检双ETF + 定投日出双周报，每次从GitHub拉代码并装依赖）
- [ ] 验证 510580/510300 流程均正常
- [ ] Day 13 报告填写完整
- [ ] PR 已发起
