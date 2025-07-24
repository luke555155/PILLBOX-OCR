FROM python:3.9-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    tesseract-ocr \
    libtesseract-dev \
    tesseract-ocr-eng \
    tesseract-ocr-chi-tra \
    tesseract-ocr-chi-sim \
    tesseract-ocr-jpn \
    tesseract-ocr-kor \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 複製需求文件
COPY requirements.txt .

# 安裝Python依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製程式碼
COPY . .

# 確保上傳目錄存在
RUN mkdir -p uploads

# 創建models目錄並設置環境變數
RUN mkdir -p models/fasttext models/yolo
ENV FASTTEXT_MODEL_PATH=/app/models/fasttext/lid.176.bin
ENV YOLO_MODEL_PATH=/app/models/yolo/best.pt
ENV TESSERACT_CMD=/usr/bin/tesseract

# 設置執行腳本為可執行
RUN chmod +x run.py

# 開放端口
EXPOSE 8000 8501

# 啟動命令
CMD ["python", "run.py"] 