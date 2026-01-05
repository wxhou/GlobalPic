# Tasks: Replace Celery with BackgroundTasks

## Phase 1: 重构图像处理 API

- [x] 1.1 创建 `BackgroundTaskProcessor` 服务类
  - 将 `processing_tasks.py` 中的处理逻辑迁移为普通函数
  - 添加异步支持和错误处理
  
- [x] 1.2 更新图像处理 API 端点
  - 修改 `/api/v1/images/{id}/process` 使用 BackgroundTasks
  - 添加任务状态查询端点

- [x] 1.3 实现手动重试逻辑
  - 在 API 中添加重试端点
  - 记录重试次数

## Phase 2: 移除 Celery 代码

- [x] 2.1 删除 `backend/app/tasks/celery_app.py`
- [x] 2.2 删除 `backend/app/tasks/processing_tasks.py`
- [x] 2.3 清理 `backend/app/tasks/__init__.py`
- [x] 2.4 更新 `requirements.txt` 移除 celery 相关依赖

## Phase 3: 更新部署配置

- [x] 3.1 更新 `docker-compose.yml` 移除 celery_worker 服务
- [x] 3.2 更新 `.env.example` 移除 Celery 配置

## Phase 4: 测试验证

- [ ] 4.1 编写测试用例验证 BackgroundTasks 功能
- [ ] 4.2 测试任务状态追踪
- [ ] 4.3 测试重试功能

## 验证标准
- [x] API 响应时间 < 5秒（任务立即返回，状态通过 API 查询）
- [ ] 单元测试覆盖率 > 80%
- [x] docker-compose 服务数量减少
