# 📦 多國語藥盒 OCR 後端資料抽取系統

這是一個自動化的藥盒OCR文字辨識與資訊抽取系統，能夠從藥盒圖像中識別語言，執行OCR辨識，並抽取關鍵的藥品資訊（如藥品名稱、成分和數量）。

## 🌟 功能特色

- 支援多種語言：繁體中文、簡體中文、英文、日文和韓文
- 自動語言檢測：使用先進的語言偵測模型識別文本語言
- 智能OCR處理：根據檢測到的語言選擇最佳的OCR引擎
- 藥盒區域檢測：使用計算機視覺技術自動識別藥盒區域
- 資訊抽取：從OCR結果中提取藥品名稱、成分和劑量信息
- 友好的用戶界面：基於Streamlit的現代化Web界面
- API支援：提供RESTful API用於集成到其他系統

## 🔧 技術架構

- **前端**: Streamlit
- **後端**: FastAPI
- **圖像處理**: OpenCV, YOLOv5/YOLOv8
- **OCR引擎**: Tesseract, EasyOCR
- **語言檢測**: fastText, langdetect
- **資料存儲**: SQLite / PostgreSQL

## 🚀 快速開始

### 方法1：使用Docker

1. 克隆此儲存庫
```bash
git clone https://github.com/yourusername/PILLBOX-OCR.git
cd PILLBOX-OCR
```

2. 使用Docker Compose啟動服務
```bash
docker-compose up -d
```

3. 在瀏覽器中訪問前端界面
```
http://localhost:8501
```

### 方法2：本地安裝

1. 克隆此儲存庫
```bash
git clone https://github.com/yourusername/PILLBOX-OCR.git
cd PILLBOX-OCR
```

2. 安裝依賴
```bash
pip install -r requirements.txt
```

3. 複製環境變數範例文件並根據需要修改
```bash
cp .env-example .env
```

4. 啟動服務
```bash
python run.py
```

5. 在瀏覽器中訪問前端界面
```
http://localhost:8501
```

## 📂 目錄結構

```
PILLBOX-OCR/
├── app/                 # 主程式目錄
│   ├── api/             # API 端點
│   ├── frontend/        # Streamlit 前端界面
│   ├── modules/         # 核心功能模組
│   │   ├── database/    # 資料庫模組
│   │   ├── image_processing/ # 圖像處理模組
│   │   ├── language_detection/ # 語言偵測模組
│   │   ├── nlp/         # 資訊抽取模組
│   │   └── ocr/         # OCR引擎模組
│   └── utils/           # 工具函數
├── models/              # 預訓練模型存放目錄
├── uploads/             # 上傳圖像暫存目錄
├── requirements.txt     # Python依賴
├── Dockerfile           # Docker配置文件
├── docker-compose.yml   # Docker Compose配置文件
└── run.py               # 啟動腳本
```

## 🤝 API端點

### 上傳圖像
```
POST /api/upload-images
```

### 處理OCR與抽取資訊
```
POST /api/process-ocr
```

### 獲取OCR結果
```
GET /api/ocr-result/{image_id}
```

## 📝 使用說明

1. **上傳圖像**: 上傳藥盒正面（必需）和背面（可選）圖像
2. **處理**: 系統自動進行語言偵測、OCR處理和資訊抽取
3. **結果查看**: 查看識別出的藥品名稱、成分和數量資訊

## ⚙️ 配置選項

可在`.env`文件中配置以下選項:
- 服務端口和主機
- 資料庫連接字符串
- 模型路徑
- API URL

## 📜 授權

此項目採用 MIT 授權 - 詳情請查看 [LICENSE](LICENSE) 文件


   1. Tesseract OCR 引擎:
       * 檔案中 TESSERACT_CMD=/usr/bin/tesseract 指向 Tesseract OCR 的執行檔。
       * 您需要在您的 Windows 電腦上安裝 Tesseract OCR。安裝後，請確保將 .env 檔案中的 TESSERACT_CMD 路徑更新為您電腦上 tesseract.exe 的實際安裝路徑 (例如 C:/Program Files/Tesseract-OCR/tesseract.exe)。


   2. `FASTTEXT_MODEL_PATH=models/fasttext/lid.176.bin`
       * 用途： 這是 FastText (https://fasttext.cc/) 的語言偵測模型，用來辨識圖片中的文字是哪種語言。
       * 操作： 您需要從 FastText 的官方網站下載名為 lid.176.bin 的模型檔案。
       * 放置位置： 下載後，請將檔案放到 E:\Git\PILLBOX-OCR\models\fasttext\ 資料夾內。

   3. `YOLO_MODEL_PATH=models/yolo/best.pt`
       * 用途： 這是 YOLO (https://github.com/ultralytics/yolov5) (You Only Look Once) 的物件偵測模型。檔案名稱 best.pt 暗示這是一個針對此專案客製化訓練過的模型，可能用來在圖片中偵測藥盒或文字區域。.pt 是 PyTorch 模型的副檔名。
       * 操作： 這個客製化模型檔案通常不會在公開網站上。您需要查看專案的 readme.md 文件或原始碼來源，看是否有提供模型的下載連結或取得方式的說明。
       * 放置位置： 取得檔案後，請將 best.pt 檔案放到 E:\Git\PILLBOX-OCR\models\yolo\ 資料夾內。