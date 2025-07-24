#!/usr/bin/env python
import os
import argparse
import subprocess
import time
import signal
import sys
from pathlib import Path

# 確保上傳目錄存在
Path("uploads").mkdir(exist_ok=True)

def run_api_server(port):
    """啟動API伺服器"""
    print(f"啟動API伺服器於 http://localhost:{port}")
    return subprocess.Popen(
        ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", str(port), "--reload"],
        env={**os.environ, "PORT": str(port)}
    )

def run_frontend(port, api_port):
    """啟動Streamlit前端"""
    print(f"啟動Streamlit前端於 http://localhost:{port}")
    return subprocess.Popen(
        ["streamlit", "run", "app/frontend/app.py", "--server.port", str(port)],
        env={**os.environ, "API_URL": f"http://localhost:{api_port}/api"}
    )

def handle_signal(signum, frame):
    """處理終止信號"""
    print("\n正在關閉服務...")
    if "api_process" in globals():
        api_process.terminate()
    if "frontend_process" in globals():
        frontend_process.terminate()
    print("服務已停止")
    sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="啟動多國語藥盒OCR系統")
    parser.add_argument("--api-port", type=int, default=8000, help="API伺服器端口")
    parser.add_argument("--frontend-port", type=int, default=8501, help="Streamlit前端端口")
    parser.add_argument("--api-only", action="store_true", help="只啟動API伺服器")
    parser.add_argument("--frontend-only", action="store_true", help="只啟動前端")
    
    args = parser.parse_args()
    
    # 註冊信號處理
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    # 啟動服務
    api_process = None
    frontend_process = None
    
    try:
        if not args.frontend_only:
            api_process = run_api_server(args.api_port)
            
        if not args.api_only:
            # 等待API伺服器啟動
            if api_process:
                print("等待API伺服器啟動...")
                time.sleep(2)
                
            frontend_process = run_frontend(args.frontend_port, args.api_port)
        
        print("\n服務已啟動！")
        print(f"API伺服器: http://localhost:{args.api_port}")
        print(f"Streamlit前端: http://localhost:{args.frontend_port}")
        print("按 Ctrl+C 停止服務\n")
        
        # 等待進程結束
        if api_process:
            api_process.wait()
        if frontend_process:
            frontend_process.wait()
            
    except KeyboardInterrupt:
        handle_signal(signal.SIGINT, None)
    except Exception as e:
        print(f"啟動服務時發生錯誤: {str(e)}")
        if api_process:
            api_process.terminate()
        if frontend_process:
            frontend_process.terminate()
        sys.exit(1) 