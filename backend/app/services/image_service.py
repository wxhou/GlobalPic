from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import List, Tuple, Optional
from datetime import datetime, timedelta
import json

from app.models.image import Image, ProcessingJob
from app.models.user import User
from app.schemas.image import ImageStatus, ProcessingStatus, OperationType

class ImageService:
    """图像服务 - 处理图像相关业务逻辑"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_image_record(
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
            processing_status=ImageStatus.PENDING,
            tags=json.dumps(tags) if tags else None
        )
        
        self.db.add(image)
        self.db.commit()
        self.db.refresh(image)
        
        return image
    
    def get_user_images(
        self,
        user_id: int,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[Image], int]:
        """获取用户图像列表"""
        
        # 查询总数
        total = self.db.query(Image).filter(Image.user_id == user_id).count()
        
        # 分页查询
        offset = (page - 1) * per_page
        images = (
            self.db.query(Image)
            .filter(Image.user_id == user_id)
            .order_by(desc(Image.created_at))
            .offset(offset)
            .limit(per_page)
            .all()
        )
        
        return images, total
    
    def get_image_by_id(self, image_id: int, user_id: int) -> Optional[Image]:
        """根据ID获取图像"""
        
        return (
            self.db.query(Image)
            .filter(and_(Image.id == image_id, Image.user_id == user_id))
            .first()
        )
    
    def delete_image(self, image_id: int, user_id: int) -> bool:
        """删除图像"""
        
        image = self.get_image_by_id(image_id, user_id)
        if not image:
            return False
        
        # 删除相关处理任务
        self.db.query(ProcessingJob).filter(ProcessingJob.image_id == image_id).delete()
        
        # 删除图像记录
        self.db.delete(image)
        self.db.commit()
        
        return True
    
    def create_processing_job(
        self,
        image_id: int,
        user_id: int,
        operation_type: OperationType,
        parameters: Optional[dict] = None
    ) -> ProcessingJob:
        """创建处理任务"""
        
        # 验证图像是否存在且属于当前用户
        image = self.get_image_by_id(image_id, user_id)
        if not image:
            raise ValueError("图像不存在或无权限访问")
        
        # 创建处理任务
        job = ProcessingJob(
            image_id=image_id,
            user_id=user_id,
            operation_type=operation_type.value,
            parameters=json.dumps(parameters) if parameters else None,
            status=ProcessingStatus.PENDING,
            progress=0
        )
        
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        
        # 更新图像处理状态
        image.processing_status = ImageStatus.PENDING
        self.db.commit()
        
        return job
    
    def get_processing_job_by_id(self, job_id: int, user_id: int) -> Optional[ProcessingJob]:
        """根据ID获取处理任务"""
        
        return (
            self.db.query(ProcessingJob)
            .filter(and_(ProcessingJob.id == job_id, ProcessingJob.user_id == user_id))
            .first()
        )
    
    def update_processing_job_status(
        self,
        job_id: int,
        status: ProcessingStatus,
        progress: Optional[int] = None,
        result_path: Optional[str] = None,
        result_urls: Optional[List[str]] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """更新处理任务状态"""
        
        job = self.db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
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
        if status == ProcessingStatus.PROCESSING and not job.started_at:
            job.started_at = datetime.utcnow()
        elif status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]:
            job.completed_at = datetime.utcnow()
        
        self.db.commit()
        
        # 如果任务完成，更新图像状态
        if status == ProcessingStatus.COMPLETED:
            image = self.db.query(Image).filter(Image.id == job.image_id).first()
            if image:
                image.is_processed = True
                image.processing_status = ImageStatus.COMPLETED
                image.processed_at = datetime.utcnow()
                self.db.commit()
        elif status == ProcessingStatus.FAILED:
            image = self.db.query(Image).filter(Image.id == job.image_id).first()
            if image:
                image.processing_status = ImageStatus.FAILED
                image.error_message = error_message
                self.db.commit()
        
        return True
    
    def get_user_processing_jobs(
        self,
        user_id: int,
        status: Optional[ProcessingStatus] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[ProcessingJob], int]:
        """获取用户处理任务列表"""
        
        query = self.db.query(ProcessingJob).filter(ProcessingJob.user_id == user_id)
        
        if status:
            query = query.filter(ProcessingJob.status == status)
        
        # 查询总数
        total = query.count()
        
        # 分页查询
        offset = (page - 1) * per_page
        jobs = (
            query.order_by(desc(ProcessingJob.created_at))
            .offset(offset)
            .limit(per_page)
            .all()
        )
        
        return jobs, total
    
    def cleanup_old_images(self, days: int = 30) -> int:
        """清理旧的未处理图像"""
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # 查找旧的未处理图像
        old_images = (
            self.db.query(Image)
            .filter(
                and_(
                    Image.created_at < cutoff_date,
                    Image.is_processed == False
                )
            )
            .all()
        )
        
        deleted_count = 0
        for image in old_images:
            # 删除相关处理任务
            self.db.query(ProcessingJob).filter(ProcessingJob.image_id == image.id).delete()
            
            # 删除图像记录
            self.db.delete(image)
            deleted_count += 1
        
        self.db.commit()
        return deleted_count