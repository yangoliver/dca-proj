"""
smile_curve_analyzer.py — 微笑曲线覆盖度分析
==============================================
分析给定总投资金额能否覆盖一条完整微笑曲线（最大回撤 → 恢复）。

核心问题：1 万元够不够撑完一次完整的"跌→投→涨"周期？
不够时给出方案 A（减金额延周期）和方案 B（追加金额）。

数据来源：akshare 拉取对应指数过去 5 年日线数据。
复用说明：analyzer.py 的 backtest_dca() 做固定日期范围回测，
本工具需先定位最大回撤区间再模拟，逻辑不同，不复用但遵循相同编码风格。

运行：python smile_curve_analyzer.py [--etf 510580] [--amount 10000]
"""
import os
import sys
import math

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(TOOLS_DIR)
sys.path.insert(0, TOOLS_DIR)


# ETF 代码 → 指数代码映射（akshare stock_zh_index_daily 用指数代码）
ETF_INDEX_MAP = {
    "510580": {"index_code": "sh000905", "name": "中证500"},
    "510300": {"index_code": "sh000300", "name": "沪深300"},
    "510050": {"index_code": "sh000016", "name": "上证50"},
    "159915": {"index_code": "sz399006", "name": "创业板指"},
}


# ==================== 1. 数据获取 ====================


def fetch_index_history(index_code: str, years: int = 5):
    """
    拉取指数历史日线数据。

    参数：
        index_code : akshare 指数代码（如 sh000905）
        years      : 回溯年数

    返回：
        list[dict] — [{date: str, price: float}, ...] 按日期升序
    """
    import akshare as ak
    import pandas as pd

    df = ak.stock_zh_index_daily(symbol=index_code)
    df["date"] = pd.to_datetime(df["date"])

    cutoff = pd.Timestamp.now() - pd.DateOffset(years=years)
    df = df[df["date"] >= cutoff].copy()
    df = df.sort_values("date").reset_index(drop=True)

    return [{"date": str(r["date"].date()), "price": float(r["close"])}
            for _, r in df.iterrows()]


# ==================== 2. 最大回撤检测 ====================


def find_max_drawdown_cycle(prices: list) -> dict:
    """
    在价格序列中找到最大回撤的完整周期。

    完整周期 = 峰值(peak) → 谷值(trough) → 恢复(recovery)
    恢复定义：价格回升到峰值水平。若 5 年内未恢复，标记到数据末尾。

    返回 dict:
        peak_idx, trough_idx, recovery_idx : 各关键点索引
        peak_date, trough_date, recovery_date : 各关键点日期
        peak_price, trough_price : 峰值/谷值价格
        drawdown_pct : 最大跌幅(%)
        recovered : 是否已恢复
        smile_period_prices : 完整微笑周期内的价格序列
    """
    n = len(prices)
    price_arr = [p["price"] for p in prices]

    # 计算运行最大值（到每个时点为止的历史最高）
    running_max = [0.0] * n
    running_max[0] = price_arr[0]
    for i in range(1, n):
        running_max[i] = max(running_max[i - 1], price_arr[i])

    # 找最大回撤的谷值位置
    max_dd_pct = 0.0
    trough_idx = 0
    for i in range(n):
        dd = (running_max[i] - price_arr[i]) / running_max[i]
        if dd > max_dd_pct:
            max_dd_pct = dd
            trough_idx = i

    # 峰值位置：谷值之前运行最大值首次达到的位置
    peak_price = running_max[trough_idx]
    peak_idx = 0
    for i in range(trough_idx + 1):
        if price_arr[i] >= peak_price:
            peak_idx = i
            break

    # 恢复位置：谷值后价格首次回到峰值水平
    trough_price = price_arr[trough_idx]
    recovery_idx = -1
    for i in range(trough_idx + 1, n):
        if price_arr[i] >= peak_price:
            recovery_idx = i
            break

    recovered = recovery_idx >= 0
    if not recovered:
        recovery_idx = n - 1

    smile_prices = prices[peak_idx:recovery_idx + 1]
    dd_pct = round(max_dd_pct * 100, 2)

    return {
        "peak_idx": peak_idx,
        "trough_idx": trough_idx,
        "recovery_idx": recovery_idx,
        "peak_date": prices[peak_idx]["date"],
        "trough_date": prices[trough_idx]["date"],
        "recovery_date": prices[recovery_idx]["date"],
        "peak_price": round(peak_price, 2),
        "trough_price": round(trough_price, 2),
        "drawdown_pct": dd_pct,
        "recovered": recovered,
        "smile_period_prices": smile_prices,
    }


# ==================== 3. 定投模拟 ====================


