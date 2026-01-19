"""
图像服务 - 处理图像相关业务逻辑（异步版本）

使用 SQLAlchemy AsyncSession 进行异步数据库操作
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, desc, select, func, delete
from typing import List, Tuple, Optional
from datetime import datetime, timedelta
import json

from app.models.image import Image, ProcessingJob
from app.models.user import User
from app.schemas.image import ImageStatus, ProcessingStatus, OperationType


class ImageService:
    """图像服务 - 处理图像相关业务逻辑"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_image_record(
        self,
        user_id: int,
        original_filename: str,
        filename: str,
        file_size: int,
        file_format: str,
        mime_type: str,
        storage_path: str,
        storage_url: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> Image:
        """创建图像记录"""
        
        # 生成存储路径和URL
        storage_provider = "local"  # 默认为本地存储
        
        # 创建图像记录
        image = Image(
            user_id=user_id,
            original_filename=original_filename,
            filename=filename,
            file_size=file_size,
            file_format=file_format,
            mime_type=mime_type,
            width=width,
            height=height,
            storage_path=storage_path,
            storage_url=storage_url,
            storage_provider=storage_provider,
            is_processed=False,
            processing_status=ImageStatus.PENDING.value,
            tags=json.dumps(tags) if tags else None
        )
        
        self.db.add(image)
        await self.db.commit()
        await self.db.refresh(image)
        
        return image
    
    async def get_user_images(
        self,
        user_id: int,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[Image], int]:
        """获取用户图像列表"""
        
        # 查询总数
        total_result = await self.db.execute(
            select(func.count(Image.id)).where(Image.user_id == user_id)
        )
        total = total_result.scalar_one()
        
        # 分页查询
        offset = (page - 1) * per_page
        result = await self.db.execute(
            select(Image)
            .where(Image.user_id == user_id)
            .order_by(desc(Image.created_at))
            .offset(offset)
            .limit(per_page)
        )
        images = result.scalars().all()
        
        return list(images), total
    
    async def get_image_by_id(self, image_id: int, user_id: int) -> Optional[Image]:
        """根据ID获取图像"""
        
        result = await self.db.execute(
            select(Image).where(and_(Image.id == image_id, Image.user_id == user_id))
        )
        return result.scalar_one_or_none()
    
    async def delete_image(self, image_id: int, user_id: int) -> bool:
        """删除图像"""
        
        image = await self.get_image_by_id(image_id, user_id)
        if not image:
            return False
        
        # 删除相关处理任务
        await self.db.execute(
            delete(ProcessingJob).where(ProcessingJob.image_id == image_id)
        )
        
        # 删除图像记录
        await self.db.delete(image)
        await self.db.commit()
        
        return True
    
    async def create_processing_job(
        self,
        image_id: int,
        user_id: int,
        operation_type: str,
        parameters: Optional[dict] = None
    ) -> ProcessingJob:
        """创建处理任务"""
        
        # 验证图像是否存在且属于当前用户
        image = await self.get_image_by_id(image_id, user_id)
        if not image:
            raise ValueError("图像不存在或无权限访问")
        
        # 创建处理任务
        job = ProcessingJob(
            image_id=image_id,
            user_id=user_id,
            operation_type=operation_type,
            parameters=json.dumps(parameters) if parameters else None,
            status=ProcessingStatus.PENDING.value,
            progress=0
        )
        
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)
        
        # 更新图像处理状态
        image.processing_status = ImageStatus.PENDING.value
        await self.db.commit()
        
        return job
    
    async def get_processing_job_by_id(self, job_id: int, user_id: int) -> Optional[ProcessingJob]:
        """根据ID获取处理任务"""
        
        result = await self.db.execute(
            select(ProcessingJob).where(
                and_(ProcessingJob.id == job_id, ProcessingJob.user_id == user_id)
            )
        )
        return result.scalar_one_or_none()
    
    async def update_processing_job_status(
        self,
        job_id: int,
        status: str,
        progress: Optional[int] = None,
        result_path: Optional[str] = None,
        result_urls: Optional[List[str]] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """更新处理任务状态"""
        
        result = await self.db.execute(
            select(ProcessingJob).where(ProcessingJob.id == job_id)
        )
        job = result.scalar_one_or_none()
        if not job:
            return False
        
        job.status = status
        
        if progress is not None:
            job.progress = progress
        
        if result_path is not None:
            job.result_path = result_path
        
        if result_urls is not None:
            job.result_urls = json.dumps(result_urls)
        
        if error_message is not None:
            job.error_message = error_message
        
        # 设置时间戳
        if status == ProcessingStatus.PROCESSING.value and not job.started_at:
            job.started_at = datetime.utcnow()
        elif status in [ProcessingStatus.COMPLETED.value, ProcessingStatus.FAILED.value]:
            job.completed_at = datetime.utcnow()
        
        await self.db.commit()
        
        # 如果任务完成，更新图像状态
        if status == ProcessingStatus.COMPLETED.value:
            img_result = await self.db.execute(
                select(Image).where(Image.id == job.image_id)
            )
            image = img_result.scalar_one_or_none()
            if image:
                image.is_processed = True
                image.processing_status = ImageStatus.COMPLETED.value
                image.processed_at = datetime.utcnow()
                await self.db.commit()
        elif status == ProcessingStatus.FAILED.value:
            img_result = await self.db.execute(
                select(Image).where(Image.id == job.image_id)
            )
            image = img_result.scalar_one_or_none()
            if image:
                image.processing_status = ImageStatus.FAILED.value
                image.error_message = error_message
                await self.db.commit()
        
        return True
    
    async def get_user_processing_jobs(
        self,
        user_id: int,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[ProcessingJob], int]:
        """获取用户处理任务列表"""
        
        query = select(ProcessingJob).where(ProcessingJob.user_id == user_id)
        
        if status:
            query = query.where(ProcessingJob.status == status)
        
        # 查询总数
        count_result = await self.db.execute(
            select(func.count(ProcessingJob.id)).select_from(query.subquery())
        )
        total = count_result.scalar_one()
        
        # 分页查询
        offset = (page - 1) * per_page
        result = await self.db.execute(
            query.order_by(desc(ProcessingJob.created_at))
            .offset(offset)
            .limit(per_page)
        )
        jobs = result.scalars().all()
        
        return list(jobs), total
    
    async def cleanup_old_images(self, days: int = 30) -> int:
        """清理旧的未处理图像"""
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # 查找旧的未处理图像
        result = await self.db.execute(
            select(Image).where(
                and_(
                    Image.created_at < cutoff_date,
                    Image.is_processed == False
                )
            )
        )
        old_images = result.scalars().all()
        
        deleted_count = 0
        for image in old_images:
            # 删除相关处理任务
            await self.db.execute(
                delete(ProcessingJob).where(ProcessingJob.image_id == image.id)
            )
            
            # 删除图像记录
            await self.db.delete(image)
            deleted_count += 1
        
        await self.db.commit()
        return deleted_count
