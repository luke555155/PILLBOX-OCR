import logging
import os
import shutil
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Path
from fastapi.responses import JSONResponse
from typing import List, Optional
from pydantic import BaseModel
from pathlib import Path as PathLib
import traceback
import json

from app.modules.image_processing.preprocess import preprocess_image
from app.modules.image_processing.object_detection import detect_medicine_box, detect_with_yolo_and_draw
from app.modules.language_detection.detector import detect_language
from app.modules.ocr.ocr_engine import perform_ocr
from app.modules.nlp.extractor import extract_medicine_info

logger = logging.getLogger(__name__)

# 創建路由
router = APIRouter()

# 上傳目錄路徑
UPLOAD_DIR = PathLib("uploads")

class OCRRequest(BaseModel):
    image_ids: List[str]
    batch_id: str

class MedicineInfo(BaseModel):
    medicineName: Optional[str] = None
    ingredients: Optional[List[str]] = None
    quantity: Optional[str] = None
    source: str
    confidence: float

class OCRResponse(BaseModel):
    imageId: str
    detectedLanguage: str
    medicineInfo: MedicineInfo
    rawText: Optional[str] = None
    processingTime: float

@router.post("/process-ocr")
async def process_ocr(request: OCRRequest, background_tasks: BackgroundTasks):
    """
    處理上傳圖像的OCR辨識並抽取藥品資訊
    
    - **image_ids**: 要處理的圖像ID列表
    - **batch_id**: 批次ID
    
    返回OCR辨識結果和抽取的藥品資訊
    """
    try:
        batch_dir = UPLOAD_DIR / request.batch_id
        
        if not batch_dir.exists():
            raise HTTPException(status_code=404, detail=f"找不到批次ID: {request.batch_id}")
        
        results = []
        
        for image_id in request.image_ids:
            # 尋找對應的圖像文件
            image_files = list(batch_dir.glob(f"{image_id}.*"))
            
            if not image_files:
                logger.warning(f"找不到圖像ID: {image_id}")
                continue
            
            image_path = str(image_files[0])
            
            # 1. 圖像預處理
            logger.info(f"1. 開始預處理圖像: {image_id}")
            preprocessed_image = preprocess_image(image_path)

            # 1.1 YOLO畫框與資訊
            yolo_draw_result = detect_with_yolo_and_draw(preprocessed_image)

            # 2. 藥盒區域檢測
            logger.info(f"2. 執行藥盒區域檢測: {image_id}")
            detected_box = detect_medicine_box(preprocessed_image)

            # 3. Tesseract OSD模式取得文字（僅console顯示）
            logger.info(f"3. Tesseract OSD模式取得文字: {image_id}")
            try:
                import pytesseract
                osd_text = pytesseract.image_to_string(detected_box, config='--psm 3')
                logger.info(f">>> [OSD模式文字]" + osd_text)
            except Exception as e:
                logger.warning(f"[OSD模式失敗] {image_id}: {str(e)}")

            # 4. 初步OCR以獲取語言樣本
            logger.info(f"4. 執行初步OCR: {image_id}")
            sample_text = perform_ocr(detected_box, "auto")  # 自動模式
            logger.info(f">>> " + sample_text)

            # 5. 語言檢測
            logger.info(f"執行語言檢測: {image_id}")
            detected_lang = detect_language(sample_text)
            logger.info(f">>> " + detected_lang)
            
            # 6. 精確OCR處理
            logger.info(f"使用 {detected_lang} 模型執行精確OCR: {image_id}")
            import time
            start_time = time.time()
            ocr_text = perform_ocr(detected_box, detected_lang)
            logger.info(f">>> " + ocr_text)
            
            # 7. 藥品資訊抽取
            logger.info(f"從OCR文字中抽取藥品資訊: {image_id}")
            medicine_info = extract_medicine_info(ocr_text, detected_lang)

            
            # 計算處理時間
            processing_time = time.time() - start_time
            
            # 構建響應
            response = OCRResponse(
                imageId=image_id,
                detectedLanguage=detected_lang,
                medicineInfo=MedicineInfo(
                    medicineName=medicine_info.get("name"),
                    ingredients=medicine_info.get("ingredients"),
                    quantity=medicine_info.get("quantity"),
                    source="front" if "_front" in image_path else "back",
                    confidence=medicine_info.get("confidence", 0.0)
                ),
                rawText=ocr_text,
                processingTime=processing_time
            )
            
            # 8. 新增yolo畫框圖與資訊
            response_dict = response.dict()
            response_dict["yolo_image_with_box"] = yolo_draw_result["image_with_box"]
            response_dict["yolo_info"] = yolo_draw_result["info"]
            results.append(response_dict)


            # 9. 背景任務儲存結果到資料庫
            background_tasks.add_task(save_result_to_db, image_id, response.dict())
        
        return results
    
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"處理OCR時發生錯誤: {str(e)}\n{tb}")
        raise HTTPException(status_code=500, detail=f"處理OCR時發生錯誤: {str(e)}\n{tb}")
    finally:
        # 若設定自動刪除，處理完後刪除該批次目錄
        delete_uploads = os.environ.get("DELETE_UPLOADS_AFTER_PROCESS", "Y").upper()
        if delete_uploads == "Y":
            try:
                if 'batch_dir' in locals() and batch_dir.exists():
                    shutil.rmtree(str(batch_dir))
                    logger.info(f"自動刪除批次目錄: {batch_dir}")
            except Exception as e:
                logger.error(f"自動刪除批次目錄失敗: {str(e)}")

@router.get("/ocr-result/{image_id}", response_model=OCRResponse)
async def get_ocr_result(image_id: str = Path(..., description="圖像ID")):
    """
    根據圖像ID獲取OCR處理結果
    
    - **image_id**: 要獲取結果的圖像ID
    
    返回OCR處理結果
    """
    # 從資料庫中檢索結果
    # 實際實現中應該從資料庫獲取結果
    # 這裡只是示例
    raise HTTPException(status_code=501, detail="尚未實現")

async def save_result_to_db(image_id: str, result_data: dict):
    """將結果保存到資料庫的背景任務"""
    try:
        logger.info(f"保存圖像 {image_id} 的處理結果到資料庫")
        # 實際實現中應該將結果存儲到資料庫
        # 實際使用時，應引入資料庫模組並實現保存邏輯
    except Exception as e:
        logger.error(f"保存結果到資料庫時發生錯誤: {str(e)}") 