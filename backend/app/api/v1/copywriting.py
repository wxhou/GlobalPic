from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.api.v1.auth import get_current_user
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


class CopywritingResponse(BaseModel):
    """文案响应"""
    title: str
    bullets: List[str]
    description: str


class CopywritingResultResponse(BaseModel):
    """文案生成结果响应"""
    success: bool
    copywrites: List[dict]
    keywords: List[str]
    platform: str
    processing_time: float
    mock: Optional[bool] = None


@router.get("/platforms", response_model=List[dict])
async def get_supported_platforms():
    """获取支持的平台列表"""
    return [
        {"id": "amazon", "name": "亚马逊", "description": "适合亚马逊Listing"},
        {"id": "tiktok", "name": "TikTok", "description": "适合短视频营销"},
        {"id": "instagram", "name": "Instagram", "description": "适合社交媒体"},
        {"id": "独立站", "name": "独立站", "description": "适合自建站"},
    ]


@router.post("/generate", response_model=CopywritingResultResponse)
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
            return CopywritingResultResponse(**result)
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "文案生成失败")
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文案生成失败: {str(e)}"
        )


@router.get("/status")
async def get_copywriting_status():
    """获取文案服务状态"""
    return copywriting_service.get_status()
