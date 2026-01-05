from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import asyncio

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.image import Image, ProcessingJob
from app.services.image_service import ImageService
from app.services.ai_processor import ai_processor
from app.schemas.image import (
    ProcessingJobCreate, ProcessingJobResponse, ProcessingJobCreateResponse,
    TextRemovalRequest, BackgroundReplacementRequest, OperationType, ProcessingStatus
)

router = APIRouter()

@router.post("/initialize", response_model=dict)
async def initialize_ai_models():
    """初始化AI模型"""
    try:
        success = await ai_processor.initialize_models()
        
        if success:
            return {
                "success": True,
                "message": "AI模型初始化成功",
                "status": ai_processor.get_processing_status()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="AI模型初始化失败"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"初始化失败: {str(e)}"
        )

@router.get("/status", response_model=dict)
async def get_processing_status():
    """获取AI处理状态"""
    return ai_processor.get_processing_status()

@router.get("/jobs", response_model=List[ProcessingJobResponse])
async def get_user_processing_jobs(
    status: Optional[ProcessingStatus] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的处理任务列表"""
    image_service = ImageService(db)
    jobs, total = image_service.get_user_processing_jobs(
        user_id=current_user.id,
        status=status,
        page=page,
        per_page=per_page
    )
    
    return jobs

@router.get("/jobs/{job_id}", response_model=ProcessingJobResponse)
async def get_processing_job_detail(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取处理任务详情"""
    image_service = ImageService(db)
    job = image_service.get_processing_job_by_id(job_id, current_user.id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="处理任务不存在"
        )
    
    return job

@router.get("/jobs/{job_id}/status", response_model=dict)
async def get_processing_job_status(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取处理任务实时状态"""
    image_service = ImageService(db)
    job = image_service.get_processing_job_by_id(job_id, current_user.id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="处理任务不存在"
        )
    
    return {
        "job_id": job.id,
        "status": job.status,
        "progress": job.progress,
        "result_urls": job.result_urls,
        "error_message": job.error_message,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
        "estimated_completion": job.estimated_completion
    }

@router.delete("/jobs/{job_id}")
async def cancel_processing_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """取消处理任务"""
    image_service = ImageService(db)
    job = image_service.get_processing_job_by_id(job_id, current_user.id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="处理任务不存在"
        )
    
    # 只有待处理或处理中的任务可以取消
    if job.status not in [ProcessingStatus.PENDING, ProcessingStatus.PROCESSING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能取消待处理或处理中的任务"
        )
    
    # 更新任务状态为失败（用户取消）
    image_service.update_processing_job_status(
        job_id=job_id,
        status=ProcessingStatus.FAILED,
        error_message="用户取消"
    )
    
    return {"success": True, "message": "任务已取消"}

@router.post("/text-removal/{image_id}", response_model=ProcessingJobCreateResponse)
async def create_text_removal_job(
    image_id: int,
    text_removal_request: TextRemovalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建文字抹除处理任务"""
    
    # 验证图像是否存在且属于当前用户
    image_service = ImageService(db)
    image = image_service.get_image_by_id(image_id, current_user.id)
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="图像不存在"
        )
    
    # 检查AI模型是否已初始化
    if not ai_processor.models_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI模型未初始化，请先调用 /processing/initialize"
        )
    
    try:
        # 创建处理任务
        processing_job = image_service.create_processing_job(
            image_id=image_id,
            user_id=current_user.id,
            operation_type=OperationType.TEXT_REMOVAL,
            parameters={
                "confidence_threshold": text_removal_request.confidence_threshold,
                "language": text_removal_request.language
            }
        )
        
        # 异步启动处理任务
        asyncio.create_task(
            _process_text_removal_async(processing_job.id, image_id, current_user.id, db)
        )
        
        return ProcessingJobCreateResponse(
            success=True,
            message="文字抹除任务创建成功",
            job=ProcessingJobResponse.from_orm(processing_job)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建任务失败: {str(e)}"
        )

