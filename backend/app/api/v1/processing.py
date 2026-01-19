from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import asyncio
from pydantic import BaseModel

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.core.response import ErrCode, error_response, success_response
from app.models.user import User
from app.models.image import Image, ProcessingJob
from app.services.image_service import ImageService
from app.services.ai_processor import ai_processor
from app.schemas.image import (
    ProcessingJobCreate, ProcessingJobResponse, ProcessingJobCreateResponse,
    TextRemovalRequest, BackgroundReplacementRequest, OperationType, ProcessingStatus
)

router = APIRouter()


class ProcessingJobIdRequest(BaseModel):
    """处理任务ID请求"""
    job_id: int


class CancelJobRequest(BaseModel):
    """取消任务请求"""
    job_id: int


class TextRemovalWithImageRequest(BaseModel):
    """文字抹除请求（包含图像ID）"""
    image_id: int
    confidence_threshold: float = 0.5
    language: str = "en"


class BackgroundReplacementWithImageRequest(BaseModel):
    """背景重绘请求（包含图像ID）"""
    image_id: int
    style_id: str = "minimal_white"
    custom_prompt: Optional[str] = None
    strength: float = 0.8


def format_job_response(job: ProcessingJob) -> dict:
    """格式化处理任务响应"""
    return {
        "id": job.id,
        "image_id": job.image_id,
        "operation_type": job.operation_type,
        "status": job.status,
        "parameters": job.parameters,
        "output_url": job.output_url,
        "quality_score": job.quality_score,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None
    }


@router.post("/processing/initialize")
async def initialize_ai_models():
    """初始化AI模型"""
    try:
        success = await ai_processor.initialize_models()

        if success:
            return success_response({
                "success": True,
                "message": "AI模型初始化成功",
                "status": ai_processor.get_processing_status()
            })
        else:
            return error_response(ErrCode.INTERNAL_ERROR, custom_message="AI模型初始化失败")

    except Exception as e:
        return error_response(ErrCode.INTERNAL_ERROR, custom_message=f"初始化失败: {str(e)}")


@router.get("/processing/status")
async def get_processing_status():
    """获取AI处理状态"""
    return success_response(ai_processor.get_processing_status())


@router.get("/processing/jobs")
async def get_user_processing_jobs(
    status: Optional[ProcessingStatus] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的处理任务列表"""
    try:
        image_service = ImageService(db)
        jobs, total = image_service.get_user_processing_jobs(
            user_id=current_user.id,
            status=status,
            page=page,
            per_page=per_page
        )

        return success_response({
            "jobs": [format_job_response(job) for job in jobs],
            "total": total,
            "page": page,
            "per_page": per_page
        })
    except Exception as e:
        # 如果出错，返回空列表而不是错误
        import logging
        logging.warning(f"获取处理任务列表失败: {e}")
        return success_response({
            "jobs": [],
            "total": 0,
            "page": page,
            "per_page": per_page
        })


@router.get("/processing/jobs/detail")
async def get_processing_job_detail(
    job_id: int = Query(..., description="处理任务ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取处理任务详情"""
    image_service = ImageService(db)
    job = image_service.get_processing_job_by_id(job_id, current_user.id)

    if not job:
        return error_response(ErrCode.NOT_FOUND, custom_message="处理任务不存在")

    return success_response({"job": format_job_response(job)})


@router.get("/processing/jobs/status")
async def get_processing_job_status(
    job_id: int = Query(..., description="处理任务ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取处理任务实时状态"""
    image_service = ImageService(db)
    job = image_service.get_processing_job_by_id(job_id, current_user.id)

    if not job:
        return error_response(ErrCode.NOT_FOUND, custom_message="处理任务不存在")

    return success_response({
        "job_id": job.id,
        "status": job.status,
        "progress": job.progress,
        "result_urls": job.result_urls,
        "error_message": job.error_message,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
        "estimated_completion": job.estimated_completion
    })


@router.post("/processing/jobs/cancel")
async def cancel_processing_job(
    request: CancelJobRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """取消处理任务"""
    image_service = ImageService(db)
    job = image_service.get_processing_job_by_id(request.job_id, current_user.id)

    if not job:
        return error_response(ErrCode.NOT_FOUND, custom_message="处理任务不存在")

    # 只有待处理或处理中的任务可以取消
    if job.status not in [ProcessingStatus.PENDING, ProcessingStatus.PROCESSING]:
        return error_response(ErrCode.OPERATION_NOT_ALLOWED, custom_message="只能取消待处理或处理中的任务")

    # 更新任务状态为失败（用户取消）
    image_service.update_processing_job_status(
        job_id=request.job_id,
        status=ProcessingStatus.FAILED,
        error_message="用户取消"
    )

    return success_response({"success": True, "message": "任务已取消"})


@router.post("/processing/text-removal")
async def create_text_removal_job(
    request: TextRemovalWithImageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建文字抹除处理任务"""

    # 验证图像是否存在且属于当前用户
    image_service = ImageService(db)
    image = image_service.get_image_by_id(request.image_id, current_user.id)

    if not image:
        return error_response(ErrCode.IMAGE_NOT_FOUND)

    # 检查AI模型是否已初始化
    if not ai_processor.models_loaded:
        return error_response(ErrCode.SERVICE_UNAVAILABLE, custom_message="AI模型未初始化，请先调用 /processing/initialize")

    try:
        # 创建处理任务
        processing_job = image_service.create_processing_job(
            image_id=request.image_id,
            user_id=current_user.id,
            operation_type=OperationType.TEXT_REMOVAL,
            parameters={
                "confidence_threshold": request.confidence_threshold,
                "language": request.language
            }
        )

        # 异步启动处理任务
        asyncio.create_task(
            _process_text_removal_async(processing_job.id, request.image_id, current_user.id, db)
        )

        return success_response({
            "success": True,
            "message": "文字抹除任务创建成功",
            "job": format_job_response(processing_job)
        })

    except Exception as e:
        return error_response(ErrCode.INTERNAL_ERROR, custom_message=f"创建任务失败: {str(e)}")


@router.post("/processing/background-replacement")
async def create_background_replacement_job(
    request: BackgroundReplacementWithImageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建背景重绘处理任务"""

    # 验证图像是否存在且属于当前用户
    image_service = ImageService(db)
    image = image_service.get_image_by_id(request.image_id, current_user.id)

    if not image:
        return error_response(ErrCode.IMAGE_NOT_FOUND)

    # 检查AI模型是否已初始化
    if not ai_processor.models_loaded:
        return error_response(ErrCode.SERVICE_UNAVAILABLE, custom_message="AI模型未初始化，请先调用 /processing/initialize")

    try:
        # 创建处理任务
        processing_job = image_service.create_processing_job(
            image_id=request.image_id,
            user_id=current_user.id,
            operation_type=OperationType.BACKGROUND_REPLACEMENT,
            parameters={
                "style_id": request.style_id,
                "custom_prompt": request.custom_prompt,
                "strength": request.strength
            }
        )

        # 异步启动处理任务
        asyncio.create_task(
            _process_background_replacement_async(processing_job.id, request.image_id, current_user.id, db)
        )

        return success_response({
            "success": True,
            "message": "背景重绘任务创建成功",
            "job": format_job_response(processing_job)
        })

    except Exception as e:
        return error_response(ErrCode.INTERNAL_ERROR, custom_message=f"创建任务失败: {str(e)}")


@router.get("/processing/background-styles")
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

    return success_response({"styles": styles})


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
