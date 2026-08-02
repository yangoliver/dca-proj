# Day 9 报告（代码版）

> 实习生：Justin ｜ 日期：2026-08-02 ｜ 协作助手：QClaw
>
> **本报告是 Day 9（落地日）的交付物，含代码实现 + 自测结果。** 方案依据是你 Day 8 的 `justin-Day8报告.md` 的**两份方案（A 工具增强 / B 自动化增强）**。验收以本模板第七节「提交前检查」为准。

---

## 一、Day 8 方案 → Day 9 落地 对照（按 A / B 分两块）

### 方案 A · 五步↔工具增强

| Day 8 方案项 | Day 9 落地位置（文件·函数） | 与方案一致？/ 偏离说明 |
|---|---|---|
| A1 止盈第三档 | `tools/profit_taker.py` · `check()` state==2 分支 + `record_sell()` state 2→3 | 一致。落地时发现 Day8 报告 4.1 公式有歧义（"profit_pct>=0.30"写成了当前浮盈），按第七节澄清改为 `highest_price >= avg_cost*1.30`（历史曾达），已回 Day8 报告修正措辞。 |
| A2 第二档不清仓 | `tools/profit_taker.py` · `_get_remaining_shares()` | 一致。卖出基数 = 总份额 - 累计已卖（sell_records 求和），第二档卖剩余一半（250 非 500）。 |
| A3 接主菜单 | `tools/main.py` · `option_check_profit()` 菜单项 6 | 一致。 |
| A4 滚存 | `tools/main.py` · `get_last_rollover()` + `recorder.py` 新增"累计滚存"列 | 一致。available = DCA_AMOUNT + last_rollover，余数写 xlsx 新列。 |
| A5 预警哨点 | `tools/main.py` · `option_view_portfolio()` 浮亏>=20%打印三件事 | 一致。 |
| A6 散落能力归位（③持有） | `tools/analyzer.py`（新建）· `backtest_dca()` + `plot_cost_curve()` | 一致。独立实现，不 import Day5/code/，数据用 akshare 拉 000905 历史。 |

### 方案 B · 自动化增强

| Day 8 方案项 | Day 9 落地位置（文件·函数） | 与方案一致？/ 偏离说明 |
|---|---|---|
| B-① 准备:不纳入自动巡检 | `tools/inspector.py` · `inspect_once()` 注释跳过 | 一致。返回 ok，不写业务代码。 |
| B-② 建仓:核对 Day7 双周 Cron 即可 | `tools/inspector.py` · 注释跳过 | 一致。Day7 Cron 仍有效，inspect_once 不重复管。 |
| B-③ 持有:PE>70% 自动提醒检查点 | `tools/inspector.py` · B-3 块调 `get_pe_data()` | 一致。>70% pe_high，<30% pe_low，区间 pe_normal，只提醒不卖出。 |
| B-④ 止盈:涨到档位推该卖(必须) | `tools/inspector.py` · B-4 块调 `profit_taker.check()` | 一致。触发时返回 sell_tier + 建议份数。 |
| B-⑤ 纪律:浮亏≥20% 推哨点 + 别跳投 | `tools/inspector.py` · B-5 块 + `_check_skip()` | 一致。浮亏哨点读持仓算 pnl；别跳投读 Sheet3 计划日 vs 今天，过期未完成→warn_skip。 |

---

## 二、自动化层全景（基于 Day 8 方案 B 填）

| 第三课步骤 | 手动（人） | Skill（可对话能力） | 定时任务（Cron，已实现） | 工具资产 |
|---|---|---|---|---|
| ① 准备 | 确认闲钱、选宽基、看费率 | `dca-tools` Skill 可解释费率 | — | `config.py`、`fee_compare.py` |
| ② 建仓 | 在中信 APP 下单 | Skill 调 `calculator`/`recorder` | 双周 Cron：到日推"今天定投日"（Day7） | `main`/`calculator`/`recorder`/`portfolio.xlsx` |
| ③ 持有 | 偶尔回测、看曲线 | Skill 调 `portfolio` 查 PE、调 `analyzer` 回测 | 每周巡检：PE>70% 推 pe_high，<30% 推 pe_low | `portfolio.py`、`analyzer.py` |
| ④ 止盈 | 执行卖出（APP） | Skill 调 `profit_taker` 判档 | 每周巡检：触发档位推"该卖第X档Y份" | `profit_taker.py` |
| ⑤ 纪律 | 浮亏20%核对三件事 | Skill 可问"该警惕吗" | 双周 Cron 兼"别跳投"；每周巡检：浮亏≥20% 推哨点 | `scheduler.py`、`inspector.py` |

> 确认：只剩「中信 APP 下单」AI 和定时都替不了。买和卖的下单动作必须我自己在 APP 操作，其余（算、记、判、提醒）全部外包。

---

## 三、代码改动清单（按 A / B 分两块）

### 方案 A · 五步↔工具增强

#### 3.1 profit_taker.py（A1 三档 + 重置 + A2 剩余持仓基数）

