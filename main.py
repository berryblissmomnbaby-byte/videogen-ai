import os
import uuid
import json
import time
import asyncio
import httpx
import re
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request

app = FastAPI(title="VideoGen AI", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
STATIC_DIR = BASE_DIR / "static"

for d in [UPLOAD_DIR, OUTPUT_DIR, STATIC_DIR]:
    d.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR)), name="outputs")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# In-memory job store (use Redis in production)
jobs: dict = {}


def update_job(job_id: str, **kwargs):
    if job_id in jobs:
        jobs[job_id].update(kwargs)


async def fetch_product_info_from_url(url: str) -> dict:
    """Scrape basic product info from URL"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            html = resp.text

        # Extract title
        title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else "Sản phẩm"
        title = re.sub(r'\s+', ' ', title)[:100]

        # Extract description
        desc_match = re.search(
            r'<meta[^>]+(?:name=["\']description["\']|property=["\']og:description["\'])[^>]+content=["\']([^"\']{10,300})',
            html, re.IGNORECASE
        )
        description = desc_match.group(1).strip() if desc_match else "Sản phẩm chất lượng cao"

        # Extract price
        price_match = re.search(r'(\d[\d\.,]+)\s*(?:đ|VNĐ|vnđ|₫|USD|\$)', html)
        price = price_match.group(0) if price_match else ""

        # Extract image URL
        img_match = re.search(
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', html, re.IGNORECASE
        )
        image_url = img_match.group(1) if img_match else ""

        # Try download product image
        local_image = None
        if image_url:
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    img_resp = await client.get(image_url, headers=headers)
                    if img_resp.status_code == 200:
                        ext = ".jpg"
                        img_path = UPLOAD_DIR / f"url_img_{uuid.uuid4().hex}{ext}"
                        img_path.write_bytes(img_resp.content)
                        local_image = str(img_path)
            except Exception:
                pass

        return {
            "title": title,
            "description": description,
            "price": price,
            "image_url": image_url,
            "local_image": local_image,
            "source_url": url,
        }
    except Exception as e:
        return {
            "title": "Sản phẩm",
            "description": "Sản phẩm tuyệt vời với chất lượng cao",
            "price": "",
            "image_url": "",
            "local_image": None,
            "source_url": url,
        }


def generate_caption_and_hashtags(product_info: dict) -> dict:
    """Generate Vietnamese marketing caption + hashtags"""
    title = product_info.get("title", "Sản phẩm")
    description = product_info.get("description", "")
    price = product_info.get("price", "")

    price_text = f"\n💰 Giá chỉ: {price}" if price else ""

    captions = [
        f"""✨ {title} - Sản phẩm HOT nhất hôm nay!

{description[:150] if description else "Chất lượng đỉnh cao, giá cực hấp dẫn!"}{price_text}

🔥 Số lượng có hạn - Đặt ngay kẻo hết!
📦 Giao hàng toàn quốc
✅ Cam kết chính hãng 100%

👇 Bình luận "GIÁ" để nhận báo giá ngay!""",

        f"""💥 DEAL SỐC - {title}

👉 {description[:120] if description else "Sản phẩm được hàng nghìn người tin dùng"}{price_text}

⚡ Flash Sale hôm nay - Giảm đến 50%
🎁 Tặng quà cho 100 đơn đầu tiên
🚚 Free ship toàn quốc

💬 Nhắn tin ngay để được tư vấn miễn phí!""",

        f"""🌟 Đừng bỏ lỡ! {title}

✔️ {description[:100] if description else "Chất lượng vượt trội"}{price_text}
✔️ Đã có hàng triệu người dùng tin chọn
✔️ Bảo hành dài hạn

