"""
止盈回测脚本 — 中证500 (000905)
=================================
目标：对比「有止盈」vs「无止盈」的定投收益

数据：Day5/code/data/000905_history.csv（不重新拉）

规则：
  - 双周定投，每次 ¥500，弹性股数法
  - 单轮浮盈 ≥ 25% → 卖持仓的 1/2
  - 继续涨 10% → 再卖剩余的 1/2
  - 永不清仓
  - 不停止定投
"""
import csv
import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ── 数据路径 ──
DATA_PATH = os.path.normpath(os.path.join(
    os.path.dirname(__file__), '..', '..', 'Day5', 'code', 'data', '000905_history.csv'
))

# ── 参数 ──
DCA_INTERVAL = 10       # 每 10 个交易日定投一次（≈双周）
DCA_AMOUNT   = 500.0    # 每次定投金额
PROFIT_TRIGGER = 0.25   # 浮盈 ≥ 25% 触发第一档
RISE_TRIGGER   = 0.10   # 再涨 10% 触发第二档

# ── 读取数据 ──
rows = []
with open(DATA_PATH, encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        rows.append({'date': r['date'], 'close': float(r['close'])})

# ── 回测主循环 ──
# 有止盈
shares_w = 0.0          # 持仓份额
invested_w = 0.0        # 累计投入
cash_w = 0.0            # 止盈累计收回金额
state_w = 0             # 0=未止盈, 1=已卖一半, 2=已卖3/4
trigger2_w = 0.0        # 第二档触发价
records_w = []          # 止盈操作记录

# 无止盈
shares_n = 0.0
invested_n = 0.0

for i, row in enumerate(rows):
    price = row['close']
    date  = row['date']

    # ── 定投（两条线同步） ──
    if i % DCA_INTERVAL == 0:
        shares_w += DCA_AMOUNT / price
        invested_w += DCA_AMOUNT
        shares_n += DCA_AMOUNT / price
        invested_n += DCA_AMOUNT

    # ── 止盈判断 ──
    avg_w  = invested_w / shares_w if shares_w > 0 else 0
    profit = (price - avg_w) / avg_w if avg_w > 0 else 0

    if state_w == 0 and profit >= PROFIT_TRIGGER:
        # 第一档：卖一半
        sell = shares_w / 2
        cash_w += sell * price
        shares_w -= sell
        trigger2_w = price * (1 + RISE_TRIGGER)
        state_w = 1
        records_w.append({
            'date': date, 'cond': '浮盈>=25%',
            'shares': sell, 'price': price, 'amount': sell * price
        })
    elif state_w == 1 and price >= trigger2_w:
        # 第二档：再卖剩余一半
        sell = shares_w / 2
        cash_w += sell * price
        shares_w -= sell
        state_w = 2
        records_w.append({
            'date': date, 'cond': '再涨10%',
            'shares': sell, 'price': price, 'amount': sell * price
        })
    elif state_w == 2 and profit < PROFIT_TRIGGER:
        # 重置，等下一轮
        state_w = 0

# ── 计算最终结果 ──
final_price = rows[-1]['close']

value_w   = shares_w * final_price          # 有止盈 - 持仓市值
total_w   = value_w + cash_w                # 有止盈 - 总资产
return_w  = (total_w - invested_w) / invested_w * 100

value_n   = shares_n * final_price          # 无止盈 - 持仓市值
return_n  = (value_n - invested_n) / invested_n * 100

# ── 输出 ──
print("=" * 60)
print("止盈回测结果")
print("=" * 60)
print(f"数据范围：{rows[0]['date']} ~ {rows[-1]['date']}")
print(f"交易日数：{len(rows)}，定投次数：{len(rows) // DCA_INTERVAL}")
print(f"最终收盘价：{final_price:.2f}")
print()

print(f"{'指标':<16} {'有止盈':>12} {'无止盈':>12}")
print("-" * 44)
print(f"{'累计投入':<14} ¥{invested_w:>10,.0f} ¥{invested_n:>10,.0f}")
print(f"{'持仓份额':<14} {shares_w:>12.2f} {shares_n:>12.2f}")
print(f"{'持仓市值':<14} ¥{value_w:>10,.0f} ¥{value_n:>10,.0f}")
print(f"{'止盈累计金额':<12} ¥{cash_w:>10,.0f} {'—':>12}")
print(f"{'总资产':<14} ¥{total_w:>10,.0f} ¥{value_n:>10,.0f}")
print(f"{'总收益率':<14} {return_w:>11.2f}% {return_n:>11.2f}%")
print(f"{'触发止盈次数':<12} {len(records_w):>12} {'—':>12}")

print()
print("=" * 60)
print("止盈操作记录")
print("=" * 60)
for idx, rec in enumerate(records_w, 1):
    print(f"  #{idx}  {rec['date']}  {rec['cond']:<10}  "
          f"卖出 {rec['shares']:.2f} 份 @ {rec['price']:.2f}  "
          f"= ¥{rec['amount']:,.0f}")

print()
print(f"平均成本（有止盈）：{invested_w / shares_w:.2f}")
print(f"平均成本（无止盈）：{invested_n / shares_n:.2f}")
