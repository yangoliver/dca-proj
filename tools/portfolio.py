"""
portfolio.py — 持仓分析 + PE 估值查询（双ETF版本）

功能：
1. analyze(etf_code)       — 分析所有历史持仓（总份额/总投入/均价/浮盈浮亏）
2. get_price_now(etf_code) — 用新浪接口获取指定 ETF 当前价格
3. get_pe_data(etf_code)   — 用乐咕 PE 接口获取对应指数当前估值和历史分位
"""

import os
import sys
from datetime import date
from typing import Optional

import requests
import pandas as pd
import akshare as ak

# 本地模块
from config import ETF_CODE, ETF_NAME, get_etf_config
from recorder import get_all_records


# ==================== 0. SSL 自愈（云端沙箱 CA 缺失兜底）====================

# 系统 CA 证书候选路径（macOS / Debian·Ubuntu / RHEL 系）
_SYSTEM_CA_PATHS = (
    "/etc/ssl/cert.pem",
    "/etc/ssl/certs/ca-certificates.crt",
    "/etc/pki/tls/certs/ca-bundle.crt",
)

# 是否已发生过 SSL 证书校验失败（下游库据此提前套用系统 CA）
_ssl_fallback_triggered = False


def _system_ca_bundle() -> Optional[str]:
    """返回本机可用的系统 CA bundle 路径，找不到返回 None。"""
    for path in _SYSTEM_CA_PATHS:
        if os.path.exists(path):
            return path
    return None


def _activate_system_ca() -> bool:
    """
    把系统 CA 写入 requests / akshare 共用的环境变量。

    akshare 内部用自己的 requests 会话，无法逐调用传参，只能靠
    REQUESTS_CA_BUNDLE / SSL_CERT_FILE 生效；只在本进程内设置，不影响外部。

    返回：是否成功启用（无系统 CA 时返回 False）
    """
    global _ssl_fallback_triggered
    ca = _system_ca_bundle()
    if not ca:
        return False
    # 强制覆盖：走到这里说明默认校验已失败，环境里既有的 REQUESTS_CA_BUNDLE
    # 很可能就是坏的那个，setdefault 会让兜底失效
    os.environ["REQUESTS_CA_BUNDLE"] = ca
    os.environ["SSL_CERT_FILE"] = ca
    _ssl_fallback_triggered = True
    return True


def _http_get(url: str, headers: Optional[dict] = None, timeout: int = 10):
    """
    带 SSL 兜底的 GET：证书校验失败时依次尝试「系统 CA」→「关闭校验」。

    背景（2026-11-03）：云端沙箱 Python 的 certifi 证书链失效
    （CERTIFICATE_VERIFY_FAILED），腾讯/新浪/乐咕三个接口全部连不上，
    巡检只能降级为「行情不可用」。本函数让代码在 CA 环境异常时自愈，
    不依赖人工改沙箱环境。

    安全说明：关闭校验仅作为最后一层，且只用于公开只读行情接口
    （无凭据、无写入），风险可接受；每次降级都会打印告警。
    """
    try:
        return requests.get(url, headers=headers, timeout=timeout)
    except (requests.exceptions.SSLError, requests.exceptions.ConnectionError) as e:
        # urllib3 有时把证书错误包成 ConnectionError，用错误标记兜住这两种形态
        if "SSLError" not in type(e).__name__ and "CERTIFICATE_VERIFY_FAILED" not in str(e):
            raise
        print(f"[SSL] 证书校验失败，尝试系统 CA: {e}")

    if _activate_system_ca():
        ca = os.environ["REQUESTS_CA_BUNDLE"]
        try:
            r = requests.get(url, headers=headers, timeout=timeout, verify=ca)
            print(f"[SSL] 已改用系统 CA 成功: {ca}")
            return r
        except Exception as e:
            print(f"[SSL] 系统 CA 仍失败: {e}")

    print("[SSL] 告警：降级为不校验证书（仅公开行情接口，无凭据无写入）")
    try:
        import urllib3

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    except Exception:
        pass
    return requests.get(url, headers=headers, timeout=timeout, verify=False)


