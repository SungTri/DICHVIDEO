import os
import sys

# Đảm bảo console hỗ trợ UTF-8 (Tiếng Việt & Emoji) trên Windows
if sys.platform.startswith("win"):
    try:
        getattr(sys.stdout, 'reconfigure')(encoding='utf-8')
        getattr(sys.stderr, 'reconfigure')(encoding='utf-8')
    except AttributeError:
        pass


# ============================================================
# CẤU HÌNH ỨNG DỤNG DỊCH VIDEO TỰ ĐỘNG
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Thư mục ---
DOWNLOADS_DIR = os.path.join(BASE_DIR, "downloads")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
TEMP_DIR = os.path.join(BASE_DIR, "temp")

# Tạo thư mục nếu chưa có
for _dir in [DOWNLOADS_DIR, OUTPUTS_DIR, TEMP_DIR]:
    os.makedirs(_dir, exist_ok=True)

# --- Whisper (nhận diện giọng nói) ---
# Model: tiny, base, small, medium, large-v2, large-v3
WHISPER_MODEL = "base"

# Tự động phát hiện GPU Nvidia/CUDA để tăng tốc Whisper
try:
    # Thêm đường dẫn DLL của các thư viện Nvidia trong site-packages vào DLL search path (Windows)
    if os.name == 'nt':
        import sys
        for p in sys.path:
            if "site-packages" in p:
                nvidia_dir = os.path.join(p, "nvidia")
                if os.path.exists(nvidia_dir):
                    for root, dirs, files in os.walk(nvidia_dir):
                        if root.endswith("bin"):
                            try:
                                os.add_dll_directory(root)
                            except Exception:
                                pass

    # Thử xem ctranslate2 có CUDA khả dụng hay không và có đủ DLL cần thiết cho faster-whisper (ctranslate2) không
    import ctranslate2
    import ctypes
    
    has_cuda_dlls = False
    try:
        ctypes.CDLL("cublas64_12.dll")
        ctypes.CDLL("cublasLt64_12.dll")
        has_cuda_dlls = True
    except Exception:
        has_cuda_dlls = False

    if ctranslate2.get_cuda_device_count() > 0 and has_cuda_dlls:
        WHISPER_DEVICE = "cuda"
        WHISPER_COMPUTE_TYPE = "float16"
        print("⚡ [Config] Phát hiện GPU NVIDIA (CUDA): Đang chạy Whisper trên GPU!")
    else:
        WHISPER_DEVICE = "cpu"
        WHISPER_COMPUTE_TYPE = "int8"
        print("ℹ️ [Config] Chạy Whisper trên CPU (int8) để đảm bảo tính tương thích và ổn định.")
except Exception:
    WHISPER_DEVICE = "cpu"
    WHISPER_COMPUTE_TYPE = "int8"
    print("ℹ️ [Config] Chạy Whisper trên CPU (int8).")

# --- Gemini API Key (Không bắt buộc) ---
# Nếu có API Key, hệ thống sẽ tự động dùng Gemini để dịch phụ đề mượt mà, đúng ngữ cảnh
# Lấy key miễn phí tại: https://aistudio.google.com/
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# --- Groq API Key (Không bắt buộc - Dự phòng Free Tier) ---
# Cho phép sử dụng các mô hình Llama 3 dịch thuật chất lượng cao thay thế khi Gemini hết hạn mức
# Lấy key miễn phí tại: https://console.groq.com/
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# --- GitHub Token (Không bắt buộc - Dự phòng Free Tier) ---
# Dùng để dịch qua GPT-4o-mini miễn phí từ GitHub Models API
# Lấy token miễn phí tại: https://github.com/settings/tokens
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

# --- SambaNova API Key (Không bắt buộc - Dự phòng Free Tier) ---
# Dùng để dịch qua Llama 3.1 70B/405B miễn phí từ SambaNova Cloud
# Lấy key miễn phí tại: https://cloud.sambanova.ai/
SAMBANOVA_API_KEY = os.environ.get("SAMBANOVA_API_KEY", "")

# --- ElevenLabs API Key (Không bắt buộc - Cho phép dùng giọng đọc cao cấp) ---
# Đăng ký tại: https://elevenlabs.io/
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ADAM = "pNInz6obpgDQGcFmaJcg"
ELEVENLABS_VOICE_BELLA = "EXAVITQu4vr4xnSDxMaL"

