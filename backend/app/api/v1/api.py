from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.images import router as images_router
from app.api.v1.processing import router as processing_router
from app.api.v1.copywriting import router as copywriting_router
from app.api.v1.batch import router as batch_router
from app.api.v1.subscription import router as subscription_router
from app.api.v1.resize import router as resize_router

api_router = APIRouter()

# 认证相关路由
api_router.include_router(auth_router, prefix="/auth", tags=["authentication"])

# 图像相关路由
api_router.include_router(images_router, prefix="/images", tags=["images"])

# AI处理相关路由
api_router.include_router(processing_router, prefix="/processing", tags=["processing"])

# 文案生成路由
api_router.include_router(copywriting_router, prefix="/copywriting", tags=["copywriting"])

# 批量处理路由
api_router.include_router(batch_router, prefix="/batch", tags=["batch"])

# 订阅和支付路由
api_router.include_router(subscription_router, prefix="/subscription", tags=["subscription"])

# 尺寸适配路由
api_router.include_router(resize_router, prefix="", tags=["resize"])