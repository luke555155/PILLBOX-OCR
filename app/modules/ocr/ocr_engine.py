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

try:
    import easyocr
    # 預載入EasyOCR讀取器
    EASYOCR_READERS = {}
    EASYOCR_AVAILABLE = True
except ImportError:
    logger.warning("未安裝EasyOCR，將僅使用Tesseract")
    EASYOCR_AVAILABLE = False

def get_easyocr_reader(lang: str) -> Optional[object]:
    """
    獲取或創建EasyOCR讀取器
    
    參數:
        lang: 語言代碼
        
    返回:
        EasyOCR Reader物件
    """
    if not EASYOCR_AVAILABLE:
        return None
        
    # 轉換語言代碼到EasyOCR支援的格式
    lang_mapping = {
        'zh-tw': ['ch_tra', 'en'],  # 繁體中文 + 英文
        'zh-cn': ['ch_sim', 'en'],  # 簡體中文 + 英文
        'en': ['en'],               # 英文
        'ja': ['ja', 'en'],         # 日文 + 英文
        'ko': ['ko', 'en'],         # 韓文 + 英文
        'auto': ['ch_tra', 'en']    # 自動模式預設繁中+英文
    }
    
    languages = lang_mapping.get(lang, ['en'])
    
    # 讀取器快取鍵
    reader_key = '_'.join(languages)
    
    # 如果讀取器已存在，直接返回
    if reader_key in EASYOCR_READERS:
        return EASYOCR_READERS[reader_key]
    
    try:
        logger.info(f"創建EasyOCR讀取器: {languages}")
        # 建立新的讀取器
        reader = easyocr.Reader(languages, gpu=False)  # 如果有GPU，可設置為True
        EASYOCR_READERS[reader_key] = reader
        return reader
    except Exception as e:
        logger.error(f"無法創建EasyOCR讀取器: {str(e)}")
        return None

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
    
    # 優先使用EasyOCR (如果可用)
    if EASYOCR_AVAILABLE:
        result = perform_easyocr(image, lang)
        if result:
            logger.info(f"EasyOCR識別成功，文字長度: {len(result)}")
            return result
    
    # 回落到Tesseract
    return perform_tesseract_ocr(image, lang)

def perform_easyocr(image: np.ndarray, lang: str) -> str:
    """
    使用EasyOCR執行文字識別
    
    參數:
        image: 輸入圖像 (numpy array)
        lang: 語言代碼
        
    返回:
        識別出的文字
    """
    try:
        # 獲取讀取器
        reader = get_easyocr_reader(lang)
        if not reader:
            return ""
            
        # 執行識別
        result = reader.readtext(image)
        
        # 組合文字結果
        text_result = []
        for detection in result:
            text = detection[1]  # 文字內容位於索引1
            confidence = detection[2]  # 置信度位於索引2
            text_result.append(text)
            
        return '\n'.join(text_result)
        
    except Exception as e:
        logger.error(f"EasyOCR處理失敗: {str(e)}")
        return ""

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