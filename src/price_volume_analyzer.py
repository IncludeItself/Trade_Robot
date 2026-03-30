import logging

import pandas as pd
import numpy as np
from typing import Dict, Literal
from src import state

# ======================
# 全局配置（实盘最优参数）
# ======================
WINDOWS = {
    "short": 10,   # 短周期：即时盘口变化
    "middle": 30,  # 中周期：主力资金趋势
    "long": 60     # 长周期：阶段趋势
}

# 阈值（可根据股票波动率微调）
PRICE_CHANGE_THRESHOLD = 0.01  # 1% 以上算明显涨跌
VOLUME_CHANGE_THRESHOLD = 0.2   # 20% 以上算放量/缩量
TREND_SLOPE_THRESHOLD = 0.0005  # 价格斜率阈值

def analyze_market_status(bar_data: list,symbol: Dict) -> Dict:
    """
    核心分析函数：输入盘口数据表，输出完整状态+买卖信号
    :param symbol: 股票代码字典，包含"symbol"和"platform"等
    :param bar_data: 包含 timestamp, price, pre_close, volume, turnover, highest, lowest
    :return: 完整分析结果字典
    """
    # ======================
    # 1. 数据预处理（必须）
    # ======================
    test_logger = logging.getLogger("test_logger")
    if bar_data is None or len(bar_data) <WINDOWS["long"]:
        return {"signal": "Wait", "reason": "数据量不足，无法分析","price":0}
    test_logger.info(f"length of bar_data in analyze_market_status：{len(bar_data)}")
    df = pd.DataFrame(bar_data)


    # 基础计算
    df["price_change"] = df["price"].pct_change()  # 价格瞬时涨跌幅
    df["cum_volume"] = df["total_volume"]                 # 接口给的是累计成交量，直接用

    # ======================
    # 2. 多窗口指标计算
    # ======================
    result = {}

    for name, window in WINDOWS.items():
        if len(df) < window:
            continue

        # 取窗口数据
        win_df = df.tail(window)
        prices = win_df["price"].values
        volumes = win_df["volume"].values  # 瞬时成交量
        returns = win_df["price_change"].fillna(0).values

        # ========== 价格指标 ==========
        # 区间涨跌幅
        pct_change = (prices[-1] - prices[0]) / prices[0]
        # 价格变化速率（线性回归斜率）
        x = np.arange(len(prices))
        slope = np.polyfit(x, prices, 1)[0] / prices.mean()  # 标准化斜率
        # 成交量加权移动平均（VWMA）
        # VWMA = Σ(price × volume) / Σvolume
        volume_weights = win_df["volume"].values  # 使用累计成交量作为权重
        total_volume = volume_weights.sum()
        if total_volume > 0:
            ma = np.sum(prices * volume_weights) / total_volume
        else:
            ma = prices.mean()

        # ========== 成交量指标 ==========
        # 窗口平均成交量
        avg_vol = volumes.mean()
        # 最近1条成交量 vs 窗口平均
        latest_vol_ratio = volumes[-1] / avg_vol if avg_vol != 0 else 1
        # 单位涨幅成交量（量价配合度）
        total_pct = sum(returns)
        vol_per_pct = sum(volumes) * np.sign(total_pct) / abs(total_pct) if abs(total_pct) > 0.0001 else 0

        # 存储窗口结果
        result[f"{name}_window"] = {
            "avg_vol": round(avg_vol, 2),
            "pct_change": round(pct_change, 4),
            "slope": round(slope, 6),
            "ma_price": round(ma, 2),
            "latest_vol_ratio": round(latest_vol_ratio, 2),
            "vol_per_pct": round(vol_per_pct, 2)
        }

    # ======================
    # 3. 核心状态判断
    # ======================
    short = result.get("short_window", {})
    middle = result.get("middle_window", {})
    long_ = result.get("long_window", {})

    avg_volume=df.iloc[-1]["volume"]/len(df) if len(df) > 0 else 0
    lowest=df.iloc[-1]["lowest"] if len(df) > 0 else 0
    highest=df.iloc[-1]["highest"] if len(df) > 0 else 0

    # vol_status 判断
    vol_status = ""
    if long_.get("avg_vol", 0)*symbol["volume_step_rate"]*symbol["volume_step_rate"]>middle.get("avg_vol", 0)*symbol["volume_step_rate"]>short.get("avg_vol",0):
        vol_status = "缩量"
    if long_.get("avg_vol")<avg_volume*symbol["volume_step_rate"]:
        vol_status = "缩量"

    # price_status 判断
    price_status = ""
    test_logger.info(f"df.iloc[-1][price]:{lowest}, lowest: {lowest}, highest: {highest}")
    if df.iloc[-1]["price"]/lowest-1>float(symbol["percent_to_lowest"]):
        price_status = "涨"
    if df.iloc[-1]["price"]/highest-1<float(symbol["percent_to_highest"]):
        price_status = "跌"

    signal = "Wait"
    reason = ""
    if price_status=="涨" and vol_status=="缩量":
        signal = "Sell"
        reason = "缩量上涨"
    if price_status=="跌" and vol_status=="缩量":
        signal = "Buy"
        reason = "缩量下跌"

    final_result = {
        "current_price": round(df["price"].iloc[-1], 2),
        "vol_status": vol_status,
        "price_status": price_status,
        # "vol_price_match": vol_price_match,
        "signal": signal,
        "reason": reason,
        "window_data": result,
        "price": df["price"].iloc[-1]
    }

    return final_result

# ======================
# 【你的程序调用示例】
# ======================
if __name__ == "__main__":
    # 模拟你的全局变量 state.tbl_bar_data
    import time
    test_data = {
        "timestamp": [time.time() - i for i in range(70)],
        "price": np.random.normal(10.0, 0.1, 70).cumsum(),
        "pre_close": [10.0] * 70,
        "open": np.random.normal(10.0, 0.05, 70),
        "highest": np.random.normal(10.1, 0.1, 70),
        "lowest": np.random.normal(9.9, 0.1, 70),
        "volume": np.arange(1000, 1070, 1),
        "turnover": np.arange(10000, 10700, 1)
    }
    # 你的全局变量
    state = type('obj', (object,), {
        'tbl_bar_data': pd.DataFrame(test_data)
    })

    # 调用分析
    analysis = analyze_market_status(state.tbl_bar_data)

    # 打印结果
    print("="*50)
    print("📊 股票实时盘口分析结果")
    print("="*50)
    print(f"当前价格: {analysis['current_price']}")
    print(f"量能状态: {analysis['vol_status']}")
    print(f"价格状态: {analysis['price_status']}")
    print(f"量价关系: {analysis['vol_price_match']}")
    print(f"\n🔥 交易信号: {analysis['signal']}")
    print(f"💡 原因: {analysis['reason']}")
    print("="*50)