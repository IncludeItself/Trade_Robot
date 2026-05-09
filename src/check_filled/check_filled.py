import logging
from datetime import datetime
import time


from data.sqllite import  get_filled_orders_symbol, update_tbl_filled_orders_symbol
from src import state
from src.check_filled.check_filled_bn import check_filled_bn
from src.check_filled.check_filled_ths import check_filled_ths
from src.common import clear_orders
from wecom.wecom import send_wecom_msg







def check_filled():
    """你的核心业务逻辑（持续运行的任务）"""
    test_logger = logging.getLogger("test_logger")
    logger = logging.getLogger("check_filled")
    test_logger.info(f"✅ check_filled任务启动 | 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    # 循环执行核心逻辑，直到标志位被置为False
    while state.is_task_running:
        for symbol_info in state.t_symbols:
            if symbol_info["platform"]=="ths" and state.is_in_a_period:
                if not check_filled_ths(symbol_info):
                    continue
            elif symbol_info["platform"]=="bn" and state.is_in_bn_period:
                if not check_filled_bn(symbol_info):
                    continue
            clear_orders(symbol_info["symbol"])
        time.sleep(6)  # 模拟业务执行间隔，根据你的需求调整

    print(f"❌ check_filled任务停止 | 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
