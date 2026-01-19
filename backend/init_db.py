#!/usr/bin/env python3
"""
数据库初始化脚本
"""
import sys
from pathlib import Path

# 添加backend目录到路径
backend_dir = Path(__file__).parent.resolve()
sys.path.insert(0, str(backend_dir))

# 设置环境变量
from dotenv import load_dotenv
load_dotenv(backend_dir / ".env")

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.core.config import settings

# 打印数据库URL用于调试
print(f"数据库URL: {settings.DATABASE_URL}")

# 使用同步SQLite引擎
db_url = settings.DATABASE_URL
if db_url.startswith("sqlite+aiosqlite://"):
    db_url = db_url.replace("sqlite+aiosqlite://", "sqlite:///", 1)

print(f"同步数据库URL: {db_url}")

engine = create_engine(db_url)

# 使用MetaData创建所有表（自动处理依赖）
print("\n创建所有数据库表...")

# 导入所有模型以确保它们被注册到Base
from app.models import User, Image, ProcessingJob, Subscription, CreditTransaction, APIKey

# 创建所有表
Base.metadata.create_all(engine)

print("数据库表创建成功！")

# 验证表是否存在
with engine.connect() as conn:
    result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"))
    tables = [row[0] for row in result.fetchall()]
    print(f"\n已创建的表 ({len(tables)}个):")
    for table in tables:
        print(f"  - {table}")
