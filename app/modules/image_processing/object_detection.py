import logging
import os

import cv2
import numpy as np
from ultralytics import YOLO
import base64

logger = logging.getLogger(__name__)

# YOLO模型路徑
YOLO_MODEL_PATH = os.environ.get("YOLO_MODEL_PATH", "models/yolo/yolov9c.pt")

# 嘗試加載YOLO模型（如果存在）
try:
    if os.path.exists(YOLO_MODEL_PATH):
        logger.info(f"嘗試加載YOLO模型: {YOLO_MODEL_PATH}")
        model = YOLO('models/yolo/yolov9c.pt')
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
        boxes = results[0].boxes if isinstance(results, list) and len(results) > 0 else None
        if boxes is None or boxes.xyxy is None or boxes.xyxy.shape[0] == 0:
            logger.warning("未檢測到藥盒，返回原始圖像")
            return image
        # 獲取最大可能性的檢測框（這裡預設取第一個）
        detection = boxes.xyxy[0].cpu().numpy()
        x1, y1, x2, y2 = map(int, detection[:4])
        # 裁剪圖像
        cropped = image[y1:y2, x1:x2]
        conf = float(boxes.conf[0]) if hasattr(boxes, 'conf') else 0.0
        logger.info(f"成功檢測到藥盒，置信度: {conf:.2f}")
        return cropped
    except Exception as e:
        logger.error(f"YOLO檢測失敗: {str(e)}")
        logger.info("轉換到備用方法")
        return detect_with_contours(image)

def detect_with_yolo_and_draw(image: np.ndarray) -> dict:
    """
    使用YOLO模型檢測藥盒，並在原圖上畫框，回傳base64圖片與偵測資訊
    返回: {'image_with_box': base64 str, 'info': {...}}
    """
    if not YOLO_AVAILABLE:
        return {"image_with_box": None, "info": None}
    try:
        results = model(image)
        boxes = results[0].boxes if isinstance(results, list) and len(results) > 0 else None
        if boxes is None or boxes.xyxy is None or boxes.xyxy.shape[0] == 0:
            return {"image_with_box": None, "info": None}
        detection = boxes.xyxy[0].cpu().numpy()
        x1, y1, x2, y2 = map(int, detection[:4])
        conf = float(boxes.conf[0]) if hasattr(boxes, 'conf') else 0.0
        cls = int(boxes.cls[0]) if hasattr(boxes, 'cls') else None
        # 畫框
        image_with_box = image.copy()
        cv2.rectangle(image_with_box, (x1, y1), (x2, y2), (0, 255, 0), 2)
        # 轉base64
        _, buffer = cv2.imencode('.jpg', image_with_box)
        img_b64 = base64.b64encode(buffer).decode('utf-8')
        info = {
            "box": [int(x1), int(y1), int(x2), int(y2)],
            "confidence": conf,
            "class": cls
        }
        logger.info(f"YOLO檢測成功")
        return {"image_with_box": img_b64, "info": info}
    except Exception as e:
        logger.error(f"YOLO檢測失敗: {str(e)}")
        return {"image_with_box": None, "info": None}

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

def get_box_image(image: np.ndarray, box: list) -> np.ndarray:
    x1, y1, x2, y2 = box
    return image[y1:y2, x1:x2]

def draw_box_on_image(image: np.ndarray, box: list, color=(0,255,0), thickness=2) -> np.ndarray:
    img = image.copy()
    x1, y1, x2, y2 = box
    import cv2
    cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)
    return img

def image_to_base64(image: np.ndarray) -> str:
    import cv2, base64
    _, buffer = cv2.imencode('.jpg', image)
    return base64.b64encode(buffer).decode('utf-8')

def detect_medicine_box_v2(image: np.ndarray) -> dict:
    """
    只偵測一次，回傳box、confidence、class、裁切圖、畫框圖（base64）
    """
    if not YOLO_AVAILABLE:
        return {"box": None, "confidence": None, "class": None, "cropped": None, "image_with_box": None}
    try:
        results = model(image)
        boxes = results[0].boxes if isinstance(results, list) and len(results) > 0 else None
        if boxes is None or boxes.xyxy is None or boxes.xyxy.shape[0] == 0:
            return {"box": None, "confidence": None, "class": None, "cropped": None, "image_with_box": None}
        detection = boxes.xyxy[0].cpu().numpy()
        x1, y1, x2, y2 = map(int, detection[:4])
        conf = float(boxes.conf[0]) if hasattr(boxes, 'conf') else 0.0
        cls = int(boxes.cls[0]) if hasattr(boxes, 'cls') else None
        box = [int(x1), int(y1), int(x2), int(y2)]
        cropped = get_box_image(image, box)
        image_with_box = draw_box_on_image(image, box)
        img_b64 = image_to_base64(image_with_box)
        return {
            "box": box,
            "confidence": conf,
            "class": cls,
            "cropped": cropped,
            "image_with_box": img_b64
        }
    except Exception as e:
        logger.error(f"YOLO檢測失敗: {str(e)}")
        return {"box": None, "confidence": None, "class": None, "cropped": None, "image_with_box": None} 