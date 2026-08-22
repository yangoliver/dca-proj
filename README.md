# 定投实习计划（dca-proj）

一个面向大学生的自学项目——通过中证500 ETF 与沪深300 ETF 的真实定投，学习金融投资与 AI Native 工作方式。

> 本项目 P1 阶段（Day 1–10）完成工具链搭建与建仓；P2 阶段（Day 11 起）进入多 ETF 并行运营与系统深化。

## 项目本质

- **投资线**：用真金白银（¥10,000/ETF）在 A 股做定期定额投资（DCA），理解定投纪律
- **技术线**：用 AI 协作体系（QClaw / akshare / WorkBuddy）完成从工具安装到自动化运营的全过程

定投核心原则：**到了时间就买，不判断，不择时。**

## 文件结构

```
dca-proj/
├── README.md                              # 本文件
├── 任务书/
│   ├── 定投实习计划_项目任务书.md      # 主任务书（最新版）
│   └── archive/                           # 旧版本归档
├── 大富翁版/
│   ├── 定投实习计划_大富翁版.md         # 游戏化叙事版（最新版）
│   └── archive/
├── Day1/                                   # P1 建仓期
│   ├── 定投实习计划_Day1参考指南.md     # P1 - Day 1 参考指南
│   └── report/
│       ├── 报告模板.md                   # 复制此模板填写
│       └── <学生>-Day1报告.md # Day 1 报告示例           # Day 1 报告
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
│       └── 报告模板.md
├── skills/                                 # QClaw 技能包
│   └── dca-tools/
│       └── SKILL.md                      # 封装 tools/ 的 QClaw 技能定义
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
└── assets/                                # 图表、素材
```

## 阶段划分

| 阶段 | 范围 | 核心目标 |
|------|------|---------|
| P1 建仓期 | Day 1–10 | 工具链搭建完毕，完成首笔建仓 |
| P2 深化期 | Day 11 起 | 多 ETF 并行运营，系统自动化 |

## AI 工具栈

| 工具 | 角色 |
|------|------|
| QClaw | 运营总监 + 问题导航（主协调） |
| Qoder CN | 代码开发工程师（Vibe Coding） |
| akshare | 数据分析师（行情/净值/费率，用于理解原理与复盘） |
| WorkBuddy | 行政助理（文档/自动化） |

## 扩展技能（Day 7）

| 技能 | 位置 | 作用 |
|------|------|------|
| dca-tools | `skills/dca-tools/SKILL.md` | 封装 tools/ 的 Python 函数为 QClaw 可调用工具，支持定投计算、持仓查询、PE估值、止盈判断、日历管理 |

## License

MIT License — 公开学习项目，欢迎参考使用。
