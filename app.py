"""
FastAPI server chính cho ứng dụng Dịch Video Tự Động.
Cung cấp REST API và WebSocket cho realtime progress.
Hỗ trợ Workspace Biên Tập tương tác.
"""
import os
import sys

# Đảm bảo console hỗ trợ UTF-8 (Tiếng Việt & Emoji) trên Windows
if sys.platform.startswith("win"):
    try:
        getattr(sys.stdout, 'reconfigure')(encoding='utf-8')
        getattr(sys.stderr, 'reconfigure')(encoding='utf-8')
    except AttributeError:
        pass

import asyncio
import uuid
import shutil
import traceback
import json
import time
from typing import Dict, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Response, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import (
    BASE_DIR, DOWNLOADS_DIR, OUTPUTS_DIR, TEMP_DIR,
    HOST, PORT, STEP_WEIGHTS, DEFAULT_VOICE
)
from services.downloader import VideoDownloader
from services.transcriber import Transcriber
from services.translator import Translator
from services.tts import TTSService
from services.video_processor import VideoProcessor


# ============================================================
# KHỞI TẠO APP VÀ SERVICES
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Kiểm tra các yêu cầu khi khởi động."""
    print("=" * 60)
    print("🎬 VIDEO TRANSLATOR - Workspace Biên Tập Chuyên Nghiệp")
    print("=" * 60)

    # Kiểm tra FFmpeg
    if VideoProcessor.check_ffmpeg():
        print("✅ FFmpeg: Đã cài đặt")
    else:
        print("❌ FFmpeg: CHƯA CÀI ĐẶT!")
        print("   Hãy cài FFmpeg từ: https://ffmpeg.org/download.html")

    print(f"🌐 Server: http://localhost:{PORT}")
    print("=" * 60)
    yield


app = FastAPI(title="Video Translator", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Khởi tạo services
downloader = VideoDownloader()
transcriber = Transcriber()
translator = Translator()
tts_service = TTSService()
video_processor = VideoProcessor()

# Lưu trữ job (history.json vĩnh viễn + in-memory cache)
HISTORY_FILE = os.path.join(BASE_DIR, "history.json")

def load_history() -> dict:
    if not os.path.exists(HISTORY_FILE):
        return {}
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[History] Lỗi đọc file history.json: {e}")
        return {}

def save_history(history_data: dict):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[History] Lỗi ghi file history.json: {e}")

jobs: Dict[str, dict] = load_history()

# Tên các bước xử lý
STEP_NAMES = [
    {"name": "Tải video", "icon": "📥"},
    {"name": "Nhận diện giọng nói", "icon": "🎙️"},
    {"name": "Dịch thuật", "icon": "🌐"},
    {"name": "Tạo lồng tiếng", "icon": "🗣️"},
    {"name": "Xuất video", "icon": "🎬"},
]


# ============================================================
# WEBSOCKET MANAGER
# ============================================================

class ConnectionManager:
    """Quản lý kết nối WebSocket cho từng job."""

    def __init__(self):
        self.connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, job_id: str, websocket: WebSocket):
        await websocket.accept()
        if job_id not in self.connections:
            self.connections[job_id] = []
        self.connections[job_id].append(websocket)

    def disconnect(self, job_id: str, websocket: WebSocket):
        if job_id in self.connections:
            try:
                self.connections[job_id].remove(websocket)
            except ValueError:
                pass
            if not self.connections[job_id]:
                del self.connections[job_id]

    async def send_update(self, job_id: str, data: dict):
        if job_id in self.connections:
            dead = []
            for ws in self.connections[job_id]:
                try:
                    await ws.send_json(data)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                try:
                    self.connections[job_id].remove(ws)
                except ValueError:
                    pass


manager = ConnectionManager()


# ============================================================
# PROGRESS HELPERS
# ============================================================

def init_job(job_id: str, series_name: str | None = None, episode_name: str | None = None, separate_vocals: bool = False) -> dict:
    """Khởi tạo trạng thái job mới và lưu vào lịch sử."""
    job = {
        "job_id": job_id,
        "status": "processing",
        "overall_progress": 0,
        "current_step": 0,
        "message": "Đang khởi tạo...",
        "series_name": series_name,
        "episode_name": episode_name,
        "separate_vocals": separate_vocals,
        "steps": [
            {
                "name": step["name"],
                "icon": step["icon"],
                "status": "pending",
                "progress": 0
            }
            for step in STEP_NAMES
        ],
        "video_info": None,
        "video_url": None,
        "segments": None,
        "download_url": None,
        "error": None,
        "original_volume": 0.15,
        "dubbed_volume": 1.0,
        "created_at": time.time(),  # Mốc thời gian tạo
        # Trạng thái style phụ đề
        "sub_style": {
            "color": "white",
            "size": 22,
            "bg": "outline"
        }
    }
    jobs[job_id] = job
    save_history(jobs)
    return job


def calculate_overall_progress(job: dict) -> int:
    """Tính tổng tiến trình dựa trên trọng số từng bước."""
    total = 0
    for i, step in enumerate(job["steps"]):
        weight = STEP_WEIGHTS.get(i, 0)
        total += weight * step["progress"] / 100
    return int(min(total, 100))


async def update_step(job_id: str, step_index: int, status: str,
                      progress: float, message: str = ""):
    """Cập nhật tiến trình của một bước và gửi qua WebSocket."""
    if job_id not in jobs:
        return

    job = jobs[job_id]

    if 0 <= step_index < len(job["steps"]):
        job["steps"][step_index]["status"] = status
        job["steps"][step_index]["progress"] = min(progress, 100)

    job["current_step"] = step_index
    job["message"] = message
    job["overall_progress"] = calculate_overall_progress(job)

    await manager.send_update(job_id, job)


def make_sync_callback(job_id: str, step_index: int, loop, message_prefix=""):
    """
    Tạo callback đồng bộ cho các service chạy trong thread.
    Callback sẽ cập nhật progress và gửi WebSocket update trên event loop.
    """
    def callback(progress: float):
        if job_id not in jobs:
            return
        job = jobs[job_id]
        if 0 <= step_index < len(job["steps"]):
            job["steps"][step_index]["progress"] = min(progress, 100)
            job["steps"][step_index]["status"] = "processing"
        job["current_step"] = step_index
        job["overall_progress"] = calculate_overall_progress(job)

        msg = f"{message_prefix} {int(progress)}%" if message_prefix else f"{int(progress)}%"
        job["message"] = msg

        # Schedule async WebSocket send trên main event loop
        try:
            asyncio.run_coroutine_threadsafe(
                manager.send_update(job_id, job), loop
            )
        except Exception:
            pass

    return callback


# ============================================================
# PIPELINE GIAI ĐOẠN 1: TẢI & DỊCH THÔ
# ============================================================

async def process_pipeline_start(job_id: str, url: str | None = None, 
                                model_size: str = "base", 
                                source_lang: str = "en", 
                                original_volume: float = 0.15,
                                video_quality: str = "best",
                                context_prompt: str | None = None):
    """Giai đoạn 1: Tải video (hoặc dùng local file), tách audio, nhận dạng giọng nói, dịch thuật thô."""
    loop = asyncio.get_event_loop()
    job = jobs[job_id]
    job["original_volume"] = original_volume

    try:
        # ============ BƯỚC 0: TẢI HOẶC CHUẨN BỊ VIDEO ============
        if url:
            # Dịch từ URL
            await update_step(job_id, 0, "processing", 0, "Đang tải video...")
            dl_callback = make_sync_callback(job_id, 0, loop, "Đang tải video")
            video_info = await asyncio.to_thread(
                downloader.download, url, job_id, dl_callback, video_quality
            )
            filename = os.path.basename(video_info["video_path"])
            video_path = video_info["video_path"]
            title = video_info["title"]
            
            # Đo thời lượng thực tế của file video đã tải về máy thay vì tin tưởng metadata online
            duration = await asyncio.to_thread(
                video_processor.get_video_duration, video_path
            )
            
            # Cảnh báo nếu thời lượng thực tế ngắn hơn đáng kể so với metadata online (do bị chặn/giới hạn xem thử)
            metadata_duration = video_info.get("duration", 0)
            if metadata_duration and duration and (metadata_duration - duration > 5):
                print(f"⚠️ [Downloader] Cảnh báo: Thời lượng video thực tế ({duration}s) ngắn hơn so với metadata gốc ({metadata_duration}s). Có thể trang web (Bilibili/Youtube) đã chặn hoặc chỉ cho tải bản xem thử 10s!")
        else:
            # Video cục bộ đã tải lên ở downloads/{job_id}/local_video.mp4
            await update_step(job_id, 0, "processing", 50, "Đang xử lý tệp video...")
            video_path = os.path.join(DOWNLOADS_DIR, job_id, "local_video.mp4")
            if not os.path.exists(video_path):
                raise FileNotFoundError("Không tìm thấy tệp video được tải lên.")
            filename = "local_video.mp4"
            title = "Tệp video cục bộ"
            duration = await asyncio.to_thread(
                video_processor.get_video_duration, video_path
            )
            await update_step(job_id, 0, "completed", 100, "Đã chuẩn bị tệp video!")

        video_url = f"/downloads/{job_id}/{filename}"

        job["video_info"] = {
            "title": title,
            "duration": duration,
            "video_path": video_path,
        }
        job["video_url"] = video_url
        
        await update_step(job_id, 0, "completed", 100, "Chuẩn bị video xong!")

        # Tách audio
        await update_step(job_id, 0, "completed", 100, "Đang tách audio...")
        audio_path = await asyncio.to_thread(
            downloader.extract_audio, video_path
        )

        # ============ BƯỚC 1: NHẬN DIỆN GIỌNG NÓI ============
        await update_step(job_id, 1, "processing", 0, f"Đang nhận diện giọng nói (model: {model_size})...")

        tr_callback = make_sync_callback(job_id, 1, loop, "Đang nhận diện")
        segments = await asyncio.to_thread(
            transcriber.transcribe, audio_path, model_size, source_lang, tr_callback
        )

        if not segments:
            raise RuntimeError("Không nhận diện được giọng nói trong video. "
                             "Video có thể không có audio hoặc không đúng ngôn ngữ chọn.")

        # Tạo SRT tiếng Anh/nguồn tạm thời
        job_temp_dir = os.path.join(TEMP_DIR, job_id)
        os.makedirs(job_temp_dir, exist_ok=True)
        srt_en_path = os.path.join(job_temp_dir, "subtitles_en.srt")
        Transcriber.generate_srt(segments, srt_en_path)

        await update_step(job_id, 1, "completed", 100,
                         f"Nhận diện được {len(segments)} đoạn!")

        # ============ BƯỚC 2: DỊCH THUẬT ============
        await update_step(job_id, 2, "processing", 0, f"Đang dịch thuật {source_lang.upper()} → VI...")

        tl_callback = make_sync_callback(job_id, 2, loop, "Đang dịch")
        
        # Nếu ngôn ngữ nguồn được tự động nhận dạng, lấy code từ Whisper segments (mặc định 'en' nếu lỗi)
        trans_lang = source_lang
        if trans_lang == "auto":
            trans_lang = "en"  # Fallback

        translated_segments = await asyncio.to_thread(
            translator.translate_segments, segments, trans_lang, tl_callback, context_prompt
        )

        # Lưu bản dịch thô
        job["segments"] = translated_segments
        job_temp_dir = os.path.join(TEMP_DIR, job_id)
        os.makedirs(job_temp_dir, exist_ok=True)
        # Tự động tạo Thumbnail Tiếng Việt ban đầu
        try:
            video_path = job.get("video_info", {}).get("video_path")
            if video_path and os.path.exists(video_path):
                from services.thumbnail_generator import ThumbnailGenerator
                raw_thumb = os.path.join(job_temp_dir, "raw_thumb.jpg")
                thumb_path = os.path.join(job_temp_dir, "thumbnail.jpg")
                ThumbnailGenerator.capture_frame(video_path, raw_thumb, 3.0)
                title = job.get("export_folder", "") or "PHIM"
                ep = f"TẬP {job.get('export_episode', '')}" if job.get('export_episode') else ""
                ThumbnailGenerator.generate_thumbnail(raw_thumb, thumb_path, title, ep)
                job["thumbnail_url"] = f"/api/download/thumbnail/{job_id}"
        except Exception as th_err:
            print(f"[Pipeline] Lỗi tạo thumbnail tự động: {th_err}")

        await update_step(job_id, 2, "completed", 100, "Đã dịch xong!")

        # ============ CHUYỂN SANG REVIEW WORKSPACE ============
        job["status"] = "review"
        job["message"] = "Vui lòng kiểm tra bản dịch và style phụ đề trong Workspace."
        save_history(jobs)
        await manager.send_update(job_id, job)
        print(f"[Pipeline] Job {job_id} đã sẵn sàng cho Review!")

    except Exception as e:
        print(f"[Pipeline Stage 1] Job {job_id} lỗi: {e}")
        traceback.print_exc()

        job["status"] = "error"
        job["error"] = str(e)
        job["message"] = f"❌ Lỗi: {str(e)}"
        save_history(jobs)
        await manager.send_update(job_id, job)


# ============================================================
# PIPELINE GIAI ĐOẠN 2: LỒNG TIẾNG & XUẤT VIDEO
# ============================================================

async def process_pipeline_finish(job_id: str, segments: list, voice: str, sub_style: dict,
                                 original_volume: float | None = None, dubbed_volume: float | None = None,
                                 separate_vocals: bool = False, output_folder: str | None = None,
                                 custom_output_dir: str | None = None, blur_bars: list[dict] | None = None,
                                 logo_settings: dict | None = None,
                                 voice_speed: float = 1.0):
    """Giai đoạn 2: Tạo lồng tiếng từ bản dịch đã sửa, xuất video theo style cấu hình."""
    loop = asyncio.get_event_loop()
    job = jobs[job_id]
    job["status"] = "processing"
    job["segments"] = segments
    job["sub_style"] = sub_style
    job["separate_vocals"] = separate_vocals
    if original_volume is not None:
        job["original_volume"] = original_volume
    if dubbed_volume is not None:
        job["dubbed_volume"] = dubbed_volume

    try:
        job_temp_dir = os.path.join(TEMP_DIR, job_id)
        video_path = job["video_info"]["video_path"]
        original_vol_val = original_volume if original_volume is not None else job.get("original_volume", 0.15)

        # ============ BƯỚC 3: TẠO LỒNG TIẾNG ============
        await update_step(job_id, 3, "processing", 0, "Đang tổng hợp giọng lồng tiếng...")

        # Ghi đè file SRT tiếng Việt bằng bản đã sửa từ frontend
        srt_vi_path = os.path.join(job_temp_dir, "subtitles_vi.srt")
        Transcriber.generate_srt(segments, srt_vi_path)

        # Tổng hợp audio lồng tiếng
        tts_output_dir = os.path.join(job_temp_dir, "tts")
        video_duration = await asyncio.to_thread(
            video_processor.get_video_duration, video_path
        )

        async def tts_callback(progress):
            await update_step(job_id, 3, "processing", progress,
                            f"Đang tạo lồng tiếng {int(progress)}%")

        if voice == "none":
            dubbed_audio_path = None
            original_vol_val = 1.0
        else:
            dubbed_audio_path = await tts_service.generate_dubbed_audio(
                segments, tts_output_dir, video_duration,
                voice=voice, voice_speed=voice_speed, progress_callback=tts_callback
            )

        await update_step(job_id, 3, "completed", 100, "Đã tạo lồng tiếng xong!")

        # ============ BƯỚC 4: XUẤT VIDEO ============
        msg = "Đang tách nhạc nền gốc bằng AI Demucs (có thể mất vài phút)..." if separate_vocals else "Đang xuất video với Style mới..."
        await update_step(job_id, 4, "processing", 0, msg)

        output_filename = f"{job_id}_translated.mp4"
        
        target_dir = OUTPUTS_DIR
        if output_folder == "custom" and custom_output_dir:
            target_dir = custom_output_dir
        elif output_folder and output_folder != "default":
            target_dir = os.path.join(OUTPUTS_DIR, output_folder)
        elif job.get("series_name"):
            target_dir = os.path.join(OUTPUTS_DIR, job["series_name"])
            
        os.makedirs(target_dir, exist_ok=True)
        output_path = os.path.join(target_dir, output_filename)
        job["output_path"] = output_path

        vp_callback = make_sync_callback(job_id, 4, loop, "Đang xuất video")
        
        # Gọi video processor hỗ trợ style
        await asyncio.to_thread(
            video_processor.export_final,
            video_path, srt_vi_path, dubbed_audio_path, output_path,
            sub_color=sub_style.get("color", "white"),
            sub_size=sub_style.get("size", 22),
            sub_bg=sub_style.get("bg", "outline"),
            sub_position=sub_style.get("position", "bottom"),
            sub_font=sub_style.get("font", "Arial"),
            sub_bg_color=sub_style.get("bg_color", "#000000"),
            sub_bg_opacity=int(sub_style.get("bg_opacity", 80)),
            sub_outline=bool(sub_style.get("outline", True)),
            sub_outline_width=float(sub_style.get("outline_width", 2.0)),
            sub_shadow=bool(sub_style.get("shadow", True)),
            sub_margin_v_percent=float(sub_style.get("margin_v_percent", 5.0)),
            original_volume=original_vol_val,
            dubbed_volume=dubbed_volume,
            separate_vocals=separate_vocals,
            progress_callback=vp_callback,
            blur_bars=blur_bars,
            logo_settings=logo_settings
        )

        await update_step(job_id, 4, "completed", 100, "Hoàn thành!")

        # ============ HOÀN THÀNH ============
        job["status"] = "completed"
        job["overall_progress"] = 100
        job["message"] = "🎉 Video đã được dịch và xuất thành công!"
        job["download_url"] = f"/api/download/{job_id}"

        save_history(jobs)
        await manager.send_update(job_id, job)
        print(f"[Pipeline Finish] Job {job_id} đã hoàn thành xuất video!")

    except Exception as e:
        print(f"[Pipeline Stage 2] Job {job_id} lỗi: {e}")
        traceback.print_exc()

        job["status"] = "error"
        job["error"] = str(e)
        job["message"] = f"❌ Lỗi: {str(e)}"
        save_history(jobs)
        await manager.send_update(job_id, job)


# ============================================================
# API ENDPOINTS
# ============================================================

class StartRequest(BaseModel):
    url: str | None = None
    job_id: str | None = None
    model_size: str = "base"
    source_lang: str = "en"
    original_volume: float = 0.15
    video_quality: str = "best"
    series_name: str | None = None
    episode_name: str | None = None
    separate_vocals: bool = False
    context_prompt: str | None = None


class FinishRequest(BaseModel):
    job_id: str
    segments: List[dict]
    voice: str = DEFAULT_VOICE
    voice_speed: float = 1.0
    sub_style: dict = {"color": "white", "size": 22, "bg": "outline"}
    original_volume: float = 0.15
    dubbed_volume: float = 1.0
    separate_vocals: bool = False
    output_folder: str | None = None
    custom_output_dir: str | None = None
    blur_bars: list[dict] | None = None
    logo_settings: dict | None = None


class SrtToAudioRequest(BaseModel):
    srt_content: str
    voice: str = DEFAULT_VOICE
    voice_speed: float = 1.0


class PreviewRequest(BaseModel):
    job_id: str
    segments: List[dict]
    voice: str = DEFAULT_VOICE
    voice_speed: float = 1.0
    original_volume: float = 0.15
    dubbed_volume: float = 1.0


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """API upload video cục bộ từ client."""
    job_id = str(uuid.uuid4())[:8]
    job_dir = os.path.join(DOWNLOADS_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)
    
    file_path = os.path.join(job_dir, "local_video.mp4")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"job_id": job_id, "status": "uploaded"}


@app.post("/api/process")
async def start_processing(request: StartRequest):
    """API bắt đầu Giai đoạn 1 (Tải & dịch thô)."""
    job_id = request.job_id
    if not job_id:
        job_id = str(uuid.uuid4())[:8]
        
    init_job(job_id, series_name=request.series_name, episode_name=request.episode_name, separate_vocals=request.separate_vocals)

    # Chạy giai đoạn 1 trong background
    asyncio.create_task(
        process_pipeline_start(
            job_id, request.url, request.model_size, 
            request.source_lang, request.original_volume,
            request.video_quality, request.context_prompt
        )
    )

    return {"job_id": job_id, "status": "processing"}


@app.post("/api/process/finish")
async def finish_processing(request: FinishRequest):
    """API bắt đầu Giai đoạn 2 (Nhận sửa đổi, chạy TTS và xuất video)."""
    job_id = request.job_id
    if job_id not in jobs:
        return JSONResponse(status_code=404, content={"error": "Job không tồn tại"})

    job = jobs[job_id]
    if job["status"] not in ["review", "completed", "error"]:
        return JSONResponse(status_code=400, content={"error": "Job đang trong trạng thái xử lý khác"})

    # Reset progress các bước sau để hiển thị animation
    job["steps"][3]["status"] = "pending"
    job["steps"][3]["progress"] = 0
    job["steps"][4]["status"] = "pending"
    job["steps"][4]["progress"] = 0

    # Chạy giai đoạn 2 trong background
    asyncio.create_task(
        process_pipeline_finish(
            job_id, request.segments, request.voice, request.sub_style,
            request.original_volume, request.dubbed_volume,
            separate_vocals=request.separate_vocals,
            output_folder=request.output_folder,
            custom_output_dir=request.custom_output_dir,
            blur_bars=request.blur_bars,
            logo_settings=request.logo_settings,
            voice_speed=request.voice_speed
        )
    )

    return {"job_id": job_id, "status": "processing"}


@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    """Kiểm tra trạng thái job."""
    if job_id not in jobs:
        return JSONResponse(status_code=404, content={"error": "Job không tồn tại"})
    return jobs[job_id]


@app.get("/api/download/{job_id}")
async def download_result(job_id: str):
    """Tải video đã dịch."""
    if job_id not in jobs:
        return JSONResponse(status_code=404, content={"error": "Job không tồn tại"})

    job = jobs[job_id]
    if job["status"] != "completed":
        return JSONResponse(status_code=400, content={"error": "Video chưa xử lý xong"})

    output_path = job.get("output_path")
    if not output_path:
        output_filename = f"{job_id}_translated.mp4"
        output_path = os.path.join(OUTPUTS_DIR, output_filename)

    if not os.path.exists(output_path):
        return JSONResponse(status_code=404, content={"error": "File không tồn tại"})

    download_name = f"{job.get('video_info', {}).get('title', 'video')}_VI.mp4"
    download_name = "".join(c for c in download_name if c.isalnum() or c in " ._-").strip()
    if not download_name:
        download_name = "translated_video.mp4"

    # Sử dụng FileResponse để stream file hiệu quả, tránh tốn RAM
    import urllib.parse
    encoded_filename = urllib.parse.quote(download_name)
    headers = {
        "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
    }
    return FileResponse(
        path=output_path,
        media_type="video/mp4",
        headers=headers
    )

@app.get("/api/download/srt/{job_id}")
async def download_srt(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    job_temp_dir = os.path.join(TEMP_DIR, job_id)
    os.makedirs(job_temp_dir, exist_ok=True)
    srt_path = os.path.join(job_temp_dir, "subtitles_vi.srt")
    
    if not os.path.exists(srt_path) and job.get("segments"):
        from services.transcriber import Transcriber
        Transcriber.generate_srt(job["segments"], srt_path)

    if not os.path.exists(srt_path):
        return JSONResponse(status_code=404, content={"error": "File SRT không tồn tại"})
        
    try:
        with open(srt_path, "rb") as f:
            file_content = f.read()
            
        import urllib.parse
        download_name = f"{job.get('video_info', {}).get('title', 'video')}_VI.srt"
        download_name = "".join(c for c in download_name if c.isalnum() or c in " ._-").strip()
        encoded_filename = urllib.parse.quote(download_name)
        
        headers = {
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        }
        
        return Response(
            content=file_content,
            media_type="application/x-subrip",
            headers=headers
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Lỗi đọc file SRT: {str(e)}"})


@app.get("/api/download/thumbnail/{job_id}")
async def download_thumbnail(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    job_temp_dir = os.path.join(TEMP_DIR, job_id)
    os.makedirs(job_temp_dir, exist_ok=True)
    thumb_path = os.path.join(job_temp_dir, "thumbnail.jpg")
    
    # Nếu chưa có thumbnail.jpg, tự động tạo mới từ video
    if not os.path.exists(thumb_path):
        video_path = job.get("video_info", {}).get("video_path")
        if video_path and os.path.exists(video_path):
            from services.thumbnail_generator import ThumbnailGenerator
            raw_thumb = os.path.join(job_temp_dir, "raw_thumb.jpg")
            ThumbnailGenerator.capture_frame(video_path, raw_thumb, 3.0)
            
            title = job.get("export_folder", "") or "PHIM"
            ep = f"TẬP {job.get('export_episode', '')}" if job.get('export_episode') else ""
            ThumbnailGenerator.generate_thumbnail(raw_thumb, thumb_path, title, ep)

    if not os.path.exists(thumb_path):
        return JSONResponse(status_code=404, content={"error": "File Thumbnail không tồn tại"})
        
    try:
        with open(thumb_path, "rb") as f:
            file_content = f.read()
            
        import urllib.parse
        download_name = f"{job.get('video_info', {}).get('title', 'video')}_Thumbnail.jpg"
        download_name = "".join(c for c in download_name if c.isalnum() or c in " ._-").strip()
        encoded_filename = urllib.parse.quote(download_name)
        
        headers = {
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        }
        return Response(content=file_content, media_type="image/jpeg", headers=headers)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Lỗi đọc file Thumbnail: {str(e)}"})


class GenerateThumbnailRequest(BaseModel):
    job_id: str
    timestamp: float = 3.0
    title_text: str = ""
    episode_text: str = ""
    style: str = "banner"


@app.post("/api/thumbnail/generate")
async def generate_thumbnail_api(request: GenerateThumbnailRequest):
    job = jobs.get(request.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    job_temp_dir = os.path.join(TEMP_DIR, request.job_id)
    os.makedirs(job_temp_dir, exist_ok=True)
    
    video_path = job.get("video_info", {}).get("video_path")
    if not video_path or not os.path.exists(video_path):
        return JSONResponse(status_code=400, content={"error": "File video không tồn tại"})
        
    from services.thumbnail_generator import ThumbnailGenerator
    raw_thumb = os.path.join(job_temp_dir, "raw_thumb.jpg")
    thumb_path = os.path.join(job_temp_dir, "thumbnail.jpg")
    
    ThumbnailGenerator.capture_frame(video_path, raw_thumb, request.timestamp)
    title = request.title_text or job.get("export_folder", "")
    ep = request.episode_text or (f"TẬP {job.get('export_episode', '')}" if job.get('export_episode') else "")
    
    ThumbnailGenerator.generate_thumbnail(raw_thumb, thumb_path, title, ep, style=request.style)
    
    job["thumbnail_url"] = f"/api/download/thumbnail/{request.job_id}?t={int(time.time())}"
    save_history(jobs)
    return {"status": "success", "thumbnail_url": job["thumbnail_url"]}


@app.post("/api/thumbnail/upload/{job_id}")
async def upload_custom_thumbnail(job_id: str, file: UploadFile = File(...)):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    job_temp_dir = os.path.join(TEMP_DIR, job_id)
    os.makedirs(job_temp_dir, exist_ok=True)
    
    custom_input_path = os.path.join(job_temp_dir, "custom_thumb_input.jpg")
    thumb_path = os.path.join(job_temp_dir, "thumbnail.jpg")
    
    with open(custom_input_path, "wb") as f:
        content = await file.read()
        f.write(content)
        
    from services.thumbnail_generator import ThumbnailGenerator
    title = job.get("export_folder", "") or "PHIM"
    ep = f"TẬP {job.get('export_episode', '')}" if job.get('export_episode') else ""
    
    ThumbnailGenerator.generate_thumbnail(custom_input_path, thumb_path, title, ep)
    
    job["thumbnail_url"] = f"/api/download/thumbnail/{job_id}?t={int(time.time())}"
    save_history(jobs)
    return {"status": "success", "thumbnail_url": job["thumbnail_url"]}


from fastapi import Form

@app.post("/api/thumbnail/standalone")
async def generate_standalone_thumbnail(
    file: UploadFile = File(...),
    title_text: str = Form(""),
    episode_text: str = Form(""),
    sub_title_text: str = Form(""),
    style: str = Form("match_original"),
    timestamp: float = Form(3.0)
):
    """API tạo thumbnail độc lập từ file ảnh hoặc video người dùng tải lên trực tiếp."""
    temp_id = str(uuid.uuid4())[:8]
    st_dir = os.path.join(TEMP_DIR, "standalone_thumb_" + temp_id)
    os.makedirs(st_dir, exist_ok=True)
    
    filename = file.filename or "input_file"
    file_ext = os.path.splitext(filename)[1].lower()
    input_save_path = os.path.join(st_dir, "input" + file_ext)
    
    with open(input_save_path, "wb") as f:
        content = await file.read()
        f.write(content)
        
    from services.thumbnail_generator import ThumbnailGenerator
    raw_thumb_path = os.path.join(st_dir, "raw.jpg")
    output_thumb_path = os.path.join(st_dir, "thumbnail.jpg")
    
    if file_ext in [".mp4", ".mkv", ".mov", ".avi", ".webm", ".flv"]:
        ThumbnailGenerator.capture_frame(input_save_path, raw_thumb_path, timestamp)
    else:
        raw_thumb_path = input_save_path

    ThumbnailGenerator.generate_thumbnail(
        raw_thumb_path,
        output_thumb_path,
        title_text=title_text,
        episode_text=episode_text,
        sub_title_text=sub_title_text,
        style=style
    )
    
    import urllib.parse
    download_name = f"Thumbnail_{title_text or 'Phim'}.jpg"
    download_name = "".join(c for c in download_name if c.isalnum() or c in " ._-").strip()
    encoded_filename = urllib.parse.quote(download_name)
    
    headers = {
        "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
    }
    
    with open(output_thumb_path, "rb") as f:
        content = f.read()
        
    return Response(content=content, media_type="image/jpeg", headers=headers)


class InteractiveThumbnailRequest(BaseModel):
    clean_id: str
    cards: list = []


@app.post("/api/thumbnail/clean")
async def clean_thumbnail_api(
    file: UploadFile = File(...),
    timestamp: float = Form(3.0)
):
    """BƯỚC 1: Tải ảnh/video lên -> AI Tẩy Sạch Chữ Gốc (Inpainting) & trả về URL ảnh sạch."""
    temp_id = str(uuid.uuid4())[:8]
    st_dir = os.path.join(TEMP_DIR, "standalone_clean_" + temp_id)
    os.makedirs(st_dir, exist_ok=True)

    filename = file.filename or "input_file"
    file_ext = os.path.splitext(filename)[1].lower()
    input_save_path = os.path.join(st_dir, "input" + file_ext)

    with open(input_save_path, "wb") as f:
        content = await file.read()
        f.write(content)

    from services.thumbnail_generator import ThumbnailGenerator
    raw_thumb_path = os.path.join(st_dir, "raw.jpg")
    cleaned_thumb_path = os.path.join(st_dir, "cleaned.jpg")

    if file_ext in [".mp4", ".mkv", ".mov", ".avi", ".webm", ".flv"]:
        ThumbnailGenerator.capture_frame(input_save_path, raw_thumb_path, timestamp)
    else:
        raw_thumb_path = input_save_path

    # Tẩy sạch chữ Trung Quốc bằng AI OpenCV Inpainting
    ThumbnailGenerator.auto_clean_text(raw_thumb_path, cleaned_thumb_path)

    return {
        "status": "success",
        "clean_id": temp_id,
        "cleaned_url": f"/downloads/standalone_clean_{temp_id}/cleaned.jpg"
    }


@app.post("/api/thumbnail/export-interactive")
async def export_interactive_thumbnail(request: InteractiveThumbnailRequest):
    """BƯỚC 3: Vẽ các thẻ chữ Tiếng Việt theo vị trí kéo thả (X%, Y%) và tải về ảnh 1080p."""
    st_dir = os.path.join(TEMP_DIR, "standalone_clean_" + request.clean_id)
    cleaned_thumb_path = os.path.join(st_dir, "cleaned.jpg")

    if not os.path.exists(cleaned_thumb_path):
        raise HTTPException(status_code=404, detail="Không tìm thấy ảnh đã tẩy chữ")

    output_thumb_path = os.path.join(st_dir, "final_thumbnail.jpg")

    from services.thumbnail_generator import ThumbnailGenerator
    ThumbnailGenerator.render_interactive_cards(cleaned_thumb_path, output_thumb_path, request.cards)

    with open(output_thumb_path, "rb") as f:
        content = f.read()

    import urllib.parse
    headers = {
        "Content-Disposition": f"attachment; filename*=UTF-8''{urllib.parse.quote('Thumbnail_BienTap.jpg')}"
    }
    return Response(content=content, media_type="image/jpeg", headers=headers)





@app.post("/api/srt-to-audio")
async def srt_to_audio(request: SrtToAudioRequest):
    """Chuyển đổi file phụ đề SRT thành audio lồng tiếng MP3."""
    if not request.srt_content.strip():
        return JSONResponse(status_code=400, content={"error": "Nội dung SRT không được để trống"})
    
    # Phân tích cú pháp SRT thành các segment thoại
    segments = Transcriber.parse_srt(request.srt_content)
    if not segments:
        return JSONResponse(status_code=400, content={"error": "Không thể phân tích cú pháp SRT hoặc file không có phân đoạn nào hợp lệ"})
    
    try:
        # Tạo thư mục tạm thời cho tiến trình tổng hợp
        job_id = f"srt_{uuid.uuid4().hex[:8]}"
        job_temp_dir = os.path.join(TEMP_DIR, job_id)
        os.makedirs(job_temp_dir, exist_ok=True)
        
        # Sắp xếp các segments theo thời gian bắt đầu
        sorted_segments = sorted(segments, key=lambda x: x["start"])
        total_duration = max(seg["end"] for seg in sorted_segments)
        
        # Gọi tts_service để tổng hợp lồng tiếng và tự động khớp thời lượng
        dubbed_audio_path = await tts_service.generate_dubbed_audio(
            sorted_segments, job_temp_dir, total_duration,
            voice=request.voice, voice_speed=request.voice_speed
        )
        
        # Sao chép kết quả cuối cùng sang outputs
        output_filename = f"srt-sang-audio-{uuid.uuid4().hex[:8]}.mp3"
        output_path = os.path.join(OUTPUTS_DIR, output_filename)
        
        if os.path.exists(dubbed_audio_path):
            shutil.copy2(dubbed_audio_path, output_path)
        else:
            return JSONResponse(status_code=500, content={"error": "Lỗi tổng hợp âm thanh đầu ra"})
            
        # Giải phóng thư mục tạm thời
        shutil.rmtree(job_temp_dir, ignore_errors=True)
        
        return {
            "status": "success",
            "download_url": f"/api/download/audio/{output_filename}",
            "filename": output_filename,
            "segments_count": len(segments),
            "duration": total_duration
        }
        
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": f"Lỗi xử lý: {str(e)}"})


@app.post("/api/process/preview")
async def preview_processing(request: PreviewRequest):
    """Tạo video xem trước lồng tiếng (chỉ trộn âm thanh, không render sub, copy stream video siêu tốc)."""
    if request.job_id not in jobs:
        return JSONResponse(status_code=404, content={"error": "Job không tồn tại"})
    
    job = jobs[request.job_id]
    
    try:
        # 1. Tạo thư mục tạm
        job_temp_dir = os.path.join(TEMP_DIR, request.job_id)
        os.makedirs(job_temp_dir, exist_ok=True)
        
        # 2. Sắp xếp các phân đoạn phụ đề
        sorted_segments = sorted(request.segments, key=lambda x: x["start"])
        
        # 3. Tính toán tổng thời lượng
        video_info = job.get("video_info", {})
        total_duration = video_info.get("duration", 0.0)
        if not total_duration and sorted_segments:
            total_duration = max(seg["end"] for seg in sorted_segments)
            
        # 4. Tổng hợp lồng tiếng (TTS)
        dubbed_audio_path = await tts_service.generate_dubbed_audio(
            sorted_segments, job_temp_dir, total_duration,
            voice=request.voice
        )
        
        # 5. Xác định đường dẫn video gốc
        video_path = video_info.get("video_path")
        if not video_path or not os.path.exists(video_path):
            video_filename = "local_video.mp4"
            if video_info.get("is_youtube", False):
                # Nếu là youtube, tìm file mp4 trong thư mục download
                job_download_dir = os.path.join(DOWNLOADS_DIR, request.job_id)
                if os.path.exists(job_download_dir):
                    video_files = [f for f in os.listdir(job_download_dir) if f.endswith('.mp4')]
                    if video_files:
                        video_filename = video_files[0]
            video_path = os.path.join(DOWNLOADS_DIR, request.job_id, video_filename)
            
        if not video_path or not os.path.exists(video_path):
            return JSONResponse(status_code=404, content={"error": "Không tìm thấy video gốc để trộn âm thanh"})
            
        # 6. Trộn âm thanh và xuất video preview siêu tốc
        preview_filename = "preview.mp4"
        preview_path = os.path.join(DOWNLOADS_DIR, request.job_id, preview_filename)
        
        # Sử dụng mix_audio (copy video stream, chỉ recode aac audio - mất ~1s)
        processor = VideoProcessor()
        processor.mix_audio(
            video_path, dubbed_audio_path, preview_path,
            original_volume=request.original_volume,
            dubbed_volume=request.dubbed_volume
        )
        
        # 7. Trả về url tải/phát video preview (thêm timestamp để tránh cache trình duyệt)
        import time
        preview_url = f"/downloads/{request.job_id}/{preview_filename}?t={int(time.time())}"
        
        return {
            "status": "success",
            "preview_url": preview_url
        }
        
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": f"Lỗi tạo preview: {str(e)}"})


@app.get("/api/download/audio/{filename}")
async def download_audio(filename: str):
    """Tải file audio kết quả từ srt-to-audio."""
    output_path = os.path.join(OUTPUTS_DIR, filename)
    if not os.path.exists(output_path):
        return JSONResponse(status_code=404, content={"error": "File không tồn tại"})
    
    # Trả về Response nhị phân trực tiếp để chống lỗi kết nối Proactor trên Windows
    # Sử dụng FileResponse để tối ưu RAM
    import urllib.parse
    encoded_filename = urllib.parse.quote(filename)
    headers = {
        "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
    }
    return FileResponse(
        path=output_path,
        media_type="audio/mpeg",
        headers=headers
    )




FOLDERS_FILE = os.path.join(BASE_DIR, "folders.json")

def load_folders() -> list:
    if not os.path.exists(FOLDERS_FILE):
        return []
    try:
        with open(FOLDERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[Folders] Lỗi đọc file folders.json: {e}")
        return []

def save_folders(folders: list):
    try:
        with open(FOLDERS_FILE, "w", encoding="utf-8") as f:
            json.dump(folders, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Folders] Lỗi ghi file folders.json: {e}")


@app.get("/api/folders")
async def get_folders():
    """Lấy danh sách tất cả thư mục (bao gồm cả thư mục tự tạo và thư mục trích xuất từ các job)."""
    custom_folders = load_folders()
    job_folders = {job["series_name"].strip() for job in jobs.values() if job.get("series_name") and isinstance(job["series_name"], str)}
    
    all_folders = list(custom_folders)
    for folder in job_folders:
        if folder not in all_folders:
            all_folders.append(folder)
            
    return all_folders


@app.post("/api/folders")
async def add_folder(request: dict):
    """Tạo thư mục sẵn trước."""
    folder_name = request.get("name", "").strip()
    if not folder_name:
        return JSONResponse(status_code=400, content={"error": "Tên thư mục không được trống"})
        
    custom_folders = load_folders()
    if folder_name not in custom_folders:
        custom_folders.append(folder_name)
        save_folders(custom_folders)
        
    return {"status": "success", "name": folder_name}


@app.delete("/api/folders/{name}")
async def delete_folder(name: str):
    """Xóa một thư mục tự tạo."""
    name = name.strip()
    custom_folders = load_folders()
    if name in custom_folders:
        custom_folders.remove(name)
        save_folders(custom_folders)
    return {"status": "success"}


@app.get("/api/voice-preview")
async def voice_preview(voice: str):
    voice = voice.strip()
    preview_dir = os.path.join(BASE_DIR, "static", "previews")
    os.makedirs(preview_dir, exist_ok=True)
    
    output_path = os.path.join(preview_dir, f"{voice}.mp3")
    
    # Nếu đã có sẵn file nghe thử trong bộ nhớ đệm, trả về luôn
    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        return FileResponse(output_path)
        
    # Tạo đoạn âm thanh ngắn khoảng 3 giây
    preview_text = "Xin chào, đây là bản nghe thử giọng đọc của tôi."
    
    try:
        from services.tts import TTSService
        tts_service = TTSService()
        await tts_service.generate_speech(preview_text, output_path, voice=voice)
        return FileResponse(output_path)
    except Exception as e:
        print(f"[Preview] Lỗi tạo file nghe thử: {e}")
        return JSONResponse(status_code=500, content={"error": f"Lỗi tạo giọng nghe thử: {str(e)}"})


@app.get("/api/history")
async def get_history():
    """Lấy danh sách lịch sử dự án."""
    sorted_jobs = sorted(
        jobs.values(),
        key=lambda x: x.get("created_at", 0),
        reverse=True
    )
    # Rút gọn bớt segments để tránh payload quá lớn khi tải danh sách
    history_list = []
    for job in sorted_jobs:
        job_copy = job.copy()
        if "segments" in job_copy:
            job_copy["segments_count"] = len(job_copy["segments"]) if job_copy["segments"] else 0
            del job_copy["segments"]
        history_list.append(job_copy)
    return history_list


@app.delete("/api/job/{job_id}")
async def delete_job(job_id: str):
    """Xóa job và dọn dẹp files."""
    if job_id in jobs:
        del jobs[job_id]
        save_history(jobs)

    # Dọn dẹp files
    for directory in [DOWNLOADS_DIR, TEMP_DIR]:
        job_dir = os.path.join(directory, job_id)
        if os.path.exists(job_dir):
            shutil.rmtree(job_dir, ignore_errors=True)

    output_file = os.path.join(OUTPUTS_DIR, f"{job_id}_translated.mp4")
    if os.path.exists(output_file):
        os.remove(output_file)

    return {"status": "deleted"}


@app.get("/api/health")
async def health_check():
    """Kiểm tra sức khỏe hệ thống."""
    ffmpeg_ok = VideoProcessor.check_ffmpeg()
    return {
        "status": "ok",
        "ffmpeg": "installed" if ffmpeg_ok else "NOT FOUND",
        "active_jobs": len([j for j in jobs.values() if j["status"] == "processing"]),
    }


# ============================================================
# WEBSOCKET
# ============================================================

@app.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """WebSocket cho realtime progress updates."""
    await manager.connect(job_id, websocket)

    # Gửi trạng thái hiện tại
    if job_id in jobs:
        try:
            await websocket.send_json(jobs[job_id])
        except Exception:
            pass

    try:
        while True:
            # Giữ kết nối
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(job_id, websocket)
    except Exception:
        manager.disconnect(job_id, websocket)

# ============================================================
# SETTINGS API
# ============================================================

SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

def load_settings() -> dict:
    if not os.path.exists(SETTINGS_FILE):
        return {}
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_settings(data: dict):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Settings] Lỗi ghi settings.json: {e}")

def get_dir_size(path: str) -> int:
    """Tính dung lượng thư mục (bytes)."""
    total = 0
    if os.path.exists(path):
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    total += os.path.getsize(fp)
                except OSError:
                    pass
    return total

def format_size(size_bytes: int) -> str:
    """Chuyển bytes thành chuỗi dễ đọc."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

