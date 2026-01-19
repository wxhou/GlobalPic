from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    # 应用程序基础配置
    APP_NAME: str = "GlobalPic AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # API配置
    API_V1_STR: str = "/api/v1"
    
    # 数据库配置 - 生产环境必须从环境变量加载
    DATABASE_URL: str = ""
    MYSQL_DB: str = "globalpic"
    MYSQL_USER: str = "globalpic"
    MYSQL_PASSWORD: str = ""
    DATABASE_TEST_URL: str = "mysql+pymysql://globalpic:password@localhost:3306/globalpic_test"
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: Optional[str] = None
    
    # 安全配置 - 生产环境必须从环境变量加载
    SECRET_KEY: str = ""
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30
    
    # AI模型配置 - 使用 ModelScope API
    MODELSCOPE_API_KEY: str = ""
    MODELSCOPE_MODEL_ID: str = "Tongyi-MAI/Z-Image-Turbo"
    ZIMAGE_MODEL_PATH: str = ""  # 不再需要本地模型
    SAM_MODEL_PATH: str = ""  # 不再需要本地模型
    OPENAI_API_KEY: str = ""
    
    # 存储配置 - 生产环境必须从环境变量加载
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_S3_BUCKET: str = "globalpic-storage"
    AWS_REGION: str = "us-east-1"
    S3_ENDPOINT_URL: Optional[str] = None

    # 邮件配置 - 生产环境必须从环境变量加载
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""

    # 支付配置 - 生产环境必须从环境变量加载
    STRIPE_PUBLIC_KEY: str = ""
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    
    # 监控配置
    SENTRY_DSN: Optional[str] = None
    LOG_LEVEL: str = "INFO"
    
    # 限流配置
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # 文件上传配置
    MAX_FILE_SIZE: int = 20971520  # 20MB
    ALLOWED_EXTENSIONS: str = "jpg,jpeg,png,webp"
    
    # CORS配置
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # CDN配置
    CDN_URL: str = "https://cdn.globalpic.ai"
    
    # 外部API配置 - 生产环境必须从环境变量加载
    OCR_API_URL: str = ""
    OCR_API_KEY: str = ""
    
    # 开发配置
    HOT_RELOAD: bool = True
    AUTO_RELOAD: bool = True
    DEV_MODE: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

# 创建全局设置实例
settings = Settings()