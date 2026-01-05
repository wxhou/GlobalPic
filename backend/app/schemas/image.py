from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class ImageStatus(str, Enum):
    """图像处理状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ProcessingStatus(str, Enum):
    """处理任务状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class OperationType(str, Enum):
    """处理操作类型"""
    TEXT_REMOVAL = "text_removal"
    BACKGROUND_REPLACEMENT = "background_replacement"

class ImageBase(BaseModel):
    """图像基础信息"""
    filename: str = Field(..., description="文件名")
    file_format: str = Field(..., description="文件格式: jpg, png, webp")
    width: Optional[int] = Field(None, description="图像宽度")
    height: Optional[int] = Field(None, description="图像高度")
    tags: Optional[List[str]] = Field(default_factory=list, description="标签")

class ImageCreate(ImageBase):
    """图像创建请求"""
    pass

class ImageResponse(ImageBase):
    """图像响应"""
    id: int
    user_id: int
    original_filename: str
    file_size: int
    mime_type: str
    storage_path: str
    storage_url: str
    storage_provider: str
    is_processed: bool
    processing_status: ImageStatus
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ImageUploadResponse(BaseModel):
    """图像上传响应"""
    success: bool
    message: str
    image: ImageResponse

class ProcessingJobBase(BaseModel):
    """处理任务基础信息"""
    operation_type: OperationType
    parameters: Optional[dict] = Field(default_factory=dict, description="处理参数")
    
    @validator('parameters')
    def validate_parameters(cls, v):
        if v is None:
            return {}
        return v

class ProcessingJobCreate(ProcessingJobBase):
    """处理任务创建请求"""
    image_id: int

class ProcessingJobResponse(ProcessingJobBase):
    """处理任务响应"""
    id: int
    image_id: int
    user_id: int
    status: ProcessingStatus
    progress: int = Field(ge=0, le=100, description="处理进度 0-100")
    estimated_completion: Optional[datetime] = None
    result_path: Optional[str] = None
    result_urls: Optional[List[str]] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ProcessingJobCreateResponse(BaseModel):
    """处理任务创建响应"""
    success: bool
    message: str
    job: ProcessingJobResponse

class BackgroundStyle(BaseModel):
    """背景风格"""
    id: str
    name: str
    description: str
    preview_url: Optional[str] = None

class TextRemovalRequest(BaseModel):
    """文字抹除请求"""
    confidence_threshold: float = Field(default=0.5, ge=0.1, le=1.0, description="文字检测置信度阈值")
    language: str = Field(default="zh", description="OCR语言")

class BackgroundReplacementRequest(BaseModel):
    """背景重绘请求"""
    style_id: str = Field(..., description="背景风格ID")
    custom_prompt: Optional[str] = Field(None, description="自定义提示词")
    strength: float = Field(default=0.8, ge=0.1, le=1.0, description="重绘强度")

class ImageListResponse(BaseModel):
    """图像列表响应"""
    images: List[ImageResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool