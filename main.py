import datetime
import logging
import signal

# from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler

from logs.logger import setup_logging
from src.gui import create_main_window
from src.start_end import start_a_task, end_a_task, stop_all_task, initialize
from config.app_config import appConfig


def schedule_jobs(scheduler):


    test_logger = logging.getLogger("test_logger")
    logger = logging.getLogger()


    # 获取sh_sz_morning_trade_start的小时和分钟
    # daily_start = appConfig["start_time"]
    # daily_start_hour, daily_start_minute = map(int, daily_start.split(":"))
    # daily_end = appConfig["end_time"]
    # daily_end_hour, daily_end_minute = map(int, daily_end.split(":"))
    morning_a_start = appConfig["sh_sz_morning_trade_start"]
    morning_a_start_hour, morning_a_start_minute = map(int, morning_a_start.split(":"))
    morning_end = appConfig["sh_sz_morning_trade_end"]
    morning_a_end_hour, morning_a_end_minute = map(int, morning_end.split(":"))
    afternoon_a_start = appConfig["sh_sz_afternoon_trade_start"]
    afternoon_a_start_hour, afternoon_a_start_minute = map(int, afternoon_a_start.split(":"))
    afternoon_a_end = appConfig["sh_sz_afternoon_trade_end"]
    afternoon_a_end_hour, afternoon_a_end_minute = map(int, afternoon_a_end.split(":"))
    trade_day = appConfig["sh_sz_trade_day"]

    # ========== 配置全天时段：9:20启动，16:20停止 ==========
    # scheduler.add_job(start_daily_task,"cron",day_of_week=trade_day,hour=daily_start_hour,minute=daily_start_minute,id="start_daily",name="启动全天任务")
    # scheduler.add_job(stop_daily_task,"cron",day_of_week=trade_day,hour=daily_end_hour,minute=daily_end_minute,id="stop_daily",name="全天停止任务")

    # ========== 配置A股上午时段：9:30启动，11:30停止 ==========
    scheduler.add_job(start_a_task,"cron",day_of_week=trade_day,hour=morning_a_start_hour,minute=morning_a_start_minute,id="start_a_morning",name="A股上午启动任务")
    scheduler.add_job(end_a_task,"cron",day_of_week=trade_day,hour=morning_a_end_hour,minute=morning_a_end_minute,id="stop_a_morning",name="A股上午停止任务")

    # ========== 配置A股下午时段：13:00启动，15:00停止 ==========
    scheduler.add_job(start_a_task,"cron",day_of_week=trade_day,hour=afternoon_a_start_hour,minute=afternoon_a_start_minute,id="start_a_afternoon",name="A股下午启动任务")
    scheduler.add_job(end_a_task,"cron",day_of_week=trade_day,hour=afternoon_a_end_hour,minute=afternoon_a_end_minute,id="stop_a_afternoon",name="A股下午停止任务")

    # 如果现在处在周一至周五的A股，手动启动任务
    start_day,end_day = map(int, trade_day.split("-"))
    # 一-日对应1-7
    today = datetime.datetime.now().isoweekday()
    test_logger.info(f"today_int:{today}")
    if start_day<=today<=end_day:
        test_logger.info(f"今天是周{today}")
        now = datetime.datetime.now()
        today_a_am_start=now.replace(hour=morning_a_start_hour, minute=morning_a_start_minute, second=0, microsecond=0)
        today_a_am_end=now.replace(hour=morning_a_end_hour, minute=morning_a_end_minute, second=0, microsecond=0)
        today_a_pm_start=now.replace(hour=afternoon_a_start_hour, minute=afternoon_a_start_minute, second=0, microsecond=0)
        today_a_pm_end=now.replace(hour=afternoon_a_end_hour, minute=afternoon_a_end_minute, second=0, microsecond=0)

        if today_a_am_start<=now<=today_a_am_end or today_a_pm_start<=now<=today_a_pm_end:
            test_logger.info(f"当前时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}，在A股交易时间段内，需要启动")
            start_a_task()



# def signal_handler(signum, frame):
#     """
#     信号处理函数：捕获终止信号，设置退出标志
#     :param signum: 信号编号（如2=SIGINT, 15=SIGTERM）
#     :param frame: 当前栈帧（无需关注）
#     """
#
#     print(f"\n接收到终止信号 {signum}，准备优雅退出...")
#     stop_all_task()

def main():
    setup_logging()

    # 获取通用 logger
    logger = logging.getLogger(__name__)

    # 获取测试专属 logger
    test_logger = logging.getLogger("test_logger")

    # 通用日志：不同环境输出不同级别
    # logger.debug("这是调试信息（测试/开发环境输出，生产环境不输出）")
    # logger.info("这是普通信息（测试/开发环境输出，生产环境不输出）")
    # logger.warning("这是警告信息（所有环境输出）")
    # logger.error("这是错误信息（所有环境输出）")

    # 测试专属日志：仅测试环境输出
    # test_logger.info("这是测试专属日志（仅 TEST 环境可见）")

    # 打印当前环境提示
    # print(f"\n当前运行环境：{config.env}")
    # print(f"日志级别：{logging.getLevelName(logging.getLogger().getEffectiveLevel())}")
    # 创建调度器，指定中国时区（关键，避免时间偏移）

    initialize()

    scheduler = BlockingScheduler(timezone="Asia/Shanghai")

    # 添加任务
    schedule_jobs(scheduler)

    # # 创建主窗口
    # main_window = create_main_window()
    #
    # def on_close():
    #     """
    #     关闭窗口时的回调函数，用于优雅地停止所有任务和调度器。
    #     """
    #     print("正在关闭应用程序...")
    #     main_window.destroy()
    #     stop_all_task()
    #     if scheduler.running:
    #         scheduler.shutdown()
    #         print("\n✅ 调度器已停止，所有任务已清理")
    #
    #
    # # 绑定主窗口关闭事件
    # main_window.protocol("WM_DELETE_WINDOW", on_close)

    # 启动调度器
    try:
        print("=" * 50)
        print(f"定时任务调度器启动 | 当前时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("任务规则：每周一至周五 9:30-11:30、13:00-15:00 运行核心任务")
        print("按 Ctrl+C 停止调度器...")
        print("=" * 50)
        scheduler.start()
        # 启动GUI主循环（阻塞式，直到关闭窗口）
        # main_window.mainloop()
    # except KeyboardInterrupt:
    except (KeyboardInterrupt, SystemExit):
        # 停止调度器时，确保核心任务也停止
        stop_all_task()
        scheduler.shutdown()
        print("\n✅ 调度器已停止，所有任务已清理")



if __name__ == "__main__":
    main()