def simulate_dca(price_sequence: list, interval_days: int, per_amount: float) -> dict:
    """
    在给定价格序列上模拟定投。

    参数：
        price_sequence : list[dict] — [{date, price}, ...]
        interval_days  : 定投间隔（天）
        per_amount     : 每期投入金额

    返回 dict:
        periods      : 实际投入期数
        total_invest : 累计投入
        total_shares : 累计份额（以价格为"单价"）
    """
    from datetime import datetime, timedelta

    if not price_sequence:
        return {"periods": 0, "total_invest": 0, "total_shares": 0}

    start_dt = datetime.strptime(price_sequence[0]["date"], "%Y-%m-%d")
    end_dt = datetime.strptime(price_sequence[-1]["date"], "%Y-%m-%d")

    # 价格查找表（日期 → 价格）
    price_map = {p["date"]: p["price"] for p in price_sequence}
    sorted_dates = sorted(price_map.keys())

    periods = 0
    total_invest = 0.0
    total_shares = 0.0
    current = start_dt

    while current <= end_dt:
        day_str = current.strftime("%Y-%m-%d")
        # 找当天或之后最近的价格
        target = day_str
        if target not in price_map:
            later = [d for d in sorted_dates if d >= day_str]
            if not later:
                break
            target = later[0]

        price = price_map[target]
        shares = per_amount / price
        total_invest += per_amount
        total_shares += shares
        periods += 1
        current += timedelta(days=interval_days)

    return {
        "periods": periods,
        "total_invest": round(total_invest, 2),
        "total_shares": round(total_shares, 4),
    }


# ==================== 4. 核心分析 ====================


def analyze_investment_plan(etf_code: str, total_amount: float,
                            interval_days: int = 14, per_amount: float = 500) -> dict:
    """
    分析给定总投资金额能否覆盖一条完整微笑曲线。

    参数：
        etf_code      : ETF代码（如 510580, 510300）
        total_amount  : 总投资金额（元）
        interval_days : 定投间隔天数（默认14）
        per_amount    : 每期投入金额（默认500）

    返回 dict:
        etf_code, etf_name     : ETF 信息
        total_amount           : 总预算
        per_amount             : 每期金额
        interval_days          : 间隔天数
        max_drawdown_pct       : 历史最大跌幅(%)
        drawdown_start         : 回撤起始日
        drawdown_end           : 回撤谷底日
        recovery_date          : 恢复日（或数据末日）
        recovered              : 是否已恢复
        smile_months           : 完整微笑曲线所需月数
        smile_periods          : 完整微笑曲线所需期数
        smile_total_invest     : 完整微笑曲线所需总投入
        plan_a / plan_b        : 两个方案（仅在资金不足时存在）
        sufficient             : 资金是否充足
    """
    if etf_code not in ETF_INDEX_MAP:
        supported = ", ".join(f"{k}({v['name']})" for k, v in ETF_INDEX_MAP.items())
        return {"error": f"不支持的 ETF 代码 {etf_code}，当前支持: {supported}"}

    info = ETF_INDEX_MAP[etf_code]
    etf_name = info["name"]
    index_code = info["index_code"]

    # 1. 拉取历史数据
    print(f"[微笑曲线] 拉取{etf_name}({index_code}) 近5年历史数据...")
    history = fetch_index_history(index_code)

    if len(history) < 20:
        return {"error": f"历史数据不足（仅{len(history)}条），请检查数据源"}

    print(f"[微笑曲线] 获取 {len(history)} 条日线数据 "
          f"({history[0]['date']} ~ {history[-1]['date']})")

    # 2. 找最大回撤完整周期
    dd = find_max_drawdown_cycle(history)
    smile_prices = dd["smile_period_prices"]

    # 计算月数
    from datetime import datetime
    d0 = datetime.strptime(dd["peak_date"], "%Y-%m-%d")
    d1 = datetime.strptime(dd["recovery_date"], "%Y-%m-%d")
    smile_months = round((d1 - d0).days / 30.44, 1)

    # 3. 模拟原始定投计划
    sim = simulate_dca(smile_prices, interval_days, per_amount)
    smile_periods = sim["periods"]
    smile_total = sim["total_invest"]

    print(f"[微笑曲线] 最大回撤: {dd['drawdown_pct']}%  "
          f"({dd['peak_date']} → {dd['trough_date']})")
    print(f"[微笑曲线] 完整微笑曲线: {smile_periods} 期, "
          f"需 ¥{smile_total:,.0f}, 约 {smile_months} 个月")

    # 4. 判断资金是否充足
    result = {
        "etf_code": etf_code,
        "etf_name": etf_name,
        "total_amount": total_amount,
        "per_amount": per_amount,
        "interval_days": interval_days,
        "max_drawdown_pct": dd["drawdown_pct"],
        "drawdown_start": dd["peak_date"],
        "drawdown_trough": dd["trough_date"],
        "drawdown_end": dd["recovery_date"],
        "recovered": dd["recovered"],
        "smile_months": smile_months,
        "smile_periods": smile_periods,
        "smile_total_invest": smile_total,
        "sufficient": total_amount >= smile_total,
    }

    if total_amount >= smile_total:
        result["surplus"] = round(total_amount - smile_total, 2)
        print(f"[微笑曲线] ✓ 资金充足！剩余 ¥{result['surplus']:,.0f}")
    else:
        gap = smile_total - total_amount
        result["shortage"] = round(gap, 2)

        # 方案 A：降低每期金额，使预算刚好覆盖完整微笑曲线
        # per_amount_a = total / N_smile 是使预算恰好撑满 N_smile 期的最大金额
        per_amount_a = max(1, math.floor(total_amount / smile_periods))
        sim_a = simulate_dca(smile_prices, interval_days, per_amount_a)

        result["plan_a"] = {
            "per_amount": per_amount_a,
            "periods": sim_a["periods"],
            "total_invest": sim_a["total_invest"],
            "months": smile_months,
        }

        # 方案 B：保持每期金额，追加总投资（向上取整到百）
        additional = math.ceil(gap / 100) * 100
        result["plan_b"] = {
            "additional_amount": additional,
            "new_total": round(total_amount + additional, 2),
            "per_amount": per_amount,
            "periods": smile_periods,
        }

        print(f"[微笑曲线] ✗ 资金不足！缺口 ¥{gap:,.0f}")

    return result


