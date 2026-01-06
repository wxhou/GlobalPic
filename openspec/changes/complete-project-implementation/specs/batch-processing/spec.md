# Batch Processing Specification

## ADDED Requirements

### Requirement: 批量任务创建
系统 MUST 支持最多50张图片的批量处理

#### Scenario: 批量上传
**Given** 用户选择了多张图片
**When** 用户提交批量处理请求
**Then** 系统验证图片数量 (最多50张)
**And** 创建批量任务记录
**And** 返回任务ID和预估时间
**And** 任务状态为 pending

#### Scenario: 参数统一配置
**Given** 用户选择了处理参数
**When** 创建批量任务
**Then** 参数应用到所有图片
**And** 支持单张图片单独参数
**And** 参数包含处理类型、风格等

### Requirement: 任务队列管理
系统 MUST 实现高效的批量任务队列

#### Scenario: 任务调度
**Given** 批量任务进入队列
**When** 调度器处理任务
**Then** 按创建时间顺序处理
**And** 支持任务优先级设置
**And** 失败任务自动重试 (最多3次)

#### Scenario: 进度跟踪
**Given** 批量任务正在处理
**When** 用户查询进度
**Then** 返回当前处理数量
**And** 返回成功/失败计数
**And** 返回预估剩余时间

### Requirement: 并行处理
系统 MUST 支持多图并行处理

#### Scenario: GPU批处理
**Given** 多个图片等待处理
**When** GPU资源充足
**Then** 自动合并为批处理
**And** 批大小根据GPU内存动态调整
**And** 批处理比单独处理快 > 30%

#### Scenario: CPU并行
**Given** 不需要GPU的处理步骤
**When** 执行OCR或后处理
**Then** 使用多进程并行处理
**And** 进程数 = CPU核心数
**And** 内存使用可控

### Requirement: 结果处理
系统 MUST 提供便捷的结果获取方式

#### Scenario: 单张结果获取
**Given** 单张图片处理完成
**When** 用户查询单张结果
**Then** 返回处理后的图片URL
**And** 返回质量评分
**And** 支持预览和下载

#### Scenario: 批量下载
**Given** 批量任务全部完成
**When** 用户请求批量下载
**Then** 系统打包所有结果为ZIP
**And** ZIP包含原图和处理后图片
**And** 生成24小时有效下载链接

#### Scenario: 结果预览
**Given** 批量任务完成
**When** 用户查看结果
**Then** 以网格形式展示所有图片
**And** 支持放大查看单张
**And** 支持标记和筛选

## MODIFIED Requirements

### Requirement: async-processing: 批量处理
BackgroundTasks MUST 支持多图并行处理

#### ADDED: Batch Processor
```python
class BatchProcessor:
    """批量处理服务"""

    def __init__(
        self,
        zimage_service: ZImageService,
        sam_service: SAMService,
        ocr_service: OCRService
    ):
        self.zimage = zimage_service
        self.sam = sam_service
        self.ocr = ocr_service

    async def process_batch(
        self,
        image_paths: List[str],
        operations: List[str],
        style_id: str = "minimal_white"
    ) -> BatchResult:
        """处理批量图片"""
        # 创建任务记录
        task = await self._create_batch_task(image_paths, operations)

        results = []
        for i, image_path in enumerate(image_paths):
            try:
                result = await self._process_single(
                    image_path,
                    operations,
                    style_id
                )
                results.append({
                    "index": i,
                    "success": True,
                    "result": result
                })
            except Exception as e:
                results.append({
                    "index": i,
                    "success": False,
                    "error": str(e)
                })

        # 更新任务状态
        task.completed_at = datetime.now()
        task.results = results

        return task

    async def generate_download_package(
        self,
        task_id: str
    ) -> str:
        """生成下载ZIP包"""
        task = await self._get_task(task_id)
        zip_path = f"/tmp/batch_{task_id}.zip"

        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for result in task.results:
                if result["success"]:
                    zipf.write(
                        result["output_path"],
                        f"processed_{result['index']}.jpg"
                    )

        return await self._upload_to_storage(zip_path)
```

#### MODIFIED: Task Status Tracking
- 新增: batch_tasks 表存储批量任务
- 新增: batch_task_items 表存储单张处理状态
- 新增: WebSocket推送进度更新
- 新增: ZIP打包和下载API