@router.post("/background-replacement/{image_id}", response_model=ProcessingJobCreateResponse)
async def create_background_replacement_job(
    image_id: int,
    background_request: BackgroundReplacementRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建背景重绘处理任务"""
    
    # 验证图像是否存在且属于当前用户
    image_service = ImageService(db)
    image = image_service.get_image_by_id(image_id, current_user.id)
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="图像不存在"
        )
    
    # 检查AI模型是否已初始化
    if not ai_processor.models_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI模型未初始化，请先调用 /processing/initialize"
        )
    
    try:
        # 创建处理任务
        processing_job = image_service.create_processing_job(
            image_id=image_id,
            user_id=current_user.id,
            operation_type=OperationType.BACKGROUND_REPLACEMENT,
            parameters={
                "style_id": background_request.style_id,
                "custom_prompt": background_request.custom_prompt,
                "strength": background_request.strength
            }
        )
        
        # 异步启动处理任务
        asyncio.create_task(
            _process_background_replacement_async(processing_job.id, image_id, current_user.id, db)
        )
        
        return ProcessingJobCreateResponse(
            success=True,
            message="背景重绘任务创建成功",
            job=ProcessingJobResponse.from_orm(processing_job)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建任务失败: {str(e)}"
        )

@router.get("/background-styles", response_model=List[dict])
async def get_background_styles():
    """获取可用的背景风格"""
    styles = [
        {
            "id": "minimal_white",
            "name": "极简白色",
            "description": "干净的白色背景，突出产品本身",
            "category": "minimalist"
        },
        {
            "id": "modern_home",
            "name": "现代家居",
            "description": "现代厨房、客厅、办公室场景",
            "category": "lifestyle"
        },
        {
            "id": "business",
            "name": "商业环境",
            "description": "专业办公桌、展示台、商店环境",
            "category": "business"
        },
        {
            "id": "natural",
            "name": "自然光线",
            "description": "户外阳光、窗边自然光场景",
            "category": "natural"
        },
        {
            "id": "amazon_standard",
            "name": "亚马逊标准",
            "description": "白色背景，产品居中，符合平台规范",
            "category": "ecommerce"
        },
        {
            "id": "tiktok_vibrant",
            "name": "TikTok风格",
            "description": "鲜艳色彩，吸引眼球，适合短视频",
            "category": "social"
        },
        {
            "id": "instagram_lifestyle",
            "name": "Instagram风格",
            "description": "时尚、生活化场景，提升品牌形象",
            "category": "social"
        },
        {
            "id": "shopify_custom",
            "name": "Shopify定制",
            "description": "多样化设计，体现品牌调性",
            "category": "ecommerce"
        }
    ]
    
    return styles

async def _process_text_removal_async(
    job_id: int,
    image_id: int,
    user_id: int,
    db: Session
):
    """异步文字抹除处理"""
    try:
        image_service = ImageService(db)
        
        # 更新任务状态为处理中
        image_service.update_processing_job_status(
            job_id=job_id,
            status=ProcessingStatus.PROCESSING,
            progress=10
        )
        
        # 获取图像信息
        image = image_service.get_image_by_id(image_id, user_id)
        if not image:
            raise ValueError("图像不存在")
        
        # 获取处理参数
        job = image_service.get_processing_job_by_id(job_id, user_id)
        if not job:
            raise ValueError("处理任务不存在")
        
        parameters = {}
        if job.parameters:
            try:
                import json
                parameters = json.loads(job.parameters)
            except:
                pass
        
        # 更新进度
        image_service.update_processing_job_status(
            job_id=job_id,
            status=ProcessingStatus.PROCESSING,
            progress=30
        )
        
        # 调用AI处理器
        result = await ai_processor.process_image(
            image_path=image.storage_path,
            operation_type="text_removal",
            parameters=parameters
        )
        
        # 更新最终结果
        if result["success"]:
            image_service.update_processing_job_status(
                job_id=job_id,
                status=ProcessingStatus.COMPLETED,
                progress=100,
                result_urls=result["result"]["output_urls"]
            )
        else:
            image_service.update_processing_job_status(
                job_id=job_id,
                status=ProcessingStatus.FAILED,
                error_message=result.get("error", "处理失败")
            )
        
    except Exception as e:
        image_service = ImageService(db)
        image_service.update_processing_job_status(
            job_id=job_id,
            status=ProcessingStatus.FAILED,
            error_message=str(e)
        )

async def _process_background_replacement_async(
    job_id: int,
    image_id: int,
    user_id: int,
    db: Session
):
    """异步背景重绘处理"""
    try:
        image_service = ImageService(db)
        
        # 更新任务状态为处理中
        image_service.update_processing_job_status(
            job_id=job_id,
            status=ProcessingStatus.PROCESSING,
            progress=10
        )
        
        # 获取图像信息
        image = image_service.get_image_by_id(image_id, user_id)
        if not image:
            raise ValueError("图像不存在")
        
        # 获取处理参数
        job = image_service.get_processing_job_by_id(job_id, user_id)
        if not job:
            raise ValueError("处理任务不存在")
        
        parameters = {}
        if job.parameters:
            try:
                import json
                parameters = json.loads(job.parameters)
            except:
                pass
        
        # 更新进度
        image_service.update_processing_job_status(
            job_id=job_id,
            status=ProcessingStatus.PROCESSING,
            progress=30
        )
        
        # 调用AI处理器
        result = await ai_processor.process_image(
            image_path=image.storage_path,
            operation_type="background_replacement",
            parameters=parameters
        )
        
        # 更新最终结果
        if result["success"]:
            image_service.update_processing_job_status(
                job_id=job_id,
                status=ProcessingStatus.COMPLETED,
                progress=100,
                result_urls=result["result"]["output_urls"]
            )
        else:
            image_service.update_processing_job_status(
                job_id=job_id,
                status=ProcessingStatus.FAILED,
                error_message=result.get("error", "处理失败")
            )
        
    except Exception as e:
        image_service = ImageService(db)
        image_service.update_processing_job_status(
            job_id=job_id,
            status=ProcessingStatus.FAILED,
            error_message=str(e)
        )