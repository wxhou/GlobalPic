from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.core.response import ErrCode, error_response, success_response
from app.models.user import User
from app.services.copywriting_service import copywriting_service

router = APIRouter()


class CopywritingGenerateRequest(BaseModel):
    """文案生成请求"""
    image_description: str
    product_name: Optional[str] = None
    platform: str = "amazon"
    count: int = 5
    tone: str = "professional"


@router.get("/platforms")
async def get_supported_platforms():
    """获取支持的平台列表"""
    return success_response({
        "platforms": [
            {"id": "amazon", "name": "亚马逊", "description": "适合亚马逊Listing"},
            {"id": "tiktok", "name": "TikTok", "description": "适合短视频营销"},
            {"id": "instagram", "name": "Instagram", "description": "适合社交媒体"},
            {"id": "独立站", "name": "独立站", "description": "适合自建站"},
        ]
    })


@router.post("/generate")
async def generate_copywriting(
    request: CopywritingGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """生成营销文案"""
    try:
        result = await copywriting_service.generate(
            image_description=request.image_description,
            platform=request.platform,
            product_name=request.product_name,
            count=request.count,
            tone=request.tone,
        )

        if result["success"]:
            return success_response({
                "success": True,
                "copywrites": result.get("copywrites", []),
                "keywords": result.get("keywords", []),
                "platform": result.get("platform"),
                "processing_time": result.get("processing_time", 0),
                "mock": result.get("mock", False)
            })
        else:
            return error_response(ErrCode.PROCESSING_FAILED, custom_message=result.get("error", "文案生成失败"))

    except Exception as e:
        return error_response(ErrCode.INTERNAL_ERROR, custom_message=f"文案生成失败: {str(e)}")


@router.get("/status")
async def get_copywriting_status():
    """获取文案服务状态"""
    return success_response(copywriting_service.get_status())
