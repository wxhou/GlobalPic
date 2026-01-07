from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
from datetime import datetime
from pydantic import BaseModel

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.image import Image, ProcessingJob
from app.schemas.image import (
    ImageUploadResponse, ImageResponse, ImageListResponse,
    ProcessingJobCreate, ProcessingJobCreateResponse, ProcessingJobResponse
)
from app.services.storage_service import StorageService
from app.services.image_service import ImageService

router = APIRouter()

# 允许的文件格式
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


class ImageIdRequest(BaseModel):
    """图像ID请求"""
    image_id: int


class DeleteImageRequest(BaseModel):
    """删除图像请求"""
    image_id: int


class ProcessingJobIdRequest(BaseModel):
    """处理任务ID请求"""
    job_id: int


def validate_file_format(filename: str) -> bool:
    """验证文件格式"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_file_size(file_content: bytes) -> bool:
    """验证文件大小"""
    return len(file_content) <= MAX_FILE_SIZE


@router.post("/images/upload", response_model=ImageUploadResponse)
async def upload_image(
    file: UploadFile = File(..., description="图像文件"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """上传图像文件"""

    # 验证文件格式
    if not validate_file_format(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件格式。支持的格式: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # 读取文件内容
    file_content = await file.read()

    # 验证文件大小
    if not validate_file_size(file_content):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件大小超过限制。最大支持 {MAX_FILE_SIZE // (1024 * 1024)}MB"
        )

    try:
        # 生成唯一文件名
        file_extension = file.filename.rsplit(".", 1)[1].lower()
        unique_filename = f"{uuid.uuid4()}.{file_extension}"

        # 初始化服务
        storage_service = StorageService()
        image_service = ImageService(db)

        # 上传文件到存储
        storage_result = await storage_service.upload_image(
            file_content=file_content,
            filename=unique_filename,
            content_type=file.content_type
        )

        # 保存图像记录到数据库
        image_record = image_service.create_image_record(
            user_id=current_user.id,
            original_filename=file.filename,
            filename=unique_filename,
            file_size=len(file_content),
            file_format=file_extension,
            mime_type=file.content_type,
            storage_path=storage_result["path"],
            storage_url=storage_result["url"]
        )

        return ImageUploadResponse(
            success=True,
            message="图像上传成功",
            image=ImageResponse.from_orm(image_record)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"上传失败: {str(e)}"
        )


@router.post("/images/upload/batch", response_model=List[ImageUploadResponse])
async def upload_images_batch(
    files: List[UploadFile] = File(..., description="图像文件列表（最多9张）"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量上传图像文件（最多9张）"""

    if len(files) > 9:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="批量上传最多支持9张图片"
        )

    if len(files) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请至少选择一张图片"
        )

    results = []

    for file in files:
        try:
            # 验证文件格式
            if not validate_file_format(file.filename):
                results.append(ImageUploadResponse(
                    success=False,
                    message=f"文件 {file.filename} 格式不支持",
                    image=None
                ))
                continue

            # 读取文件内容
            file_content = await file.read()

            # 验证文件大小
            if not validate_file_size(file_content):
                results.append(ImageUploadResponse(
                    success=False,
                    message=f"文件 {file.filename} 大小超过限制",
                    image=None
                ))
                continue

            # 生成唯一文件名
            file_extension = file.filename.rsplit(".", 1)[1].lower()
            unique_filename = f"{uuid.uuid4()}.{file_extension}"

            # 初始化服务
            storage_service = StorageService()
            image_service = ImageService(db)

            # 上传文件到存储
            storage_result = await storage_service.upload_image(
                file_content=file_content,
                filename=unique_filename,
                content_type=file.content_type
            )

            # 保存图像记录到数据库
            image_record = image_service.create_image_record(
                user_id=current_user.id,
                original_filename=file.filename,
                filename=unique_filename,
                file_size=len(file_content),
                file_format=file_extension,
                mime_type=file.content_type,
                storage_path=storage_result["path"],
                storage_url=storage_result["url"]
            )

            results.append(ImageUploadResponse(
                success=True,
                message="上传成功",
                image=ImageResponse.from_orm(image_record)
            ))

        except Exception as e:
            results.append(ImageUploadResponse(
                success=False,
                message=f"上传失败: {str(e)}",
                image=None
            ))

    return results


@router.get("/images", response_model=ImageListResponse)
async def get_images(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户图像列表"""

    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 20
    if per_page > 100:
        per_page = 100

    image_service = ImageService(db)

    images, total = image_service.get_user_images(
        user_id=current_user.id,
        page=page,
        per_page=per_page
    )

    return ImageListResponse(
        images=[ImageResponse.from_orm(image) for image in images],
        total=total,
        page=page,
        per_page=per_page,
        has_next=page * per_page < total,
        has_prev=page > 1
    )


@router.get("/images/detail", response_model=ImageResponse)
async def get_image(
    image_id: int = Query(..., description="图像ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取图像详情"""

    image_service = ImageService(db)
    image = image_service.get_image_by_id(image_id, current_user.id)

    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="图像不存在"
        )

    return ImageResponse.from_orm(image)


@router.post("/images/delete")
async def delete_image(
    request: DeleteImageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除图像"""

    image_service = ImageService(db)
    image = image_service.get_image_by_id(request.image_id, current_user.id)

    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="图像不存在"
        )

    # 删除存储文件
    storage_service = StorageService()
    await storage_service.delete_image(image.storage_path)

    # 删除数据库记录
    image_service.delete_image(request.image_id, current_user.id)

    return {"success": True, "message": "图像删除成功"}


@router.post("/images/process", response_model=ProcessingJobCreateResponse)
async def create_processing_job(
    request: ImageIdRequest,
    job_data: ProcessingJobCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建图像处理任务"""

    # 验证图像是否存在且属于当前用户
    image_service = ImageService(db)
    image = image_service.get_image_by_id(request.image_id, current_user.id)

    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="图像不存在"
        )

    # 创建处理任务
    processing_job = image_service.create_processing_job(
        image_id=request.image_id,
        user_id=current_user.id,
        operation_type=job_data.operation_type,
        parameters=job_data.parameters or {}
    )

    return ProcessingJobCreateResponse(
        success=True,
        message="处理任务创建成功",
        job=ProcessingJobResponse.from_orm(processing_job)
    )


@router.get("/images/jobs", response_model=ProcessingJobResponse)
async def get_processing_job(
    job_id: int = Query(..., description="处理任务ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取处理任务状态"""

    image_service = ImageService(db)
    job = image_service.get_processing_job_by_id(job_id, current_user.id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="处理任务不存在"
        )

    return ProcessingJobResponse.from_orm(job)
