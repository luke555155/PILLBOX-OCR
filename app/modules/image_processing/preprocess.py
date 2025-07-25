import cv2
import numpy as np
import logging
from pathlib import Path
from typing import Union, Optional, Tuple
from PIL import Image, ExifTags

logger = logging.getLogger(__name__)

def load_image_with_exif(path):
    image = Image.open(path)
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = image._getexif()
        if exif is not None:
            orientation_value = exif.get(orientation, None)
            if orientation_value == 3:
                image = image.rotate(180, expand=True)
            elif orientation_value == 6:
                image = image.rotate(270, expand=True)
            elif orientation_value == 8:
                image = image.rotate(90, expand=True)
    except Exception:
        pass
    return np.array(image)

def preprocess_image(image_path: Union[str, Path], resize_dim: Optional[Tuple[int, int]] = None) -> np.ndarray:
    """
    預處理藥盒圖像以準備OCR
    
    參數:
        image_path: 圖像文件路徑
        resize_dim: 可選的調整大小尺寸 (width, height)
        
    返回:
        預處理後的圖像 (numpy array)
    """
    logger.info(f"開始預處理圖像: {image_path}")
    
    try:
        # 讀取圖像（自動校正EXIF方向）
        image = load_image_with_exif(str(image_path))
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)  # PIL為RGB, OpenCV為BGR
        if image is None:
            raise ValueError(f"無法讀取圖像: {image_path}")
        
        # 調整大小 (如果提供了尺寸)
        if resize_dim is not None:
            image = cv2.resize(image, resize_dim, interpolation=cv2.INTER_AREA)
        
        # 轉換為灰度圖像以進行處理
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 應用高斯模糊以減少噪聲
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # 應用自適應閾值處理以處理不同照明條件
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # 應用形態學運算以清理雜訊
        kernel = np.ones((3, 3), np.uint8)
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # 返回原始彩色圖像和處理後的二值圖像
        logger.info(f"圖像預處理完成: {image_path}")
        return image  # 返回原始圖像，進行物件偵測時會用到彩色圖像
        
    except Exception as e:
        logger.error(f"圖像預處理失敗: {str(e)}")
        raise e

def enhance_image_for_ocr(image: np.ndarray) -> np.ndarray:
    """
    專為OCR優化圖像
    
    參數:
        image: 輸入圖像 (numpy array)
        
    返回:
        增強後的圖像 (numpy array)
    """
    try:
        # 轉換為灰度
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # 應用CLAHE (限制性對比度自適應直方圖均衡) 增強對比度
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # 雙向濾波來保留邊緣同時消除噪聲
        filtered = cv2.bilateralFilter(enhanced, 9, 75, 75)
        
        # 應用自適應閾值
        thresh = cv2.adaptiveThreshold(
            filtered, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        return thresh
        
    except Exception as e:
        logger.error(f"OCR圖像增強失敗: {str(e)}")
        raise e 