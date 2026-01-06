# Async Processing Specification

## MODIFIED Requirements

### Requirement: Celery任务队列
图像处理任务实现方式 MUST 从 Celery 迁移到 BackgroundTasks

#### Scenario: 提交图像处理任务
**Given** 用户已上传图像并选择处理参数
**When** 用户提交处理请求
**Then** API 立即返回任务 ID，状态为 `pending`
**And** 处理任务在后台异步执行
**And** 用户可以通过任务 ID 查询处理状态

#### Scenario: 查询任务状态
**Given** 用户已提交处理任务
**When** 用户查询任务状态
**Then** 返回当前处理进度（0-100）
**And** 返回当前状态（pending/processing/completed/failed）
**And** 完成后返回结果 URL

#### Scenario: 任务失败重试
**Given** 图像处理任务失败
**When** 用户请求重试任务
**Then** 创建新的处理任务，继承原参数
**And** 重试次数记录在数据库中
**And** 超过最大重试次数后拒绝再次重试

#### REMOVED: Celery Worker Configuration
- 移除 `celery_app.py` 中的 Worker 配置
- 移除 `processing_tasks.py` 中的 `@celery_app.task` 装饰器
- 移除 Celery Beat 定时任务配置

#### ADDED: BackgroundTask Service
```python
from fastapi import BackgroundTasks

class BackgroundTaskProcessor:
    """后台任务处理器"""

    async def process_image(
        self,
        background_tasks: BackgroundTasks,
        job_id: int,
        image_id: int,
        user_id: int,
        operation_type: str,
        parameters: dict
    ) -> int:
        """提交图像处理任务到后台"""
        # 创建任务记录
        task = ProcessingTask(
            job_id=job_id,
            image_id=image_id,
            user_id=user_id,
            operation_type=operation_type,
            parameters=parameters,
            status=ProcessingStatus.PENDING
        )

        # 添加到后台任务
        background_tasks.add_task(
            self._execute_processing,
            job_id=job_id,
            image_id=image_id,
            user_id=user_id,
            operation_type=operation_type,
            parameters=parameters
        )

        return task.id
```

#### REMOVED Environment Variables
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- `CELERY_CONCURRENCY`

#### MODIFIED Environment Variables
- `REDIS_URL` - 保留用于缓存，不再用于 Celery
