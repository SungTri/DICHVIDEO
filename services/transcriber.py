"""
Service nhận diện giọng nói sử dụng faster-whisper.
Chạy hoàn toàn local, không cần API key.
"""
import os
from faster_whisper import WhisperModel
from huggingface_hub import snapshot_download
from config import WHISPER_MODEL, WHISPER_DEVICE, WHISPER_COMPUTE_TYPE, BASE_DIR

MODELS_DIR = os.path.join(BASE_DIR, "models")


class Transcriber:
    """Nhận diện giọng nói và tạo phụ đề SRT."""

    def __init__(self):
        self._models = {}  # Cache loaded models by size

    def _download_model(self, model_size: str) -> str:
        """
        Tải model Whisper vào thư mục local để tránh lỗi symlink trên Windows.
        
        Returns:
            Đường dẫn thư mục model
        """
        model_dir = os.path.join(MODELS_DIR, f"faster-whisper-{model_size}")

        # Kiểm tra model đã tải chưa
        if os.path.exists(model_dir) and any(
            f.endswith('.bin') for f in os.listdir(model_dir)
        ):
            print(f"[Transcriber] Model '{model_size}' đã có sẵn.")
            return model_dir

        os.makedirs(model_dir, exist_ok=True)
        repo_id = f"Systran/faster-whisper-{model_size}"

        print(f"[Transcriber] Đang tải model '{model_size}' từ HuggingFace...")
        snapshot_download(
            repo_id,
            local_dir=model_dir,
        )
        print(f"[Transcriber] Đã tải model vào: {model_dir}")
        return model_dir

    def _load_model(self, model_size: str):
        """Load model Whisper (lazy loading - chỉ load khi cần)."""
        if model_size not in self._models:
            print(f"[Transcriber] Đang nạp model Whisper '{model_size}'...")
            model_path = self._download_model(model_size)
            threads = min(4, os.cpu_count() or 4)
            try:
                self._models[model_size] = WhisperModel(
                    model_path,
                    device=WHISPER_DEVICE,
                    compute_type=WHISPER_COMPUTE_TYPE,
                    cpu_threads=threads,
                    num_workers=threads if WHISPER_DEVICE == "cpu" else 1
                )
                print(f"[Transcriber] Model '{model_size}' đã sẵn sàng trên {WHISPER_DEVICE}!")
            except Exception as e:
                print(f"⚠️ [Transcriber] Không thể chạy Whisper trên GPU ({e}). Tự động chuyển sang chạy bằng CPU (int8)!")
                self._models[model_size] = WhisperModel(
                    model_path,
                    device="cpu",
                    compute_type="int8",
                    cpu_threads=threads,
                    num_workers=threads
                )
                print(f"[Transcriber] Model '{model_size}' đã sẵn sàng trên CPU (int8)!")
        return self._models[model_size]

    def transcribe(self, audio_path: str, model_size: str = "base", 
                  source_lang: str = "en", progress_callback=None) -> list:
        """
        Nhận diện giọng nói từ file audio.
        
        Args:
            audio_path: Đường dẫn file audio (WAV)
            model_size: Kích thước model Whisper (base, small, medium)
            source_lang: Ngôn ngữ nguồn ('en', 'zh', 'ja', 'auto')
            progress_callback: Hàm callback(progress_percent)
            
        Returns:
            Danh sách segments: [{'index', 'start', 'end', 'text'}, ...]
        """
        model = self._load_model(model_size)

        # auto -> None để Whisper tự động phát hiện ngôn ngữ nguồn
        lang = None if source_lang == "auto" else source_lang

        try:
            segments_gen, info = model.transcribe(
                audio_path,
                beam_size=1,
                language=lang,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            # Thử duyệt qua generator để kích hoạt nạp thư viện CUDA thực tế
            segments_list = list(segments_gen)
        except RuntimeError as cuda_err:
            if any(term in str(cuda_err).lower() for term in ["cublas", "cuda", "cudnn"]):
                print(f"⚠️ [Transcriber] Lỗi thư viện CUDA khi chạy ({cuda_err}). Đang tự động chuyển Whisper sang CPU...")
                model_path = self._download_model(model_size)
                threads = min(4, os.cpu_count() or 4)
                model = WhisperModel(
                    model_path,
                    device="cpu",
                    compute_type="int8",
                    cpu_threads=threads,
                    num_workers=threads
                )
                self._models[model_size] = model
                
                # Chạy lại trên CPU
                segments_gen, info = model.transcribe(
                    audio_path,
                    beam_size=1,
                    language=lang,
                    vad_filter=True,
                    vad_parameters=dict(min_silence_duration_ms=500)
                )
                segments_list = list(segments_gen)
            else:
                raise cuda_err

        total_duration = getattr(info, 'duration', 0) or 0
        result = []

        for i, segment in enumerate(segments_list):
            text = segment.text.strip()
            if not text:
                continue

            result.append({
                'index': len(result) + 1,
                'start': segment.start,
                'end': segment.end,
                'text': text
            })

            # Ước lượng tiến trình dựa trên vị trí audio
            if progress_callback and total_duration > 0:
                progress = min(segment.end / total_duration * 100, 99)
                progress_callback(progress)

        if progress_callback:
            progress_callback(100)

        print(f"[Transcriber] Nhận diện được {len(result)} đoạn.")
        return result

    @staticmethod
    def format_timestamp(seconds: float) -> str:
        """Chuyển đổi giây sang định dạng SRT timestamp (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    @staticmethod
    def generate_srt(segments: list, output_path: str) -> str:
        """
        Tạo file phụ đề SRT từ danh sách segments.
        
        Args:
            segments: Danh sách segments
            output_path: Đường dẫn file SRT đầu ra
            
        Returns:
            Đường dẫn file SRT
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            for i, seg in enumerate(segments, 1):
                start_ts = Transcriber.format_timestamp(seg['start'])
                end_ts = Transcriber.format_timestamp(seg['end'])
                f.write(f"{i}\n")
                f.write(f"{start_ts} --> {end_ts}\n")
                # Xử lý an toàn: loại bỏ các dòng trắng liên tiếp, tránh làm hỏng định dạng SRT
                safe_text = str(seg['text']).replace('\r\n', '\n').strip()
                safe_text = '\n'.join([line.strip() for line in safe_text.split('\n') if line.strip()])
                f.write(f"{safe_text}\n\n")

        print(f"[Transcriber] Đã tạo file SRT: {output_path}")
        return output_path

    @staticmethod
    def parse_time(time_str: str) -> float:
        """Chuyển đổi định dạng SRT timestamp (HH:MM:SS,mmm hoặc HH:MM:SS.mmm) sang giây (float)."""
        time_str = time_str.replace(',', '.')
        parts = time_str.split(':')
        hours = float(parts[0])
        minutes = float(parts[1])
        seconds = float(parts[2])
        return hours * 3600 + minutes * 60 + seconds

    @staticmethod
    def parse_srt(srt_text: str) -> list:
        """Phân tích nội dung SRT thành danh sách segments (start, end, text)."""
        normalized = srt_text.replace('\r\n', '\n').strip()
        if not normalized:
            return []
        
        blocks = normalized.split('\n\n')
        segments = []
        
        for idx, block in enumerate(blocks, 1):
            block = block.strip()
            if not block:
                continue
            lines = block.split('\n')
            if len(lines) >= 3:
                time_line = lines[1]
                text = " ".join(lines[2:]).strip()
                
                parts = time_line.split("-->")
                if len(parts) == 2:
                    try:
                        start = Transcriber.parse_time(parts[0].strip())
                        end = Transcriber.parse_time(parts[1].strip())
                        segments.append({
                            "index": idx,
                            "start": start,
                            "end": end,
                            "text": text
                        })
                    except Exception as e:
                        print(f"[Transcriber] Lỗi parse block {idx}: {e}")
                        continue
        return segments
