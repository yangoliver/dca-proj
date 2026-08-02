"""
inspector.py — 每周巡检纯函数（方案B）
======================================
纯函数，无 input()，无业务副作用（不改 xlsx）。
check() 更新 highest_price 属"观测追踪"，非业务动作。
可被 Cron / Skill / main 任意调用。

五个检查点：
  B-1 准备：返回 ok（不需检查）
  B-2 建仓：已有 Day7 Cron，跳过
  B-3 持有 PE：>70% 提醒偏高，<30% 提醒低估
  B-4 止盈：调 profit_taker.check()，返回触发状态
  B-5 纪律：浮亏 >= 20% 推哨点 + 别跳投检查
"""
import os
import sys
from datetime import datetime, date

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(TOOLS_DIR)
sys.path.insert(0, TOOLS_DIR)

# 路径修正
import recorder
recorder.EXCEL_PATH = os.path.join(PROJECT_DIR, "data", "portfolio.xlsx")

EXCEL_FILE = os.path.join(PROJECT_DIR, "data", "portfolio.xlsx")


def _check_skip() -> str:
    """
    别跳投检查：定投日已过但无对应买入记录 -> warn_skip。
    读 Sheet3 计划 + Sheet1 记录，纯读取不写。
    """
    try:
        import openpyxl
        if not os.path.exists(EXCEL_FILE):
            return "ok"
        wb = openpyxl.load_workbook(EXCEL_FILE, read_only=True)

        # 读 Sheet3 计划
        if "Sheet3" not in wb.sheetnames:
            wb.close()
            return "ok"
        ws3 = wb["Sheet3"]
        today = date.today()
        overdue_periods = []
        for row in ws3.iter_rows(min_row=2, values_only=True):
            if not row or row[0] is None:
                continue
            no = int(row[0])
            planned_str = str(row[1]) if row[1] else ""
            status = str(row[4]) if row[4] else ""
            if "已完成" in status:
                continue
            try:
                planned_date = datetime.strptime(planned_str, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                continue
            if planned_date < today:
                days_overdue = (today - planned_date).days
                overdue_periods.append((no, planned_str, days_overdue))

        wb.close()

        if overdue_periods:
            no, planned, days = overdue_periods[0]  # 报最近的一期
            return (f"warn_skip: 第{no}期(计划{planned})已过{days}天未买入，"
                    f"别跳投、按计划补齐")
        return "ok"
    except Exception:
        return "ok"


def inspect_once() -> dict:
    """
    执行全部巡检，返回结构化结论。

    返回 dict:
        price          : float  — 当前价
        pnl_pct        : float  — 浮盈亏比(%)
        profit_action  : str    — 止盈判断结论
        profit_trigger : bool   — 是否触发止盈
        pe_pct         : float  — PE 分位(%)
        pe_alert       : str    — PE 结论
        warning_20     : bool   — 浮亏>=20%?
        skip_alert     : str    — 别跳投结论
        summary        : str    — 一段话总结（可直接推微信）
    """
    from portfolio import get_price_now, get_pe_data
    import profit_taker

    result = {
        "price": 0,
        "pnl_pct": 0,
        "profit_action": "ok",
        "profit_trigger": False,
        "pe_pct": 0,
        "pe_alert": "ok",
        "warning_20": False,
        "skip_alert": "ok",
        "summary": "",
    }

    # B-1 准备：不需定时检查
    # B-2 建仓：已有 Day7 双周 Cron

    # 获取当前价格
    price = get_price_now()
    if price:
        result["price"] = price

    # B-3 持有 PE
    try:
        pe_data = get_pe_data()
        if pe_data and "pe_5y_pct" in pe_data:
            pe_pct = pe_data["pe_5y_pct"]
            result["pe_pct"] = pe_pct
            if pe_pct > 70:
                result["pe_alert"] = f"pe_high: 估值偏高({pe_pct:.1f}%)，仅提醒不触发卖出"
            elif pe_pct < 30:
                result["pe_alert"] = f"pe_low: 低估区间({pe_pct:.1f}%)，可分批加回"
            else:
                result["pe_alert"] = f"pe_normal: 估值中性({pe_pct:.1f}%)"
    except Exception:
        result["pe_alert"] = "pe_error: PE数据获取失败"

    # B-4 止盈
    if price and price > 0:
        try:
            pt_result = profit_taker.check(price)
            result["profit_action"] = pt_result["action"]
            result["profit_trigger"] = pt_result["trigger"]
            if pt_result["trigger"]:
                result["profit_action"] = (
                    f"sell_tier: {pt_result['action']}，"
                    f"建议卖 {pt_result['sell_shares']:.0f} 份"
                )
        except Exception:
            result["profit_action"] = "profit_error: 止盈检查失败"

    # B-5 纪律（浮亏哨点）
    try:
        records = recorder.get_all_records()
        if records and price and price > 0:
            last = records[-1]
            total_invest = float(last["累计投入"])
            total_shares = float(last["累计份额"])
            if total_shares > 0 and total_invest > 0:
                avg_cost = total_invest / total_shares
                pnl_pct = (price - avg_cost) / avg_cost * 100
                result["pnl_pct"] = round(pnl_pct, 2)
                if pnl_pct <= -20:
                    result["warning_20"] = True
    except Exception:
        pass

    # B-5 纪律（别跳投）
    result["skip_alert"] = _check_skip()

    # 生成 summary
    parts = []
    parts.append(f"本周巡检：当前价 {result['price']:.3f} 元")
    parts.append(f"浮盈亏 {result['pnl_pct']:.2f}%")
    parts.append(result["pe_alert"])

    if result["profit_trigger"]:
        parts.append(f"[触发] {result['profit_action']}")
    else:
        parts.append(f"止盈状态：{result['profit_action']}")

    if result["warning_20"]:
        parts.append("[预警] 浮亏超20%，请核对三件事：闲钱?现金流?纪律?——不卖，只看")

    if result["skip_alert"] != "ok":
        parts.append(f"[提醒] {result['skip_alert']}")

    result["summary"] = "。".join(parts) + "。不替你下单，只给结论。"

    return result


# 兼容旧名
check_all = inspect_once


if __name__ == "__main__":
    r = inspect_once()
    print(r["summary"])
