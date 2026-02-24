#!/bin/bash
# VideoGen AI - Quick Start Script
echo "🎬 VideoGen AI - Khởi động..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 chưa được cài. Tải tại: https://python.org"
    exit 1
fi

# Check FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  FFmpeg chưa được cài."
    echo "   Ubuntu/Debian: sudo apt install ffmpeg"
    echo "   Mac:           brew install ffmpeg"
    echo "   Windows:       https://ffmpeg.org/download.html"
    echo ""
fi

# Create venv if not exists
if [ ! -d "venv" ]; then
    echo "📦 Tạo môi trường ảo..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null

# Install deps
echo "📥 Cài đặt thư viện..."
pip install -r requirements.txt -q

# Start server
echo ""
echo "✅ Khởi động thành công!"
echo "🌐 Mở trình duyệt: http://localhost:8000"
echo "📱 Dùng trên Mobile: http://[IP_MÁY_TÍNH]:8000"
echo "   (Xem IP bằng lệnh: ifconfig hoặc ipconfig)"
echo ""
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
