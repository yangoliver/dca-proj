# Day 7 参考指南 — 把 tools 变成 QClaw 技能 + 双周定投自动化

> **核心目标**：把你写的 tools/ 目录封装成一个 QClaw Skill，让 AI 能主动调用你的工具来管定投；再创建一个定时任务，让 AI 每双周提醒你执行定投。

---

## 一、今天任务清单

### 必做任务（今天必须完成）

| # | 任务 | 完成标准 |
|---|------|---------|
| 1 | **理解 Skill 是什么** | 能用自己的话解释 QClaw Skill 和普通 Python 脚本有什么区别 |
| 2 | **设计 SKILL.md** | 把 tools/ 里的每个函数封装成一个「工具」，定义名称、参数、返回值 |
| 3 | **写出 SKILL.md** | 在 `skills/dca-tools/` 下写出完整的 SKILL.md |
| 4 | **安装 Skill 并测试** | 让 QClaw 加载技能并测试查持仓、算份额、查估值三个场景 |
| 5 | **创建双周定投 Cron** | 设置一个定时任务，每 14 天推送到你微信 |
| 6 | **手动触发 Cron 验证** | 确认推送能收到，信息准确 |
| 7 | **更新 README** | 在项目 README 里加上 skills/ 目录说明 |
| 8 | **Day 7 报告 + PR** | 报告提交到 GitHub，PR 包含 skills/ 目录 |

### 扩展任务（加分）

| # | 任务 | 完成标准 |
|---|------|---------|
| 9 | **赚回工具成本** | 读 Day 7 报告模板的 4.4 节，算一下你的工具值多少钱 |

---

## 二、第一课：为什么要变成 Skill？

### 2.1 你现在的困境

tools/ 里的 Python 工具已经能干了：

```
查持仓 → python main.py → 选 2
算份额 → python calculator.py
查价格 → python portfolio.py → get_price_now()
查估值 → python portfolio.py → get_pe_data()
```

但每次都要你**打开终端 → 跑脚本 → 看输出**。你的 QClaw 帮不了你，因为它不知道你的 tools/ 里有这些东西。

### 2.2 Skill 的本质

一个 QClaw Skill 就是一本「工具使用说明书」。它告诉 QClaw：

> 「这个目录下有这些 Python 函数。各自的作用是——这个算份额、那个查持仓、那个看估值。当用户问相关问题时，你可以用它们。」

**有了 Skill 之后**：

| 之前（你手动） | 之后（你对 QClaw 说） |
|---------------|---------------------|
| 打开终端 → python main.py → 选 2 | "帮我看看持仓" |
| 打开终端 → python calculator.py 3.95 | "3.95 元能买多少？" |
| 打开终端 → python portfolio.py | "现在 PE 分位多少？" |

**入口从终端变成了对话**。你问一句话，AI 帮你跑代码。

### 2.3 为什么 SKILL.md 不写完整的 Python 代码？

SKILL.md **不是源码复制**，而是「工具接口清单」——定义每个工具叫什么名字、输入什么参数、输出什么结果。

下面的指导不会给你完整的 SKILL.md 内容，只给你格式、思路、验证标准。**你写的东西要能通过验收。**

---

## 三、第二课：设计工具清单

### 3.1 先列出所有能用到的函数

打开你的 tools/ 目录，找出所有**纯函数**（输入 → 计算 → 输出，没有交互菜单）。

问 QClaw：
> "我的 tools/ 目录下有这些 Python 模块：calculator.py、recorder.py、portfolio.py、scheduler.py、profit_taker.py。帮我看看哪些函数是纯函数（不需要交互式输入/菜单），适合封装成 Skill 的工具。"

### 3.2 每个工具要定义什么

对于一个工具，你需要定义清楚：

```
工具名称：____
做什么用：____（一句话）
调哪个函数：____（模块名.函数名）
输入参数：____（参数名 + 类型 + 含义）
输出结果：____（返回什么，怎么解析）
示例：____（给 QClaw 一个调用示例）
```

### 3.3 核心技能：写出第一个工具定义

打开 `skills/dca-tools/SKILL.md`（先创建目录和文件），用 Qoder CN 写出第一个工具：

