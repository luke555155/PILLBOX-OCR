import os
import uuid
import logging
import json
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import shutil
import datetime

logger = logging.getLogger(__name__)

def generate_unique_id() -> str:
    """生成唯一的ID"""
    return str(uuid.uuid4())

def ensure_directory_exists(directory_path: Union[str, Path]) -> None:
    """確保目錄存在，如果不存在則創建"""
    path = Path(directory_path)
    path.mkdir(parents=True, exist_ok=True)

def save_json(data: Dict[str, Any], file_path: Union[str, Path]) -> bool:
    """將字典保存為JSON文件"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"保存JSON文件失敗: {str(e)}")
        return False

def load_json(file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """載入JSON文件為字典"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"載入JSON文件失敗: {str(e)}")
        return None

def cleanup_old_files(directory: Union[str, Path], days: int = 7) -> int:
    """
    清理指定目錄中超過指定天數的文件
    
    參數:
        directory: 要清理的目錄
        days: 天數閾值，超過此天數的文件將被刪除
        
    返回:
        刪除的文件數量
    """
    try:
        directory_path = Path(directory)
        if not directory_path.exists() or not directory_path.is_dir():
            logger.warning(f"目錄不存在或不是有效的目錄: {directory}")
            return 0
            
        now = datetime.datetime.now()
        threshold = now - datetime.timedelta(days=days)
        
        deleted_count = 0
        
        for item in directory_path.glob("**/*"):
            if not item.is_file():
                continue
                
            # 獲取文件修改時間
            mtime = datetime.datetime.fromtimestamp(item.stat().st_mtime)
            
            # 如果文件比閾值還舊，則刪除
            if mtime < threshold:
                item.unlink()
                deleted_count += 1
                
        logger.info(f"清理了 {deleted_count} 個超過 {days} 天的檔案，目錄: {directory}")
        return deleted_count
        
    except Exception as e:
        logger.error(f"清理舊檔案失敗: {str(e)}")
        return 0

def get_file_extension(filename: str) -> str:
    """獲取檔案副檔名（小寫，包含點號）"""
    return os.path.splitext(filename)[1].lower()

def is_valid_image_extension(extension: str) -> bool:
    """檢查是否為有效的圖像副檔名"""
    valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']
    return extension.lower() in valid_extensions 