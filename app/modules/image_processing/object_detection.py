import cv2
import numpy as np
import logging
import torch
from typing import List, Tuple, Optional, Dict, Union
from pathlib import Path
import os

logger = logging.getLogger(__name__)

# YOLO模型路徑
YOLO_MODEL_PATH = os.environ.get("YOLO_MODEL_PATH", "models/yolo/best.pt")

# 嘗試加載YOLO模型（如果存在）
try:
    if os.path.exists(YOLO_MODEL_PATH):
        logger.info(f"嘗試加載YOLO模型: {YOLO_MODEL_PATH}")
        model = torch.hub.load('ultralytics/yolov5', 'custom', path=YOLO_MODEL_PATH)
        model.conf = 0.25  # 信心閾值
        YOLO_AVAILABLE = True
    else:
        logger.warning(f"找不到YOLO模型: {YOLO_MODEL_PATH}，將使用傳統邊緣檢測方法")
        YOLO_AVAILABLE = False
except Exception as e:
    logger.warning(f"載入YOLO模型失敗: {str(e)}，將使用傳統邊緣檢測方法")
    YOLO_AVAILABLE = False

def detect_medicine_box(image: np.ndarray) -> np.ndarray:
    """
    從圖像中檢測藥盒區域
    
    參數:
        image: 輸入圖像 (numpy array)
        
    返回:
        檢測到的藥盒圖像區域 (numpy array)
    """
    if YOLO_AVAILABLE:
        return detect_with_yolo(image)
    else:
        return detect_with_contours(image)

def detect_with_yolo(image: np.ndarray) -> np.ndarray:
    """
    使用YOLO模型檢測藥盒
    
    參數:
        image: 輸入圖像 (numpy array)
        
    返回:
        檢測到的藥盒圖像區域 (numpy array)
    """
    try:
        # 執行YOLO預測
        results = model(image)
        
        # 檢查是否檢測到物體
        if len(results.xyxy[0]) == 0:
            logger.warning("未檢測到藥盒，返回原始圖像")
            return image
            
        # 獲取最大可能性的檢測框
        detection = results.xyxy[0][0].cpu().numpy()
        x1, y1, x2, y2 = map(int, detection[:4])
        
        # 裁剪圖像
        cropped = image[y1:y2, x1:x2]
        logger.info(f"成功檢測到藥盒，置信度: {detection[4]:.2f}")
        
        return cropped
        
    except Exception as e:
        logger.error(f"YOLO檢測失敗: {str(e)}")
        logger.info("轉換到備用方法")
        return detect_with_contours(image)

def detect_with_contours(image: np.ndarray) -> np.ndarray:
    """
    使用傳統的輪廓檢測方法找到藥盒
    
    參數:
        image: 輸入圖像 (numpy array)
        
    返回:
        檢測到的藥盒圖像區域 (numpy array)
    """
    try:
        # 轉換到灰度圖像
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 高斯模糊
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # 檢測邊緣
        edges = cv2.Canny(blurred, 50, 150)
        
        # 查找輪廓
        contours, _ = cv2.findContours(edges.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 如果沒有找到輪廓，返回原始圖像
        if len(contours) == 0:
            logger.warning("未檢測到藥盒輪廓，返回原始圖像")
            return image
            
        # 找到最大輪廓
        largest_contour = max(contours, key=cv2.contourArea)
        
        # 獲取最小外接矩形
        x, y, w, h = cv2.boundingRect(largest_contour)
        
        # 檢查輪廓區域是否足夠大
        image_area = image.shape[0] * image.shape[1]
        contour_area = w * h
        
        if contour_area < (image_area * 0.1):  # 如果輪廓太小 (小於10%的圖像面積)
            logger.warning("檢測到的輪廓太小，返回原始圖像")
            return image
            
        # 裁剪圖像
        cropped = image[y:y+h, x:x+w]
        
        # 記錄並返回
        logger.info(f"成功檢測到藥盒輪廓，區域佔比: {contour_area/image_area:.2f}")
        return cropped
        
    except Exception as e:
        logger.error(f"輪廓檢測失敗: {str(e)}")
        return image  # 如有錯誤，返回原始圖像 