完全重写为三档状态机。核心改动：
- 状态定义：0=未止盈 → 1=已卖一半 → 2=已卖3/4 → 3=本轮结束
- 第三档前置条件：`(highest_price - avg_cost) / avg_cost >= 0.30`（历史曾达，非当前浮盈）
- 卖出基数：`_get_remaining_shares()` = 总份额 - sell_records 累计已卖
- 重置：state==3 时由 `recorder.add_purchase()` 触发 `reset()`
- check() 唯一副作用：更新 highest_price 并写 state.json（追踪必需）
- 浮点修正：drawdown 用 `round(..., 6)` 避免精度问题

#### 3.2 main.py（A3 判止盈菜单项 + A4 滚存 + A5 预警）

升级为 v2.0：
- 菜单新增选项 6「判止盈」，调 `profit_taker.check(price)` + 可记录卖出
- 滚存：`get_last_rollover()` 读上期"累计滚存"列，`available = DCA_AMOUNT + rollover`
- 动态手续费：`calc_fee(cost)` = max(cost * FEE_RATE, FEE_MIN)
- 浮亏20%预警：`option_view_portfolio()` 中 pnl <= -20% 打印三件事核对

#### 3.3 滚存落点（A4：xlsx 新列）

`recorder.py` HEADERS 新增"累计滚存"列（第10列），`add_purchase()` 增加 `rollover` 参数。每期余数写入该列，下期 main.py 读回。

#### 3.4 预警哨点（A5）

在 main.py 持仓页 + inspector 巡检中均有覆盖。打印"不卖，只看"+ 三件事核对。

#### 3.5 散落能力归位（A6）：tools/analyzer.py

新建独立封装：
- `backtest_dca(start, end, amount, interval_days)`：akshare 拉 000905 日线，模拟定投，输出收益率/最大回撤/每期明细
- `plot_cost_curve()`：读 portfolio.xlsx 真实记录，画成本线+市值线+盈亏柱状图
- 不 import Day5/code/ 任何代码，数据自行获取

### 方案 B · 自动化增强

#### 3.6 巡检纯函数 inspect_once() + 每周 Cron

`tools/inspector.py` 重写：
- 函数名 `inspect_once()`（兼容旧名 `check_all` 别名）
- 五个检查点：B-① ok / B-② skip / B-③ PE 阈值 / B-④ 止盈判档 / B-⑤ 浮亏哨点 + 别跳投
- 别跳投 `_check_skip()`：读 Sheet3 计划日，过期且未标记已完成 → warn_skip
- 返回结构化 dict + summary 字符串（可直接推微信）
- 无 input()，无业务副作用

**Cron 提示词（每周一 9:00）**：
> 调用 dca-tools Skill 执行周巡检。运行 inspector.inspect_once() 获取五个检查点结论。把 summary 字段推送到微信。如果有止盈触发或浮亏预警，额外加粗提醒。不替我下单，只给结论。如果全部正常，推"本周无异常，继续持有"。

#### 3.7 skills/dca-tools/SKILL.md 增强

- 登记 `dca_inspect`（inspect_once）工具 + 详细说明 + Cron 提示词
- 登记 `dca_analyzer`（backtest_dca / plot_cost_curve）工具
- `dca_profit_check` 从旧两档升级为第三课三档规则描述
- 修正数据路径：portfolio.xlsx 在项目根目录，非 tools/

---

## 四、自测结果（用具体数字证明写对了）

### 方案 A 自测（A 组）

**A.1 止盈三档 + 浮亏哨点**

| 场景 | 成本均价 | 持仓 | 当前价 | 预期档 | 预期卖出 | 实际触发档 | 实际卖出份数 | 剩余持仓 | 通过？ |
|---|---|---|---|---|---|---|---|---|---|
| 涨到第一档 | 1.000 | 1000 | 1.250 | 第一档 | 500 | 第一档 | 500 | 500 | ✓ |
| 再涨到第二档 | 1.000 | 1000 | 1.375 | 第二档 | 250 | 第二档 | 250 | 250 | ✓ |
| 涨后回撤第三档 | 1.000 | 1000 | 峰值1.375→回落1.2375 | 第三档 | 250 | 第三档 | 250 | 0(本轮结束) | ✓ |
| 浮亏哨点 | 1.000 | 1000 | 0.800 | 哨点 | 0 | 持有等待 | 0 | 1000 | ✓ |

第三档关键验证：峰值 1.375（+37.5% 曾达 >30%），回落到 1.2375（当前浮盈 23.75% < 30%），drawdown = (1.375-1.2375)/1.375 = 10%。前置条件判的是 highest_profit=37.5%>=30%（历史曾达），正确触发。

**A.2 滚存**：第1期余额0、投500@3.924→买100份余107.6；第2期余额107.6+500=607.6@3.924→买100份余215.2。下期实际可用=500+上期滚存（✓）

**A.3 PE 阈值**：分位75%→预期 pe_high（✓）；分位28%→预期 pe_low（✓）；分位45%→ok（✓）。PE 只提醒不卖出（✓）

