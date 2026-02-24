# 🎬 VideoGen AI
**Tạo video marketing tự động từ link sản phẩm hoặc ảnh — sẵn sàng đăng TikTok ngay**

---

## 🚀 CHẠY NHANH (3 bước)

### Windows
```batch
# 1. Cài FFmpeg: https://ffmpeg.org/download.html → Giải nén → Thêm vào PATH
# 2. Double-click file start.bat
# 3. Mở Chrome → http://localhost:8000
```

### Mac / Linux
```bash
# 1. Cài FFmpeg
brew install ffmpeg          # Mac
sudo apt install ffmpeg      # Ubuntu

# 2. Cấp quyền và chạy
chmod +x start.sh
./start.sh

# 3. Mở Chrome → http://localhost:8000
```

---

## 📦 CÀI ĐẶT THỦ CÔNG

### Yêu cầu hệ thống
- Python 3.9+
- FFmpeg
- 2GB RAM trở lên

### Bước 1: Cài Python
- Tải tại: https://python.org/downloads
- Tick ✅ "Add Python to PATH" khi cài

### Bước 2: Cài FFmpeg

**Windows:**
1. Tải tại: https://ffmpeg.org/download.html → Windows builds
2. Giải nén vào `C:\ffmpeg`
3. Thêm `C:\ffmpeg\bin` vào System PATH:
   - Windows Search → "Environment Variables"
   - System Variables → Path → Edit → New → `C:\ffmpeg\bin`

**Mac:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install ffmpeg -y
```

### Bước 3: Cài thư viện Python
```bash
cd videogen
python -m venv venv

# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### Bước 4: Khởi động
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Bước 5: Mở App
```
Laptop/Desktop: http://localhost:8000
Mobile cùng WiFi: http://[IP_LAN]:8000
```

**Tìm IP LAN:**
- Windows: `ipconfig` → IPv4 Address
- Mac/Linux: `ifconfig` → inet

---

## 📱 DÙNG TRÊN MOBILE

1. Đảm bảo điện thoại và máy tính **cùng mạng WiFi**
2. Tìm IP LAN của máy tính (xem trên)
3. Mở Chrome/Safari trên điện thoại
4. Nhập: `http://192.168.x.x:8000` (thay IP thật của bạn)
5. Dùng như web bình thường!

**Tip**: Thêm vào màn hình chính để dùng như app:
- iPhone: Safari → Share → "Add to Home Screen"
- Android: Chrome → menu ⋮ → "Add to Home Screen"

---

## 🌐 DEPLOY LÊN INTERNET MIỄN PHÍ

### Cách 1: Render.com (Khuyến nghị)
1. Đăng ký tại https://render.com (miễn phí)
2. New → Web Service → Connect GitHub repo
3. Chọn file `render.yaml` → Deploy
4. Lấy URL dạng: `https://videogen-ai.onrender.com`

### Cách 2: Railway.app
1. Đăng ký tại https://railway.app
2. New Project → Deploy from GitHub
3. Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Cách 3: Fly.io
```bash
# Cài fly CLI
curl -L https://fly.io/install.sh | sh
fly auth login
fly launch
fly deploy
```

---

## 🎮 CÁCH SỬ DỤNG

1. **Mở App** tại http://localhost:8000
2. **Nhập link sản phẩm** (Shopee/Lazada/Tiki) HOẶC **upload ảnh**
3. **Nhấn "TẠO VIDEO NGAY"**
4. **Đợi 15–60 giây** (xem thanh tiến trình)
5. **Tải video + copy caption + copy hashtag**
6. **Đăng lên TikTok!**

---

## 📁 CẤU TRÚC PROJECT

```
videogen/
├── main.py              # Backend FastAPI
├── requirements.txt     # Python dependencies
├── start.sh             # Mac/Linux start script
├── start.bat            # Windows start script
├── render.yaml          # Render.com config
├── Procfile             # Railway/Heroku config
├── templates/
│   └── index.html       # Frontend UI
├── static/              # Static files
├── uploads/             # Ảnh upload tạm
└── outputs/             # Video đã tạo
```

---

## ❓ FAQ

**Q: Video không có âm thanh?**
A: Bình thường. Bạn có thể thêm nhạc trong TikTok sau khi upload.

**Q: Không tải được từ link Shopee?**
A: Shopee có chặn bot. Hãy upload ảnh sản phẩm thay thế.

**Q: App chạy chậm?**
A: Lần đầu cài FFmpeg render có thể lâu hơn. Lần sau sẽ nhanh hơn.

**Q: Port 8000 bị chiếm?**
A: Đổi port: `uvicorn main:app --port 8080`

---

## 🛠️ NÂNG CẤP (Tùy chọn)

Thêm API keys để nâng cao chất lượng:

```bash
# .env file
OPENAI_API_KEY=sk-...        # GPT-4 để tạo caption hay hơn
REPLICATE_API_KEY=r8_...     # Stable Diffusion tạo ảnh
```

---

*VideoGen AI v2.0 · Made for TikTok creators*
