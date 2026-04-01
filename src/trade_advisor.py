import logging
from typing import Dict

import numpy as np
import pandas as pd

from config.app_config import appConfig
from src import state
from src.state import get_period


# ======================
# 全局配置（实盘最优参数）
# ======================
WINDOWS = {
    "short": 10,   # 短周期：即时盘口变化
    "middle": 30,  # 中周期：主力资金趋势
    "long": 60     # 长周期：阶段趋势
}


def price_advice(bar_data: list,symbol: Dict):
    logger = logging.getLogger("price_advice")

    if bar_data is None or len(bar_data)==0:
        return {
            "signal":"Wait",
            "price":0,
            "reason":"",
        }

    df = pd.DataFrame(bar_data)
    result = {}
    for name, window in WINDOWS.items():
        if len(df) < window:
            continue
        # 取窗口数据
        win_df = df.tail(window)
        prices = win_df["price"].values
        volumes = win_df["volume"].values

        # ========== 价格指标 ==========
        # 区间最大涨幅
        pct_change = (prices[-1]-prices[0])/prices[0] if prices[0] != 0 else 0
        # 价格变化速率（线性回归斜率）
        x = np.arange(len(prices))
        slope = np.polyfit(x, prices, 1)[0] / prices.mean()  # 标准化斜率
        cum_volume=win_df.iloc[-1]["total_volume"]-win_df.iloc[0]["total_volume"]
        if cum_volume==0:
            ma=prices[-1]
        else:
            ma=(win_df.iloc[-1]["total_turnover"]-win_df.iloc[0]["total_turnover"])/cum_volume
        # ========== 成交量指标 ==========
        # 窗口平均成交量
        avg_vol = volumes.mean()
        vol_per_pct = sum(volumes)/pct_change if pct_change!=0 else 1

        # 存储窗口结果
        result[f"{name}_window"] = {
            "avg_vol": round(avg_vol, 2),
            "pct_change": round(pct_change, 4),
            "slope": round(slope, 6),
            "ma_price": round(ma, 2),
            "vol_per_pct": round(vol_per_pct, 2),
            "min": prices.min(),
            "max": prices.max(),
        }

    short = result.get("short_window", {})
    middle = result.get("middle_window", {})
    long_ = result.get("long_window", {})
    # 日级指标
    last_second = df.tail(1).iloc[0]
    last_day=state.get_last_bar_history(symbol["symbol"])
    lowest_2d = min(float(last_second["lowest"]), float(last_day["lowest"])) if last_day is not None else float(last_second["lowest"])
    highest_2d = max(float(last_second["highest"]), float(last_day["highest"])) if last_day is not None else float(last_second["highest"])
    vol_last=last_day.get("volume",0) if last_day is not None else 0
    if last_second["timestamp"] == df.iloc[0]["timestamp"]:
        expected_vol=0
    else:
        expected_vol=round(last_second["total_volume"]*get_period(symbol["exchange"])/(last_second["timestamp"]-df.iloc[0]["timestamp"]),2)

    volume_status=""
    if long_!={} and long_["avg_vol"]*2*2<middle["avg_vol"]*2<short["avg_vol"] and vol_last*2<expected_vol:
        volume_status="volume explode"
    elif long_!={} and long_["avg_vol"]>middle["avg_vol"]*2>short["avg_vol"]*2*2:
        volume_status="volume extremely shrink"


    if volume_status == "volume explode":
        return {
            "signal":"Wait",
            "price":last_second["price"],
            "reason":"长、中、短成交量翻倍中，主力停止后再操作"
        }

    step = (highest_2d - lowest_2d) / 5
    logger.info(f"两天最高价为{highest_2d},最低价为{lowest_2d},五分之一为：{step}")
    if highest_2d-step<last_second["price"]<highest_2d:
        return {
            "signal":"Sell",
            "price":last_second["price"],
            "reason":"价格处在两天第一五分位上，且没有明显放量，上涨动能不够"
        }
    if lowest_2d<last_second["price"]<lowest_2d+step:
        return {
            "signal":"Buy",
            "price":last_second["price"],
            "reason":"价格处在两天最后五分位上，且没有明显放量，下跌企稳"
        }
    step = (highest_2d - lowest_2d) / 4
    logger.info(f"两天最高价为{highest_2d},最低价为{lowest_2d},四分之一为：{step}")
    if volume_status == "volume extremely shrink" and highest_2d-step<last_second["price"]<highest_2d:
        return {
            "signal":"Sell",
            "price":last_second["price"],
            "reason":"价格处在两天第一四分位上，且明显缩量"
        }
    if volume_status == "volume extremely shrink" and lowest_2d<last_second["price"]<lowest_2d+step:
        return {
            "signal":"Buy",
            "price":last_second["price"],
            "reason":"价格处在两天最后四分位上，且明显缩量"
        }
    middle_break=(last_second["price"]-middle.get("min",0.0))/middle.get("min",0.0) if middle.get("min",0.0)!=0 else 0
    if middle_break>appConfig["break_up"] and short["avg_vol"]<middle["avg_vol"]:
        return {
            "signal":"Sell",
            "price":last_second["price"],
            "reason":f"中窗口上涨{round(middle_break,2)},且短窗口平均成交量：{short["avg_vol"]}，小于中窗口平均成交量：{middle["avg_vol"]}"
        }
    middle_dive=(last_second["price"]-middle.get("max",0.0))/middle.get("max",0.0) if middle.get("max",0.0)!=0 else 0
    if middle_dive<-appConfig["break_up"] and short["avg_vol"]<middle["avg_vol"]:
        return {
            "signal":"Buy",
            "price":last_second["price"],
            "reason":f"中窗口下跌{round(-middle_break,2)},且短窗口平均成交量：{short["avg_vol"]}，小于中窗口平均成交量：{middle["avg_vol"]}"
        }
    return {
        "signal":"Wait",
        "price":last_second["price"],
        "reason":"暂无明显的买卖点"
    }
    pass