def mask_key(key: str) -> str:
    """Che giấu API key, chỉ hiện 4 ký tự cuối."""
    if not key:
        return ""
    if "," in key:
        return ",".join(mask_key(k.strip()) for k in key.split(","))
    if len(key) < 8:
        return ""
    return "•" * (len(key) - 4) + key[-4:]


@app.get("/api/settings")
async def get_settings():
    """Trả về toàn bộ cấu hình hiện tại."""
    import config
    
    user_settings = load_settings()
    
    # API Keys (masked)
    api_keys = {
        "gemini": mask_key(getattr(config, "GEMINI_API_KEY", "")),
        "groq": mask_key(getattr(config, "GROQ_API_KEY", "")),
        "github": mask_key(getattr(config, "GITHUB_TOKEN", "")),
        "sambanova": mask_key(getattr(config, "SAMBANOVA_API_KEY", "")),
        "elevenlabs": mask_key(getattr(config, "ELEVENLABS_API_KEY", "")),
    }
    
    # Trạng thái kết nối (đã cấu hình hay chưa)
    api_status = {
        "gemini": bool(getattr(config, "GEMINI_API_KEY", "")),
        "groq": bool(getattr(config, "GROQ_API_KEY", "")),
        "github": bool(getattr(config, "GITHUB_TOKEN", "")),
        "sambanova": bool(getattr(config, "SAMBANOVA_API_KEY", "")),
        "elevenlabs": bool(getattr(config, "ELEVENLABS_API_KEY", "")),
    }
    
    # Thư mục
    directories = {
        "downloads": getattr(config, "DOWNLOADS_DIR", ""),
        "outputs": getattr(config, "OUTPUTS_DIR", ""),
        "temp": getattr(config, "TEMP_DIR", ""),
    }
    
    # Giọng đọc
    voices = {
        "default_female": getattr(config, "TTS_VOICE_FEMALE", "vi-VN-HoaiMyNeural"),
        "default_male": getattr(config, "TTS_VOICE_MALE", "vi-VN-NamMinhNeural"),
        "elevenlabs_adam_id": getattr(config, "ELEVENLABS_VOICE_ADAM", ""),
        "elevenlabs_bella_id": getattr(config, "ELEVENLABS_VOICE_BELLA", ""),
    }
    
    # Âm thanh
    audio = {
        "original_volume": getattr(config, "ORIGINAL_AUDIO_VOLUME", 0.15),
        "dubbed_volume": getattr(config, "DUBBED_AUDIO_VOLUME", 1.0),
    }
    
    # Thông tin hệ thống
    has_ffmpeg = VideoProcessor.check_ffmpeg()
    whisper_device = getattr(config, "WHISPER_DEVICE", "cpu")
    whisper_compute = getattr(config, "WHISPER_COMPUTE_TYPE", "int8")
    
    system_info = {
        "ffmpeg": has_ffmpeg,
        "gpu_cuda": whisper_device == "cuda",
        "whisper_device": whisper_device,
        "whisper_compute_type": whisper_compute,
        "downloads_size": format_size(get_dir_size(DOWNLOADS_DIR)),
        "outputs_size": format_size(get_dir_size(OUTPUTS_DIR)),
        "temp_size": format_size(get_dir_size(TEMP_DIR)),
        "version": "1.0.0",
    }
    
    return {
        "api_keys": api_keys,
        "api_status": api_status,
        "directories": directories,
        "voices": voices,
        "audio": audio,
        "system_info": system_info,
    }


