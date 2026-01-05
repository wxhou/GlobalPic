import logging
import sys
from app.core.config import settings

def setup_logging():
    """配置日志系统"""
    
    # 配置根日志器
    logging.basicConfig(
        level=logging.DEBUG if settings.DEBUG else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # 创建logs目录
    import os
    os.makedirs("logs", exist_ok=True)
    
    # 添加文件处理器（开发环境）
    if settings.DEBUG:
        file_handler = logging.FileHandler("logs/app.log")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))
        logging.getLogger().addHandler(file_handler)
    
    # 记录启动信息
    logger = logging.getLogger(__name__)
    logger.info(f"应用程序启动: {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"环境: {settings.ENVIRONMENT}, 调试模式: {settings.DEBUG}")