def _ak_call(fn, **kwargs):
    """
    调用 akshare 接口，SSL 证书失败时自动套用系统 CA 重试一次。

    akshare 内部自建 requests 会话、没有 verify 参数入口，
    只能通过 REQUESTS_CA_BUNDLE 环境变量生效。
    """
    try:
        return fn(**kwargs)
    except Exception as e:
        msg = f"{type(e).__name__}: {e}"
        if "CERTIFICATE_VERIFY_FAILED" in msg or "SSLError" in msg:
            if _activate_system_ca():
                print(f"[SSL] akshare 证书校验失败，改用系统 CA 重试")
                return fn(**kwargs)
        raise


# 指数代码映射（akshare PE/PB 用中文名，指数点位用代码）
INDEX_CODE_MAP = {
    "中证500": "000905",
    "沪深300": "000300",
}


# ==================== 1. 持仓分析 ====================


def analyze(etf_code: str = ETF_CODE) -> dict:
    """
    读取所有历史买入记录，计算当前持仓状态。

    参数：
        etf_code : str — ETF 代码（默认 510580）

    返回：
        dict，包含：
            records_count  : 记录条数
            total_shares   : 累计份额（份）
            total_invest   : 累计投入（元）
            avg_cost       : 平均成本（元/份）
            latest_price   : 最新价格（从新浪拉）
            market_value   : 市值（元）
            pnl_value      : 浮盈/浮亏（元）
            pnl_pct        : 浮盈/浮亏（%）
    """
    records = get_all_records(etf_code=etf_code)

    if not records:
        print("[警告] 持仓记录为空，请先运行 add_purchase()")
        return {}

    # 累计份额和投入（直接取最后一条记录的值，更可靠）
    last = records[-1]
    total_shares = float(last["累计份额"])
    total_invest = float(last["累计投入"])

    # 平均成本 = 累计投入 ÷ 累计份额
    avg_cost = total_invest / total_shares if total_shares > 0 else 0

    # 获取最新价格
    latest_price = get_price_now(etf_code=etf_code)
    if latest_price is None:
        print("[警告] 无法获取最新价格，请检查网络")
        latest_price = 0

    # 市值和盈亏
    market_value = total_shares * latest_price
    pnl_value = market_value - total_invest
    pnl_pct = (pnl_value / total_invest * 100) if total_invest > 0 else 0

    result = {
        "records_count": len(records),
        "total_shares": total_shares,
        "total_invest": total_invest,
        "avg_cost": avg_cost,
        "latest_price": latest_price,
        "market_value": market_value,
        "pnl_value": pnl_value,
        "pnl_pct": pnl_pct,
    }

    etf_cfg = get_etf_config(etf_code)
    _print_analyze_result(result, etf_code, etf_cfg["name"])
    return result


def _print_analyze_result(r: dict, etf_code: str, etf_name: str):
    """格式化打印持仓分析结果。"""
    pnl_str = f"+¥{r['pnl_value']:.2f}" if r['pnl_value'] >= 0 else f"-¥{abs(r['pnl_value']):.2f}"
    pnl_pct_str = f"+{r['pnl_pct']:.2f}%" if r['pnl_pct'] >= 0 else f"{r['pnl_pct']:.2f}%"

    print("\n" + "=" * 48)
    print(f"  {etf_name}（{etf_code}）持仓分析")
    print("=" * 48)
    print(f"  累计买入次数  : {r['records_count']} 次")
    print(f"  累计份额      : {r['total_shares']:.0f} 份")
    print(f"  累计投入      : ¥{r['total_invest']:.2f}")
    print(f"  平均成本      : ¥{r['avg_cost']:.4f} /份")
    print(f"  ─────────────────────────────")
    print(f"  最新价格      : ¥{r['latest_price']:.3f} /份")
    print(f"  当前市值      : ¥{r['market_value']:.2f}")
    print(f"  浮盈/浮亏    : {pnl_str}（{pnl_pct_str}）")
    print("=" * 48)


# ==================== 2. 实时价格（新浪接口）====================


