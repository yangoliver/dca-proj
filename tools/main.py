"""
main.py — 定投工具 v2.0 主入口（Day8 修复版）

功能菜单：
1. 执行定投  — 查价->计算(含滚存)->记录->显示持仓->标记日历
2. 查看持仓  — 显示累计份额/成本/浮盈浮亏 + 浮亏20%预警
3. 历史记录  — 显示所有买入流水
4. PE 估值   — 显示中证500当前估值和分位 + 阈值提醒
5. 定投日历  — 显示全部20期双周计划（含已完成状态）
6. 判止盈   — 三档止盈判断（对齐第三课）
0. 退出

运行：python main.py
"""

import os
import sys
from datetime import datetime, date

# 中文输出不乱码（reconfigure 不关闭原 buffer）
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# 本地模块
import config
from calculator import calculate_shares, print_result
from recorder  import add_purchase, get_all_records, print_records
from portfolio  import analyze, get_price_now, get_pe_data, summary
from scheduler  import generate_schedule, init_schedule, mark_done, print_schedule

# ==================== 路径处理 ====================
TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(TOOLS_DIR)
EXCEL_FILE = os.path.join(PROJECT_DIR, config.EXCEL_PATH)

# 修正 recorder / scheduler 的路径引用
import recorder, scheduler
recorder.EXCEL_PATH = EXCEL_FILE
scheduler.EXCEL_PATH = EXCEL_FILE


# ==================== 辅助函数 ====================

def calc_fee(cost: float) -> float:
    """动态手续费：max(成交额 * 费率, 最低)"""
    return round(max(cost * config.FEE_RATE, config.FEE_MIN), 2)


def get_last_rollover() -> float:
    """读取上期滚存余额"""
    records = get_all_records()
    if not records:
        return 0.0
    last = records[-1]
    return float(last.get("累计滚存", 0) or 0)


def print_header():
    print("\n" + "=" * 54)
    print(f"  {config.ETF_NAME}（{config.ETF_CODE}）定投工具 v2.0")
    print("=" * 54)


def get_valid_price() -> float:
    """获取有效价格，支持手动输入或自动查询。"""
    print("\n[查价] 正在从新浪获取实时价格...")
    price = get_price_now()
    if price is not None:
        print(f"  当前价格：{price:.3f} 元/份")
        confirm = input("  使用此价格？(Y/手动输入): ").strip()
        if confirm.lower() != "y" and confirm != "":
            try:
                price = float(confirm)
                print(f"  已改用手动输入价格 {price:.3f} 元")
            except ValueError:
                print(f"  输入无效，使用自动价格 {price:.3f} 元")
    else:
        price = input("  网络获取失败，请手动输入当前价格: ").strip()
        try:
            price = float(price)
        except ValueError:
            print("[错误] 无效价格，退出")
            sys.exit(1)
    return price


def pause():
    input("\n  按回车继续...")


# ==================== 选项1：执行定投 ====================


def option_execute_dca():
    print_header()
    print("  > 执行定投")
    print("=" * 54)

    # Step 1：查价
    price = get_valid_price()

    # Step 2：滚存累积
    last_rollover = get_last_rollover()
    available = config.DCA_AMOUNT + last_rollover
    if last_rollover > 0:
        print(f"\n  [滚存] 上期余额 {last_rollover:.2f} 元，本期可用 {available:.2f} 元")

    # Step 3：计算
    result = calculate_shares(available, price)
    print_result(result)

    # Step 4：确认执行
    confirm = input("\n  确认以此价格买入？(Y/N): ").strip()
    if confirm.lower() != "y":
        print("  [取消] 本次定投未执行")
        return

    # Step 5：动态手续费
    fee = calc_fee(result["cost"])

    # Step 6：累计投入/份额
    records = get_all_records()
    if records:
        total_invest = float(records[-1]["累计投入"]) + result["cost"] + fee
        total_shares = int(records[-1]["累计份额"]) + result["shares"]
    else:
        total_invest = result["cost"] + fee
        total_shares = result["shares"]

    # Step 7：写入 Excel（含滚存）
    today_str = date.today().strftime("%Y-%m-%d")
    remark = f"弹性股数法，滚存{result['remainder']:.2f}元"
    add_purchase(
        buy_date     = today_str,
        buy_price    = price,
        shares       = result["shares"],
        cost         = result["cost"],
        fee          = fee,
        total_invest = round(total_invest, 2),
        total_shares = total_shares,
        rollover     = result["remainder"],
        remark       = remark,
    )

    # Step 8：初始化日历（如尚未初始化）
    init_schedule(config.FIRST_DATE, config.TOTAL_COUNT, EXCEL_FILE)

    # Step 9：计算期数并标记日历
    period_no = len(get_all_records())
    mark_done(
        no           = period_no,
        actual_date  = today_str,
        actual_price = price,
        actual_shares= result["shares"],
        remark       = remark,
        excel_path   = EXCEL_FILE,
    )

    # Step 10：显示当前持仓
    print("\n  -> 更新后持仓：")
    analyze()

    print(f"\n  [完成] 第{period_no}期定投完成！")