```
工具名称：dca_calculate
做什么用：用弹性股数法计算给定金额能买多少手 ETF
调哪个函数：calculator.py 的 calculate_shares(amount, price)
输入参数：amount（float，定投金额，如 500）、price（float，当前单价，如 3.924）
输出结果：dict，包含 hands/shares/cost/remainder/unit_price/amount
示例：
    calculate_shares(500, 3.924)
    → {"hands": 1, "shares": 100, "cost": 392.4, "remainder": 107.6, ...}
```

### 3.4 写出剩余的工具定义

依次定义以下工具：

1. **dca_calculate** → 弹性股数法（上面写好了）
2. **dca_portfolio** → 查持仓（analyze()，无参数，返回持仓状态 dict）
3. **dca_price** → 实时价格（get_price_now()，无参数，返回 float 或 None）
4. **dca_pe** → PE 估值（get_pe_data()，无参数，返回估值 dict）
5. **dca_records** → 历史流水（get_all_records()，无参数，返回 list[dict]）
6. **dca_record_purchase** → 记录买入（add_purchase(...)，多个参数，写操作）
7. **dca_profit_check** → 止盈判断（check(price)，返回 dict）
8. **dca_schedule** → 定投日历（generate_schedule(first_date, count)，返回 list[dict]）

### 3.5 验证标准

```
☐ 每个工具都有名称、用途描述、函数路径
☐ 每个工具都标明了输入参数的类型和含义
☐ 每个工具都标注了输出结果的格式
☐ 写操作（dca_record_purchase）特别标注了"需要用户确认"
☐ 路径注意事项有说明（sys.path 需要加 tools/ 和项目根目录）
```

---

## 四、第三课：写出 SKILL.md 的结构

### 4.1 SKILL.md 的整体结构

一个 QClaw Skill 的 SKILL.md 长这样：

```
YAML 头部
├── name（技能名称，如 dca-tools）
├── description（一句话描述+触发词）

正文
├── # DCA定投工具集
│   ├── 项目说明（指向 tools/ 目录）
│   ├── 工具概览（表格：工具名 → 功能 → 对应模块）
│   ├── 各工具详细说明（每个工具写 2-4 段）
│   ├── 自动化流程说明（可选）
│   └── 数据文件说明（portfolio.xlsx, profit_taker_state.json）
```

### 4.2 核心技能：写出头部

先写 YAML 头部。用 Qoder CN 写：

```yaml
---
name: dca-tools
description: |-
  自己写一行描述
  自己写触发词（什么场景下 QClaw 应该调用这个 Skill）
---
```

**不要照抄上面的模板**，自己想：
- 这个 Skill 叫什么名字合适？
- 什么场景下 QClaw 会用到它？（触发词）
- 一句话怎么描述它的作用？

### 4.3 核心技能：写出工具概览表格

写一个 markdown 表格列出所有工具：

| 工具名 | 功能 | 对应模块 |
|--------|------|---------|
| dca_calculate | 弹性股数法计算买入方案 | tools/calculator.py |
| dca_portfolio | 查看当前持仓状态 | tools/portfolio.py |
| ... | ... | ... |

### 4.4 核心技能：写出每个工具的详细说明

每个工具写 2-4 段：
1. **作用**：一句话说清
2. **怎么调用**：给 QClaw 一个 python 调用示例
3. **参数说明**：列出所有参数 + 类型 + 含义
4. **返回值说明**：返回数据结构
5. **注意事项**（如果有）：路径问题、网络问题、写操作需要用户确认

**用 Qoder CN 写**，或者问 QClaw：
> "帮我看看 SKILL.md 里 tools/calculator.py 的 calculate_shares 函数该怎么描述给 AI 用？"

**验证标准**：

```
☐ 每个工具都有作用和参数说明
☐ 每个工具都有调用示例（Python 代码）
☐ 写操作特别标注了"需要用户确认"
☐ 路径问题有说明（sys.path 加 tools/，portfolio.xlsx 在项目根目录）
☐ 整体结构清晰，QClaw 读了就知道怎么用
```

---

## 五、第四课：安装 Skill 并测试

### 5.1 在 QClaw 中激活你的 Skill

