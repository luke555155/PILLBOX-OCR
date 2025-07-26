import cv2
import numpy as np
import os
import logging
import pytesseract
from typing import Optional, Dict, List, Union, Tuple
from pathlib import Path
import io
from google.cloud import vision
from google.oauth2 import service_account

logger = logging.getLogger(__name__)

# 設定 pytesseract 路徑 (如果需要)
TESSERACT_CMD = os.environ.get("TESSERACT_CMD")
if TESSERACT_CMD and os.path.exists(TESSERACT_CMD):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

# 支援的語言
SUPPORTED_LANGUAGES = {
    'zh-tw': 'chi_tra',  # 繁體中文
    'zh-cn': 'chi_sim',  # 簡體中文
    'en': 'eng',         # 英文
    'ja': 'jpn',         # 日文
    'ko': 'kor',         # 韓文
    'auto': 'eng+chi_tra'  # 自動模式預設使用英文+繁中
}

def perform_gcp_vision_ocr(image: np.ndarray) -> tuple[str, str]:
    """
    使用 Google Cloud Vision API 執行 OCR
    參數:
        image: 輸入圖像 (numpy array)
    返回:
        (識別出的文字, locale 語系)
    """
    try:
        # 將 numpy array 轉為 PNG bytes
        is_success, buffer = cv2.imencode(".png", image)
        if not is_success:
            logger.error("無法將圖像編碼為 PNG 格式")
            return "", "en"

        content = buffer.tobytes()

        # 檢查憑證路徑
        cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if not cred_path or not os.path.exists(cred_path):
            logger.error("找不到 GCP 憑證檔案，請設置 GOOGLE_APPLICATION_CREDENTIALS")
            return "", "en"

        # 建立 GCP 客戶端
        credentials = service_account.Credentials.from_service_account_file(cred_path)
        client = vision.ImageAnnotatorClient(credentials=credentials)

        # 建立圖片物件
        image_gcp = vision.Image(content=content)
        response = client.text_detection(image=image_gcp)

        # ✅ 全部記錄 GCP 原始回應內容（可選，開發用）
        logger.info("GCP 回應 JSON:\n" + str(response))

        texts = response.text_annotations
        if texts:
            locale = getattr(texts[0], "locale", None) or "en"
            logger.info(f"GCP Vision OCR 識別成功，共 {len(texts)} 區塊")
            logger.info("辨識文字區塊詳細內容：")
            for i, t in enumerate(texts):
                logger.info(
                    f"[{i}] {t.description.strip()} (conf={t.confidence if hasattr(t, 'confidence') else 'N/A'})")
            return texts[0].description, locale
        else:
            logger.warning("GCP Vision OCR 無識別結果")
            return "", "en"
    except Exception as e:
        logger.error(f"GCP Vision OCR 處理失敗: {str(e)}")
        return "", "en"


def perform_ocr(image: np.ndarray, lang: str = 'auto', mode: str = 'local') -> Union[str, tuple[str, str]]:
    """
    對圖像執行OCR處理
    參數:
        image: 輸入圖像 (numpy array)
        lang: 語言代碼 ('zh-tw', 'zh-cn', 'en', 'ja', 'ko', 'auto')
        mode: 'local' 或 'gcp'
    返回:
        識別出的文字 或 (文字, locale)
    """
    if mode == 'gcp':
        return perform_gcp_vision_ocr(image)
    if lang not in SUPPORTED_LANGUAGES:
        logger.warning(f"不支援的語言: {lang}，使用預設語言: auto")
        lang = 'auto'
    return perform_tesseract_ocr(image, lang)

def perform_tesseract_ocr(image: np.ndarray, lang: str) -> str:
    """
    使用Tesseract執行OCR處理
    
    參數:
        image: 輸入圖像 (numpy array)
        lang: 語言代碼
        
    返回:
        識別出的文字
    """
    try:
        # 轉換語言代碼到Tesseract格式
        tesseract_lang = SUPPORTED_LANGUAGES.get(lang, 'eng+chi_tra')
        # 文字識別
        text = pytesseract.image_to_string(
            image,
            lang=tesseract_lang,
            config='--psm 6'  # 假設頁面為單一文本塊
        )
        logger.info(f"Tesseract OCR識別成功，使用語言: {tesseract_lang}")
        return text
    except Exception as e:
        logger.error(f"Tesseract OCR處理失敗: {str(e)}")
        return "" 