def _get_price_tencent(etf_code: str) -> float:
    """
    腾讯行情接口取现价（主源）。

    格式：v_sh510580="1~中证500ETF~510580~现价~昨收~今开~...";（~ 分隔，
    fields[3]=现价，2026-11-02 经新浪/腾讯双源对照确认）。

    选为主源的原因（2026-11-02）：
    - 新浪 hq.sinajs.cn 对云端沙箱 IP 风控（403），腾讯对云 IP 友好；
    - 盘前（9:30 前）新浪现价返回 0.000，腾讯用昨收充当现价，全时段可用。

    异常：
        请求失败、字段解析失败时抛出异常，由 get_price_now 捕获降级。
    """
    url = f"https://qt.gtimg.cn/q=sh{etf_code}"
    r = _http_get(url, timeout=10)
    r.raise_for_status()
    content = r.text
    start = content.find('"') + 1
    end = content.find('"', start)
    fields = content[start:end].split("~")
    price = float(fields[3])
    if price <= 0:
        raise ValueError(f"腾讯返回异常价格: {price}")
    return price


def _get_price_sina(etf_code: str) -> float:
    """
    新浪行情接口取现价（兜底源）。

    字段序：名称,今开,昨收,现价,最高,最低,...（逗号分隔，
    fields[3]=现价；fields[1] 是今开——2026-11-02 经腾讯行情对照确认）。

    异常：
        请求失败、字段解析失败时抛出异常，由 get_price_now 捕获。
    """
    url = f"https://hq.sinajs.cn/list=sh{etf_code}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://finance.sina.com.cn/",
    }
    r = _http_get(url, headers=headers, timeout=10)
    r.raise_for_status()
    content = r.text
    # 找等号后的引号内容
    start = content.find('"') + 1
    end = content.find('"', start)
    fields = content[start:end].split(",")
    price = float(fields[3])
    if price <= 0:
        raise ValueError(f"新浪返回异常价格: {price}")
    return price


def get_price_now(etf_code: str = ETF_CODE) -> Optional[float]:
    """
    获取指定 ETF 当前价格：腾讯为主源，失败自动降级到新浪行情。

    源顺序（2026-11-02 定）：腾讯为主——对云端 IP 友好（新浪 403 风控）、
    盘前也有价（新浪盘前现价为 0）；新浪为兜底。

    参数：
        etf_code : str — ETF 代码（默认 510580）

    返回：
        float — 当前价格（元/份），两源均失败返回 None
    """
    try:
        return _get_price_tencent(etf_code)
    except Exception as e:
        print(f"[腾讯行情失败，降级新浪] sh{etf_code}: {e}")
    try:
        return _get_price_sina(etf_code)
    except Exception as e:
        print(f"[价格获取失败] 腾讯/新浪均不可用 sh{etf_code}: {e}")
        return None


# ==================== 3. PE 估值数据（乐咕接口）====================