📲 Xem ngay - Mua liền tay!
🛒 Link trong bio hoặc bình luận để đặt hàng"""
    ]

    hashtags = [
        "#muasắm #sảnphẩmhot #deal #giảmgiá #tiktokshop",
        f"#{title.replace(' ', '').lower()[:15]} #trending #viral #mua1tặng1",
        "#shopee #lazada #tiktok #reviewsảnphẩm #unboxing"
    ]

    return {
        "captions": captions,
        "hashtags": hashtags,
        "main_caption": captions[0],
        "main_hashtags": hashtags[0] + " " + hashtags[1]
    }


async def create_video_from_image(image_path: str, product_info: dict, job_id: str) -> str:
    """Create marketing video using FFmpeg"""
    try:
        import subprocess
        import textwrap

        output_path = OUTPUT_DIR / f"video_{job_id}.mp4"
        title = product_info.get("title", "Sản phẩm")[:40]
        description = product_info.get("description", "")[:60]
        price = product_info.get("price", "")

        # Create overlay text
        overlay_lines = []
        overlay_lines.append(("✨ " + title, 80, "white", 32))
        if description:
            overlay_lines.append((description[:55] + "...", 130, "#FFD700", 22))
        if price:
            overlay_lines.append(("💰 " + price, 175, "#FF6B6B", 26))
        overlay_lines.append(("🛒 Mua ngay hôm nay!", 220, "#00FF88", 24))

        # Build drawtext filter chain
        drawtext_filters = []
        for i, (text, y, color, size) in enumerate(overlay_lines):
            safe_text = text.replace("'", "\\'").replace(":", "\\:").replace("[", "").replace("]", "")
            safe_text = safe_text.encode('ascii', errors='ignore').decode()
            hex_color = color.lstrip('#') if color.startswith('#') else 'ffffff'
            
            fade_in = f"if(lt(t,0.5),0,if(lt(t,1.5),t-0.5,1))"
            drawtext_filters.append(
                f"drawtext=text='{safe_text}'"
                f":fontsize={size}"
                f":fontcolor=white"
                f":x=(w-text_w)/2"
                f":y={y}"
                f":alpha='{fade_in}'"
                f":box=1:boxcolor=black@0.5:boxborderw=8"
            )

        # Watermark
        drawtext_filters.append(
            "drawtext=text='VideoGen AI'"
            ":fontsize=16:fontcolor=white@0.7"
            ":x=w-tw-20:y=h-th-20"
        )

        vf_chain = ",".join(drawtext_filters)

        # FFmpeg command - zoom effect + text overlay
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", image_path,
            "-t", "15",
            "-vf",
            f"scale=1080:1920:force_original_aspect_ratio=decrease,"
            f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,"
            f"zoompan=z='min(zoom+0.0008,1.3)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=375:s=1080x1920,"
            f"{vf_chain}",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-r", "30",
            str(output_path)
        ]

        update_job(job_id, step="Đang render video...", progress=70)
        
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0 or not output_path.exists():
            # Fallback: simpler FFmpeg without zoompan
            cmd_fallback = [
                "ffmpeg", "-y",
                "-loop", "1",
                "-i", image_path,
                "-t", "10",
                "-vf",
                "scale=1080:1920:force_original_aspect_ratio=decrease,"
                "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black",
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-crf", "28",
                "-pix_fmt", "yuv420p",
                str(output_path)
            ]
            proc2 = await asyncio.create_subprocess_exec(
                *cmd_fallback,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc2.communicate()

        return str(output_path) if output_path.exists() else ""

    except Exception as e:
        print(f"Video creation error: {e}")
        return ""


async def create_placeholder_video(job_id: str, product_info: dict) -> str:
    """Create a simple colored video when no image available"""
    try:
        output_path = OUTPUT_DIR / f"video_{job_id}.mp4"
        title = product_info.get("title", "Sản phẩm")[:35]
        
        safe_title = title.encode('ascii', errors='ignore').decode() or "San pham"
        
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", "color=c=0x1a1a2e:size=1080x1920:rate=30",
            "-t", "10",
            "-vf",
            f"drawtext=text='VideoGen AI'"
            f":fontsize=48:fontcolor=white:x=(w-text_w)/2:y=h/2-60,"
            f"drawtext=text='{safe_title}'"
            f":fontsize=32:fontcolor=gold:x=(w-text_w)/2:y=h/2+20",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-pix_fmt", "yuv420p",
            str(output_path)
        ]
        
        proc = await asyncio.create_subprocess_exec(*cmd,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await proc.communicate()
        
        return str(output_path) if output_path.exists() else ""
    except Exception as e:
        return ""


async def process_job(job_id: str, product_url: Optional[str], image_path: Optional[str]):
    """Main background job processor"""
    try:
        update_job(job_id, status="processing", step="Đang phân tích sản phẩm...", progress=10)
        await asyncio.sleep(0.5)

        product_info = {}

        if product_url:
            update_job(job_id, step="Đang tải thông tin sản phẩm...", progress=20)
            product_info = await fetch_product_info_from_url(product_url)
            if product_info.get("local_image"):
                image_path = product_info["local_image"]

        elif image_path:
            product_info = {
                "title": "Sản phẩm của bạn",
                "description": "Sản phẩm chất lượng cao, giá tốt nhất thị trường",
                "price": "",
                "source_url": "",
            }

        update_job(job_id, step="Đang tạo nội dung marketing...", progress=40)
        await asyncio.sleep(0.5)
        content = generate_caption_and_hashtags(product_info)

        update_job(job_id, step="Đang tạo video...", progress=55)

        video_path = ""
        if image_path and Path(image_path).exists():
            video_path = await create_video_from_image(image_path, product_info, job_id)
        
        if not video_path:
            update_job(job_id, step="Đang tạo video demo...", progress=65)
            video_path = await create_placeholder_video(job_id, product_info)

        update_job(job_id, step="Đang tạo caption & hashtag...", progress=85)
        await asyncio.sleep(0.5)

        video_filename = Path(video_path).name if video_path else ""

        update_job(
            job_id,
            status="done",
            step="Hoàn tất! ✅",
            progress=100,
            result={
                "video_url": f"/outputs/{video_filename}" if video_filename else "",
                "video_filename": video_filename,
                "product_title": product_info.get("title", ""),
                "product_description": product_info.get("description", ""),
                "captions": content["captions"],
                "hashtags": content["hashtags"],
                "main_caption": content["main_caption"],
                "main_hashtags": content["main_hashtags"],
            }
        )

    except Exception as e:
        update_job(job_id, status="error", step=f"Lỗi: {str(e)}", progress=0)


# === ROUTES ===

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/create-video")
async def create_video(
    background_tasks: BackgroundTasks,
    product_url: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
):
    if not product_url and not image:
        raise HTTPException(400, "Vui lòng nhập link sản phẩm hoặc upload ảnh")

    job_id = uuid.uuid4().hex
    jobs[job_id] = {
        "status": "pending",
        "step": "Đang chuẩn bị...",
        "progress": 0,
        "result": None
    }

    image_path = None
    if image and image.filename:
        ext = Path(image.filename).suffix or ".jpg"
        save_path = UPLOAD_DIR / f"upload_{job_id}{ext}"
        save_path.write_bytes(await image.read())
        image_path = str(save_path)

    background_tasks.add_task(process_job, job_id, product_url, image_path)

    return {"job_id": job_id}


@app.get("/api/job/{job_id}")
async def get_job(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Job không tồn tại")
    return jobs[job_id]


@app.get("/api/download/{filename}")
async def download_video(filename: str):
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(404, "File không tồn tại")
    return FileResponse(
        str(file_path),
        media_type="video/mp4",
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}
