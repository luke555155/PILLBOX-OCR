import os
import uuid
import shutil
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from typing import List, Optional
from pydantic import BaseModel
from pathlib import Path

logger = logging.getLogger(__name__)

# 創建路由
router = APIRouter()

# 創建上傳目錄
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

class ImageUploadResponse(BaseModel):
    """圖像上傳回應模型"""
    image_ids: List[str]
    message: str


@router.post("/upload-images", response_model=ImageUploadResponse)
async def upload_images(
    front_image: UploadFile = File(...),
    back_image: Optional[UploadFile] = File(None),
    batch_id: Optional[str] = Form(None)
):
    """
    上傳藥盒正面和背面的圖像
    
    - **front_image**: 藥盒正面圖像（必須）
    - **back_image**: 藥盒背面圖像（可選）
    - **batch_id**: 批次ID（可選，如果不提供將自動生成）
    
    返回上傳圖像的IDs和批次ID
    """
    # 驗證文件類型
    allowed_extensions = [".jpg", ".jpeg", ".png"]
    for image in [front_image, back_image] if back_image else [front_image]:
        ext = os.path.splitext(image.filename)[1].lower()
        if ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"不支援的檔案格式：{ext}。請上傳 JPG, JPEG 或 PNG 圖像。"
            )
    
    try:
        # 如果沒有提供batch_id，則生成一個新的
        if not batch_id:
            batch_id = str(uuid.uuid4())
        
        # 創建此批次的目錄
        batch_dir = UPLOAD_DIR / batch_id
        batch_dir.mkdir(exist_ok=True)
        
        image_ids = []
        
        # 保存正面圖像
        front_id = str(uuid.uuid4())
        front_path = batch_dir / f"{front_id}{os.path.splitext(front_image.filename)[1]}"
        with open(front_path, "wb") as buffer:
            shutil.copyfileobj(front_image.file, buffer)
        image_ids.append(front_id)
        
        # 如果有提供背面圖像，也保存它
        if back_image:
            back_id = str(uuid.uuid4())
            back_path = batch_dir / f"{back_id}{os.path.splitext(back_image.filename)[1]}"
            with open(back_path, "wb") as buffer:
                shutil.copyfileobj(back_image.file, buffer)
            image_ids.append(back_id)
        
        logger.info(f"成功上傳了 {len(image_ids)} 張圖像，批次ID: {batch_id}")
        
        return ImageUploadResponse(
            image_ids=image_ids,
            message=f"成功上傳了 {len(image_ids)} 張圖像"
        )
    
    except Exception as e:
        logger.error(f"上傳圖像時發生錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail=f"上傳圖像時發生錯誤: {str(e)}") 