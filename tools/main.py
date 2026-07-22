"""
main.py — 定投工具 v1.0 主入口

功能菜单：
1. 执行定投  — 查价→计算→记录→显示持仓→标记日历
2. 查看持仓  — 显示累计份额/成本/浮盈浮亏
3. 历史记录  — 显示所有买入流水
4. PE 估值   — 显示中证500当前估值和分位
5. 定投日历  — 显示全部20期双周计划
0. 退出

运行：python main.py
"""

import os
import sys
import io
from datetime import datetime, date

# 中文输出不乱码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 本地模块
import config
from calculator import calculate_shares, print_result
from recorder  import add_purchase, get_all_records, print_records
from portfolio  import analyze, get_price_now, get_pe_data, summary
from scheduler  import generate_schedule, init_schedule, mark_done, print_schedule

# ==================== 路径处理 ====================
# main.py 在 tools/ 下，portfolio.xlsx 放在项目根目录
TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(TOOLS_DIR)
EXCEL_FILE = os.path.join(PROJECT_DIR, config.EXCEL_PATH)

# 修正 recorder / scheduler 的路径引用
import recorder, scheduler
recorder.EXCEL_PATH = EXCEL_FILE
scheduler.EXCEL_PATH = EXCEL_FILE

# ==================== 辅助函数 ====================


def print_header():
    print("\n" + "=" * 54)
    print(f"  {config.ETF_NAME}（{config.ETF_CODE}）定投工具 v1.0")
    print("=" * 54)


def get_valid_price() -> float:
    """获取有效价格，支持手动输入或自动查询。"""
    print("\n[查价] 正在从新浪获取实时价格...")
    price = get_price_now()
    if price is not None:
        print(f"  当前价格：¥{price:.3f} /份")
        confirm = input("  使用此价格？(Y/手动输入): ").strip()
        if confirm.lower() != "y" and confirm != "":
            try:
                price = float(confirm)
                print(f"  已改用手动输入价格 ¥{price:.3f}")
            except ValueError:
                print("  输入无效，使用自动价格 ¥{:.3f}".format(price))
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
    print("  ▶ 执行定投")
    print("=" * 54)

    # Step 1：查价
    price = get_valid_price()

    # Step 2：计算
    result = calculate_shares(config.DCA_AMOUNT, price)
    print_result(result)

    # Step 3：确认执行
    confirm = input("\n  确认以此价格买入？(Y/N): ").strip()
    if confirm.lower() != "y":
        print("  [取消] 本次定投未执行")
        return

    # Step 4：手续费（估算，固定5元，保留2位小数）
    fee = 5.00

    # Step 5：累计投入/份额（读取现有记录）
    records = get_all_records()
    if records:
        total_invest  = float(records[-1]["累计投入"]) + result["cost"] + fee
        total_shares  = int(records[-1]["累计份额"])  + result["shares"]
    else:
        total_invest  = result["cost"] + fee
        total_shares  = result["shares"]

    # Step 6：写入 Excel
    today_str = date.today().strftime("%Y-%m-%d")
    remark = f"弹性股数法，滚存¥{result['remainder']:.2f}"
    add_purchase(
        buy_date     = today_str,
        buy_price    = price,
        shares       = result["shares"],
        cost         = result["cost"],
        fee          = fee,
        total_invest = round(total_invest, 2),
        total_shares = total_shares,
        remark       = remark,
    )

    # Step 7：初始化日历（如尚未初始化）
    init_schedule(config.FIRST_DATE, config.TOTAL_COUNT, EXCEL_FILE)

    # Step 8：计算期数并标记日历
    # 期数 = 已有记录数（含本次）
    period_no = len(get_all_records())
    mark_done(
        no           = period_no,
        actual_date  = today_str,
        actual_price = price,
        actual_shares= result["shares"],
        remark       = remark,
        excel_path   = EXCEL_FILE,
    )

    # Step 9：显示当前持仓
    print("\n  → 更新后持仓：")
    analyze()

    print(f"\n  ✅ 第{period_no}期定投完成！")


# ==================== 选项2~5 ====================


def option_view_portfolio():
    print_header()
    print("  ▶ 查看持仓")
    analyze()
    pause()


def option_view_records():
    print_header()
    print("  ▶ 历史记录")
    records = get_all_records()
    if not records:
        print("  [空] 暂无买入记录")
    else:
        print_records()
    pause()


def option_view_pe():
    print_header()
    print("  ▶ PE 估值")
    get_pe_data()
    pause()


def option_view_calendar():
    print_header()
    print("  ▶ 定投日历")
    # 确保日历已初始化
    init_schedule(config.FIRST_DATE, config.TOTAL_COUNT, EXCEL_FILE)
    print_schedule(config.FIRST_DATE, config.TOTAL_COUNT)
    pause()


# ==================== 主循环 ====================


def main():
    # 确保 portfolio.xlsx 存在（至少有一个 sheet）
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
  ╔══════════════════════════════════════╗
  ║     定投工具 v1.0  — 主菜单         ║
  ╠══════════════════════════════════════╣
  ║  1. 执行定投（买入 → 记录 → 标记）  ║
  ║  2. 查看持仓（份额/成本/盈亏）      ║
  ║  3. 历史记录（全部买入流水）         ║
  ║  4. PE 估值（中证500分位/高低点）   ║
  ║  5. 定投日历（20期计划）            ║
  ║  0. 退出                             ║
  ╚══════════════════════════════════════╝
  """
    while True:
        print_header()
        print(menu)
        choice = input("  请选择（0-5）: ").strip()

        if   choice == "1": option_execute_dca()
        elif choice == "2": option_view_portfolio()
        elif choice == "3": option_view_records()
        elif choice == "4": option_view_pe()
        elif choice == "5": option_view_calendar()
        elif choice == "0":
            print("\n  再见！坚持纪律，定投成功 🚀\n")
            break
        else:
            print("\n  [无效] 请输入 0~5 之间的数字")


if __name__ == "__main__":
    main()
