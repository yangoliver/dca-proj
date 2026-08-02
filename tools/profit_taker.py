"""
profit_taker.py — 三档止盈状态机（对齐第三课）
================================================
规则（第三课·第五步）：
  第一档：浮盈 >= 25% -> 卖剩余一半
  第二档：第一档卖价再涨 10% -> 卖剩余一半
  第三档：浮盈曾达 +30%，从最高点回撤 >= 10% -> 清剩余全部，本轮结束

状态：0=未止盈 -> 1=已卖一半 -> 2=已卖3/4 -> 3=本轮结束
重置：state==3 时，下一次 add_purchase 触发 reset()

卖出基数 = 总份额 - 累计已卖（从 sell_records 求和）
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# -- 路径 --
TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS_DIR)

from recorder import get_all_records
from config import ETF_CODE, ETF_NAME

STATE_FILE = os.path.join(TOOLS_DIR, "profit_taker_state.json")

# -- 止盈参数（第三课） --
PROFIT_TRIGGER = 0.25   # 第一档：浮盈 >= 25%
RISE_TRIGGER   = 0.10   # 第二档：再涨 10%
MOVE_TRIGGER   = 0.30   # 第三档前置：浮盈曾达 +30%
DRAWDOWN_PCT   = 0.10   # 第三档：从最高点回撤 >= 10%

STATE_NAMES = ["未止盈", "已卖一半", "已卖3/4", "本轮结束"]


# ==================== 状态读写 ====================

def _load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return _initial_state()


def _initial_state() -> dict:
    return {
        "state": 0,
        "trigger2_price": 0,
        "highest_price": 0,
        "avg_cost_at_sell": 0,
        "sell_records": [],
    }


def _save_state(state: dict):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


# ==================== 持仓数据 ====================

def _get_holdings() -> dict:
    try:
        records = get_all_records()
    except Exception:
        records = []
    if not records:
        return {"total_shares": 0, "total_invest": 0, "avg_cost": 0, "records_count": 0}
    last = records[-1]
    total_shares = float(last["累计份额"])
    total_invest = float(last["累计投入"])
    avg_cost = total_invest / total_shares if total_shares > 0 else 0
    return {
        "total_shares": total_shares,
        "total_invest": total_invest,
        "avg_cost": avg_cost,
        "records_count": len(records),
    }


def _get_remaining_shares(state_data: dict) -> float:
    """剩余持仓 = 总份额 - 累计已卖"""
    holdings = _get_holdings()
    cumulative_sold = sum(r["shares"] for r in state_data.get("sell_records", []))
    return holdings["total_shares"] - cumulative_sold


# ==================== 核心函数 ====================

def check(current_price: float) -> dict:
    """
    判断当前是否需要止盈（唯一副作用：更新 highest_price）。

    返回 dict:
        action, profit_pct, state, state_name, trigger,
        sell_shares, sell_amount, message
    """
    holdings = _get_holdings()
    state_data = _load_state()

    if holdings["total_shares"] <= 0:
        return {
            "action": "继续定投", "profit_pct": 0, "state": 0,
            "state_name": "未止盈", "trigger": False,
            "sell_shares": 0, "sell_amount": 0,
            "message": "持仓为空，请先买入",
        }

    avg_cost = holdings["avg_cost"]
    profit_pct = (current_price - avg_cost) / avg_cost
    state = state_data["state"]
    remaining = _get_remaining_shares(state_data)

    # 更新 highest_price
    if current_price > state_data.get("highest_price", 0):
        state_data["highest_price"] = current_price
        _save_state(state_data)

    result = {
        "action": "", "profit_pct": round(profit_pct * 100, 2),
        "state": state, "state_name": STATE_NAMES[state],
        "trigger": False, "sell_shares": 0, "sell_amount": 0, "message": "",
    }

    if state == 0:
        if profit_pct >= PROFIT_TRIGGER:
            sell = remaining / 2
            result.update({
                "action": "卖一半（第一档）", "trigger": True,
                "sell_shares": round(sell, 2),
                "sell_amount": round(sell * current_price, 2),
                "message": f"浮盈 {profit_pct*100:.2f}% >= 25%，触发第一档，建议卖 {sell:.0f} 份",
            })
        else:
            need = PROFIT_TRIGGER * 100 - profit_pct * 100
            result.update({
                "action": "继续持有",
                "message": f"浮盈 {profit_pct*100:.2f}%，距第一档还差 {need:.2f}%",
            })

    elif state == 1:
        trigger2 = state_data["trigger2_price"]
        if current_price >= trigger2:
            sell = remaining / 2
            result.update({
                "action": "再卖一半（第二档）", "trigger": True,
                "sell_shares": round(sell, 2),
                "sell_amount": round(sell * current_price, 2),
                "message": f"价格 {current_price:.3f} >= 触发价 {trigger2:.3f}，触发第二档，建议卖 {sell:.0f} 份",
            })
        else:
            gap = (trigger2 - current_price) / current_price * 100
            result.update({
                "action": "持有等待",
                "message": f"已卖一半，距第二档还差 {gap:.2f}%（需涨到 {trigger2:.3f}）",
            })

    elif state == 2:
        highest = state_data.get("highest_price", 0)
        # 前置条件：历史最高价曾达 +30%（不要求当前仍 >= 30%）
        highest_profit = (highest - avg_cost) / avg_cost if avg_cost > 0 else 0
        if highest_profit >= MOVE_TRIGGER and highest > 0:
            drawdown = round((highest - current_price) / highest, 6)
            if drawdown >= DRAWDOWN_PCT:
                sell = remaining
                result.update({
                    "action": "移动止盈（第三档）", "trigger": True,
                    "sell_shares": round(sell, 2),
                    "sell_amount": round(sell * current_price, 2),
                    "message": f"从最高点 {highest:.3f} 回撤 {drawdown*100:.1f}% >= 10%，清剩余 {sell:.0f} 份，本轮结束",
                })
            else:
                result.update({
                    "action": "持有等待（移动止盈监控中）",
                    "message": f"最高 {highest:.3f}(曾+{highest_profit*100:.1f}%)，当前回撤 {drawdown*100:.1f}%（需 >= 10%）",
                })
        else:
            result.update({
                "action": "持有等待",
                "message": f"最高价 {highest:.3f} 未达第三档前置（需曾涨到 +30%，即 >= {avg_cost*1.30:.3f}）",
            })

    elif state == 3:
        result.update({
            "action": "本轮已结束",
            "message": "本轮止盈已完成，等待下一次买入后自动重置",
        })

    return result


def record_sell(sell_date: str, price: float, shares: float, cond: str):
    """记录一次止盈卖出并推进状态。"""
    state_data = _load_state()
    holdings = _get_holdings()

    state_data["sell_records"].append({
        "date": sell_date, "price": price, "shares": shares,
        "amount": round(shares * price, 2), "condition": cond,
    })

    if state_data["state"] == 0:
        state_data["state"] = 1
        state_data["trigger2_price"] = round(price * (1 + RISE_TRIGGER), 4)
        state_data["avg_cost_at_sell"] = holdings["avg_cost"]
    elif state_data["state"] == 1:
        state_data["state"] = 2
    elif state_data["state"] == 2:
        state_data["state"] = 3

    _save_state(state_data)
    print(f"[止盈记录] {sell_date} | 卖出 {shares:.0f} 份 @ {price:.3f} | "
          f"条件: {cond} | 金额: {shares * price:,.2f} | 状态 -> {state_data['state']}")


def reset():
    """重置止盈状态（新一轮开始）。"""
    _save_state(_initial_state())
    print("[止盈状态] 已重置为「未止盈」，新一轮开始")


# ==================== CLI ====================

def cli():
    import argparse
    parser = argparse.ArgumentParser(description="三档止盈判断工具")
    parser.add_argument("price", nargs="?", type=float, help="当前价格")
    parser.add_argument("--sell", action="store_true", help="记录卖出")
    parser.add_argument("--sell-date", type=str, help="卖出日期")
    parser.add_argument("--sell-shares", type=float, help="卖出份额")
    parser.add_argument("--sell-cond", type=str, default="第一档", help="触发条件")
    parser.add_argument("--reset", action="store_true", help="重置状态")
    parser.add_argument("--history", action="store_true", help="查看历史")
    args = parser.parse_args()

    if args.reset:
        reset()
        return

    if args.history:
        state_data = _load_state()
        records = state_data.get("sell_records", [])
        if not records:
            print("[止盈历史] 暂无卖出记录")
        else:
            print("\n" + "=" * 60)
            for i, r in enumerate(records, 1):
                print(f"  {i}. {r['date']} | {r['condition']} | "
                      f"{r['shares']:.0f}份 @ {r['price']:.3f} | {r['amount']:,.2f}元")
            print("=" * 60)
        return

    if args.sell:
        if args.price is None:
            print("[错误] 需要指定价格")
            return
        from datetime import date
        sell_date = args.sell_date or date.today().isoformat()
        shares = args.sell_shares or _get_remaining_shares(_load_state()) / 2
        record_sell(sell_date, args.price, shares, args.sell_cond)
        return

    if args.price is None:
        print("用法: python profit_taker.py <价格>")
        print("      python profit_taker.py --history")
        print("      python profit_taker.py --reset")
        return

    result = check(args.price)
    holdings = _get_holdings()

    print("\n" + "=" * 52)
    print(f"  {ETF_NAME}（{ETF_CODE}）止盈状态")
    print("=" * 52)
    print(f"  当前价格  : {args.price:.3f} 元")
    print(f"  平均成本  : {holdings['avg_cost']:.4f} 元")
    print(f"  持仓份额  : {holdings['total_shares']:.0f} 份")
    print(f"  剩余可卖  : {_get_remaining_shares(_load_state()):.0f} 份")
    print("  " + "-" * 31)
    print(f"  浮盈      : {result['profit_pct']:.2f}%")
    print(f"  状态      : {result['state_name']}")
    print(f"  触发止盈  : {'是' if result['trigger'] else '否'}")
    print(f"  建议操作  : {result['action']}")
    if result["sell_shares"] > 0:
        print(f"  建议卖出  : {result['sell_shares']:.0f} 份（{result['sell_amount']:,.2f}元）")
    print("  " + "-" * 31)
    print(f"  {result['message']}")
    print("=" * 52)


if __name__ == "__main__":
    cli()
