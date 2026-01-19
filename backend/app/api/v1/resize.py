"""
尺寸适配API
提供图像尺寸调整和平台适配接口
"""
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from app.core.response import ErrCode, error_response, success_response
from app.services.resize_service import resize_service

router = APIRouter()


class ResizeRequestCombined(BaseModel):
    """组合的调整尺寸请求"""
    image_id: int
    width: int = Field(..., gt=0, le=4096, description="目标宽度")
    height: int = Field(..., gt=0, le=4096, description="目标高度")
    maintain_aspect_ratio: bool = Field(True, description="是否保持宽高比")
    resample_method: Optional[str] = Field("lanczos", description="重采样方法")
    fit_mode: Optional[str] = Field("contain", description="适配模式")
    background_color: Optional[str] = Field("#FFFFFF", description="背景颜色")


class CropRequest(BaseModel):
    """裁剪请求"""
    ratio: str = Field(..., description="裁剪比例，如 16:9, 1:1")
    position: Optional[str] = Field("center", description="裁剪位置")


class SmartResizeRequest(BaseModel):
    """智能调整请求"""
    max_width: int = Field(2048, ge=100, le=4096)
    max_height: int = Field(2048, ge=100, le=4096)
    resample_method: Optional[str] = Field("lanczos", description="重采样方法")


class ImageIdRequest(BaseModel):
    """图像ID请求"""
    image_id: int


class PlatformPresetResponse(BaseModel):
    """平台预设响应"""
    id: str
    name: str
    width: int
    height: int
    description: str


@router.get("/presets")
async def get_presets(category: Optional[str] = None):
    """获取平台尺寸预设列表"""
    presets = resize_service.get_presets(category)
    return success_response({"presets": presets})


@router.get("/categories")
async def get_categories():
    """获取预设分类列表"""
    return success_response({"categories": resize_service.get_categories()})


@router.get("/status")
async def get_resize_status():
    """获取尺寸调整服务状态"""
    return success_response(resize_service.get_status())


@router.post("/resize")
async def resize_image(request: ResizeRequestCombined):
    """调整图片尺寸"""
    try:
        # TODO: 从数据库获取图片
        # image = await get_image_by_id(request.image_id, current_user)

        # 这里需要实现从存储加载图片的逻辑
        # image = load_image_from_storage(image.storage_path)

        # 执行调整尺寸
        # result_image = resize_service.resize_image(
        #     image,
        #     request.width,
        #     request.height,
        #     request.maintain_aspect_ratio,
        #     request.resample_method,
        #     request.fit_mode,
        #     request.background_color,
        # )

        # 保存结果
        # result_path = save_image_to_storage(result_image)

        return success_response({
            "success": True,
            "message": "尺寸调整功能开发中",
            "image_id": request.image_id,
            "params": {
                "width": request.width,
                "height": request.height,
                "maintain_aspect_ratio": request.maintain_aspect_ratio,
                "resample_method": request.resample_method,
                "fit_mode": request.fit_mode,
                "background_color": request.background_color,
            },
        })

    except ValueError as e:
        return error_response(ErrCode.INVALID_REQUEST, custom_message=str(e))
    except Exception as e:
        return error_response(ErrCode.INTERNAL_ERROR, custom_message=f"尺寸调整失败: {str(e)}")


@router.post("/crop")
async def crop_image(request: ImageIdRequest, crop_params: CropRequest):
    """按比例裁剪图片"""
    try:
        # TODO: 实现裁剪逻辑

        return success_response({
            "success": True,
            "message": "裁剪功能开发中",
            "image_id": request.image_id,
            "params": crop_params.dict(),
        })

    except ValueError as e:
        return error_response(ErrCode.INVALID_REQUEST, custom_message=str(e))
    except Exception as e:
        return error_response(ErrCode.INTERNAL_ERROR, custom_message=f"裁剪失败: {str(e)}")


@router.post("/smart-resize")
async def smart_resize(request: ImageIdRequest, smart_params: SmartResizeRequest):
    """智能调整图片尺寸（限制最大尺寸）"""
    try:
        # TODO: 实现智能调整逻辑

        return success_response({
            "success": True,
            "message": "智能调整功能开发中",
            "image_id": request.image_id,
            "params": smart_params.dict(),
        })

    except Exception as e:
        return error_response(ErrCode.INTERNAL_ERROR, custom_message=f"智能调整失败: {str(e)}")
