from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Image(Base):
    __tablename__ = "images"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 文件信息
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)  # bytes
    file_format = Column(String(50), nullable=False)  # jpg, png, webp
    mime_type = Column(String(100), nullable=False)
    
    # 图像信息
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    color_space = Column(String(50), default="RGB")
    
    # 存储信息
    storage_path = Column(String(500), nullable=False)
    storage_url = Column(String(500), nullable=False)
    storage_provider = Column(String(50), default="minio")  # minio, s3
    
    # 状态
    is_processed = Column(Boolean, default=False)
    processing_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    
    # 元数据
    tags = Column(Text, nullable=True)  # JSON string for tags
    extra_data = Column(Text, nullable=True)  # JSON string for additional metadata
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # 关系
    user = relationship("User", back_populates="images")
    processing_jobs = relationship("ProcessingJob", back_populates="image")
    
    def __repr__(self):
        return f"<Image(id={self.id}, filename='{self.filename}')>"

class ProcessingJob(Base):
    __tablename__ = "processing_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(Integer, ForeignKey("images.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 处理配置
    operation_type = Column(String(100), nullable=False)  # text_removal, background_replacement, etc.
    parameters = Column(Text, nullable=True)  # JSON string for processing parameters
    
    # 处理状态
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    progress = Column(Integer, default=0)  # 0-100
    estimated_completion = Column(DateTime(timezone=True), nullable=True)
    
    # 结果
    result_path = Column(String(500), nullable=True)
    result_urls = Column(Text, nullable=True)  # JSON string for multiple result URLs
    error_message = Column(Text, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # 关系
    image = relationship("Image", back_populates="processing_jobs")
    user = relationship("User")
    
    def __repr__(self):
        return f"<ProcessingJob(id={self.id}, image_id={self.image_id}, status='{self.status}')>"