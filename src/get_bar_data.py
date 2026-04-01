import datetime
import logging
import time

from api.api import get_symbol_bar_data
from data.sqllite import insert_bar_data, get_last_bar_data
from src import state
# from api.api import get_symbol_bar_data


def get_bar_data():
    """你的核心业务逻辑（持续运行的任务）"""
    test_logger = logging.getLogger("test_logger")
    logger = logging.getLogger("get_bar_data")
    test_logger.info(f"✅ get bar data任务启动 | 时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 循环执行核心逻辑，直到标志位被置为False

    test_logger.info(f"is_task_running: {state.is_task_running}")
    while state.is_task_running:
        test_logger.info(f"is_in_a_period: {state.is_in_a_period}")
        test_logger.info(f"state.t_symbols: {state.t_symbols}")
        for symbol in state.t_symbols:
            last_bar_data=state.t_last_bar_data.get(symbol["symbol"],None)
            if last_bar_data or last_bar_data is None:
                last_bar_data=get_last_bar_data(symbol["symbol"])
            exchange = symbol["exchange"]
            if exchange=="a" and state.is_in_a_period:
                bar_data=get_symbol_bar_data(exchange,symbol["pre_fix"]+symbol["symbol"])
                if bar_data and len(bar_data)>0:
                    new_bar_data={
                        "symbol": symbol["symbol"],
                        "timestamp": bar_data["timestamp"],
                        "date": bar_data["date"],
                        "time": bar_data["time"],
                        "price": bar_data["price"],
                        "pre_close": bar_data["pre_close"],
                        "open": bar_data["open"],
                        "highest": bar_data["highest"],
                        "lowest": bar_data["lowest"],
                        "volume": bar_data["volume"]-last_bar_data["total_volume"] if last_bar_data else bar_data["volume"],
                        "turnover": bar_data["turnover"]-last_bar_data["total_turnover"] if last_bar_data else bar_data["turnover"],
                        "total_volume": bar_data["volume"],
                        "total_turnover": bar_data["turnover"],
                    }
                    insert_bar_data(new_bar_data)
                    logger.info(f"insert bar data: {new_bar_data}")
                    state.t_last_bar_data[symbol["symbol"]]=new_bar_data
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        test_logger.info(f"get bar data任务运行中 | 当前时间: {current_time}")

            # 获取所有股票代码
            # symbol_list = get_symbol_bar_data()



        time.sleep(5)  # 模拟业务执行间隔，根据你的需求调整

    test_logger.info(f"❌ get bar data任务停止 | 时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
