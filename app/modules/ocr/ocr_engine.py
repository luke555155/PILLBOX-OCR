import cv2
import numpy as np
import os
import logging
import pytesseract
from typing import Optional, Dict, List, Union, Tuple
from pathlib import Path

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

def perform_ocr(image: np.ndarray, lang: str = 'auto') -> str:
    """
    對圖像執行OCR處理
    
    參數:
        image: 輸入圖像 (numpy array)
        lang: 語言代碼 ('zh-tw', 'zh-cn', 'en', 'ja', 'ko', 'auto')
        
    返回:
        識別出的文字
    """
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