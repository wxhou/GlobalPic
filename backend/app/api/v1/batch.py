from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.core.response import ErrCode, error_response, success_response
from app.models.user import User
from app.services.batch_processor import batch_processor

router = APIRouter()


class BatchImageItem(BaseModel):
    """批量处理图片项"""
    image: str  # base64编码
    filename: Optional[str] = None


class BatchCreateRequest(BaseModel):
    """批量创建请求"""
    images: List[BatchImageItem]
    operations: List[str] = ["text_removal", "background_replacement"]
    style_id: str = "minimal_white"


class TaskIdRequest(BaseModel):
    """任务ID请求"""
    task_id: str


@router.post("/batch/create")
async def create_batch_task(
    request: BatchCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建批量处理任务"""
    # 验证图片数量
    if len(request.images) > 50:
        return error_response(ErrCode.BATCH_LIMIT_EXCEEDED, custom_message="单次批量处理最多支持50张图片")

    if len(request.images) < 1:
        return error_response(ErrCode.INVALID_REQUEST, custom_message="至少需要上传1张图片")

    # 验证操作类型
    valid_operations = {"text_removal", "background_replacement"}
    for op in request.operations:
        if op not in valid_operations:
            return error_response(ErrCode.INVALID_REQUEST, custom_message=f"不支持的操作类型: {op}")

    try:
        # 创建批量任务
        image_data_list = [
            {"image": img.image, "filename": img.filename}
            for img in request.images
        ]

        result = await batch_processor.create_task(
            user_id=current_user.id,
            image_data_list=image_data_list,
            operations=request.operations,
            style_id=request.style_id,
        )

        return success_response({
            "success": True,
            "task_id": result["task_id"],
            "status": result["status"],
            "total_images": result["total_images"],
            "estimated_time": result["estimated_time"],
        })

    except Exception as e:
        return error_response(ErrCode.INTERNAL_ERROR, custom_message=f"创建批量任务失败: {str(e)}")


@router.get("/batch/status")
async def get_batch_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """获取批量任务状态"""
    result = await batch_processor.get_task_status(task_id)

    if not result:
        return error_response(ErrCode.NOT_FOUND, custom_message="任务不存在")

    return success_response(result)


@router.get("/batch/results")
async def get_batch_results(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """获取批量任务结果"""
    result = await batch_processor.get_task_results(task_id)

    if not result:
        return error_response(ErrCode.NOT_FOUND, custom_message="任务不存在")

    return success_response(result)


@router.post("/batch/cancel")
async def cancel_batch_task(
    request: TaskIdRequest,
    current_user: User = Depends(get_current_user)
):
    """取消批量任务"""
    success = await batch_processor.cancel_task(request.task_id, current_user.id)

    if not success:
        return error_response(ErrCode.OPERATION_NOT_ALLOWED, custom_message="取消任务失败，可能任务已结束或不存在")

    return success_response({"success": True, "message": "任务已取消"})


@router.get("/batch/processor-status")
async def get_batch_processor_status():
    """获取批量处理器状态"""
    return success_response(batch_processor.get_status())


@router.get("/batch/download")
async def download_batch_results(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """下载批量任务结果（ZIP包）"""
    result = await batch_processor.get_task_status(task_id)

    if not result:
        return error_response(ErrCode.NOT_FOUND, custom_message="任务不存在")

    if result["status"] != "completed":
        return error_response(ErrCode.OPERATION_NOT_ALLOWED, custom_message="任务未完成，无法下载")

    zip_base64 = await batch_processor.generate_download_package(task_id)

    if not zip_base64:
        return error_response(ErrCode.INTERNAL_ERROR, custom_message="生成下载包失败")

    return success_response({
        "task_id": task_id,
        "download_url": f"data:application/zip;base64,{zip_base64}",
        "filename": f"batch_results_{task_id}.zip"
    })
