# 定投实习计划（dca-proj）

Oliver 带高中毕业生杨知行做的 约 9 个月（20 次双周）实习项目——通过中证500 ETF 定投学习金融投资与 AI Native 工作方式。

> 注：本项目于 2026-07-18 统一命名为『定投实习计划』，聚焦中证500 ETF 被动定投实践。

## 项目本质

- **投资线**：用真金白银（¥10,000）在 A 股做定期定额投资（DCA），理解定投纪律
- **公司线**：用 QClaw 主导的 AI 协作体系（Qoder CN / akshare / WorkBuddy）完成从工具安装到自动化运营的全过程

定投核心原则：**到了时间就买，不判断，不择时。**

## 文件结构

```
dca-proj/
├── README.md                           # 本文件
├── 任务书/
│   ├── 定投实习计划_项目任务书.md    # 主任务书（最新版）
│   └── archive/                         # 旧版本归档
├── 大富翁版/
│   ├── 定投实习计划_大富翁版.md      # 游戏化叙事版（最新版）
│   └── archive/
├── Day1/
│   ├── 定投实习计划_Day1参考指南.md      # Day 1 作业说明（Markdown）
│   └── report/                                # 作业报告目录（杨知行 PR 提交处）
│       ├── 报告模板.md                        # 报告模板
│       └── justin-Day1报告.md                 # 杨知行的 Day 1 报告
├── Day2/
│   ├── 定投实习计划_Day2参考指南.md      # Day 2 作业说明
│   └── report/                           # Day 2 报告
│       └── 报告模板.md                   # 复制此模板填写
├── Day3/
│   ├── 定投实习计划_Day3参考指南.md      # Day 3 作业说明（买入日+止盈框架）
│   └── report/                           # Day 3 报告
│       └── 报告模板.md                   # 复制此模板填写
├── Day4/
│   ├── 定投实习计划_Day4参考指南.md      # Day 4 作业说明（PE+弹性股数法+程序）
│   └── report/                           # Day 4 报告
│       └── 报告模板.md                   # 复制此模板填写
├── Day5/
│   ├── 定投实习计划_Day5参考指南.md      # Day 5 作业说明（近3年回测+Git规范）
│   ├── code/                             # 回测脚本
│   │   ├── backtest_3years.py
│   │   └── data/
│   │       └── 000905_history.csv
│   └── report/                           # Day 5 报告
│       └── 报告模板.md                   # 复制此模板填写
├── Day6/
│   ├── 定投实习计划_Day6参考指南.md      # Day 6 作业说明（止盈机制+止盈工具+PR协作）
│   ├── code/                             # 止盈回测脚本
│   └── report/                           # Day 6 报告
│       └── 报告模板.md                   # 复制此模板填写
├── tools/                               # 定投工具v1.0（Day4作业）
│   ├── main.py / config.py / calculator.py / recorder.py / portfolio.py / scheduler.py
│   ├── requirements.txt
│   └── portfolio.xlsx                   # 持仓记录+定投日历（每次买入后提交GitHub）
└── assets/                              # 图表、素材
```

## 版本说明

主文件始终保持最新版本，不再使用 v7.x / v2.x 编号——版本历史由 Git 提交记录管理。

旧版本不再保留（已确认无需追溯），如需查看历史请使用 `git log`。

## 核心修订记录

2026-07-18：去除"估值分位点作为投资决策信号"的逻辑，将 akshare 定位从"数据信号源"改为"事前分析 + 事后复盘工具"，明确定投纪律优先。

## AI 工具栈

| 工具 | 角色 |
|------|------|
| QClaw | 运营总监 + 问题导航（主协调） |
| Qoder CN | 代码开发工程师（Vibe Coding） |
| akshare | 数据分析师（行情/净值/费率，用于理解原理与复盘） |
| WorkBuddy | 行政助理（文档/自动化） |

## License

Private — 仅限项目参与者使用。
