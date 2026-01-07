from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.api.v1.auth import get_current_user
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


class BatchCreateResponse(BaseModel):
    """批量创建响应"""
    success: bool
    task_id: str
    status: str
    total_images: int
    estimated_time: int


class BatchStatusResponse(BaseModel):
    """批量状态响应"""
    task_id: str
    status: str
    total_images: int
    processed_images: int
    success_count: int
    failed_count: int
    progress: float
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


class BatchResultResponse(BaseModel):
    """批量结果响应"""
    task_id: str
    status: str
    results: List[dict]
    errors: List[dict]
    success_count: int
    failed_count: int


class TaskIdRequest(BaseModel):
    """任务ID请求"""
    task_id: str


@router.post("/batch/create", response_model=BatchCreateResponse)
async def create_batch_task(
    request: BatchCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建批量处理任务"""
    # 验证图片数量
    if len(request.images) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="单次批量处理最多支持50张图片"
        )

    if len(request.images) < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="至少需要上传1张图片"
        )

    # 验证操作类型
    valid_operations = {"text_removal", "background_replacement"}
    for op in request.operations:
        if op not in valid_operations:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的操作类型: {op}"
            )

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

        return BatchCreateResponse(
            success=True,
            task_id=result["task_id"],
            status=result["status"],
            total_images=result["total_images"],
            estimated_time=result["estimated_time"],
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建批量任务失败: {str(e)}"
        )


@router.get("/batch/status", response_model=BatchStatusResponse)
async def get_batch_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """获取批量任务状态"""
    result = await batch_processor.get_task_status(task_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )

    return BatchStatusResponse(**result)


@router.get("/batch/results", response_model=BatchResultResponse)
async def get_batch_results(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """获取批量任务结果"""
    result = await batch_processor.get_task_results(task_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )

    return BatchResultResponse(**result)


@router.get("/batch/download")
async def download_batch_results(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """下载批量处理结果（ZIP包）"""
    task = await batch_processor.get_task_results(task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )

    if task["status"] != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="任务尚未完成"
        )

    zip_data = await batch_processor.generate_download_package(task_id)

    if not zip_data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="生成下载包失败"
        )

    from fastapi.responses import StreamingResponse
    import base64

    return StreamingResponse(
        iter([base64.b64decode(zip_data)]),
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=batch_{task_id}.zip"
        }
    )


@router.post("/batch/cancel")
async def cancel_batch_task(
    request: TaskIdRequest,
    current_user: User = Depends(get_current_user)
):
    """取消批量任务"""
    success = await batch_processor.cancel_task(request.task_id, current_user.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="取消任务失败，可能任务已结束或不存在"
        )

    return {"success": True, "message": "任务已取消"}


@router.get("/batch/processor-status")
async def get_batch_processor_status():
    """获取批量处理器状态"""
    return batch_processor.get_status()
