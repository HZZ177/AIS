import sys
import threading
from datetime import datetime
from loguru import logger
from .file_path import log_path


current_date = datetime.now().strftime("%Y-%m-%d")
current_hour = datetime.now().strftime("%H")

# 自定义每个级别日志的信息头颜色
logger.level("DEBUG", color="<blue>")
logger.level("INFO", color="<green>")
logger.level("SUCCESS", color="<bold><green>")
logger.level("WARNING", color="<yellow>")
logger.level("ERROR", color="<red>")
logger.level("CRITICAL", color="<bold><red>")


# 配置自定义 logger handler，输出日志到：1、标准输出 2、日志输出文件 3、Allure报告
logger.configure(
    handlers=[
        {
            "sink": sys.stdout,  # 日志输出到标准输出
            "level": "DEBUG",  # 日志级别
            "format": "<green>{time:YYYY-MM-DD HH:mm:ss.SSSS} | {module}:{line}</green> | <level>{level}</level> | {message}",
            "colorize": True,  # 启用颜色
            "backtrace": False,   # 控制是否追溯详细的回溯信息（即代码调用链和变量状态等详细信息）
            "diagnose": False,    # 控制不会包含详细的诊断信息
            "enqueue": False,  # 关闭多线程安全队列
        },
        {
            "sink": f"{log_path}/{current_date}/AIS_{current_hour}.log",  # 指定日志输出到文件
            "level": "INFO",  # 日志级别
            "format": "{time:YYYY-MM-DD HH:mm:ss.SSSS} | {module}:{line} | {level} | {message}",  # 日志格式
            "rotation": "1 hour",  # 每小时自动分割日志
            "retention": "1 week",  # 保留最近 7 天的日志文件
            "compression": "zip",  # 压缩日志文件
            "backtrace": True,   # 控制是否追溯详细的回溯信息（即代码调用链和变量状态等详细信息）
            "diagnose": True,  # 控制是否包含详细的诊断信息
            "enqueue": False,  # 关闭多线程安全队列
        }
    ]
)


# 定义全局异常捕获函数，处理未捕获的异常
def handle_uncaught_exception(exc_type, exc_value, exc_traceback):
    # 忽略系统退出异常（如 Ctrl+C 中断）
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    # 记录未捕获的异常栈信息
    logger.opt(exception=(exc_type, exc_value, exc_traceback)).error("未捕获的异常")


# 设置全局异常捕获钩子
sys.excepthook = handle_uncaught_exception

# 捕获线程中的未捕获异常（Python 3.8+ 支持）
if hasattr(threading, "excepthook"):
    threading.excepthook = lambda args: logger.opt(exception=(args.exc_type, args.exc_value, args.exc_traceback)).error("线程中未捕获的异常")

# 供其他模块引用的 logger
logger = logger
