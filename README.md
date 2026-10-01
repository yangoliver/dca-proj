# 定投实习计划（dca-proj）

一个面向大学生的自学项目——通过中证500 ETF 与沪深300 ETF 的真实定投，学习金融投资与 AI Native 工作方式。

> 本项目 P1 阶段（Day 1–10）完成工具链搭建与建仓；P2 阶段（Day 11 起）进入多 ETF 并行运营与系统深化。

## 项目本质

- **投资线**：用真金白银（¥10,000/ETF）在 A 股做定期定额投资（DCA），理解定投纪律
- **技术线**：用 AI 协作体系（WorkBuddy / akshare）完成从工具安装到自动化运营的全过程

定投核心原则：**到了时间就买，不判断，不择时。**

## 平台说明（QClaw → WorkBuddy）

本项目 Day 1–13 的参考指南写于 2026 年 7–8 月，当时使用的 AI 助手是 **QClaw**（微信机器人形态）。QClaw 已下线，请改用 **WorkBuddy**。

> **注意**：这不只是"换个名字"。凡是涉及**平台机制**的操作，请以下表右列为准——照正文里的 QClaw 原文做会失败。

| 场景 | 正文里的 QClaw 做法 | 请改为（WorkBuddy） |
|---|---|---|
| 日常对话 | 加 QClaw 微信 → 发微信消息 | 打开 WorkBuddy 桌面端，或在微信里打开 **WorkBuddy 小程序**，直接对话 |
| Day 1 前置检查 | "手机可收发微信""QClaw 微信已添加" | 改为"已安装 WorkBuddy 并能正常对话"；**"添加微信好友"这一步作废**——WorkBuddy 不需要加好友（桌面端或小程序直接可用） |
| Day 7 装载技能 | 让 QClaw 用 `skillhub_install` / `skill_workshop` 注册 | 把 `SKILL.md` 放到 `~/.workbuddy/skills/dca-tools/`（用户级）或 `{仓库}/.workbuddy/skills/dca-tools/`（项目级） |
| 技能路径 | `projects/dca-proj/skills/dca-tools/SKILL.md` | 同上。仓库里的 `skills/` 只是**源码存放处，不是加载路径** |
| Day 7 建定时任务 | 让 QClaw 创建 Cron（如 `0 9 * * 1-5`） | WorkBuddy **小程序「云端工作」+ 自动化**：按「每天 / 每周 / 每月」设规则，**不支持 cron 表达式**；也可用自然语言对话创建（"每两周提醒我定投"） |
| Day 13 自动化配置 | `agentId` / `sessionTarget: isolated` / `delivery.channel: wechat-access` 等 JSON 字段 | WorkBuddy 自动化没有这些字段，在界面里按配置项填写即可 |
| 接收提醒 | 推送到**个人微信** | 自动化结果推送到 **WorkBuddy 小程序**（在微信里直接查看），也可推到**企业微信 bot** |
| 在微信里对话 | 加 QClaw 微信好友 → 发消息 | 打开**微信里的 WorkBuddy 小程序**直接下指令；也可在 WorkBuddy 里配置**「微信助理」**并扫码绑定，从微信发指令、结果回推微信（需电脑端 WorkBuddy 保持运行） |
| 转发微信消息给 AI | 转发给 QClaw | **电脑版微信**：多选消息 → 转发 → 转发到其他应用 → 选 WorkBuddy，聊天记录/图片/文档/公众号文章会成为任务材料（仅电脑端微信支持；手机微信不能直接转发） |

**执行方式：WorkBuddy 有两套自动化，别选错**

| | 小程序「云端工作」+ 自动化 | 桌面端「自动化」 |
|---|---|---|
| 在哪执行 | 云端沙箱 | 本地客户端 |
| 电脑必须开机？ | **不需要** | **需要**，且 WorkBuddy 要处于运行状态 |
| 适合什么 | 提醒、汇总、不碰本地文件的任务 | 需要读写本地文件的任务（例如直接改 `data/portfolio.xlsx`） |

> Day 7 的「双周定投提醒」属于前者——**用小程序云端自动化，电脑关机也能收到**。
> 官方文档也写明：小程序端的自动化是「云端工作」下的配置指引，「连接电脑」下的自动化只用于接收电脑端任务结果。

**Skill 兼容性**：仓库里 `skills/dca-tools/SKILL.md` 的 frontmatter（`name` / `description` / 触发词）格式与 WorkBuddy 兼容——**内容不用改，换个位置加载即可**。

**不改动的部分**：`Day1`–`Day10` 的 `justin-DayN报告.md` 是当时的历史作业记录，保留原文与 QClaw 字样，作为项目演进的佐证。

## 文件结构

