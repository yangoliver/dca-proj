"""
fee_compare.py — 中证500 ETF 费率对比（独立脚本）
=================================================
对比 3 只主流中证500 ETF 的管理费率+托管费率，
计算持有 1/3/5 年的复合费率成本。

运行：python fee_compare.py
"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ==================== 费率数据 ====================
# 数据来源：各基金公司官网/天天基金，截至 2026 年

ETFS = [
    {"code": "510580", "name": "易方达中证500ETF", "mgmt": 0.0015, "custody": 0.0005},
    {"code": "510500", "name": "南方中证500ETF",   "mgmt": 0.0050, "custody": 0.0010},
    {"code": "159922", "name": "嘉实中证500ETF",   "mgmt": 0.0050, "custody": 0.0010},
]

HOLD_YEARS = [1, 3, 5]
INVEST_AMOUNT = 10000  # 假设投入 1 万元


def calc_compound_cost(amount: float, annual_rate: float, years: int) -> float:
    """计算复合费率成本（每年扣除费率后的损失）"""
    value = amount
    for _ in range(years):
        value *= (1 - annual_rate)
    return amount - value


def main():
    print("=" * 66)
    print("  中证500 ETF 费率对比（管理费 + 托管费）")
    print("=" * 66)
    print(f"  假设投入：{INVEST_AMOUNT:,} 元")
    print("-" * 66)
    print(f"  {'ETF':<20} {'管理费':>8} {'托管费':>8} {'合计':>8}")
    print("-" * 66)

    for etf in ETFS:
        total = etf["mgmt"] + etf["custody"]
        print(f"  {etf['name']:<18} {etf['mgmt']*100:>7.2f}% {etf['custody']*100:>7.2f}% {total*100:>7.2f}%")

    print("-" * 66)
    print(f"\n  持有成本对比（{INVEST_AMOUNT:,} 元，复合扣除）：")
    print(f"  {'ETF':<20} {'1年':>10} {'3年':>10} {'5年':>10}")
    print("-" * 66)

    for etf in ETFS:
        total_rate = etf["mgmt"] + etf["custody"]
        costs = [calc_compound_cost(INVEST_AMOUNT, total_rate, y) for y in HOLD_YEARS]
        print(f"  {etf['name']:<18} {costs[0]:>9.1f}元 {costs[1]:>9.1f}元 {costs[2]:>9.1f}元")

    print("-" * 66)

    # 对比结论
    low = ETFS[0]
    high = ETFS[1]
    diff_5y = (
        calc_compound_cost(INVEST_AMOUNT, high["mgmt"] + high["custody"], 5)
        - calc_compound_cost(INVEST_AMOUNT, low["mgmt"] + low["custody"], 5)
    )
    print(f"\n  结论：{low['name']}（{low['code']}）费率最低，")
    print(f"  持有5年比 {high['name']} 节省约 {diff_5y:.1f} 元（每万元）。")
    print(f"  定投选低费率，长期复利差距显著。")
    print("=" * 66)


if __name__ == "__main__":
    main()
