# Day 10 参考指南 — 月度复盘 · 第二笔定投 · 创建月度汇报 Skill

> **核心目标**：Day 10 三件事——① 认识 AGENTS.md；② 做第二笔定投（8月3日）；③ 创建一个"写月度汇报"的 Skill，然后用它生成正式月报。
>
> **时间节奏建议**：上午 ① ②，下午 ③。
>
> **重要原则**：今天所有动手的事都是你自己的工作。QClaw 是你的助手，不替你做决定。

---

## 一、任务清单

| # | 任务 | 完成标准 |
|---|------|----------|
| 1 | 读懂 AGENTS.md 并用它检查代码目录 | 能说出 AGENTS.md 三件以上规范；tools/ 和 skills/ 均无违规或已修正 |
| 2 | **执行第二笔定投**（8月3日） | 中信证券 APP 买入 510580，下单成功，截图保存 |
| 3 | 用工具记录本次买入 | 用 main.py 菜单1执行，工具自动更新 portfolio.xlsx |
| 4 | 创建月度汇报 Skill | 根据 Skill 设计草稿，引导 QClaw 写出 SKILL.md |
| 5 | 用 Skill 生成正式月报 | 运行 Skill，把输出保存为正式汇报文件 |

---

## 二、认识 AGENTS.md + 代码规范自查

### 2.1 读懂 AGENTS.md

打开项目根目录的 `AGENTS.md` 文件，通读一遍。

这份文件是 Oliver 和 QClaw 总结的**协作规范**——把之前所有天的 Git/GitHub 操作规范、代码规范提炼成一份标准答案。以后遇到规范问题，先查 AGENTS.md。

重点读第六节"代码规范"，这节的规范直接约束你的 `tools/` 和 `skills/` 两个目录：

> **六、代码规范（关键四条）**
> 1. 不用绝对路径
> 2. 用 os.path.join() 拼接路径
> 3. 变量/函数命名用 snake_case
> 4. 数据文件放 data/

读完以后，用自己的话回答：

> **AGENTS.md 代码规范告诉我的三件事：**
>
> 1. ___
> 2. ___
> 3. ___

### 2.2 用 AGENTS.md 检查 tools/ 和 skills/ 目录

把下面这条发给 QClaw：

> ```
> 我的项目在 ~/ws/dca-proj。
> 请帮我检查：
> 1. tools/ 目录里所有 .py 文件，有没有写死的 Windows 盘符或绝对路径
> 2. skills/dca-tools/SKILL.md 有没有写死的盘符或绝对路径
>
> 每找到一个，告诉我：文件路径、行号、具体内容。
> 如果都没找到，告诉我一声。
> ```

**发现问题时在这里修正：**

如果 QClaw 找到了问题，把修正方案填在下面，然后执行：

| 文件 | 行号 | 问题内容 | 修正方案 |
|------|------|---------|---------|
| | | | |

**如果都没有问题，记录：**

> tools/ 和 skills/dca-tools/SKILL.md 均未发现硬编码路径，符合 AGENTS.md 代码规范。

---

## 三、第二笔定投：8月3日

### 3.1 今天该做什么

今天是第二期定投日（8月3日）。第一期滚存了 ¥107.60，本期实际可用 ¥607.60。

**定投是机械规则**：到了时间就买，不判断，不择时。

### 3.2 执行步骤

**Step 1：查当前价格**

```bash
cd ~/ws/dca-proj
python3 tools/main.py
```

选菜单 **1（执行定投）**，工具会自动读入上期滚存、计算弹性股数法、显示买入方案。记录：
- 当前价格：___ 元/份

**Step 2：APP 买入**

1. 打开中信证券 APP → 搜索 **510580**
2. 选择「买」，输入金额 **¥607.60**（或 ¥607 取整也可）
3. 确认价格市价、金额正确 → 确认 → 输入密码
4. **截图**保存到 `Day10/report/assets/dca_2nd_purchase.png`