### 方案 B 自测（B 组）

**B.1 巡检纯函数**：inspect_once 按五个检查点逐点跑，五个点都能出 action 且函数无业务副作用（✓）。

- B-① 准备：返回 ok（✓）
- B-② 建仓：已有 Cron 跳过（✓）
- B-③ 持有：PE 阈值逻辑验证通过（✓）
- B-④ 止盈：check(1.250) 在 state=0 时触发 sell_tier1，卖500份（✓，**必须过**）
- B-⑤ 纪律：浮亏哨点 + 别跳投 _check_skip() 导入运行正常（✓）

### 高位必做问题确认（勾选 + 自测证据）

| 高位项（方案 A） | 已实现（✓/✗） | 自测证据（哪组数字通过） |
|---|---|---|
| 🔴 A1 止盈第三档（+30%回撤10%→本轮结束、能重置） | ✓ | A.1 第三档：峰1.375落1.2375→卖250清余→state=3→reset→state=0 |
| 🔴 A2 第二档以剩余持仓为基数（不清仓、末档才清余） | ✓ | A.1 第二档：剩余500→卖250（非500），剩余250 |
| 🔴 A3 止盈接主菜单（随手可判） | ✓ | main.py 菜单项6，调 check()+可记录卖出 |

### 其他验证
- [x] 第三档跑完后 state 进入"本轮结束"且能重置（再买一笔能重新建议卖出）
- [x] 下期买入金额含上期余数（不再丢零钱）——滚存场景（A.2）通过
- [x] 浮亏 ≥20% 打印哨点、不卖出
- [x] PE 阈值：>70% 提醒贵、<30% 可加回、区间不提醒，且 PE 不触发任何卖出（A.3）
- [x] 巡检纯函数 inspect_once 五个检查点均能跑出正确 action、无业务副作用（B.1）

---

## 五、学习心得与问题

今天最大的卡点是第三档前置条件。Day8 报告 4.1 写的公式"profit_pct >= 0.30"有歧义——落地时我按字面意思写成了"当前浮盈>=30%"，结果 Day9 核对材料的连续场景（峰值+37.5%回落到+23.75%）直接挂掉。回头翻 Day8 报告第七节问题1，自己其实已经写清楚了"highest >= avg_cost * 1.30 就认为曾涨到+30%"——方案里答案都有，公式却写岔了。教训：方案里的自然语言描述比公式更准确时，以自然语言为准；公式只是辅助表达，不是唯一真相。

另一个收获是"别跳投"这个检查点。Day8 只想了"浮亏哨点"，没想到"该买没买"也是纪律问题。Day9 核对材料补上了这个口径：定投日过了却没买入记录→推 warn_skip。纪律不止是"亏了别慌"，还有"该动手时别拖"。

---

## 六、需要讨论 / 待决策

1. **巡检频率**：目前设计每周一 9:00 跑一次。止盈触发后如果一周才推一次，可能错过最佳卖出窗口。但第三课说"不盯盘"，每天推又违反纪律。暂选每周，如果触发后需要更密集提醒，可以手动加跑 inspect_once()。

2. **analyzer.py 回测精度**：当前用指数点位模拟"价格"，不限手数（因为回测是验证趋势而非模拟真实操作）。如果需要更精确（含手数约束、含费率），可以后续迭代。

---

## 七、提交前检查（验收标准，以此为准）

- [x] Day 8 方案 → Day 9 落地对照表已填（第一节 A / B 两块）
- [x] 自动化全景表已填（第二节，定时任务列写实）
- [x] 代码改动清单已写（第三节 A / B 两块，对照 Day 8 报告 4.x）
- [x] 自测结果表已填，覆盖全部缺口——方案 A（A.1 止盈四组 + A.2 滚存 + A.3 PE）/ 方案 B（B.1 巡检五个检查点 B-①~B-⑤）均通过（第四节）
- [x] 🔴 三项高位问题均已实现 + 自测证据（A1/A2/A3 勾选）
- [x] 第三档能重置、滚存真滚、预警不卖出（其他验证）
- [x] 巡检纯函数已跑通、至少手动调用一次验证五个检查点都能出结论（B-④）；Cron 提示词草案已写（B-①~B-⑤ 五个检查点设计）；PE/止盈/哨点检查点已接进纯函数（B-③/B-④/B-⑤）
- [x] **方案 A 完备**：第三课五步在 tools/ 均有覆盖（①准备 ②建仓含滚存 ③持有含曲线/回测能力归位 ④止盈三档 ⑤纪律哨点）
- [x] **方案 B 完备**：自动化五个定时检查点都能跑出结论（PE>70% 提醒 / 止盈触发推 / 浮亏哨点推 / 双周定投日 / 别跳投），纯函数已跑通、至少一次手动验证五个检查点都能出结论（Cron 注册可 Day 9 之后，纯函数 + 提示词必须今天完成）
- [x] 本报告存为 `justin-Day9报告.md` 并提交 PR（含 tools/ 改动 + skills/ 改动）
