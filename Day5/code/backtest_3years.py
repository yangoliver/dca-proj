import pandas as pd
import math

df = pd.read_csv(r'D:\ws\dca-proj\csi500_000905_daily.csv')
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date').reset_index(drop=True)

# 指数点位换算 ETF 价格（除以1000，中证500 ETF 实际价格约 5~9 元/份）
SCALE = 1000
df['price'] = df['close'] / SCALE

# ============================================================
# 定投策略：每14个交易日买入一次，每次¥500，弹性股数法
# ============================================================
dca_amount = 500       # 每次投入金额
dca_interval = 14      # 每隔14个交易日
remainder = 0.0        # 零钱滚存

total_invested = 0.0
total_shares = 0
buy_count = 0
records = []           # 每次买入记录

for i in range(0, len(df), dca_interval):
    row = df.iloc[i]
    price = row['price']
    date = row['date']

    # 可用金额 = 本次定投 + 上次零钱
    available = dca_amount + remainder
    # 弹性股数法：能买几手
    lots = math.floor(available / price / 100)
    if lots == 0:
        # 不够一手，钱全部滚入下次
        remainder = available
        continue

    actual_shares = lots * 100
    actual_cost = actual_shares * price
    remainder = available - actual_cost

    total_invested += actual_cost
    total_shares += actual_shares
    buy_count += 1
    records.append({
        'date': date, 'price': price, 'lots': lots,
        'shares': actual_shares, 'cost': actual_cost, 'remainder': remainder
    })

# 最终市值
final_price = df.iloc[-1]['price']
final_date = df.iloc[-1]['date']
dca_market_value = total_shares * final_price
dca_return = (dca_market_value - total_invested) / total_invested * 100
dca_avg_cost = total_invested / total_shares

print("=" * 50)
print("【定投策略】双周定投 ¥500/次，弹性股数法")
print("=" * 50)
print(f"  起始日期：{df.iloc[0]['date'].strftime('%Y-%m-%d')}")
print(f"  结束日期：{final_date.strftime('%Y-%m-%d')}")
print(f"  买入次数：{buy_count} 次")
print(f"  累计投入：¥{total_invested:,.2f}")
print(f"  累计份额：{total_shares:,} 份")
print(f"  平均成本：¥{dca_avg_cost:.4f}/份")
print(f"  最终市值：¥{dca_market_value:,.2f}")
print(f"  收益率：{dca_return:+.2f}%")

# ============================================================
# 一次性买入策略：起点投入¥10,000
# ============================================================
lumpsum_amount = 10000
first_price = df.iloc[0]['price']
lumpsum_lots = math.floor(lumpsum_amount / first_price / 100)
lumpsum_shares = lumpsum_lots * 100
lumpsum_cost = lumpsum_shares * first_price
lumpsum_market_value = lumpsum_shares * final_price
lumpsum_return = (lumpsum_market_value - lumpsum_cost) / lumpsum_cost * 100

print()
print("=" * 50)
print("【一次性买入】起始日投入 ¥10,000")
print("=" * 50)
print(f"  买入日期：{df.iloc[0]['date'].strftime('%Y-%m-%d')}")
print(f"  买入价格：¥{first_price:.4f}")
print(f"  买入份额：{lumpsum_shares:,} 份")
print(f"  实际花费：¥{lumpsum_cost:,.2f}")
print(f"  最终市值：¥{lumpsum_market_value:,.2f}")
print(f"  收益率：{lumpsum_return:+.2f}%")

# ============================================================
# 对比
# ============================================================
gap = dca_return - lumpsum_return
print()
print("=" * 50)
print("【对比结论】")
print("=" * 50)
print(f"  定投收益率：{dca_return:+.2f}%  最终市值 ¥{dca_market_value:,.2f}")
print(f"  一次性买入：{lumpsum_return:+.2f}%  最终市值 ¥{lumpsum_market_value:,.2f}")
print(f"  差距：{abs(gap):.2f} 个百分点")
winner = "定投" if dca_return > lumpsum_return else "一次性买入"
print(f"  谁赢了？{winner}")