```
dca-proj/
├── README.md                              # 本文件
├── 任务书/
│   └── 定投实习计划_项目任务书.md      # 主任务书（最新版）
├── Day1/                                   # P1 建仓期
│   ├── 定投实习计划_Day1参考指南.md     # P1 - Day 1 参考指南
│   └── report/
│       ├── 报告模板.md                   # 复制此模板填写
│       └── <学生>-Day1报告.md # Day 1 报告示例
├── Day2/
│   ├── 定投实习计划_Day2参考指南.md     # P1 - Day 2 参考指南
│   └── report/
│       ├── 报告模板.md
│       ├── <学生>-Day2报告.md # Day 2 报告示例
│       └── assets/
│           └── dca_vs_lumpsum.png
├── Day3/
│   ├── 定投实习计划_Day3参考指南.md     # P1 - Day 3 参考指南
│   └── report/
│       ├── 报告模板.md
│       ├── <学生>-Day3报告.md # Day 3 报告示例
│       └── assets/
│           ├── dca_cost_curve.png
│           ├── dca_shares.png
│           ├── position_snapshot.png
│           └── image_1784539969513_ewbjjyd.jpg
├── Day4/
│   ├── 定投实习计划_Day4参考指南.md     # P1 - Day 4 参考指南（PE+弹性股数法+程序）
│   ├── 定投工具设计案.md                # 工具设计规范
│   └── report/
│       ├── 报告模板.md
│       └── <学生>-Day4报告.md # Day 4 报告示例
├── Day5/
│   ├── 定投实习计划_Day5参考指南.md     # P1 - Day 5 参考指南
│   ├── code/
│   │   ├── backtest_3years.py
│   │   ├── plot_returns.py
│   │   └── data/
│   │       └── 000905_history.csv        # 近3年历史数据
│   └── report/
│       ├── 报告模板.md
│       ├── <学生>-Day5报告.md # Day 5 报告示例
│       ├── csi500_数据分析.md
│       └── assets/
├── Day6/
│   ├── 定投实习计划_Day6参考指南.md     # P1 - Day 6 参考指南（止盈机制+止盈工具+PR协作）
│   ├── code/
│   │   └── profit_taker_backtest.py
│   └── report/
│       ├── 报告模板.md
│       └── <学生>-Day6报告.md # Day 6 报告示例
├── Day7/
│   ├── 定投实习计划_Day7参考指南.md     # P1 - Day 7 参考指南（Skill封装+Cron自动化）
│   └── report/
│       ├── 报告模板.md
│       └── <学生>-Day7报告.md # Day 7 报告示例
├── Day8/                                   # 实践→理论·复盘出方案
│   ├── 定投实习计划_Day8参考指南.md     # P1 - Day 8 参考指南
│   ├── Day8核对材料.md
│   └── report/
│       ├── 报告模板.md
│       └── <学生>-Day8报告.md # Day 8 报告示例
├── Day9/                                   # 落地 Day8 方案
│   ├── 定投实习计划_Day9参考指南.md     # P1 - Day 9 参考指南
│   ├── Day9核对材料.md
│   └── report/
│       ├── 报告模板.md
│       └── <学生>-Day9报告.md # Day 9 报告示例
├── Day10/                                  # P1 建仓期终点
│   ├── 定投实习计划_Day10参考指南.md    # P1 - Day 10 参考指南（月度复盘+月度汇报Skill）
│   ├── 月度汇报模板.md
│   └── report/
│       ├── 报告模板.md
│       ├── <学生>-Day10报告.md # Day 10 报告示例
│       ├── 月度汇报_2026年7-8月.md
│       └── assets/
├── Day11/                                  # P2 深化期
│   ├── 定投实习计划_Day11参考指南.md    # P2 - Day 11 参考指南（规则漏洞修复）
│   └── report/
│       ├── 报告模板.md
│       └── <学生>-Day11报告.md # Day 11 报告示例
├── Day12/                                  # P2 - 双ETF并行
│   ├── 定投实习计划_Day12参考指南.md    # P2 - Day 12 参考指南（510580第3期+510300微笑曲线）
│   └── report/
│       ├── 报告模板.md
│       └── <学生>-Day12报告.md # Day 12 报告示例
├── Day13/                                  # P2 - 系统改造（进行中）
│   ├── 定投实习计划_Day13参考指南.md    # P2 - Day 13 参考指南（双ETF工具链改造）
│   └── report/
│       ├── 报告模板.md
│       └── <学生>-Day13报告.md # Day 13 报告示例
├── skills/                                 # 技能源码存放处（非加载路径，见「平台说明」）
│   ├── dca-tools/
│   │   └── SKILL.md                      # 封装 tools/ 的技能定义
│   └── monthly-report/
│       └── SKILL.md                      # 月度汇报技能（Day 10）
├── data/
│   └── portfolio.xlsx                     # 权威持仓记录+定投日历（每次买入后提交GitHub）
├── tools/                                 # 定投工具（所有天共用）
│   ├── main.py / config.py / calculator.py / recorder.py / portfolio.py / scheduler.py
│   ├── profit_taker.py                   # 止盈工具
│   ├── analyzer.py / dashboard.py / inspector.py / fee_compare.py
│   └── smile_curve_analyzer.py           # 微笑曲线分析工具
├── reading/                               # 极简财商系列阅读材料
│   ├── Index.md                          # 系列目录页
│   ├── 第零课 ~ 第三课（5 篇 Markdown）
│   └── assets/                           # 文章配图
```

## 阶段划分

| 阶段 | 范围 | 核心目标 |
|------|------|---------|
| P1 建仓期 | Day 1–10 | 工具链搭建完毕，完成首笔建仓 |
| P2 深化期 | Day 11 起 | 多 ETF 并行运营，系统自动化 |

## AI 工具栈

| 工具 | 角色 |
|------|------|
| WorkBuddy | 运营总监 + 问题导航 + 代码开发（主协调） |
| akshare | 数据分析师（行情/净值/费率，用于理解原理与复盘） |

## 扩展技能（Day 7）

| 技能 | 位置 | 作用 |
|------|------|------|
| dca-tools | `skills/dca-tools/SKILL.md`（源码；加载路径见「平台说明」） | 封装 tools/ 的 Python 函数为 WorkBuddy 可调用工具，支持定投计算、持仓查询、PE估值、止盈判断、日历管理 |

## License

MIT License — 公开学习项目，欢迎参考使用。
