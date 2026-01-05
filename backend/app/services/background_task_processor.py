"""
后台任务处理器
使用 FastAPI BackgroundTasks 替代 Celery 进行图像处理
"""
import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai_processor import ai_processor
from app.services.image_service import ImageService
from app.schemas.image import ProcessingStatus, OperationType

logger = logging.getLogger(__name__)


class BackgroundTaskProcessor:
    """后台任务处理器"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def _update_job_status(
        self,
        job_id: int,
        status: ProcessingStatus,
        progress: int = 0,
        error_message: Optional[str] = None,
        result_urls: Optional[list] = None
    ) -> None:
        """更新任务状态"""
        image_service = ImageService(self.db)
        image_service.update_processing_job_status(
            job_id=job_id,
            status=status,
            progress=progress,
            error_message=error_message,
            result_urls=result_urls
        )
    
    async def process_text_removal(
        self,
        job_id: int,
        image_id: int,
        user_id: int,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        文字抹除处理任务
        
        Args:
            job_id: 处理任务ID
            image_id: 图像ID
            user_id: 用户ID
            parameters: 处理参数
        """
        logger.info(f"开始文字抹除处理任务: job_id={job_id}, image_id={image_id}")
        
        try:
            image_service = ImageService(self.db)
            
            # 获取图像信息
            image = image_service.get_image_by_id(image_id, user_id)
            if not image:
                raise ValueError(f"图像不存在: image_id={image_id}")
            
            # 更新任务状态为处理中
            await self._update_job_status(
                job_id=job_id,
                status=ProcessingStatus.PROCESSING,
                progress=10
            )
            
            # 调用AI处理器
            import asyncio
            result = await ai_processor.process_image(
                image_path=image.storage_path,
                operation_type="text_removal",
                parameters=parameters
            )
            
            if result["success"]:
                # 更新任务完成
                await self._update_job_status(
                    job_id=job_id,
                    status=ProcessingStatus.COMPLETED,
                    progress=100,
                    result_urls=result["result"]["output_urls"]
                )
                logger.info(f"文字抹除处理完成: job_id={job_id}")
                return {"success": True, "result": result["result"]}
            else:
                # 处理失败
                logger.error(f"文字抹除处理失败: {result.get('error')}")
                await self._update_job_status(
                    job_id=job_id,
                    status=ProcessingStatus.FAILED,
                    error_message=result.get('error')
                )
                return {"success": False, "error": result.get('error')}
        
        except Exception as e:
            logger.error(f"文字抹除处理异常: {e}")
            await self._update_job_status(
                job_id=job_id,
                status=ProcessingStatus.FAILED,
                error_message=str(e)
            )
            return {"success": False, "error": str(e)}
    
    async def process_background_replacement(
        self,
        job_id: int,
        image_id: int,
        user_id: int,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        背景重绘处理任务
        
        Args:
            job_id: 处理任务ID
            image_id: 图像ID
            user_id: 用户ID
            parameters: 处理参数
        """
        logger.info(f"开始背景重绘处理任务: job_id={job_id}, image_id={image_id}")
        
        try:
            image_service = ImageService(self.db)
            
            # 获取图像信息
            image = image_service.get_image_by_id(image_id, user_id)
            if not image:
                raise ValueError(f"图像不存在: image_id={image_id}")
            
            # 更新任务状态为处理中
            await self._update_job_status(
                job_id=job_id,
                status=ProcessingStatus.PROCESSING,
                progress=10
            )
            
            # 调用AI处理器
            result = await ai_processor.process_image(
                image_path=image.storage_path,
                operation_type="background_replacement",
                parameters=parameters
            )
            
            if result["success"]:
                # 更新任务完成
                await self._update_job_status(
                    job_id=job_id,
                    status=ProcessingStatus.COMPLETED,
                    progress=100,
                    result_urls=result["result"]["output_urls"]
                )
                logger.info(f"背景重绘处理完成: job_id={job_id}")
                return {"success": True, "result": result["result"]}
            else:
                # 处理失败
                logger.error(f"背景重绘处理失败: {result.get('error')}")
                await self._update_job_status(
                    job_id=job_id,
                    status=ProcessingStatus.FAILED,
                    error_message=result.get('error')
                )
                return {"success": False, "error": result.get('error')}
        
        except Exception as e:
            logger.error(f"背景重绘处理异常: {e}")
            await self._update_job_status(
                job_id=job_id,
                status=ProcessingStatus.FAILED,
                error_message=str(e)
            )
            return {"success": False, "error": str(e)}
    
    async def process_image(
        self,
        job_id: int,
        image_id: int,
        user_id: int,
        operation_type: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        统一图像处理入口
        
        Args:
            job_id: 处理任务ID
            image_id: 图像ID
            user_id: 用户ID
            operation_type: 操作类型
            parameters: 处理参数
        """
        if operation_type == OperationType.TEXT_REMOVAL:
            return await self.process_text_removal(
                job_id=job_id,
                image_id=image_id,
                user_id=user_id,
                parameters=parameters
            )
        elif operation_type == OperationType.BACKGROUND_REPLACEMENT:
            return await self.process_background_replacement(
                job_id=job_id,
                image_id=image_id,
                user_id=user_id,
                parameters=parameters
            )
        else:
            error_msg = f"不支持的操作类型: {operation_type}"
            await self._update_job_status(
                job_id=job_id,
                status=ProcessingStatus.FAILED,
                error_message=error_msg
            )
            return {"success": False, "error": error_msg}