**Step 3：回工具记录买入**

回到 main.py，如果工具已退出，重新运行选菜单1，按 APP 显示的实际成交价输入：
- 工具会自动更新 portfolio.xlsx 和定投日历

记录本次买入信息：

| 字段 | 值 |
|------|-----|
| 成交日期 | 2026-08-03 |
| 成交价格 | ¥___/份 |
| 买入手数 | ___手（___份） |
| 实际花费 | ¥___ |
| 滚存余额 | ¥___ |
| 累计份额 | ___份 |
| 累计投入 | ¥___ |

---

## 四、创建月度汇报 Skill

### 4.1 这是什么练习

你之前做过一次 Skill（Day7 的 dca-tools）。这次更进一步——**先有一份空白模板，再把它变成 Skill**。

这是一个"元技能"练习：学的是"怎么把任何重复的工作变成 Skill"。

### 4.2 打开 Skill 设计草稿，理解月报需要什么

打开 `Day10/月度汇报模板.md`，这是 Skill 的"设计草稿"——包含月报需要哪些必填信息、数据来源是什么。通读一遍，理解 Skill 最终要生成的报告长什么样。

### 4.3 和 QClaw 一起创建 SKILL.md

把下面这段提示词发给 QClaw：

> ```
> 请帮我基于 Day10/月度汇报模板.md，创建一份月度汇报 Skill。
>
> Skill 保存路径：skills/monthly-report/SKILL.md
> Skill 名称：monthly-report
>
> 需求很简单：
> 这个 Skill 的唯一功能，就是读取 data/portfolio.xlsx 的持仓数据，
> 然后按月度汇报模板的格式，把数字填好、输出成 Markdown。
>
> 数据来源：
> - 持仓数据 → data/portfolio.xlsx Sheet1（累计投入、累计份额、持仓均价、最新价格）
> - 定投日历 → data/portfolio.xlsx Sheet3（各期计划/执行状态）
>
> 模板里的数字节（第一节），由 Skill 读 Excel 填。
> 模板里的反思节（第二～六节），留给用户自己填，Skill 跳过不写。
>
> 请：
> 1. 先读一遍 Day10/月度汇报模板.md（用 read 工具）
> 2. 写 SKILL.md 保存到 skills/monthly-report/SKILL.md
> 3. 告诉我保存成功
> ```

QClaw 写完后，检查 `skills/monthly-report/SKILL.md` 是否存在，内容是否完整。

### 4.4 用 Skill 生成月报数字节

Skill 只负责把第一节"持仓现状"的数字填好。

把这段发给 QClaw：

> ```
> 请用 monthly-report Skill，读取 data/portfolio.xlsx，
> 生成第一节"持仓现状"的完整数字，输出为 Markdown 格式。
>
> 截图路径：Day10/report/assets/dca_2nd_purchase.png
> ```

把 Skill 输出的第一节内容，复制进 `Day10/report/月度汇报_2026年7-8月.md`。

第二～六节（纪律检查、学习反思、能力矩阵、下月计划、给 Oliver 的话）——这些是你自己写的，Skill 帮不了你。

全部填完后检查：数字是否和 portfolio.xlsx 一致，有无漏空。

---

## 五、提交前检查

| 检查项 | 状态 |
|--------|------|
| AGENTS.md 规范自查已完成（第二节，已记录结果） | ☐ |
| 第二笔定投已完成（APP买入 + 截图） | ☐ |
| 截图已保存到 Day10/report/assets/ | ☐ |
| main.py 已执行并更新 portfolio.xlsx | ☐ |
| `skills/monthly-report/SKILL.md` 已创建 | ☐ |
| 月度汇报已生成并检查（数字准确、反思真实） | ☐ |
| `git diff --name-only origin/master` 无多余文件 | ☐ |
| 已 push 并发起 PR（justin-dev → yangoliver/master） | ☐ |
