"""
dashboard.py — 实盘成本/市值/盈亏图（独立脚本）
================================================
读取 portfolio.xlsx，生成：
  - 成本线（累计投入）
  - 市值线（份额 x 当期价格）
  - 盈亏面积图

输出：tools/output/dashboard.png

运行：python dashboard.py
"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(TOOLS_DIR)
sys.path.insert(0, TOOLS_DIR)

# 路径修正：portfolio.xlsx 在项目根目录
import recorder
recorder.EXCEL_PATH = os.path.join(PROJECT_DIR, "portfolio.xlsx")

OUTPUT_DIR = os.path.join(TOOLS_DIR, "output")


def generate_dashboard():
    """生成成本/市值/盈亏图"""
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
        print("[dashboard] 无买入记录，跳过")
        return None

    # 获取当前价格
    price = get_price_now()
    if not price:
        print("[dashboard] 无法获取当前价格，使用最后买入价")
        price = float(records[-1]["买入价格"])

    # 构建数据
    periods = list(range(1, len(records) + 1))
    cum_invest = [float(r["累计投入"]) for r in records]
    cum_shares = [float(r["累计份额"]) for r in records]
    market_value = [s * price for s in cum_shares]
    pnl = [mv - ci for mv, ci in zip(market_value, cum_invest)]

    # 绘图
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    # 上图：成本线 + 市值线
    ax1.plot(periods, cum_invest, "b-o", markersize=4, label="累计投入")
    ax1.plot(periods, market_value, "r-s", markersize=4, label=f"市值(价格{price:.3f})")
    ax1.set_ylabel("金额(元)")
    ax1.set_title("510580 定投实盘：成本 vs 市值")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # 下图：盈亏面积图
    colors = ["green" if p >= 0 else "red" for p in pnl]
    ax2.bar(periods, pnl, color=colors, alpha=0.6)
    ax2.axhline(y=0, color="black", linewidth=0.5)
    ax2.set_xlabel("期数")
    ax2.set_ylabel("盈亏(元)")
    ax2.set_title("每期浮盈/浮亏")
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()

    # 保存
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, "dashboard.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"[dashboard] 图表已保存: {out_path}")
    return out_path


if __name__ == "__main__":
    generate_dashboard()