@app.post("/api/settings")
async def update_settings(request: dict):
    """Lưu cấu hình mới."""
    import config
    
    user_settings = load_settings()
    
    # Cập nhật API Keys (chỉ lưu nếu giá trị mới không phải masked)
    if "api_keys" in request:
        keys = request["api_keys"]
        if "gemini" in keys:
            new_g = keys["gemini"]
            old_g = getattr(config, "GEMINI_API_KEY", "")
            if "•" in new_g:
                new_g_list = [k.strip() for k in new_g.split(",")]
                old_g_list = [k.strip() for k in str(old_g).split(",")] if old_g else []
                
                old_map = {}
                for ok in old_g_list:
                    if ok:
                        old_map[mask_key(ok)] = ok
                        
                merged = []
                for nk in new_g_list:
                    if "•" in nk:
                        if nk in old_map:
                            merged.append(old_map[nk])
                    elif nk:
                        merged.append(nk)
                final_g = ",".join(merged)
            else:
                final_g = new_g
            config.GEMINI_API_KEY = final_g
            user_settings.setdefault("api_keys", {})["gemini"] = final_g
        if keys.get("groq") and "•" not in keys["groq"]:
            config.GROQ_API_KEY = keys["groq"]
            user_settings.setdefault("api_keys", {})["groq"] = keys["groq"]
        if keys.get("github") and "•" not in keys["github"]:
            config.GITHUB_TOKEN = keys["github"]
            user_settings.setdefault("api_keys", {})["github"] = keys["github"]
        if keys.get("sambanova") and "•" not in keys["sambanova"]:
            config.SAMBANOVA_API_KEY = keys["sambanova"]
            user_settings.setdefault("api_keys", {})["sambanova"] = keys["sambanova"]
        if keys.get("elevenlabs") and "•" not in keys["elevenlabs"]:
            config.ELEVENLABS_API_KEY = keys["elevenlabs"]
            user_settings.setdefault("api_keys", {})["elevenlabs"] = keys["elevenlabs"]
    
    # Cập nhật giọng đọc
    if "voices" in request:
        v = request["voices"]
        if v.get("default_female"):
            config.TTS_VOICE_FEMALE = v["default_female"]
            config.DEFAULT_VOICE = v["default_female"]
        if v.get("default_male"):
            config.TTS_VOICE_MALE = v["default_male"]
        if v.get("elevenlabs_adam_id"):
            config.ELEVENLABS_VOICE_ADAM = v["elevenlabs_adam_id"]
        if v.get("elevenlabs_bella_id"):
            config.ELEVENLABS_VOICE_BELLA = v["elevenlabs_bella_id"]
        user_settings["voices"] = v
    
    # Cập nhật âm lượng
    if "audio" in request:
        a = request["audio"]
        if "original_volume" in a:
            config.ORIGINAL_AUDIO_VOLUME = float(a["original_volume"])
        if "dubbed_volume" in a:
            config.DUBBED_AUDIO_VOLUME = float(a["dubbed_volume"])
        user_settings["audio"] = a
    
    # Cập nhật thư mục
    if "directories" in request:
        d = request["directories"]
        if d.get("downloads"):
            os.makedirs(d["downloads"], exist_ok=True)
            config.DOWNLOADS_DIR = d["downloads"]
        if d.get("outputs"):
            os.makedirs(d["outputs"], exist_ok=True)
            config.OUTPUTS_DIR = d["outputs"]
        if d.get("temp"):
            os.makedirs(d["temp"], exist_ok=True)
            config.TEMP_DIR = d["temp"]
        user_settings["directories"] = d
    
    save_settings(user_settings)
    return {"status": "ok", "message": "Đã lưu cài đặt thành công!"}


