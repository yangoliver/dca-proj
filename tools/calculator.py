"""
calculator.py — 弹性股数法

核心逻辑：
ETF 最小买卖单位是「手」（1手 = 100份），
所以不能直接用 500 ÷ 单价 算出精确份数。
需要先算出最多能买几手，再反推实际花的钱和剩余滚存。

公式：
    手数 = floor(定投金额 ÷ (单价 × 100))
    实际份额 = 手数 × 100
    实际花费 = 实际份额 × 单价
    滚存 = 定投金额 - 实际花费
"""


def calculate_shares(amount: float, price: float) -> dict:
    """
    弹性股数法：给定金额和单价，计算最优买入方案。

    参数：
        amount : float  — 本期定投金额（元），例如 500
        price  : float  — 当前ETF单价（元/份），例如 3.885

    返回：
        dict，包含以下键：
            hands      : int     — 买入多少手（1手=100份）
            shares     : int     — 买入多少份
            cost       : float   — 实际花费（元）
            remainder  : float   — 剩余滚存（元）
            unit_price : float   — 单价（回显）
            amount     : float   — 原始定投金额（回显）
    """
    if price <= 0:
        raise ValueError("单价必须大于0")

    # 每手 = 100份
    LOT_SIZE = 100

    # 最多能买几手（向下取整，不能超出预算）
    hands = int(amount // (price * LOT_SIZE))

    # 实际买到的份数
    shares = hands * LOT_SIZE

    # 实际花掉的钱
    cost = shares * price

    # 剩余未投入的零头
    remainder = round(amount - cost, 2)

    return {
        "hands":     hands,
        "shares":    shares,
        "cost":      round(cost, 2),
        "remainder": remainder,
        "unit_price": price,
        "amount":     amount,
    }


def print_result(result: dict) -> None:
    """格式化打印计算结果（供命令行查看）"""
    r = result
    print("=" * 40)
    print(f"  弹性股数法计算结果")
    print("=" * 40)
    print(f"  单价        : ¥{r['unit_price']:.3f} /份")
    print(f"  定投金额    : ¥{r['amount']:.2f}")
    print(f"  ─────────────────────────────")
    print(f"  可买手数    : {r['hands']} 手")
    print(f"  实际份额    : {r['shares']} 份")
    print(f"  实际花费    : ¥{r['cost']:.2f}")
    print(f"  剩余滚存    : ¥{r['remainder']:.2f}")
    print("=" * 40)

    if r['remainder'] > 0:
        print(f"  → ¥{r['remainder']:.2f} 元滚存，下期一并投入")


if __name__ == "__main__":
    # 示例：模拟今日买入（2026-07-21，价格 ¥3.885）
    example_price = 3.885
    example_amount = 500

    result = calculate_shares(example_amount, example_price)
    print_result(result)
