@echo off
echo 🎬 VideoGen AI - Khoi dong...

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Python chua duoc cai. Tai tai: https://python.org
    pause
    exit
)

if not exist venv (
    echo 📦 Tao moi truong ao...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo 📥 Cai dat thu vien...
pip install -r requirements.txt -q

echo.
echo ✅ Khoi dong thanh cong!
echo 🌐 Mo trinh duyet: http://localhost:8000
echo.
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
