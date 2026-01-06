# Proposal: Replace Celery with BackgroundTasks

## Summary
将图像处理任务从 Celery 任务队列迁移到 FastAPI 的 BackgroundTasks，简化架构并移除 Celery 依赖。

## Problem Statement
当前系统使用 Celery 作为异步任务队列，需要额外运行 Worker 进程，增加了架构复杂度和运维成本。

### 当前问题
1. **额外基础设施**：需要运行 Celery Worker 和 Beat 服务
2. **资源消耗**：Celery Worker 持续占用内存
3. **配置复杂**：需要配置 Broker 和 Result Backend
4. **调试困难**：任务状态分散在多个进程中

## Proposed Solution
使用 FastAPI 内置的 `BackgroundTasks` 替代 Celery，将异步任务直接在 API 进程中执行。

### 优势
1. **简化架构**：无需额外 Worker 进程
2. **降低资源消耗**：按需执行任务
3. **简化部署**：减少容器数量
4. **统一监控**：所有任务在同一进程中

### 限制
1. **无持久化**：服务重启后任务丢失（可接受，因为有状态API）
2. **单节点限制**：任务只在单个节点执行
3. **无自动重试**：需要手动实现重试逻辑

## Scope
- 移除 Celery 相关代码和配置
- 重构图像处理 API 使用 BackgroundTasks
- 保留处理状态追踪功能
- 更新 docker-compose.yml 移除 celery_worker 服务

## Dependencies
- 无外部依赖变化
- 保持 Redis 用于缓存

## Timeline
- Phase 1: 重构 API 端点使用 BackgroundTasks
- Phase 2: 移除 Celery 代码
- Phase 3: 更新部署配置

## Risks and Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| 服务重启丢失任务 | 中 | 任务状态持久化到数据库 |
| 单节点性能限制 | 低 | 小规模部署场景可接受 |
| 无自动重试 | 低 | 实现手动重试逻辑 |

## Success Criteria
1. 图像处理 API 正常工作
2. docker-compose 服务数量减少
3. 单元测试通过