# --- Audio Separation (Lọc giọng gốc bằng AI Demucs) ---
ENABLE_DEMUCS = True  # Kích hoạt tính năng này trong hệ thống

# --- TTS (tổng hợp giọng nói) ---
TTS_VOICE_FEMALE = "vi-VN-HoaiMyNeural"
TTS_VOICE_MALE = "vi-VN-NamMinhNeural"
DEFAULT_VOICE = TTS_VOICE_FEMALE

# --- FFmpeg ---
_FFMPEG_DIR = os.path.join(
    os.path.expanduser("~"),
    "AppData", "Local", "Microsoft", "WinGet", "Packages",
    "Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe",
    "ffmpeg-8.1.2-full_build", "bin"
)
# Dùng đường dẫn tuyệt đối nếu tồn tại, ngược lại dùng tên command
FFMPEG_PATH = os.path.join(_FFMPEG_DIR, "ffmpeg.exe") if os.path.isdir(_FFMPEG_DIR) else "ffmpeg"
FFPROBE_PATH = os.path.join(_FFMPEG_DIR, "ffprobe.exe") if os.path.isdir(_FFMPEG_DIR) else "ffprobe"

# --- Audio mixing ---
ORIGINAL_AUDIO_VOLUME = 0.15   # Giảm audio gốc xuống 15%
DUBBED_AUDIO_VOLUME = 1.0      # Audio lồng tiếng 100%

# --- Server ---
HOST = "0.0.0.0"
PORT = 8000

# --- Trọng số tiến trình cho từng bước (tổng = 100) ---
STEP_WEIGHTS = {
    0: 15,   # Tải video
    1: 25,   # Nhận diện giọng nói
    2: 15,   # Dịch thuật
    3: 25,   # Tạo lồng tiếng
    4: 20,   # Xuất video
}
# Config updated


# --- Tải cấu hình từ settings.json nếu tồn tại ---
def load_persistent_settings():
    global DOWNLOADS_DIR, OUTPUTS_DIR, TEMP_DIR
    global GEMINI_API_KEY, GROQ_API_KEY, GITHUB_TOKEN, SAMBANOVA_API_KEY, ELEVENLABS_API_KEY
    global TTS_VOICE_FEMALE, TTS_VOICE_MALE, DEFAULT_VOICE
    global ORIGINAL_AUDIO_VOLUME, DUBBED_AUDIO_VOLUME
    
    settings_path = os.path.join(BASE_DIR, "settings.json")
    if not os.path.exists(settings_path):
        return
        
    try:
        import json
        with open(settings_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        if not data:
            return
            
        # API Keys
        keys = data.get("api_keys", {})
        if keys.get("gemini"): GEMINI_API_KEY = keys["gemini"]
        if keys.get("groq"): GROQ_API_KEY = keys["groq"]
        if keys.get("github"): GITHUB_TOKEN = keys["github"]
        if keys.get("sambanova"): SAMBANOVA_API_KEY = keys["sambanova"]
        if keys.get("elevenlabs"): ELEVENLABS_API_KEY = keys["elevenlabs"]
        
        # Directories
        dirs = data.get("directories", {})
        if dirs.get("downloads"):
            DOWNLOADS_DIR = dirs["downloads"]
            os.makedirs(DOWNLOADS_DIR, exist_ok=True)
        if dirs.get("outputs"):
            OUTPUTS_DIR = dirs["outputs"]
            os.makedirs(OUTPUTS_DIR, exist_ok=True)
        if dirs.get("temp"):
            TEMP_DIR = dirs["temp"]
            os.makedirs(TEMP_DIR, exist_ok=True)
            
        # Voices
        voices = data.get("voices", {})
        if voices.get("default_female"):
            TTS_VOICE_FEMALE = voices["default_female"]
            DEFAULT_VOICE = TTS_VOICE_FEMALE
        if voices.get("default_male"):
            TTS_VOICE_MALE = voices["default_male"]
        pass
            
        # Audio volumes
        audio = data.get("audio", {})
        if "original_volume" in audio:
            ORIGINAL_AUDIO_VOLUME = float(audio["original_volume"])
        if "dubbed_volume" in audio:
            DUBBED_AUDIO_VOLUME = float(audio["dubbed_volume"])
            
        print("⚙️ [Config] Đã nạp cấu hình tùy chỉnh từ settings.json thành công!")
    except Exception as e:
        print(f"⚠️ [Config] Lỗi khi nạp settings.json: {e}")

load_persistent_settings()


