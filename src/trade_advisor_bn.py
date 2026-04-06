from ast import Dict
from api.bnapi import BnApi

def price_advice_bn(kline_data: list, symbol: Dict) -> dict:
    """
    专属高抛低吸策略：
    1. 涨到过去4小时高位 + 不放量 → 卖出
    2. 跌到过去4小时低位 + 不放量 → 买入
    3. 其他情况 → 观望
    """
    # ===================== 1. 数据校验 =====================

    bn=BnApi()
    current_price=0
    try:
        current_price = float(bn.client.futures_symbol_ticker(symbol=symbol["symbol"])["price"])
    except Exception as e:
        return{
            "signal": "Wait",
            "price": 0.0,
            "reason": f"获取{symbol['symbol']}当前价格失败，{e}"
        }


    if not kline_data or len(kline_data) < 12:
        return {
            "signal": "Wait",
            "price": 0.0,
            "reason": "K线数据不足，5分钟K线至少需要12根（=4小时）"
        }

    # ===================== 2. 基础数据 =====================
    last = kline_data[-1]         # 最新K线

    current_open = last["open"]
    current_high = last["highest"]
    current_low = last["lowest"]
    current_volume = last["volume"]

    # 最近1根K线之前的平均成交量（判断是否放量/不放量）
    recent_volumes = [k["volume"] for k in kline_data[-6:-1]]  # 取前5根
    avg_volume = sum(recent_volumes) / len(recent_volumes) if recent_volumes else 1

    # ===================== 3. 核心：过去4小时 高低位（12根5分钟K线） =====================
    hours_4_data = kline_data[-12:]  # 12根 = 4小时
    high_4h = max([k["highest"] for k in hours_4_data])  # 4小时最高位
    low_4h = min([k["lowest"] for k in hours_4_data])   # 4小时最低位

    # ===================== 4. 无量判断（核心） =====================
    # 不放量 = 当前成交量 ≤ 平均成交量的 1.0 倍（无量）
    no_volume_surge = current_volume <= avg_volume * 1.0

    # ===================== 5. 你的专属买卖规则 =====================
    # 卖出规则：涨到4小时高位附近 + 不放量
    step=(high_4h-low_4h)/4
    sell_condition = (current_price >= high_4h-step) and no_volume_surge

    # 买入规则：跌到4小时低位附近 + 不放量
    buy_condition = (current_price <= low_4h+step) and no_volume_surge

    # ===================== 6. 输出信号 =====================
    if sell_condition:
        signal = "Sell"
        reason = f"卖出：触及4小时高位({high_4h:.4f})，无量上涨，必然回落"
    elif buy_condition:
        signal = "Buy"
        reason = f"买入：触及4小时低位({low_4h:.4f})，无量下跌，跌无可跌"
    else:
        signal = "Wait"
        reason = f"观望：4小时区间【{low_4h:.4f} ~ {high_4h:.4f}】，无买卖点"

    # if signal == "Sell":
    #     put_price=current_price*1.0005
    # else:
    #     put_price=current_price*0.9995
    return {
        "signal": signal,
        "price": round(current_price, 3),
        "reason": reason
    }