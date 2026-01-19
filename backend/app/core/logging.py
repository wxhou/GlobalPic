"""
日志配置
使用 loguru 作为日志库
"""
import os
import sys
from loguru import logger
from app.core.config import settings


def setup_logging():
    """配置日志系统"""
    
    # 创建logs目录
    os.makedirs("logs", exist_ok=True)
    
    # 移除默认的处理器
    logger.remove()
    
    # 添加控制台输出
    logger.add(
        sys.stdout,
        level="DEBUG" if settings.DEBUG else "INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>"
    )
    
    # 添加普通日志文件
    logger.add(
        "logs/app.log",
        level="DEBUG",
        rotation="10 MB",
        retention="10 days",
        encoding="utf-8",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>"
    )
    
    # 添加错误日志文件（只记录ERROR及以上级别）
    logger.add(
        "logs/error.log",
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        encoding="utf-8",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>"
    )
    
    # 记录启动信息
    logger.info(f"应用程序启动: {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"环境: {settings.ENVIRONMENT}, 调试模式: {settings.DEBUG}")
