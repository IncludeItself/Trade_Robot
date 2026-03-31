import datetime
import logging
import threading

from data.excel_data import get_symbols_from_excel, get_grid
from data.sqllite import refresh_tbl_pending_order, refresh_tbl_bar_data, get_pending_orders, get_filled_orders, \
    get_last_bar_datas
from src.place_orders import place_orders
from src.check_filled import check_filled
from src.get_bar_data import get_bar_data
from src import state


# 全局标志位：控制核心任务的运行/停止
check_filled_thread = None  # 存储核心任务的线程对象
get_bar_data_thread = None
place_orders_thread = None

def daily_task():
    """每日任务，用于更新bar数据"""
    refresh_tbl_pending_order()
    refresh_tbl_bar_data()
    insert_bar_history()

def initialize():

    global check_filled_thread, get_bar_data_thread, place_orders_thread
    # 清理tbl_pending_order数据表
    daily_task()

    state.t_symbols=get_symbols_from_excel()
    state.t_pending_orders=get_pending_orders(state.t_symbols)
    state.t_filled_orders=get_filled_orders(state.t_symbols)
    # state.t_bar_data=get_bar_data_from_db(state.t_symbols)
    state.t_grid=get_grid(state.t_symbols)
    state.t_last_bar_data=get_last_bar_datas(state.t_symbols)

    state.is_task_running = True
    # 启动新线程运行核心任务（避免阻塞调度器）
    check_filled_thread = threading.Thread(target=check_filled)
    check_filled_thread.daemon = True  # 守护线程，主程序退出时自动结束
    check_filled_thread.start()
    # 启动新线程运行核心任务（避免阻塞调度器）
    get_bar_data_thread = threading.Thread(target=get_bar_data)
    get_bar_data_thread.daemon = True  # 守护线程，主程序退出时自动结束
    get_bar_data_thread.start()
    # 启动新线程运行核心任务（避免阻塞调度器）
    place_orders_thread = threading.Thread(target=place_orders)
    place_orders_thread.daemon = True  # 守护线程，主程序退出时自动结束
    place_orders_thread.start()


def start_a_task():
    test_logger = logging.getLogger("test_logger")
    logger = logging.getLogger()
    """定时启动核心任务的函数"""
    if not state.is_in_a_period:
        test_logger.info(f"A股已启动 | 时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        state.is_in_a_period = True
    else:
        test_logger.info(f"⚠️ A股已在运行 | 时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def end_a_task():
    """定时结束核心任务的函数"""
    logger = logging.getLogger()
    logger.info(f"A股任务停止")
    if state.is_in_a_period:
        print(f"A股已结束 | 时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        state.is_in_a_period = False
    else:
        print(f"⚠️ A股已结束 | 时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")



def stop_all_task():
    """定时停止核心任务的函数"""
    global check_filled_thread, get_bar_data_thread, place_orders_thread

    state.is_in_a_period = False
    state.is_in_h_period = False
    # state.is_in_us_period = False
    state.is_task_running = False

    # 等待线程结束（确保任务安全退出）
    if check_filled_thread is not None:
        check_filled_thread.join()
        check_filled_thread = None
    # 等待线程结束（确保任务安全退出）
    if get_bar_data_thread is not None:
        get_bar_data_thread.join()
        get_bar_data_thread = None
    # 等待线程结束（确保任务安全退出）
    if place_orders_thread is not None:
        place_orders_thread.join()
        place_orders_thread = None

    print(f"⚠️ 三大任务结束 | 时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