def get_pe_data(etf_code: str = ETF_CODE) -> dict:
    """
    用乐咕乐股 akshare 接口获取对应指数当前估值和历史分位。

    参数：
        etf_code : str — ETF 代码（默认 510580），自动路由到对应指数

    数据源：akshare.stock_index_pe_lg(symbol=指数名)
            akshare.stock_index_pb_lg(symbol=指数名)

    返回：
        dict，包含：
            pe_ttm       : 滚动PE(TTM)
            pe_static    : 静态PE
            pb           : 市净率
            index_point  : 指数点位
            pe_5y_pct    : 近5年分位（%）
            pe_5y_high   : 近5年最高PE
            pe_5y_low    : 近5年最低PE
            pe_10y_pct   : 近10年分位（%）
    """
    etf_cfg = get_etf_config(etf_code)
    index_name = etf_cfg["index"]
    index_code = INDEX_CODE_MAP.get(index_name, "")

    print(f"\n[PE数据] 正在从乐咕乐股获取{index_name}估值...")

    # 若本进程内已发生过 SSL 证书失败，提前给 akshare 套系统 CA（它无 verify 参数入口）
    if _ssl_fallback_triggered:
        _activate_system_ca()

    try:
        # 拉PE历史
        df_pe = _ak_call(ak.stock_index_pe_lg, symbol=index_name)
        df_pe["日期_dt"] = pd.to_datetime(df_pe["日期"])

        # 拉PB（最新一期）
        df_pb = _ak_call(ak.stock_index_pb_lg, symbol=index_name)
        latest_pb = df_pb.iloc[-1]["市净率"]

        # 最新一行 = 当前数据
        latest = df_pe.iloc[-1]
        pe_ttm = float(latest["滚动市盈率"])
        pe_static = float(latest["静态市盈率"])
        index_point = float(latest["指数"])
        pe_date = latest["日期"]

        # 近5年数据（动态窗口）
        cutoff_5y = pd.Timestamp.now() - pd.DateOffset(years=5)
        df_5y = df_pe[df_pe["日期_dt"] >= cutoff_5y]["滚动市盈率"].dropna()

        # 近10年数据（动态窗口）
        cutoff_10y = pd.Timestamp.now() - pd.DateOffset(years=10)
        df_10y = df_pe[df_pe["日期_dt"] >= cutoff_10y]["滚动市盈率"].dropna()

        # 计算分位
        pct_5y = (df_5y < pe_ttm).sum() / len(df_5y) * 100
        pct_10y = (df_10y < pe_ttm).sum() / len(df_10y) * 100

        # 近5年高低点（从5年窗口内找）
        pe_5y_high = float(df_5y.max())
        pe_5y_low = float(df_5y.min())
        high_date = df_pe.loc[df_5y.idxmax(), "日期"]
        low_date = df_pe.loc[df_5y.idxmin(), "日期"]

        result = {
            "pe_date": pe_date,
            "index_point": index_point,
            "index_name": index_name,
            "index_code": index_code,
            "pe_ttm": pe_ttm,
            "pe_static": pe_static,
            "pb": float(latest_pb),
            "pe_5y_pct": round(pct_5y, 1),
            "pe_5y_high": pe_5y_high,
            "pe_5y_low": pe_5y_low,
            "pe_10y_pct": round(pct_10y, 1),
            "pe_5y_high_date": high_date if isinstance(high_date, str) else str(high_date),
            "pe_5y_low_date": low_date if isinstance(low_date, str) else str(low_date),
        }

        _print_pe_result(result)
        return result

    except Exception as e:
        print(f"[PE数据获取失败] {e}")
        return {}


def _print_pe_result(r: dict):
    """格式化打印PE数据。"""
    index_name = r.get("index_name", "中证500")
    index_code = r.get("index_code", "000905")
    print("\n" + "=" * 50)
    print(f"  {index_name}（{index_code}）估值数据  [{r['pe_date']}]")
    print("=" * 50)
    print(f"  指数点位      : {r['index_point']:.2f}")
    print(f"  滚动PE(TTM)  : {r['pe_ttm']:.2f}")
    print(f"  静态PE        : {r['pe_static']:.2f}")
    print(f"  市净率(PB)    : {r['pb']:.2f}")
    print(f"  ─────────────────────────────")
    print(f"  近5年PE分位  : {r['pe_5y_pct']:.1f}%  （{r['pe_5y_low']:.2f} ~ {r['pe_5y_high']:.2f}）")
    print(f"  近10年PE分位 : {r['pe_10y_pct']:.1f}%")
    print(f"  近5年最高PE  : {r['pe_5y_high']:.2f}（{r['pe_5y_high_date'][:10]}）")
    print(f"  近5年最低PE  : {r['pe_5y_low']:.2f}（{r['pe_5y_low_date'][:10]}）")
    print("=" * 50)


# ==================== 一键总览 ====================


def summary(etf_code: str = ETF_CODE):
    """一键查看完整持仓状态（含PE估值）。"""
    etf_cfg = get_etf_config(etf_code)
    print("\n" + "=" * 56)
    print(f"  {etf_cfg['name']}（{etf_code}）定投持仓总览")
    print("=" * 56)

    analyze(etf_code=etf_code)
    get_pe_data(etf_code=etf_code)


# ==================== 测试 ====================
if __name__ == "__main__":
    summary()