@app.post("/api/cleanup")
async def cleanup_data(request: dict):
    """Dọn dẹp dữ liệu: xóa temp, lịch sử, hoặc downloads."""
    target = request.get("target", "")
    results = []
    
    if target == "temp" or target == "all":
        if os.path.exists(TEMP_DIR):
            size_before = get_dir_size(TEMP_DIR)
            shutil.rmtree(TEMP_DIR, ignore_errors=True)
            os.makedirs(TEMP_DIR, exist_ok=True)
            results.append(f"Đã xóa thư mục tạm ({format_size(size_before)})")
    
    if target == "history" or target == "all":
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
            jobs.clear()
            results.append("Đã xóa toàn bộ lịch sử dự án")
    
    if target == "downloads" or target == "all":
        if os.path.exists(DOWNLOADS_DIR):
            size_before = get_dir_size(DOWNLOADS_DIR)
            shutil.rmtree(DOWNLOADS_DIR, ignore_errors=True)
            os.makedirs(DOWNLOADS_DIR, exist_ok=True)
            results.append(f"Đã xóa thư mục Downloads ({format_size(size_before)})")
    
    return {"status": "ok", "message": " | ".join(results) if results else "Không có gì để xóa."}


# ============================================================
# STATIC FILES & STARTUP
# ============================================================

# Serve downloads directory để frontend play video nguồn
app.mount("/downloads", StaticFiles(directory=DOWNLOADS_DIR), name="downloads")

# Serve static files (frontend)
static_dir = os.path.join(BASE_DIR, "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def serve_index():
    """Serve trang chính."""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse(content={"message": "Video Translator API is running"})





# ============================================================
# CHẠY SERVER
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host=HOST,
        port=PORT,
        reload=False,
        log_level="info"
    )
# Server entry point

