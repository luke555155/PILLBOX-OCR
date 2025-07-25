import streamlit as st
import requests
import json
from PIL import Image, ExifTags
import io
import os
import time
from typing import Dict, List, Optional, Any
import base64

# 後端API URL
API_URL = os.environ.get("API_URL", "http://localhost:8000/api")

# 頁面設置
st.set_page_config(page_title="多國語藥盒OCR系統", page_icon="💊", layout="wide")

# 顯示標題
st.title("💊 多國語藥盒OCR系統")
st.markdown("上傳藥盒圖像，自動識別語言、辨識文字並提取藥品資訊")

# 創建標籤頁
tab1, tab2, tab3 = st.tabs(["上傳圖像", "處理結果", "使用說明"])

def load_and_fix_image(file):
    image = Image.open(file)
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
    return image

with tab1:
    st.header("上傳藥盒圖像")
    
    # 上傳圖像
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 藥盒正面")
        front_image = st.file_uploader("上傳藥盒正面圖像", type=["jpg", "jpeg", "png"], key="front")
        if front_image:
            st.image(load_and_fix_image(front_image), caption="藥盒正面", use_container_width=True)
    
    with col2:
        st.markdown("### 藥盒背面 (選填)")
        back_image = st.file_uploader("上傳藥盒背面圖像", type=["jpg", "jpeg", "png"], key="back")
        if back_image:
            st.image(load_and_fix_image(back_image), caption="藥盒背面", use_container_width=True)
    
    # 處理按鈕
    if st.button("開始處理", type="primary"):
        if not front_image:
            st.error("請至少上傳藥盒正面圖像")
        else:
            with st.spinner("上傳圖像中..."):
                # 準備上傳的檔案
                if front_image:
                    front_image.seek(0)
                if back_image:
                    back_image.seek(0)
                files = {"front_image": front_image}
                if back_image:
                    files["back_image"] = back_image
                
                try:
                    # 上傳圖像
                    upload_response = requests.post(
                        f"{API_URL}/upload-images",
                        files=files
                    )
                    
                    if upload_response.status_code == 200:
                        upload_data = upload_response.json()
                        image_ids = upload_data.get("image_ids", [])
                        batch_id = upload_data.get("batch_id", None)
                        st.success(f"成功上傳了 {len(image_ids)} 張圖像")
                        
                        # 儲存圖像ID和批次ID到session_state以便後續處理
                        st.session_state.image_ids = image_ids
                        st.session_state.batch_id = batch_id
                        
                        # 自動切換到處理結果標籤頁並開始處理
                        st.rerun()
                    else:
                        st.error(f"上傳失敗: {upload_response.text}")
                        
                except Exception as e:
                    st.error(f"處理出錯: {str(e)}")