SKILL.md 写好之后，问你的 QClaw：

> "我写了一个 QClaw Skill，放在 projects/dca-proj/skills/dca-tools/SKILL.md。帮我加载这个技能。"

如果 QClaw 问你要怎么做，可以按以下方式操作：

- **方式 A（推荐）**：如果 QClaw 支持 `skillhub_install` 或 `skill_workshop`，让它直接帮你注册
- **方式 B**：问 QClaw 怎么在你的环境里注册一个本地 Skill，按它的指引操作

### 5.2 三个必测场景

**测试 1：查持仓**
> "用 dca-tools 帮我看看现在持仓怎么样了"

预期：QClaw 调用 `analyze()` → 显示累计份额、平均成本、浮盈/浮亏。

**测试 2：算份额**
> "假设今天 ¥3.95，500 块能买多少手 510580？"

预期：QClaw 调用 `calculate_shares(500, 3.95)` → 显示手数、花费、滚存。

**测试 3：查 PE**
> "中证500 现在 PE 分位多少？贵不贵？"

预期：QClaw 调用 `get_pe_data()` → 显示 PE、分位、历史高低点。

**如果测试不通怎么办？**

- 先看报错信息
- 问 QClaw："访问 portfolio.xlsx 时报错找不到文件，怎么办？"
- 修改 SKILL.md 里的路径说明
- 再试

### 5.3 验证标准

```
☐ 测试 1：持仓查询正常，数据准确（和 portfolio.xlsx 对比）
☐ 测试 2：份额计算正常，结果正确（和 calculator.py 直接跑的一致）
☐ 测试 3：PE 查询正常，有数据展示
☐ 所有报错都解决了
```

---

## 六、第五课：创建双周定投 Cron

### 6.1 Cron 是什么？

Cron 是一个**定时器**——你告诉它"每 14 天做一件事"，到日子它自动触发。

你用 Cron 实现的是：

```
第 1 次触发（8 月 3 日）：
  ① 查 510580 价格               → get_price_now()
  ② 算 ¥500 能买多少             → calculate_shares(500, 价格)
  ③ 查当前持仓                    → analyze()
  ④ 推微信通知你："今天定投日！..."
  ⑤ 你手动下单后告诉 AI "买好了"
  ⑥ AI 记录买入                   → add_purchase()
  ⑦ 标记日历                      → mark_done()

第 2 次触发（8 月 17 日）：
  同上...
```

**你只管下单，其他全是 AI 的事。**

### 6.2 核心技能：问 QClaw 创建 Cron

问你的 QClaw：

> "我的 dca-proj 项目有双周定投计划，第一期 2026-07-20，每 14 天一次，总共 20 期。请帮我创建一个定时任务：
>
> 1. 任务名：双周定投提醒
> 2. 周期：每 14 天触发一次，从 2026-08-03 起
> 3. 执行内容：触发时调用 dca-tools Skill，查今日价格、算 ¥500 能买多少手、看当前持仓，然后给我推送定投提醒
> 4. 推送方式：通过当前渠道推送到我微信
> 5. 提醒末尾加上：「要求：(1) 不要回复 HEARTBEAT_OK (2) 不要调用 message 工具 (3) 直接输出提醒文字 (4) 控制在 3-5 句话以内」
>
> 创建完后先手动触发一次让我看看效果。"

**关键**：你描述需求，QClaw 帮你创建。不需要手动敲 cron 命令。

### 6.3 验证 Cron

手动触发后，检查收到的推送消息——应该包含：

```
📅 定投提醒
─────────────
510580 当前价格：¥3.95
¥500 建议买 1 手（100份）
实际花费：¥395，滚存：¥105
─────────────
当前持仓：累计投入 ¥392.4，当前市值 ¥395.0，浮盈 +0.66%
请到中信 APP 下单，买完后告诉我"买好了"
```

**验证标准**：
- ✅ 推送收到
- ✅ 包含价格
- ✅ 包含建议手数
- ✅ 包含当前持仓概况
- ✅ 价格和实际数据一致（可以打开新浪查一下对比）

---

## 七、第六课：更新 README

### 7.1 为什么改 README？

