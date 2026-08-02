"""
analyzer.py — 回测 + 成本曲线（独立封装，方案A·③持有）
=====================================================
在 tools/ 下独立实现回测和曲线能力，不 import Day5/code/ 任何代码。
数据来源：akshare 拉中证500指数历史 / 读 portfolio.xlsx 真实记录。

功能：
1. backtest_dca(start, end, amount, interval_days) — 模拟定投回测
2. plot_cost_curve() — 从 portfolio.xlsx 读真实记录画成本/市值曲线

运行：python analyzer.py [--backtest] [--plot]
"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(TOOLS_DIR)
sys.path.insert(0, TOOLS_DIR)

# 路径修正
import recorder
recorder.EXCEL_PATH = os.path.join(PROJECT_DIR, "data", "portfolio.xlsx")

OUTPUT_DIR = os.path.join(TOOLS_DIR, "output")


def backtest_dca(start: str = "2022-01-01", end: str = "2025-01-01",
                 amount: float = 500, interval_days: int = 14) -> dict:
    """
    用中证500指数历史数据模拟定投回测。

    参数：
        start         : 回测起始日
        end           : 回测结束日
        amount        : 每期投入金额
        interval_days : 定投间隔天数

    返回 dict:
        periods       : 定投期数
        total_invest  : 累计投入
        final_shares  : 累计份额（以指数点位为"价格"）
        avg_cost      : 平均成本
        final_value   : 期末市值
        return_pct    : 收益率(%)
        max_drawdown  : 最大回撤(%)
        schedule      : 每期明细 list[dict]
    """
    import akshare as ak
    import pandas as pd

    print(f"[回测] 拉取中证500指数数据 ({start} ~ {end})...")
    df = ak.stock_zh_index_daily(symbol="sh000905")
    df["date"] = pd.to_datetime(df["date"])
    mask = (df["date"] >= start) & (df["date"] <= end)
    df = df[mask].reset_index(drop=True)

    if df.empty:
        print("[回测] 无数据，请检查日期范围")
        return {}

    # 模拟定投
    from datetime import datetime, timedelta
    start_dt = datetime.strptime(start, "%Y-%m-%d")
    end_dt = datetime.strptime(end, "%Y-%m-%d")

    schedule = []
    total_invest = 0.0
    total_shares = 0.0
    invest_dates = []

    current = start_dt
    while current <= end_dt:
        # 找最近交易日的收盘价
        day_str = current.strftime("%Y-%m-%d")
        row = df[df["date"] >= day_str]
        if row.empty:
            current += timedelta(days=interval_days)
            continue
        price = float(row.iloc[0]["close"])
        shares = amount / price  # 指数回测不限手数
        total_invest += amount
        total_shares += shares
        invest_dates.append(price)
        schedule.append({
            "date": day_str,
            "price": round(price, 2),
            "shares": round(shares, 4),
            "cum_invest": round(total_invest, 2),
            "cum_shares": round(total_shares, 4),
        })
        current += timedelta(days=interval_days)

    if not schedule:
        print("[回测] 无有效定投日")
        return {}

    # 期末市值（用最后一个交易日收盘价）
    final_price = float(df.iloc[-1]["close"])
    final_value = total_shares * final_price
    avg_cost = total_invest / total_shares
    return_pct = (final_value - total_invest) / total_invest * 100

    # 最大回撤（基于每期市值）
    values = [s["cum_shares"] * final_price for s in schedule]
    peak = values[0]
    max_dd = 0
    for v in values:
        if v > peak:
            peak = v
        dd = (peak - v) / peak * 100
        if dd > max_dd:
            max_dd = dd

    result = {
        "periods": len(schedule),
        "total_invest": round(total_invest, 2),
        "final_shares": round(total_shares, 4),
        "avg_cost": round(avg_cost, 2),
        "final_price": round(final_price, 2),
        "final_value": round(final_value, 2),
        "return_pct": round(return_pct, 2),
        "max_drawdown": round(max_dd, 2),
        "schedule": schedule,
    }

    _print_backtest(result)
    return result


def _print_backtest(r: dict):
    """打印回测结果摘要"""
    print("\n" + "=" * 52)
    print("  中证500 定投回测结果")
    print("=" * 52)
    print(f"  定投期数      : {r['periods']} 期")
    print(f"  累计投入      : {r['total_invest']:,.2f} 元")
    print(f"  平均成本      : {r['avg_cost']:.2f} 点")
    print(f"  期末指数      : {r['final_price']:.2f} 点")
    print(f"  期末市值      : {r['final_value']:,.2f} 元")
    print(f"  收益率        : {r['return_pct']:+.2f}%")
    print(f"  最大回撤      : {r['max_drawdown']:.2f}%")
    print("=" * 52)


def plot_cost_curve(save_path: str = None) -> str:
    """
    从 portfolio.xlsx 读真实买入记录，画成本线 + 市值线 + 盈亏柱状图。
    与 dashboard.py 类似但集成在 analyzer 里，供 Skill/回测对比调用。

    返回：输出文件路径
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager

    # 中文字体
    for fname in ["Microsoft YaHei", "SimHei", "PingFang SC"]:
        if any(fname in f.name for f in font_manager.fontManager.ttflist):
            plt.rcParams["font.sans-serif"] = [fname]
            break
    plt.rcParams["axes.unicode_minus"] = False

    from recorder import get_all_records
    from portfolio import get_price_now

    records = get_all_records()
    if not records:
        print("[analyzer] 无买入记录，无法画曲线")
        return ""

    price = get_price_now()
    if not price:
        price = float(records[-1]["买入价格"])

    periods = list(range(1, len(records) + 1))
    cum_invest = [float(r["累计投入"]) for r in records]
    cum_shares = [float(r["累计份额"]) for r in records]
    market_value = [s * price for s in cum_shares]
    pnl = [mv - ci for mv, ci in zip(market_value, cum_invest)]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    ax1.plot(periods, cum_invest, "b-o", markersize=4, label="累计投入")
    ax1.plot(periods, market_value, "r-s", markersize=4, label=f"市值(价格{price:.3f})")
    ax1.set_ylabel("金额(元)")
    ax1.set_title("510580 定投实盘：成本 vs 市值")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    colors = ["green" if p >= 0 else "red" for p in pnl]
    ax2.bar(periods, pnl, color=colors, alpha=0.6)
    ax2.axhline(y=0, color="black", linewidth=0.5)
    ax2.set_xlabel("期数")
    ax2.set_ylabel("盈亏(元)")
    ax2.set_title("每期浮盈/浮亏")
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = save_path or os.path.join(OUTPUT_DIR, "cost_curve.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"[analyzer] 成本曲线已保存: {out_path}")
    return out_path


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="定投回测 + 曲线工具")
    parser.add_argument("--backtest", action="store_true", help="运行3年回测")
    parser.add_argument("--plot", action="store_true", help="画实盘成本曲线")
    parser.add_argument("--start", default="2022-01-01", help="回测起始日")
    parser.add_argument("--end", default="2025-01-01", help="回测结束日")
    args = parser.parse_args()

    if args.backtest:
        backtest_dca(args.start, args.end)
    if args.plot:
        plot_cost_curve()
    if not args.backtest and not args.plot:
        print("用法: python analyzer.py --backtest [--start 2022-01-01 --end 2025-01-01]")
        print("      python analyzer.py --plot")