# ==================== 5. 格式化输出 ====================


def print_analysis(result: dict):
    """格式化打印分析结果。"""
    if "error" in result:
        print(f"\n[错误] {result['error']}")
        return

    print("\n" + "=" * 56)
    print(f"  {result['etf_name']}（{result['etf_code']}）微笑曲线覆盖度分析")
    print("=" * 56)

    print(f"  投资参数")
    print(f"    总金额        : ¥{result['total_amount']:,.0f}")
    print(f"    每期金额      : ¥{result['per_amount']:.0f}")
    print(f"    定投间隔      : {result['interval_days']} 天")

    print(f"\n  历史最大回撤")
    print(f"    最大跌幅      : {result['max_drawdown_pct']}%")
    print(f"    回撤起始      : {result['drawdown_start']}")
    print(f"    回撤谷底      : {result['drawdown_trough']}")
    rec_tag = "" if result["recovered"] else "（截至数据末日未完全恢复）"
    print(f"    恢复日期      : {result['drawdown_end']}{rec_tag}")
    print(f"    持续时长      : 约 {result['smile_months']} 个月")

    print(f"\n  完整微笑曲线")
    print(f"    所需期数      : {result['smile_periods']} 期")
    print(f"    所需总投入    : ¥{result['smile_total_invest']:,.0f}")

    if result["sufficient"]:
        print(f"\n  ✓ 资金充足！")
        print(f"    覆盖后剩余  : ¥{result['surplus']:,.0f}")
    else:
        print(f"\n  ✗ 资金不足！缺口 ¥{result['shortage']:,.0f}")
        pa = result["plan_a"]
        pb = result["plan_b"]
        print(f"\n  方案 A：降低每期金额")
        print(f"    每期金额      : ¥{pa['per_amount']}")
        print(f"    可覆盖期数    : {pa['periods']} 期")
        print(f"    实际投入      : ¥{pa['total_invest']:,.0f}")
        print(f"    覆盖时长      : 约 {pa['months']} 个月")
        print(f"\n  方案 B：追加总投资（假设情景，需出资人同意）")
        print(f"    需追加        : ¥{pb['additional_amount']:,.0f}")
        print(f"    新总金额      : ¥{pb['new_total']:,.0f}")
        print(f"    每期保持      : ¥{pb['per_amount']:.0f}")
        print(f"    可覆盖期数    : {pb['periods']} 期")

    print("=" * 56)


# ==================== CLI ====================


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="微笑曲线覆盖度分析")
    parser.add_argument("--etf", default="510580", help="ETF代码（默认 510580）")
    parser.add_argument("--amount", type=float, default=10000, help="总投资金额（默认 10000）")
    parser.add_argument("--interval", type=int, default=14, help="定投间隔天数（默认 14）")
    parser.add_argument("--per", type=float, default=500, help="每期金额（默认 500）")
    args = parser.parse_args()

    result = analyze_investment_plan(
        etf_code=args.etf,
        total_amount=args.amount,
        interval_days=args.interval,
        per_amount=args.per,
    )
    print_analysis(result)
