import pandas as pd
import math
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

data_path = os.path.join(os.path.dirname(__file__), 'data', '000905_history.csv')
df = pd.read_csv(data_path)
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date').reset_index(drop=True)
SCALE = 1000
df['price'] = df['close'] / SCALE

# ============================================================
# 一次性买入
# ============================================================
first_price = df.iloc[0]['price']
ls_lots = math.floor(10000 / first_price / 100)
ls_shares = ls_lots * 100
ls_cost = ls_shares * first_price

# ============================================================
# 定投：每14天一次，弹性股数法，记录每日状态
# ============================================================
dca_amount = 500
dca_interval = 14
remainder = 0.0
total_invested = 0.0
total_shares = 0

# 预计算买入日索引
buy_day_indices = set(range(0, len(df), dca_interval))

dca_daily_ret = []
ls_daily_ret = []

for i, row in df.iterrows():
    p = row['price']

    # 如果是定投买入日
    if i in buy_day_indices:
        available = dca_amount + remainder
        lots = math.floor(available / p / 100)
        if lots > 0:
            actual_shares = lots * 100
            actual_cost = actual_shares * p
            remainder = available - actual_cost
            total_invested += actual_cost
            total_shares += actual_shares
        else:
            remainder += dca_amount

    # 定投收益率
    if total_invested > 0:
        dca_ret = (total_shares * p - total_invested) / total_invested * 100
    else:
        dca_ret = 0.0
    dca_daily_ret.append(dca_ret)

    # 一次性买入收益率
    ls_ret = (ls_shares * p - ls_cost) / ls_cost * 100
    ls_daily_ret.append(ls_ret)

final_price = df.iloc[-1]['price']
dca_return = (total_shares * final_price - total_invested) / total_invested * 100
ls_return = (ls_shares * final_price - ls_cost) / ls_cost * 100

# ============================================================
# 画图
# ============================================================
fig, ax = plt.subplots(figsize=(12, 6))

dates = df['date']
ax.plot(dates, ls_daily_ret, color='#e74c3c', linewidth=1.5, label='一次性买入', alpha=0.85)
ax.plot(dates, dca_daily_ret, color='#2980b9', linewidth=2, label='双周定投 (500元/14天)')

# 零线
ax.axhline(y=0, color='gray', linestyle='--', linewidth=0.8, alpha=0.5)

# 年份分界线 + 标签
ylim = ax.get_ylim()
for year in [2024, 2025, 2026]:
    ax.axvline(x=pd.Timestamp(f'{year}-01-01'), color='gray', linestyle=':', linewidth=0.6, alpha=0.4)
    ax.text(pd.Timestamp(f'{year}-07-01'), ylim[1] * 0.93, str(year),
            ha='center', fontsize=9, color='gray', alpha=0.5)

# 微笑曲线区间标注
for start, end, label in [
    (pd.Timestamp('2023-08-01'), pd.Timestamp('2024-05-31'), '微笑曲线1'),
    (pd.Timestamp('2024-05-01'), pd.Timestamp('2024-11-30'), '微笑曲线2'),
    (pd.Timestamp('2024-11-01'), pd.Timestamp('2025-09-30'), '微笑曲线3'),
]:
    ax.axvspan(start, end, alpha=0.05, color='#27ae60')
    mid = start + (end - start) / 2
    ax.text(mid, ylim[0] * 0.88, label, ha='center', fontsize=8,
            color='#27ae60', fontstyle='italic', alpha=0.6)

# 标注最终收益率
ax.annotate(f'定投 {dca_return:+.1f}%', xy=(dates.iloc[-1], dca_daily_ret[-1]),
            xytext=(-90, 15), textcoords='offset points',
            fontsize=10, color='#2980b9',
            arrowprops=dict(arrowstyle='->', color='#2980b9', lw=1.2))
ax.annotate(f'一次性 {ls_return:+.1f}%', xy=(dates.iloc[-1], ls_daily_ret[-1]),
            xytext=(-90, -25), textcoords='offset points',
            fontsize=10, color='#e74c3c',
            arrowprops=dict(arrowstyle='->', color='#e74c3c', lw=1.2))

ax.set_title('中证500 定投 vs 一次性买入 收益曲线 (2023-01 ~ 2026-07)', fontsize=14, pad=12)
ax.set_xlabel('日期', fontsize=11)
ax.set_ylabel('收益率 (%)', fontsize=11)
ax.legend(loc='upper left', fontsize=11, framealpha=0.9)
ax.grid(True, alpha=0.3)
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
plt.xticks(rotation=30, fontsize=9)
plt.tight_layout()

out = os.path.join(os.path.dirname(__file__), '..', 'report', 'assets', 'dca_vs_lumpsum_3years.png')
fig.savefig(out, dpi=150, bbox_inches='tight')
print(f'图表已保存: {out}')
print(f'定投: {dca_return:+.2f}%  一次性: {ls_return:+.2f}%')
print(f'买入次数: {sum(1 for i in range(0, len(df), dca_interval))}  累计投入: {total_invested:,.2f}  累计份额: {total_shares:,}')
