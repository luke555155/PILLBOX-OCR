import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# 創建FastAPI應用
app = FastAPI(
    title="藥盒OCR系統",
    description="多國語藥盒OCR後端資料抽取系統API",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生產環境中應限制允許的源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 導入路由
from app.api.endpoints import image_upload, ocr_process

# 註冊路由
app.include_router(image_upload.router, prefix="/api", tags=["影像上傳"])
app.include_router(ocr_process.router, prefix="/api", tags=["OCR處理"])

@app.get("/")
async def root():
    """健康檢查端點"""
    return {"status": "online", "message": "藥盒OCR系統API正在運行"}

if __name__ == "__main__":
    import uvicorn
    # 從環境變數獲取主機和端口，如果沒有則使用預設值
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    logger.info(f"啟動服務於 {host}:{port}")
    uvicorn.run("app.main:app", host=host, port=port, reload=True) 