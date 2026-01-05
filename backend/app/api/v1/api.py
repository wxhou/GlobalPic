from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.images import router as images_router
from app.api.v1.processing import router as processing_router

api_router = APIRouter()

# 认证相关路由
api_router.include_router(auth_router, prefix="/auth", tags=["authentication"])

# 图像相关路由
api_router.include_router(images_router, prefix="/images", tags=["images"])

# AI处理相关路由
api_router.include_router(processing_router, prefix="/processing", tags=["processing"])

# TODO: 添加其他模块路由
# from app.api.v1.users import router as users_router
# api_router.include_router(users_router, prefix="/users", tags=["users"])