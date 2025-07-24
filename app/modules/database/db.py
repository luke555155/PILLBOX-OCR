import os
import logging
from typing import Dict, List, Optional, Any, Union
from sqlalchemy import create_engine, Column, String, Integer, Float, JSON, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import json

logger = logging.getLogger(__name__)

# 資料庫設定
DB_ENGINE = os.environ.get("DB_ENGINE", "sqlite:///medicine_ocr.db")

# 初始化資料庫連接
engine = create_engine(DB_ENGINE)
Base = declarative_base()
Session = sessionmaker(bind=engine)

class MedicineOCRResult(Base):
    """藥品OCR結果表"""
    __tablename__ = "medicine_ocr_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    image_id = Column(String(50), unique=True, nullable=False, index=True)
    batch_id = Column(String(50), nullable=False, index=True)
    detected_language = Column(String(10), nullable=True)
    medicine_name = Column(String(255), nullable=True)
    ingredients = Column(Text, nullable=True)  # JSON格式存儲
    quantity = Column(String(100), nullable=True)
    source = Column(String(20), nullable=True)  # front/back
    confidence = Column(Float, nullable=False, default=0.0)
    raw_text = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "id": self.id,
            "image_id": self.image_id,
            "batch_id": self.batch_id,
            "detected_language": self.detected_language,
            "medicine_name": self.medicine_name,
            "ingredients": json.loads(self.ingredients) if self.ingredients else [],
            "quantity": self.quantity,
            "source": self.source,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat()
        }

# 創建資料庫表格
def create_tables():
    """建立資料庫表格"""
    try:
        Base.metadata.create_all(engine)
        logger.info("成功創建資料庫表格")
    except Exception as e:
        logger.error(f"創建資料庫表格失敗: {str(e)}")
        raise e

def save_ocr_result(
    image_id: str,
    batch_id: str,
    detected_language: str,
    medicine_name: Optional[str],
    ingredients: List[str],
    quantity: Optional[str],
    source: str,
    confidence: float,
    raw_text: Optional[str] = None
) -> bool:
    """
    保存OCR處理結果到資料庫
    
    參數:
        image_id: 圖像ID
        batch_id: 批次ID
        detected_language: 檢測到的語言
        medicine_name: 藥品名稱
        ingredients: 成分列表
        quantity: 數量
        source: 來源 (front/back)
        confidence: 置信度
        raw_text: 原始OCR文本
        
    返回:
        保存成功返回True，否則返回False
    """
    try:
        session = Session()
        
        # 序列化成分列表為JSON字符串
        ingredients_json = json.dumps(ingredients, ensure_ascii=False)
        
        # 創建新記錄
        ocr_result = MedicineOCRResult(
            image_id=image_id,
            batch_id=batch_id,
            detected_language=detected_language,
            medicine_name=medicine_name,
            ingredients=ingredients_json,
            quantity=quantity,
            source=source,
            confidence=confidence,
            raw_text=raw_text
        )
        
        # 如果已存在相同image_id的記錄，先刪除
        existing = session.query(MedicineOCRResult).filter_by(image_id=image_id).first()
        if existing:
            session.delete(existing)
            
        # 添加新記錄
        session.add(ocr_result)
        session.commit()
        
        logger.info(f"成功保存OCR結果，圖像ID: {image_id}")
        return True
        
    except Exception as e:
        logger.error(f"保存OCR結果失敗: {str(e)}")
        session.rollback()
        return False
        
    finally:
        session.close()

def get_ocr_result(image_id: str) -> Optional[Dict[str, Any]]:
    """
    根據圖像ID獲取OCR處理結果
    
    參數:
        image_id: 圖像ID
        
    返回:
        如果找到記錄，返回包含OCR結果的字典，否則返回None
    """
    try:
        session = Session()
        result = session.query(MedicineOCRResult).filter_by(image_id=image_id).first()
        
        if result:
            return result.to_dict()
        else:
            logger.warning(f"找不到圖像ID: {image_id} 的OCR結果")
            return None
            
    except Exception as e:
        logger.error(f"獲取OCR結果失敗: {str(e)}")
        return None
        
    finally:
        session.close()

def get_batch_results(batch_id: str) -> List[Dict[str, Any]]:
    """
    獲取批次中的所有OCR結果
    
    參數:
        batch_id: 批次ID
        
    返回:
        OCR結果列表
    """
    try:
        session = Session()
        results = session.query(MedicineOCRResult).filter_by(batch_id=batch_id).all()
        
        return [result.to_dict() for result in results]
            
    except Exception as e:
        logger.error(f"獲取批次結果失敗: {str(e)}")
        return []
        
    finally:
        session.close()

# 確保資料庫表格存在
create_tables() 