README 是项目的「门面」——别人（包括 6 个月后的你）看这个项目时，第一眼看的就是它。

你需要把 `skills/dca-tools/` 加到文件结构里，让将来的人知道：
- 项目里有一个 QClaw 技能
- 它包含了哪些工具
- 它和 tools/ 是什么关系

### 7.2 核心技能：改 README

在 `dca-proj/README.md` 的文件结构部分，加上：

```
├── Day7/
│   ├── 定投实习计划_Day7参考指南.md      # Day 7 作业说明
│   └── report/                           # Day 7 报告
│       └── （报告模板.md + 你的报告）
├── skills/
│   └── dca-tools/
│       └── SKILL.md                      # QClaw 技能定义文件
├── tools/                               # 定投工具（所有天共用）
│   ├── main.py / config.py / calculator.py / recorder.py / portfolio.py / scheduler.py
│   ├── profit_taker.py                  # 止盈工具（Day6新增）
│   ├── requirements.txt
│   └── portfolio.xlsx                   # 持仓记录+定投日历（每次买入后提交GitHub）
```

如果 README 里已经有「项目本质」「AI 工具栈」等部分，考虑在「AI 工具栈」后加一条说明：

```
## 扩展技能

| 技能名 | 作用 |
|--------|------|
| dca-tools（skills/dca-tools/） | 封装 tools/ 的 Python 函数为 QClaw 可调用工具，支持定投全流程 |
```

---

## 八、第七课：Git 协作与 Pull Request

### 8.1 这次 PR 提交什么

```
skills/dca-tools/
└── SKILL.md                    # 你写的技能定义文件

Day7/
├── 定投实习计划_Day7参考指南.md    # Day 7 指南（不用传，由 Oliver 管理）
└── report/
    ├── 报告模板.md
    └── justin-Day7报告.md         # 你的 Day 7 报告

README.md                       # 修改：加上 skills/ 和 Day7/ 的目录说明
```

### 8.2 创建 PR

```bash
# 1. 在 fork 的仓库里创建新分支
git checkout -b day7-skill-cron

# 2. 提交
git add skills/dca-tools/SKILL.md
git add Day7/report/justin-Day7报告.md
git add Day7/report/报告模板.md
git add README.md
git commit -m "feat(Day7): 创建 dca-tools Skill + 设置双周定投 Cron"

# 3. 推到自己仓库
git push origin day7-skill-cron

# 4. 在 GitHub 上创建 PR
#    从 your-name/day7-skill-cron → yangoliver/master
```

### 8.3 PR 描述写什么

```markdown
## Day 7 交付

### 做了什么
- 创建了 skills/dca-tools/SKILL.md，封装了 tools/ 目录的 8 个工具函数
- 安装了 Skill 并通过了三个测试（持仓/份额/估值）
- 创建了双周定投 Cron，手动触发验证通过
- 更新了 README 文件结构

### 验证结果
- 测试 1（查持仓）：✅
- 测试 2（算份额）：✅
- 测试 3（查 PE）：✅
- Cron 手动触发：✅

### 需要讨论
- （如果有疑问，写在这里）
```

---

## 九、给杨知行的提示

### 9.1 遇到困难时问 QClaw

- "QClaw 的 SKILL.md 怎么写？格式是什么？"
- "tools/ 里的函数怎么注册成 Skill 的工具？"
- "cron 怎么设置推送到微信？"
- "我的测试报错了，报错信息是……"

### 9.2 15 分钟原则

卡住超过 15 分钟就问 QClaw。不要憋着。

### 9.3 不要照抄

本指南提供思路、格式、验证标准，**不提供完整 SKILL.md 内容**。你的技能你自己写。

---

## 十、验收清单

```
☐ 能用自己的话解释 Skill 是什么
☐ skills/dca-tools/SKILL.md 已创建，包含所有 8 个工具定义
☐ 每个工具都有名称、作用、函数路径、参数、返回值
☐ Skill 已安装，三个测试全部通过
☐ Cron 已创建，手动触发验证通过
☐ README 已更新，加上 skills/ 目录
☐ Day 7 报告已填写
☐ 提交 PR，包含 skills/dca-tools/、Day7/report/、README 修改
```