# ==================== 选项2：查看持仓（含浮亏预警） ====================


def option_view_portfolio():
    print_header()
    print("  > 查看持仓")
    analyze()

    # 浮亏20%预警哨点
    records = get_all_records()
    if records:
        price = get_price_now()
        if price:
            total_invest = float(records[-1]["累计投入"])
            total_shares = float(records[-1]["累计份额"])
            if total_shares > 0:
                avg_cost = total_invest / total_shares
                pnl_pct = (price - avg_cost) / avg_cost
                if pnl_pct <= -0.20:
                    print("\n  " + "!" * 50)
                    print("  !! 浮亏已超过 20%！请核对三件事：")
                    print("  !!  1. 这笔钱还是闲钱吗？（性质变了->可以停；没变->继续）")
                    print("  !!  2. 后续现金流还在吗？（断了->自然停；没断->继续）")
                    print("  !!  3. 纪律还在吗？（反复想'这次跳过'=事实上停扣）")
                    print("  !!  结论：不卖。浮亏不是卖出理由，只是提醒你别犯恐慌错。")
                    print("  " + "!" * 50)
    pause()


# ==================== 选项3~5 ====================


def option_view_records():
    print_header()
    print("  > 历史记录")
    records = get_all_records()
    if not records:
        print("  [空] 暂无买入记录")
    else:
        print_records()
    pause()


def option_view_pe():
    print_header()
    print("  > PE 估值")
    get_pe_data()
    pause()


def option_view_calendar():
    print_header()
    print("  > 定投日历")
    init_schedule(config.FIRST_DATE, config.TOTAL_COUNT, EXCEL_FILE)
    print_schedule(config.FIRST_DATE, config.TOTAL_COUNT)
    pause()


# ==================== 选项6：判止盈 ====================


def option_check_profit():
    print_header()
    print("  > 判止盈（三档状态机）")
    print("=" * 54)

    import profit_taker

    price = get_valid_price()
    result = profit_taker.check(price)

    print(f"\n  浮盈      : {result['profit_pct']:.2f}%")
    print(f"  状态      : {result['state_name']}")
    print(f"  触发止盈  : {'是' if result['trigger'] else '否'}")
    print(f"  建议操作  : {result['action']}")
    if result["sell_shares"] > 0:
        print(f"  建议卖出  : {result['sell_shares']:.0f} 份（{result['sell_amount']:,.2f}元）")
    print(f"\n  {result['message']}")

    if result["trigger"]:
        confirm = input("\n  是否记录本次卖出？(Y/N): ").strip()
        if confirm.lower() == "y":
            today_str = date.today().strftime("%Y-%m-%d")
            profit_taker.record_sell(
                today_str, price, result["sell_shares"], result["action"]
            )
            print("  [已记录] 卖出记录已保存")

    pause()


# ==================== 主循环 ====================


def main():
    # 确保 portfolio.xlsx 存在
    if not os.path.exists(EXCEL_FILE):
        from openpyxl import Workbook
        import recorder as _rec
        wb = Workbook()
        ws = wb.active
        ws.title = "Sheet1"
        _rec._write_headers(ws)
        wb.create_sheet("Sheet3")
        wb.save(EXCEL_FILE)
        print(f"[初始化] portfolio.xlsx 已创建于 {EXCEL_FILE}")

    menu = """
  +======================================+
  |     定投工具 v2.0  — 主菜单          |
  +======================================+
  |  1. 执行定投（买入 -> 记录 -> 标记） |
  |  2. 查看持仓（份额/成本/盈亏/预警） |
  |  3. 历史记录（全部买入流水）         |
  |  4. PE 估值（中证500分位/高低点）    |
  |  5. 定投日历（20期计划）             |
  |  6. 判止盈（三档状态机）             |
  |  0. 退出                             |
  +======================================+
  """
    while True:
        print_header()
        print(menu)
        choice = input("  请选择（0-6）: ").strip()

        if   choice == "1": option_execute_dca()
        elif choice == "2": option_view_portfolio()
        elif choice == "3": option_view_records()
        elif choice == "4": option_view_pe()
        elif choice == "5": option_view_calendar()
        elif choice == "6": option_check_profit()
        elif choice == "0":
            print("\n  再见！坚持纪律，定投成功\n")
            break
        else:
            print("\n  [无效] 请输入 0~6 之间的数字")


if __name__ == "__main__":
    main()
