"""
Service tải video từ URL sử dụng yt-dlp.
Hỗ trợ YouTube, TikTok, Facebook, và nhiều platform khác.
"""
import os
import subprocess
import yt_dlp
from config import DOWNLOADS_DIR, FFMPEG_PATH


class VideoDownloader:
    """Tải video từ URL và tách audio."""

    def __init__(self):
        self.downloads_dir = DOWNLOADS_DIR

    def download(self, url: str, job_id: str, progress_callback=None, video_quality: str = "best") -> dict:
        """
        Tải video từ URL.
        
        Args:
            url: Link video (YouTube, TikTok, Facebook, v.v.)
            job_id: ID của job hiện tại
            progress_callback: Hàm callback(progress_percent)
            video_quality: Cấu hình chất lượng video ('best', '1080p', '720p', '360p')
            
        Returns:
            dict chứa thông tin video: title, duration, thumbnail, video_path
        """
        output_dir = os.path.join(self.downloads_dir, job_id)
        os.makedirs(output_dir, exist_ok=True)

        def progress_hook(d):
            if d['status'] == 'downloading':
                if progress_callback:
                    total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                    if total > 0:
                        pct = d.get('downloaded_bytes', 0) / total * 100
                        progress_callback(min(pct, 99))
            elif d['status'] == 'finished':
                if progress_callback:
                    progress_callback(100)

        # Xác định định dạng tải video dựa trên chất lượng được chọn
        if video_quality == "1080p":
            ydl_format = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]'
        elif video_quality == "720p":
            ydl_format = 'bestvideo[height<=720]+bestaudio/best[height<=720]'
        elif video_quality == "360p":
            ydl_format = 'bestvideo[height<=360]+bestaudio/best[height<=360]'
        else: # best
            ydl_format = 'bestvideo+bestaudio/best'

        ydl_opts = {
            'format': ydl_format,
            'outtmpl': os.path.join(output_dir, '%(title).50s.%(ext)s'),
            'progress_hooks': [progress_hook],
            'merge_output_format': 'mp4',
            'quiet': True,
            'no_warnings': True,
            'ffmpeg_location': os.path.dirname(FFMPEG_PATH) if os.path.dirname(FFMPEG_PATH) else None,
            'js_runtimes': {'node': {}},
            'remote_components': 'ejs:github',
            'extractor_args': {
                'youtube': {
                    'player_client': ['ios', 'android', 'web_embedded']
                }
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }
        }

        # Loại bỏ None values
        ydl_opts = {k: v for k, v in ydl_opts.items() if v is not None}

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore
            info = ydl.extract_info(url, download=True)
            video_path = ydl.prepare_filename(info)

            # Đảm bảo file có extension .mp4
            if not video_path.endswith('.mp4'):
                mp4_path = os.path.splitext(video_path)[0] + '.mp4'
                if os.path.exists(mp4_path):
                    video_path = mp4_path

            video_info = {
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'thumbnail': info.get('thumbnail', ''),
                'video_path': video_path,
                'uploader': info.get('uploader', ''),
            }

        return video_info

    def extract_audio(self, video_path: str, output_path: str | None = None) -> str:
        """
        Tách audio từ video thành file WAV (16kHz mono cho Whisper).
        
        Args:
            video_path: Đường dẫn file video
            output_path: Đường dẫn file audio đầu ra (tùy chọn)
            
        Returns:
            Đường dẫn file audio WAV
        """
        if output_path is None:
            output_path = os.path.splitext(video_path)[0] + '.wav'

        cmd = [
            FFMPEG_PATH, '-i', video_path,
            '-vn',                    # Không lấy video
            '-acodec', 'pcm_s16le',   # PCM 16-bit
            '-ar', '16000',           # Sample rate 16kHz (tối ưu cho Whisper)
            '-ac', '1',               # Mono
            '-y',                     # Ghi đè nếu tồn tại
            output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Lỗi tách audio: {result.stderr}")

        return output_path
