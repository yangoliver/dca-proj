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
│   ├── 定投实习计划_Day1参考指南.md      # Day 1 作业说明
│   └── report/                           # Day 1 报告
│       ├── 报告模板.md                   # 复制此模板填写
│       └── justin-Day1报告.md            # 杨知行的 Day 1 报告
├── Day2/
│   ├── 定投实习计划_Day2参考指南.md      # Day 2 作业说明
│   └── report/                           # Day 2 报告
│       ├── 报告模板.md                   # 复制此模板填写
│       ├── justin-Day2报告.md            # 杨知行的 Day 2 报告
│       └── assets/
│           └── dca_vs_lumpsum.png        # 对比图
├── Day3/
│   ├── 定投实习计划_Day3参考指南.md      # Day 3 作业说明
│   └── report/                           # Day 3 报告
│       ├── 报告模板.md                   # 复制此模板填写
│       ├── justin-Day3报告.md            # 杨知行的 Day 3 报告
│       └── assets/
│           ├── dca_cost_curve.png
│           ├── dca_shares.png
│           ├── position_snapshot.png
│           └── image_1784539969513_ewbjjyd.jpg
├── Day4/
│   ├── 定投实习计划_Day4参考指南.md      # Day 4 作业说明（PE+弹性股数法+程序）
│   ├── 定投工具设计案.md                 # 工具设计规范（Oliver 参考）
│   └── report/                           # Day 4 报告
│       ├── 报告模板.md                   # 复制此模板填写
│       └── justin-Day4报告.md            # 杨知行的 Day 4 报告
├── Day5/
│   ├── 定投实习计划_Day5参考指南.md      # Day 5 作业说明
│   ├── code/                             # 回测脚本
│   │   ├── backtest_3years.py
│   │   ├── plot_returns.py
│   │   └── data/
│   │       └── 000905_history.csv        # 近3年历史数据（用于止盈回测）
│   └── report/                           # Day 5 报告
│       ├── 报告模板.md                   # 复制此模板填写
│       ├── justin-Day5报告.md            # 杨知行的 Day 5 报告
│       ├── csi500_数据分析.md
│       └── assets/
│           ├── dca_vs_lumpsum_3years.png
│           └── .gitkeep
├── Day6/
│   ├── 定投实习计划_Day6参考指南.md      # Day 6 作业说明（止盈机制+止盈工具+PR协作）
│   ├── code/                             # 止盈回测脚本
│   │   └── profit_taker_backtest.py     # 回测脚本（数据用 Day5/code/data/000905_history.csv）
│   └── report/                           # Day 6 报告
│       └── 报告模板.md                   # 复制此模板填写
├── Day7/
│   ├── 定投实习计划_Day7参考指南.md      # Day 7 作业说明（Skill封装+Cron自动化）
│   └── report/                           # Day 7 报告
│       └── 报告模板.md                   # 复制此模板填写
├── Day8/
│   ├── 定投实习计划_Day8参考指南.md      # Day 8 作业说明（以第三课五步复盘工具缺口并补齐；流程册）
│   ├── 定投实习计划_Day8参考思路.md      # Day 8 配套核对材料（缺口核对表 + 参考改法；自查写方案后再打开）
│   └── report/                           # Day 8 报告（自建）
├── skills/                              # QClaw 技能包
│   └── dca-tools/
│       └── SKILL.md                     # 封装 tools/ 的 QClaw 技能定义
├── tools/                               # 定投工具（所有天共用）
│   ├── main.py / config.py / calculator.py / recorder.py / portfolio.py / scheduler.py
│   ├── profit_taker.py                 # 止盈工具（Day6新增）
│   ├── requirements.txt
│   └── portfolio.xlsx                   # 持仓记录+定投日历（每次买入后提交GitHub）
├── reading/                             # 极简财商系列阅读材料
│   ├── Index.md                         # 系列目录页
│   ├── 第零课 ~ 第三课（5 篇 Markdown）
│   └── assets/                          # 文章配图（PNG）
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

## 扩展技能（Day 7）

| 技能 | 位置 | 作用 |
|------|------|------|
| dca-tools | `skills/dca-tools/SKILL.md` | 封装 tools/ 的 Python 函数为 QClaw 可调用工具，支持定投计算、持仓查询、PE估值、止盈判断、日历管理 |

## License

Private — 仅限项目参与者使用。
