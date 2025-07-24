📦 多國語藥盒 OCR 後端資料抽取系統設計文件
🧩 系統功能概述
本系統接收使用者於兩可區域上傳兩張圖片（分別為藥盒正面、背面），並進行以下流程：

自動檢測語言

執行對應語言的 OCR 辨識

從 OCR 結果中抽取關鍵資訊（品名、成分、數量）

回傳 JSON 結構結果

🧱 架構總覽（以 FastAPI + Python 為主）
A[使用者上傳藥盒圖片] --> B[FastAPI 接收並儲存]
B --> C[圖像預處理（OpenCV）]
C --> D[物件偵測 YOLO：擷取藥盒區域]
D --> E[初步 OCR（Tesseract）提取樣本文字]
E --> F[語言偵測（FastText）]
F --> G[依語系切換 OCR 模型（EasyOCR）]
G --> H[精準文字辨識]
H --> I[關鍵資訊抽取（規則 + NLP）]
I --> J[儲存至 SQLite / PostgreSQL]
I --> K[回傳 JSON 結果]
🧰 元件與模組說明
✅ 前端框架
元件	說明
Streamlit	UI/UX 現代化設計介面

✅ 後端框架
元件	選型	說明
API Server	FastAPI	高性能 async 框架，支援 OpenAPI、自動產生 Swagger

✅ 圖像處理模組
功能	套件	說明
圖像預處理	OpenCV	執行旋轉矯正、灰階、邊緣提取、縮放等
物件偵測	YOLOv5 / YOLOv8	檢測藥盒主要區域，可用預訓練模型，提升辨識效果

✅ 語言偵測與 OCR
功能	模型/工具	說明
初步 OCR	Tesseract	輕量 OCR 模型，用來提取語言樣本文字
語言偵測	FastText / CLD3	使用文字樣本自動判斷語言（zh-tw, en, ja...）
精準 OCR	EasyOCR	根據語言選擇對應模型，多語支援佳，支援 GPU

✅ NLP / 抽取模組
功能	工具/模型	說明
成分與數據抽取	正則 + 關鍵詞過濾	如：劑量、mg/g、膠囊/錠數
品名辨識	LLM 或 Regex 樣板	使用語義分析進行藥品名稱抽取（結合本地 Ollama Server）
多語支援	fasttext embeddings	支援多語成分統一詞彙或翻譯對應

✅ 資料儲存
層級	工具	說明
選用	MongoDB	若藥品資訊需儲存為彈性 JSON 格式，可考慮

✅ JSON 輸出格式範例
json
複製
編輯
{
  "imageId": "abc123",
  "detectedLanguage": "zh-tw",
  "medicineName": "普拿疼加強錠",
  "ingredients": [
    "Acetaminophen 500mg",
    "Caffeine 65mg"
  ],
  "quantity": "20 錠",
  "source": "front",
  "confidence": 0.94
}
🐳 容器化部署
本系統整體採用 Docker 容器化佈署，建議使用 Docker Compose 管理以下服務：

FastAPI 主應用服務

YOLO 模型推論服務（可封裝為 Python Module）

EasyOCR 模組

本地 Ollama（作為 LLM 抽取器）

MongoDB / PostgreSQL 作為儲存引擎

