"""
profit_taker.py — 止盈判断工具（项目级）
========================================
功能：
1. check(current_price) — 输入当前价格，返回止盈判断结果
2. record_sell(...)     — 记录一次止盈卖出
3. CLI                  — 运行后显示当前止盈状态和建议操作

数据来源：
  - 持仓均价：从 portfolio.xlsx（通过 recorder.py）
  - 卖出记录 / 状态：tools/profit_taker_state.json
"""
import json
import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ── 路径 ──
TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS_DIR)

from recorder import get_all_records
from config import ETF_CODE, ETF_NAME

STATE_FILE = os.path.join(TOOLS_DIR, 'profit_taker_state.json')

# ── 止盈参数 ──
PROFIT_TRIGGER = 0.25   # 浮盈 ≥ 25% 触发第一档
RISE_TRIGGER   = 0.10   # 再涨 10% 触发第二档


# ==================== 状态读写 ====================

def _load_state() -> dict:
    """读取止盈状态文件，不存在则返回初始状态。"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding='utf-8') as f:
            return json.load(f)
    return {
        'state': 0,           # 0=未止盈, 1=已卖一半, 2=已卖3/4
        'trigger2_price': 0,  # 第二档触发价
        'avg_cost_at_sell': 0,  # 触发止盈时的均价（用于重置判断）
        'sell_records': [],   # 历史卖出记录
    }


def _save_state(state: dict):
    """保存止盈状态。"""
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


# ==================== 持仓数据 ====================

def _get_holdings() -> dict:
    """
    从 portfolio.xlsx 读取当前持仓。

    返回：
        dict: {total_shares, total_invest, avg_cost, records_count}
    """
    try:
        records = get_all_records()
    except Exception as e:
        print(f"[警告] 读取 portfolio.xlsx 失败: {e}")
        records = []
    if not records:
        return {'total_shares': 0, 'total_invest': 0, 'avg_cost': 0, 'records_count': 0}

    last = records[-1]
    total_shares = float(last['累计份额'])
    total_invest = float(last['累计投入'])
    avg_cost = total_invest / total_shares if total_shares > 0 else 0

    return {
        'total_shares': total_shares,
        'total_invest': total_invest,
        'avg_cost': avg_cost,
        'records_count': len(records),
    }


# ==================== 核心函数 ====================

def check(current_price: float) -> dict:
    """
    判断当前是否需要止盈。

    参数：
        current_price : float — 当前价格（元/份）

    返回：
        dict:
            action       : str  — "继续定投" / "卖一半" / "再卖一半" / "持有等待"
            profit_pct   : float — 当前浮盈（%）
            state        : int   — 当前止盈状态（0/1/2）
            state_name   : str   — 状态中文名
            trigger      : bool  — 是否触发止盈
            sell_shares  : float — 建议卖出份额（0=不卖）
            sell_amount  : float — 建议卖出金额（0=不卖）
            message      : str  — 说明文字
    """
    holdings = _get_holdings()
    state_data = _load_state()

    if holdings['total_shares'] <= 0:
        return {
            'action': '继续定投',
            'profit_pct': 0,
            'state': 0,
            'state_name': '未止盈',
            'trigger': False,
            'sell_shares': 0,
            'sell_amount': 0,
            'message': '持仓为空，请先买入',
        }

    avg_cost = holdings['avg_cost']
    shares = holdings['total_shares']
    profit_pct = (current_price - avg_cost) / avg_cost * 100
    state = state_data['state']

    result = {
        'action': '',
        'profit_pct': round(profit_pct, 2),
        'state': state,
        'state_name': ['未止盈', '已卖一半', '已卖四分之三'][state],
        'trigger': False,
        'sell_shares': 0,
        'sell_amount': 0,
        'message': '',
    }

    if state == 0:
        # 未止盈 → 检查是否达到 25%
        if profit_pct >= PROFIT_TRIGGER * 100:
            sell = shares / 2
            result.update({
                'action': '卖一半',
                'trigger': True,
                'sell_shares': round(sell, 2),
                'sell_amount': round(sell * current_price, 2),
                'message': f'浮盈 {profit_pct:.2f}% ≥ 25%，触发第一档止盈，建议卖出 {sell:.0f} 份',
            })
        else:
            need = PROFIT_TRIGGER * 100 - profit_pct
            result.update({
                'action': '继续定投',
                'message': f'浮盈 {profit_pct:.2f}%，距止盈还差 {need:.2f}%',
            })

    elif state == 1:
        # 已卖一半 → 检查是否再涨 10%
        trigger2 = state_data['trigger2_price']
        if current_price >= trigger2:
            sell = shares / 2
            result.update({
                'action': '再卖一半',
                'trigger': True,
                'sell_shares': round(sell, 2),
                'sell_amount': round(sell * current_price, 2),
                'message': f'价格 {current_price:.3f} ≥ 触发价 {trigger2:.3f}，触发第二档止盈，建议卖出 {sell:.0f} 份',
            })
        else:
            gap = (trigger2 - current_price) / current_price * 100
            result.update({
                'action': '持有等待',
                'message': f'已卖一半，价格距第二档触发价还差 {gap:.2f}%（需涨到 {trigger2:.3f}）',
            })

    elif state == 2:
        # 已卖 3/4 → 等浮盈回落到 25% 以下重置
        if profit_pct < PROFIT_TRIGGER * 100:
            result.update({
                'action': '继续定投',
                'message': f'浮盈回落至 {profit_pct:.2f}%，止盈周期重置，等待下一轮',
            })
            # 自动重置状态
            state_data['state'] = 0
            _save_state(state_data)
        else:
            result.update({
                'action': '持有等待',
                'message': f'浮盈仍为 {profit_pct:.2f}%，等待回落至 25% 以下重置',
            })

    return result


def record_sell(sell_date: str, price: float, shares: float, cond: str):
    """
    记录一次止盈卖出。

    参数：
        sell_date : str   — 卖出日期 YYYY-MM-DD
        price     : float — 卖出价格
        shares    : float — 卖出份额
        cond      : str   — 触发条件（如 "浮盈>=25%" 或 "再涨10%"）
    """
    state_data = _load_state()
    holdings = _get_holdings()

    # 记录卖出
    state_data['sell_records'].append({
        'date': sell_date,
        'price': price,
        'shares': shares,
        'amount': round(shares * price, 2),
        'condition': cond,
    })

    # 更新状态
    if state_data['state'] == 0:
        state_data['state'] = 1
        state_data['trigger2_price'] = price * (1 + RISE_TRIGGER)
        state_data['avg_cost_at_sell'] = holdings['avg_cost']
    elif state_data['state'] == 1:
        state_data['state'] = 2

    _save_state(state_data)

    print(f"[止盈记录] {sell_date} | 卖出 {shares:.0f} 份 @ {price:.3f} | "
          f"条件: {cond} | 金额: ¥{shares * price:,.2f}")


def reset():
    """重置止盈状态（新一轮）。"""
    state_data = _load_state()
    state_data['state'] = 0
    state_data['trigger2_price'] = 0
    _save_state(state_data)
    print("[止盈状态] 已重置为「未止盈」")


# ==================== CLI ====================

def cli():
    """命令行模式：显示当前止盈状态。"""
    import argparse

    parser = argparse.ArgumentParser(description='止盈判断工具')
    parser.add_argument('price', nargs='?', type=float, help='当前价格（元/份）')
    parser.add_argument('--sell', action='store_true', help='记录一次止盈卖出')
    parser.add_argument('--sell-date', type=str, help='卖出日期（默认今天）')
    parser.add_argument('--sell-cond', type=str, default='浮盈>=25%', help='触发条件')
    parser.add_argument('--reset', action='store_true', help='重置止盈状态')
    parser.add_argument('--history', action='store_true', help='查看历史卖出记录')
    args = parser.parse_args()

    # 重置
    if args.reset:
        reset()
        return

    # 查看历史
    if args.history:
        state_data = _load_state()
        records = state_data.get('sell_records', [])
        if not records:
            print("[止盈历史] 暂无卖出记录")
        else:
            print(f"\n{'=' * 60}")
            print(f"{'序号':^4} {'日期':^12} {'条件':^12} {'份额':^8} {'价格':^10} {'金额':^12}")
            print(f"{'=' * 60}")
            total_amount = 0
            for i, r in enumerate(records, 1):
                print(f"{i:^4} {r['date']:^12} {r['condition']:^12} "
                      f"{r['shares']:^8.0f} {r['price']:^10.3f} ¥{r['amount']:>10,.2f}")
                total_amount += r['amount']
            print(f"{'=' * 60}")
            print(f"累计止盈金额: ¥{total_amount:,.2f}")
        return

    # 记录卖出
    if args.sell:
        if args.price is None:
            print("[错误] 记录卖出需要指定价格，如: --sell --price 5.0")
            return
        from datetime import date
        sell_date = args.sell_date or date.today().isoformat()
        holdings = _get_holdings()
        state_data = _load_state()
        shares_to_sell = holdings['total_shares'] / 2
        record_sell(sell_date, args.price, shares_to_sell, args.sell_cond)
        return

    # 默认：检查止盈状态
    if args.price is None:
        print("[错误] 请提供当前价格，如: python profit_taker.py 5.0")
        print("       或查看历史: python profit_taker.py --history")
        return

    result = check(args.price)

    # 获取持仓信息
    holdings = _get_holdings()

    print(f"\n{'=' * 52}")
    print(f"  {ETF_NAME}（{ETF_CODE}）止盈状态")
    print(f"{'=' * 52}")
    print(f"  当前价格      : ¥{args.price:.3f} /份")
    print(f"  平均成本      : ¥{holdings['avg_cost']:.4f} /份")
    print(f"  持仓份额      : {holdings['total_shares']:.0f} 份")
    print(f"  ─────────────────────────────────")
    print(f"  当前浮盈      : {result['profit_pct']:.2f}%")
    print(f"  止盈状态      : {result['state_name']}")
    print(f"  是否触发止盈  : {'是' if result['trigger'] else '否'}")
    print(f"  建议操作      : {result['action']}")
    if result['sell_shares'] > 0:
        print(f"  建议卖出      : {result['sell_shares']:.0f} 份（¥{result['sell_amount']:,.2f}）")
    print(f"  ─────────────────────────────────")
    print(f"  {result['message']}")
    print(f"{'=' * 52}")


# ==================== 测试 ====================
if __name__ == '__main__':
    cli()
