"""
Service nhận diện giọng nói sử dụng faster-whisper.
Chạy hoàn toàn local, không cần API key.
"""
import os
import subprocess
import glob
import re
from faster_whisper import WhisperModel
from huggingface_hub import snapshot_download
from config import WHISPER_MODEL, WHISPER_DEVICE, WHISPER_COMPUTE_TYPE, BASE_DIR

try:
    from rapidocr_onnxruntime import RapidOCR
    _ocr_engine = RapidOCR()
except Exception:
    _ocr_engine = None

MODELS_DIR = os.path.join(BASE_DIR, "models")


class Transcriber:
    """Nhận diện giọng nói và tạo phụ đề SRT chuẩn thời gian từng câu."""

    def __init__(self):
        self._models = {}

    def _download_model(self, model_size: str) -> str:
        model_dir = os.path.join(MODELS_DIR, f"faster-whisper-{model_size}")
        if os.path.exists(model_dir) and any(f.endswith('.bin') for f in os.listdir(model_dir)):
            return model_dir

        os.makedirs(model_dir, exist_ok=True)
        repo_id = f"Systran/faster-whisper-{model_size}"
        print(f"[Transcriber] Đang tải model '{model_size}' từ HuggingFace...")
        snapshot_download(repo_id, local_dir=model_dir)
        return model_dir

    def _load_model(self, model_size: str):
        if model_size not in self._models:
            model_path = self._download_model(model_size)
            print(f"[Transcriber] Đang nạp model Whisper '{model_size}'...")
            try:
                self._models[model_size] = WhisperModel(
                    model_path,
                    device=WHISPER_DEVICE,
                    compute_type=WHISPER_COMPUTE_TYPE,
                    cpu_threads=min(4, os.cpu_count() or 4),
                    num_workers=2
                )
                print(f"[Transcriber] Model '{model_size}' đã sẵn sàng trên {WHISPER_DEVICE}!")
            except Exception as e:
                print(f"⚠️ [Transcriber] Lỗi {WHISPER_DEVICE} ({e}). Chuyển sang CPU...")
                threads = min(4, os.cpu_count() or 4)
                self._models[model_size] = WhisperModel(
                    model_path,
                    device="cpu",
                    compute_type="int8",
                    cpu_threads=threads,
                    num_workers=threads
                )
                print(f"[Transcriber] Model '{model_size}' đã sẵn sàng trên CPU!")
        return self._models[model_size]

    def scan_video_ocr_full(self, v_path: str) -> list:
        if not _ocr_engine or not os.path.exists(v_path):
            return []
        try:
            cmd_dur = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{v_path}"'
            res_dur = subprocess.run(cmd_dur, shell=True, capture_output=True, text=True)
            v_dur = float(res_dur.stdout.strip()) if res_dur.stdout.strip() else 0
        except Exception:
            v_dur = 0

        if v_dur <= 0:
            return []

        ocr_full = []
        sample_t = 1.0
        frame_idx = 0
        job_dir = os.path.dirname(v_path)
        while sample_t < v_dur:
            tmp_img = os.path.join(job_dir, f"app_ocr_{frame_idx}.jpg")
            cmd_f = f'ffmpeg -y -ss {sample_t:.2f} -i "{v_path}" -vframes 1 "{tmp_img}"'
            subprocess.run(cmd_f, shell=True, capture_output=True)
            if os.path.exists(tmp_img):
                try:
                    ocr_res, _ = _ocr_engine(tmp_img)
                    if ocr_res:
                        for item in ocr_res:
                            txt = item[1].strip()
                            score = item[2]
                            if score >= 0.70 and len(txt) >= 2 and not any(w in txt for w in ["动漫", "虚构", "架空", "@", "http", "制作"]):
                                if not any(r['text'] == txt for r in ocr_full):
                                    ocr_full.append({
                                        'index': len(ocr_full) + 1,
                                        'start': round(sample_t, 3),
                                        'end': round(min(v_dur, sample_t + 2.5), 3),
                                        'text': txt
                                    })
                except Exception:
                    pass
                try:
                    os.remove(tmp_img)
                except Exception:
                    pass
            sample_t += 1.5
            frame_idx += 1

        ocr_full.sort(key=lambda x: x['start'])
        return ocr_full

    def transcribe(self, audio_path: str, model_size: str = "base", 
                   source_lang: str = "zh", progress_callback=None) -> list:
        """
        Nhận diện giọng nói chuẩn xác thời gian từng câu gốc từ Whisper.
        """
        model = self._load_model(model_size)
        lang = None if source_lang == "auto" else source_lang

        try:
            segments_gen, info = model.transcribe(
                audio_path,
                beam_size=5,
                language=lang,
                condition_on_previous_text=True,
                vad_filter=False,
                no_speech_threshold=0.6
            )
            segments_list = list(segments_gen)
        except RuntimeError as cuda_err:
            if any(term in str(cuda_err).lower() for term in ["cublas", "cuda", "cudnn"]):
                print(f"⚠️ [Transcriber] Chuyển Whisper sang CPU do lỗi CUDA: {cuda_err}")
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
                segments_gen, info = model.transcribe(
                    audio_path,
                    beam_size=5,
                    language=lang,
                    condition_on_previous_text=True,
                    vad_filter=False,
                    no_speech_threshold=0.6
                )
                segments_list = list(segments_gen)
            else:
                raise cuda_err

        # Chuyển đổi chuẩn xác từng câu thoại theo đúng thời gian nói thực tế
        result = []
        total_duration = getattr(info, 'duration', 0) or 0

        for seg in segments_list:
            text = seg.text.strip()
            if not text:
                continue

            if total_duration > 0 and seg.start >= (total_duration - 0.2):
                break

            seg_end = min(seg.end, total_duration) if total_duration > 0 else seg.end

            result.append({
                'index': len(result) + 1,
                'start': round(seg.start, 3),
                'end': round(seg_end, 3),
                'text': text
            })

            if progress_callback and total_duration > 0:
                progress_callback(min(seg.end / total_duration * 100, 99))

        if progress_callback:
            progress_callback(100)

        # Tìm đường dẫn MP4 để quét OCR khôi phục chữ in màn hình
        v_path = audio_path
        if v_path.lower().endswith('.wav') or not v_path.lower().endswith(('.mp4', '.mkv', '.mov', '.avi', '.webm', '.flv')):
            possible_mp4 = os.path.splitext(audio_path)[0] + '.mp4'
            job_dir = os.path.dirname(audio_path)
            job_id = os.path.basename(job_dir)
            c1 = os.path.join("downloads", job_id, "local_video.mp4")
            c2 = os.path.join(os.getcwd(), "downloads", job_id, "local_video.mp4")
            if os.path.exists(possible_mp4):
                v_path = possible_mp4
            elif os.path.exists(c1):
                v_path = c1
            elif os.path.exists(c2):
                v_path = c2
            else:
                v_matches = glob.glob(os.path.join("downloads", job_id, "*.*")) + glob.glob(os.path.join(job_dir, "*.*"))
                for m in v_matches:
                    if m.lower().endswith(('.mp4', '.mkv', '.mov', '.avi', '.webm', '.flv')):
                        v_path = m
                        break

        # Nếu audio rỗng (ví dụ video câm/chỉ có nhạc), tự động chạy Full Video OCR
        if _ocr_engine and os.path.exists(v_path) and len(result) <= 1:
            print("⚠️ [Transcriber] Whisper không phát hiện âm thanh. Đang chạy Video OCR đọc chữ in...")
            ocr_full = self.scan_video_ocr_full(v_path)
            if ocr_full:
                result.extend(ocr_full)
                result.sort(key=lambda x: x['start'])

                # PASS 2: Quét mắt nhìn OCR đọc chữ in khung hình cho tất cả các khoảng trống thoại >= 0.8s
        if _ocr_engine and os.path.exists(v_path) and len(result) >= 2:
            ocr_recovered = []
            for i in range(len(result) - 1):
                curr_s = result[i]
                next_s = result[i + 1]
                gap_dur = next_s['start'] - curr_s['end']
                if gap_dur >= 0.8:
                    s_t = curr_s['end']
                    e_t = next_s['start']
                    sample_t = s_t + 0.4
                    while sample_t < e_t:
                        tmp_img = os.path.join(os.path.dirname(v_path), f"ocr_gap_{i}_{int(sample_t*10)}.jpg")
                        cmd = f'ffmpeg -y -ss {sample_t:.2f} -i "{v_path}" -vframes 1 "{tmp_img}"'
                        subprocess.run(cmd, shell=True, capture_output=True)
                        if os.path.exists(tmp_img):
                            try:
                                ocr_res, _ = _ocr_engine(tmp_img)
                                if ocr_res:
                                    for item in ocr_res:
                                        txt = item[1].strip()
                                        score = item[2]
                                        if score >= 0.70 and len(txt) >= 2 and not any(w in txt for w in ["动漫", "虚构", "架空", "@", "http", "制作"]):
                                            if txt != curr_s['text'] and txt != next_s['text'] and not any(r['text'] == txt for r in ocr_recovered):
                                                ocr_recovered.append({
                                                    'start': round(sample_t, 3),
                                                    'end': round(min(e_t - 0.05, sample_t + 1.6), 3),
                                                    'text': txt
                                                })
                            except Exception:
                                pass
                            try:
                                os.remove(tmp_img)
                            except Exception:
                                pass
                        sample_t += 1.0

            if ocr_recovered:
                print(f"[Transcriber OCR Gap Sweep] Đã đọc chữ từ khung hình và bù đắp thành công {len(ocr_recovered)} câu thoại/chữ in trong các khoảng trống!")
                result.extend(ocr_recovered)
                result.sort(key=lambda x: x['start'])

        # Sắp xếp theo thứ tự thời gian bắt đầu và khử 100% hiện tượng đè/chồng lấn thời gian
        result.sort(key=lambda x: x['start'])
        for idx in range(len(result) - 1):
            curr_s = result[idx]
            next_s = result[idx + 1]
            if curr_s['end'] >= next_s['start']:
                curr_s['end'] = max(curr_s['start'] + 0.2, round(next_s['start'] - 0.05, 3))

        # Cập nhật số thứ tự index
        for idx, s in enumerate(result, 1):
            s['index'] = idx

        print(f"[Transcriber] Hoàn tất nhận diện {len(result)} câu thoại chuẩn xác thời gian (khử 100% chồng lấn).")
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
        Tạo file phụ đề SRT chuẩn 1 dải duy nhất, khử 100% chồng lấn/trùng mốc (Strict Monotonic Single-Track).
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        if not segments:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("")
            return output_path

        # 1. Sắp xếp chặt chẽ theo mốc bắt đầu, ưu tiên câu dài hơn nếu cùng mốc
        raw = sorted([dict(s) for s in segments if s.get('text', '').strip()], 
                     key=lambda x: (x['start'], -len(str(x.get('text', '')))))

        # 2. Khử các đoạn trùng lặp nội dung con ở cùng một mốc thời gian (<= 0.6s)
        deduped = []
        for s in raw:
            t_txt = str(s['text']).strip()
            t_start = s['start']
            is_dup = False
            for existing in deduped[-5:]:
                e_txt = str(existing['text']).strip()
                e_start = existing['start']
                if abs(t_start - e_start) <= 0.6:
                    if t_txt == e_txt or t_txt in e_txt or e_txt in t_txt:
                        if len(t_txt) > len(e_txt):
                            existing['text'] = t_txt
                        is_dup = True
                        break
            if not is_dup:
                deduped.append(s)

        # 3. Chuỗi thời gian tuyến tính đơn điệu bắt buộc (Đảm bảo 100% không đè timestamp)
        sequenced = []
        for s in deduped:
            start_t = s['start']
            end_t = s['end']
            
            if sequenced:
                prev_end = sequenced[-1]['end']
                if start_t <= prev_end + 0.04:
                    start_t = round(prev_end + 0.05, 3)
                    
            if end_t <= start_t + 0.3:
                end_t = round(start_t + 0.6, 3)
                
            sequenced.append({
                'index': len(sequenced) + 1,
                'start': round(start_t, 3),
                'end': round(end_t, 3),
                'text': str(s['text']).strip()
            })

        with open(output_path, 'w', encoding='utf-8') as f:
            for i, seg in enumerate(sequenced, 1):
                start_ts = Transcriber.format_timestamp(seg['start'])
                end_ts = Transcriber.format_timestamp(seg['end'])
                safe_text = str(seg['text']).replace('\r\n', '\n').strip()
                safe_text = '\n'.join([line.strip() for line in safe_text.split('\n') if line.strip()])
                f.write(f"{i}\n")
                f.write(f"{start_ts} --> {end_ts}\n")
                f.write(f"{safe_text}\n\n")

        print(f"[Transcriber] Đã tạo file SRT chuẩn 1 dải thẳng tắp CapCut (0 overlap): {output_path}")
        return output_path

    @staticmethod
    def parse_time(time_str: str) -> float:
        time_str = time_str.replace(',', '.')
        parts = time_str.split(':')
        hours = float(parts[0])
        minutes = float(parts[1])
        seconds = float(parts[2])
        return hours * 3600 + minutes * 60 + seconds

    @staticmethod
    def parse_srt(srt_text: str) -> list:
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
                        continue
        return segments
