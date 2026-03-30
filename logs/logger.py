import os
import logging
from logging.handlers import RotatingFileHandler
from config.env_config import config

# -------------------------- 1. 定义环境常量和配置 --------------------------
# 通过环境变量区分环境（推荐），也可直接赋值（如 ENV = "DEV"）
ENV = config.env  # 默认开发环境

# 各环境的日志配置
LOG_CONFIG = {
    "TEST": {
        "level": logging.DEBUG,  # 测试环境输出所有日志
        "console": True,  # 输出到控制台
        "file": True,  # 输出到文件
        "file_path": "logs/test.log",
        "test_logger_enabled": True  # 启用测试专属日志
    },
    "DEV": {
        "level": logging.DEBUG,
        "console": True,
        "file": False,  # 开发环境只输出到控制台
        "test_logger_enabled": False
    },
    "PROD": {
        "level": logging.DEBUG,  # 生产环境只输出警告及以上WARNING
        "console": True,  # 生产环境禁用控制台输出
        "file": True,
        "file_path": "logs/prod.log",
        "max_bytes": 10 * 1024 * 1024,  # 日志文件最大 10MB
        "backup_count": 5,  # 最多保留 5 个备份
        "test_logger_enabled": False  # 禁用测试专属日志
    }
}


# -------------------------- 2. 初始化通用日志配置 --------------------------
def setup_logging():
    # 获取当前环境的配置
    log_config = LOG_CONFIG.get(ENV, LOG_CONFIG["DEV"])

    # 1. 获取根 logger 并设置基础级别
    root_logger = logging.getLogger()
    root_logger.setLevel(log_config["level"])
    root_logger.handlers.clear()  # 清空默认 handler，避免重复输出

    # 2. 定义日志格式（可根据环境调整）
    if ENV == "PROD":
        # 生产环境日志格式：包含时间、级别、模块、行号、内容
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
        )
    else:
        # 测试/开发环境：更简洁，带颜色（可选）
        formatter = logging.Formatter(
            "\033[32m%(asctime)s\033[0m - \033[34m%(name)s\033[0m - %(levelname)s - %(message)s"
        )

    # 3. 添加控制台 handler（测试/开发环境启用）
    if log_config["console"]:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_config["level"])
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # 4. 添加文件 handler（测试/生产环境启用）
    if log_config["file"]:
        # 创建日志目录
        os.makedirs(os.path.dirname(log_config["file_path"]), exist_ok=True)

        if ENV == "PROD":
            # 生产环境使用轮转文件 handler，避免日志文件过大
            file_handler = RotatingFileHandler(
                log_config["file_path"],
                maxBytes=log_config.get("max_bytes", 10 * 1024 * 1024),
                backupCount=log_config.get("backup_count", 5),
                encoding="utf-8"
            )
        else:
            # 测试环境普通文件 handler
            file_handler = logging.FileHandler(log_config["file_path"], encoding="utf-8")

        file_handler.setLevel(log_config["level"])
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # 5. 初始化测试专属 logger
    test_logger = logging.getLogger("test_logger")
    if not log_config["test_logger_enabled"]:
        # 禁用测试专属日志（设置为最高级别，不会输出）
        test_logger.setLevel(logging.CRITICAL + 1)


# -------------------------- 3. 使用示例 --------------------------
if __name__ == "__main__":
    # 初始化日志配置
    setup_logging()

    # 获取通用 logger
    logger = logging.getLogger(__name__)

    # 获取测试专属 logger
    test_logger = logging.getLogger("test_logger")

    # 通用日志：不同环境输出不同级别
    logger.debug("这是调试信息（测试/开发环境输出，生产环境不输出）")
    logger.info("这是普通信息（测试/开发环境输出，生产环境不输出）")
    logger.warning("这是警告信息（所有环境输出）")
    logger.error("这是错误信息（所有环境输出）")

    # 测试专属日志：仅测试环境输出
    test_logger.info("这是测试专属日志（仅 TEST 环境可见）")

    # 打印当前环境提示
    print(f"\n当前运行环境：{ENV}")
    print(f"日志级别：{logging.getLevelName(logging.getLogger().getEffectiveLevel())}")