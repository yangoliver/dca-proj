"""
config.py — 定投工具配置（双ETF版本）

支持的 ETF：
  - 510580 易方达中证500ETF
  - 510300 华泰柏瑞沪深300ETF

使用说明：
1. ETF_LIST 中定义每只 ETF 的名称、跟踪指数、首期日期、定投金额
2. 公共参数（周期、手续费等）对所有 ETF 生效
3. 旧变量 ETF_CODE / ETF_NAME 保留为默认值，向后兼容
"""

# ==================== ETF 列表 ====================

ETF_LIST = {
    "510580": {
        "name": "易方达中证500ETF",
        "index": "中证500",
        "first_date": "2026-07-20",
        "amount": 500,
    },
    "510300": {
        "name": "华泰柏瑞沪深300ETF",
        "index": "沪深300",
        "first_date": "2026-08-31",
        "amount": 500,
    },
}

# 默认 ETF（向后兼容：现有工具不改参数也能跑）
DEFAULT_ETF = "510580"
ETF_CODE = DEFAULT_ETF
ETF_NAME = ETF_LIST[DEFAULT_ETF]["name"]

# ==================== 辅助函数 ====================


def get_etf_config(etf_code: str) -> dict:
    """
    获取指定 ETF 的配置。

    参数：
        etf_code : str — ETF 代码，如 "510580"

    返回：
        dict — 包含 name, index, first_date, amount
    """
    if etf_code not in ETF_LIST:
        supported = ", ".join(ETF_LIST.keys())
        raise ValueError(f"不支持的 ETF 代码 {etf_code}，当前支持: {supported}")
    return ETF_LIST[etf_code]


def sheet_name(etf_code: str, kind: str) -> str:
    """
    返回 Excel sheet 名称。

    参数：
        etf_code : str  — ETF 代码
        kind     : str  — "buy" 或 "schedule"

    返回：
        str — 如 "510580_买入记录" 或 "510580_定投日历"
    """
    if kind == "buy":
        return f"{etf_code}_买入记录"
    elif kind == "schedule":
        return f"{etf_code}_定投日历"
    else:
        raise ValueError(f"kind 必须是 'buy' 或 'schedule'，收到 '{kind}'")


# ==================== 公共配置（所有 ETF 共享） ====================

# 每期定投金额（元）— 未指定 etf_code 时的默认值
DCA_AMOUNT = 500

# 第一期定投日期（格式：YYYY-MM-DD）— 默认 ETF 的首期
FIRST_DATE = "2026-07-20"

# 定投周期（天）
DCA_INTERVAL_DAYS = 14

# Excel文件路径（相对项目根目录）
EXCEL_PATH = "data/portfolio.xlsx"

# 定投日历总期数
TOTAL_COUNT = 20

# 手续费参数（动态计算：max(成交额 * FEE_RATE, FEE_MIN)）
FEE_RATE = 0.00025   # 万2.5
FEE_MIN = 5.0        # 最低5元