with tab2:
    st.header("處理結果")
    
    # 檢查是否有上傳的圖像
    if "image_ids" in st.session_state and st.session_state.image_ids:
        # 顯示處理進度
        if "ocr_results" not in st.session_state:
            with st.spinner("正在進行OCR處理..."):
                try:
                    # 發送OCR處理請求
                    process_response = requests.post(
                        f"{API_URL}/process-ocr",
                        json={
                            "image_ids": st.session_state.image_ids,
                            "batch_id": st.session_state.batch_id
                        }
                    )
                    
                    if process_response.status_code == 200:
                        ocr_results = process_response.json()
                        st.session_state.ocr_results = ocr_results
                    else:
                        st.error(f"OCR處理失敗: {process_response.text}")
                        
                except Exception as e:
                    st.error(f"處理出錯: {str(e)}")
        
        # 顯示處理結果
        if "ocr_results" in st.session_state:
            results = st.session_state.ocr_results
            
            for i, result in enumerate(results):
                with st.expander(f"圖像 {i+1} 結果", expanded=True):
                    # 建立兩欄顯示
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        # 顯示處理的圖像
                        image_source = "正面" if result.get("medicineInfo", {}).get("source") == "front" else "背面"
                        st.markdown(f"### 藥盒{image_source}")
                        
                        # 信心度指示器
                        confidence = result.get("medicineInfo", {}).get("confidence", 0)
                        st.progress(confidence, text=f"辨識信心度: {confidence:.2%}")
                        
                        # 顯示語言
                        detected_lang = result.get("detectedLanguage", "未知")
                        lang_display = {
                            "zh-tw": "繁體中文", 
                            "zh-cn": "簡體中文", 
                            "en": "英文",
                            "ja": "日文",
                            "ko": "韓文"
                        }
                        st.info(f"檢測語言: {lang_display.get(detected_lang, detected_lang)}")
                        
                    with col2:
                        # 顯示藥品資訊
                        st.markdown("### 藥品資訊")
                        
                        medicine_info = result.get("medicineInfo", {})
                        
                        # 藥品名稱
                        medicine_name = medicine_info.get("medicineName", "無法辨識")
                        st.markdown(f"**藥品名稱**: {medicine_name}")
                        
                        # 藥品成分
                        ingredients = medicine_info.get("ingredients", [])
                        if ingredients:
                            st.markdown("**成分**:")
                            for ingredient in ingredients:
                                st.markdown(f"- {ingredient}")
                        else:
                            st.markdown("**成分**: 無法辨識")
                        
                        # 藥品數量
                        quantity = medicine_info.get("quantity", "無法辨識")
                        st.markdown(f"**數量**: {quantity}")
                        
                        # 顯示原始OCR文字
                        with st.expander("顯示原始OCR文字"):
                            st.text(result.get("rawText", "無OCR文字"))
                            
                            # 複製按鈕
                            if result.get("rawText"):
                                if st.button("複製文字", key=f"copy_{i}"):
                                    st.code(result.get("rawText", ""), language="text")
                                    st.success("文字已複製到剪貼簿！")
                        
                        # 顯示YOLO畫框圖與資訊
                        yolo_img_b64 = result.get("yolo_image_with_box")
                        yolo_info = result.get("yolo_info")
                        if yolo_img_b64:
                            img_bytes = base64.b64decode(yolo_img_b64)
                            img = Image.open(io.BytesIO(img_bytes))
                            st.image(img, caption="YOLO標註圖", use_container_width=True)
                        else:
                            st.info("未偵測到物件或YOLO未啟用")
                        if yolo_info:
                            st.markdown("**YOLO 偵測資訊**:")
                            st.json(yolo_info)
            
            # 提供重新開始按鈕
            if st.button("重新上傳"):
                # 清除session_state
                batch_id = st.session_state.get("batch_id")
                if batch_id:
                    try:
                        delete_response = requests.delete(f"{API_URL}/delete-batch/{batch_id}")
                        if delete_response.status_code == 200:
                            st.info("已刪除上傳檔案")
                        else:
                            st.warning(f"刪除檔案失敗: {delete_response.text}")
                    except Exception as e:
                        st.warning(f"刪除檔案時發生錯誤: {str(e)}")
                if "image_ids" in st.session_state:
                    del st.session_state.image_ids
                if "ocr_results" in st.session_state:
                    del st.session_state.ocr_results
                if "batch_id" in st.session_state:
                    del st.session_state.batch_id
                # 切換回上傳標籤頁
                st.rerun()
    else:
        st.info("請先在「上傳圖像」標籤頁上傳藥盒圖像")

with tab3:
    st.header("使用說明")
    
    st.markdown("""
    ### 如何使用此系統
    
    1. **上傳圖像**:
       - 在「上傳圖像」標籤頁中，上傳藥盒的正面圖像（必填）
       - 選擇性上傳藥盒的背面圖像（可選）
       - 支援的圖像格式: JPG, JPEG, PNG
    
    2. **處理結果**:
       - 系統會自動檢測圖像中的語言
       - 根據檢測到的語言選擇最佳的OCR模型進行文字辨識
       - 從辨識出的文字中抽取關鍵藥品資訊:
         - 藥品名稱
         - 成分列表
         - 數量/劑量
       - 您可以查看原始OCR文字，以便進行手動驗證
    
    3. **支援的語言**:
       - 繁體中文 (zh-tw)
       - 簡體中文 (zh-cn)
       - 英文 (en)
       - 日文 (ja)
       - 韓文 (ko)
    
    ### 注意事項
    
    - 圖像品質越好，OCR辨識效果越佳
    - 避免強烈反光或陰影
    - 盡量讓藥盒文字在圖像中清晰可見
    - 系統會自動嘗試檢測和修正圖像中的問題
    """)

# 頁腳
st.markdown("---")
st.markdown("💊 多國語藥盒OCR系統 | 版本 1.0.0 | © 2023") 