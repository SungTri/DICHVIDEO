"""
Service nhận diện giọng nói sử dụng faster-whisper và bóc tách chữ in khung hình RapidOCR.
Chạy hoàn toàn local, không cần API key.
"""
import os
import re
import subprocess
import glob
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
        """Nạp model Whisper (có cache trong bộ nhớ)."""
        if model_size not in self._models:
            model_path = self._download_model(model_size)
            print(f"[Transcriber] Đang nạp model Whisper '{model_size}'...")
            
            try:
                # Ưu tiên chạy GPU (CUDA) với compute_type float16
                self._models[model_size] = WhisperModel(
                    model_path,
                    device=WHISPER_DEVICE,
                    compute_type=WHISPER_COMPUTE_TYPE,
                    cpu_threads=min(4, os.cpu_count() or 4),
                    num_workers=2
                )
                print(f"[Transcriber] Model '{model_size}' đã sẵn sàng trên {WHISPER_DEVICE}!")
            except Exception as e:
                # Fallback về CPU nếu CUDA gặp lỗi
                print(f"⚠️ [Transcriber] Không thể chạy trên {WHISPER_DEVICE} ({e}). Đang chuyển sang CPU...")
                threads = min(4, os.cpu_count() or 4)
                self._models[model_size] = WhisperModel(
                    model_path,
                    device="cpu",
                    compute_type="int8",
                    cpu_threads=threads,
                    num_workers=threads
                )
                print(f"[Transcriber] Model '{model_size}' đã sẵn sàng trên CPU (int8)!")
        return self._models[model_size]

    def scan_video_ocr_full(self, v_path: str) -> list:
        """Phương thức dự phòng Lưới An Toàn: Chụp ảnh và bóc chữ in trên toàn bộ video MP4."""
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
        Nhận diện giọng nói từ file audio và khôi phục thoại từ video OCR.

        Args:
            audio_path: Đường dẫn file audio (WAV) hoặc video (MP4)
            model_size: Kích thước model Whisper (base, small, medium)
            source_lang: Ngôn ngữ nguồn ('en', 'zh', 'ja', 'auto')
            progress_callback: Hàm callback(progress_percent)

        Returns:
            Danh sách segments: [{'index', 'start', 'end', 'text'}, ...]
        """
        model = self._load_model(model_size)

        # auto -> None để Whisper tự động phát hiện ngôn ngữ nguồn
        lang = None if source_lang == "auto" else source_lang
        prompt_map = {
            "zh": "以下是中文短剧、漫剧和动画的完整对话与旁白字幕，请完整识别出所有说话内容：",
            "en": "The following is the full transcript of all narration and dialogue in this video:"
        }
        init_prompt = prompt_map.get(source_lang, None)

        try:
            segments_gen, info = model.transcribe(
                audio_path,
                beam_size=10, temperature=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
                best_of=10,
                language=lang,
                initial_prompt=init_prompt,
                condition_on_previous_text=True,
                vad_filter=False,
                no_speech_threshold=None, log_prob_threshold=None, compression_ratio_threshold=None
            )
            segments_list = list(segments_gen)
        except RuntimeError as cuda_err:
            if any(term in str(cuda_err).lower() for term in ["cublas", "cuda", "cudnn"]):
                print(f"⚠️ [Transcriber] Lỗi thư viện CUDA ({cuda_err}). Đang chuyển Whisper sang CPU...")
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
                    beam_size=10, temperature=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
                    best_of=10,
                    language=lang,
                    initial_prompt=init_prompt,
                    condition_on_previous_text=True,
                    vad_filter=False,
                    no_speech_threshold=None, log_prob_threshold=None, compression_ratio_threshold=None
                )
                segments_list = list(segments_gen)
            else:
                raise cuda_err

        # Chuyển đổi sang format chuẩn của app
        result = []
        for seg in segments_list:
            text = seg.text.strip()
            if not text:
                continue

            # Tự động cắt tách các câu ghép và đoạn dài Tiếng Trung theo dấu câu (: , . ! ? 、 ; ...)
            delims = r'([：:，。！？、；;])'
            has_delim = any(p in text for p in ["：", ":", "，", "。", "！", "？", "、", "；", ";"])
            if has_delim:
                parts = [p.strip() for p in re.split(delims, text) if p.strip()]
                raw_clauses = []
                for p in parts:
                    if p in '：:，。！？、；;' and raw_clauses:
                        raw_clauses[-1] += p
                    else:
                        raw_clauses.append(p)
                
                total_len = sum(len(c) for c in raw_clauses)
                if total_len > 0 and len(raw_clauses) > 1:
                    c_start = seg.start
                    dur_total = seg.end - seg.start
                    for c_txt in raw_clauses:
                        c_dur = (len(c_txt) / total_len) * dur_total
                        c_end = c_start + c_dur
                        clean_c = c_txt.strip('：:，。！？、；; ')
                        if clean_c:
                            result.append({
                                'index': len(result) + 1,
                                'start': round(c_start, 3),
                                'end': round(c_end, 3),
                                'text': clean_c
                            })
                        c_start = c_end
                    continue

            result.append({
                'index': len(result) + 1,
                'start': round(seg.start, 3),
                'end': round(seg.end, 3),
                'text': text
            })

        # Chia nhỏ các segment quá dài (> 5 giây hoặc > 80 ký tự)
        max_dur_result = []
        for seg in result:
            dur = seg['end'] - seg['start']
            text = seg['text']
            if (dur > 5.0 or len(text) > 80) and not any(p in text for p in ["，", "。"]):
                words = text.split()
                if len(words) > 8:
                    chunk_size = 7
                    chunks = [' '.join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
                    chunk_dur = dur / len(chunks)
                    curr_t = seg['start']
                    for chunk_txt in chunks:
                        max_dur_result.append({
                            'index': len(max_dur_result) + 1,
                            'start': round(curr_t, 3),
                            'end': round(curr_t + chunk_dur, 3),
                            'text': chunk_txt
                        })
                        curr_t += chunk_dur
                else:
                    max_dur_result.append(seg)
            else:
                max_dur_result.append(seg)
        result = max_dur_result

        print(f"[Transcriber] Bóc tách và chia được {len(result)} khối phụ đề độc lập.")

        # PASS 1.1: Nếu nhận diện 0 câu thoại, tự động fallback sang Tiếng Trung ('zh') để quét lại
        if not result and source_lang != "zh":
            print("⚠️ [Transcriber] Không tìm thấy thoại với ngôn ngữ chọn. Tự động fallback sang Tiếng Trung ('zh')...")
            try:
                sub_gen, _ = model.transcribe(
                    audio_path,
                    beam_size=10, temperature=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
                    best_of=10,
                    language="zh",
                    initial_prompt="以下是中文短剧、漫剧和动画的完整对话与旁白字幕，请完整识别出所有说话内容：",
                    condition_on_previous_text=True,
                    vad_filter=False,
                    no_speech_threshold=None, log_prob_threshold=None, compression_ratio_threshold=None
                )
                for s in sub_gen:
                    t_txt = s.text.strip()
                    if t_txt and len(t_txt) > 1:
                        result.append({
                            'index': len(result) + 1,
                            'start': round(s.start, 3),
                            'end': round(s.end, 3),
                            'text': t_txt
                        })
            except Exception as fe:
                print(f"⚠️ [Transcriber Fallback Error]: {fe}")

        # PASS 2: Tự động quét vét 100% các khoảng trống thoại >= 2.0s bị bỏ lọt
        gap_recovered = []
        for i in range(len(result) - 1):
            curr_s = result[i]
            next_s = result[i + 1]
            gap_dur = next_s['start'] - curr_s['end']
            if gap_dur >= 2.0:
                s_t = curr_s['end']
                e_t = next_s['start']
                try:
                    sub_segs, _ = model.transcribe(
                        audio_path,
                        language=lang or "zh",
                        beam_size=10, temperature=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
                        best_of=10,
                        initial_prompt="以下是未识别的完整中文对话与旁白字幕：",
                        clip_timestamps=[s_t, e_t],
                        vad_filter=False,
                        no_speech_threshold=None,
                        log_prob_threshold=None,
                        compression_ratio_threshold=None
                    )
                    for s in sub_segs:
                        txt_clean = s.text.strip()
                        if txt_clean and len(txt_clean) > 1 and "请完整识别" not in txt_clean:
                            gap_recovered.append({
                                'start': round(s.start, 3),
                                'end': round(s.end, 3),
                                'text': txt_clean
                            })
                except Exception:
                    pass
        if gap_recovered:
            print(f"[Transcriber 2nd Pass] Đã quét vét và khôi phục thành công {len(gap_recovered)} câu thoại bị lọt trong các khoảng trống!")
            result.extend(gap_recovered)
            result.sort(key=lambda x: x['start'])

        # Xác định chuẩn xác đường dẫn file video MP4 để chụp khung hình OCR
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

        # PASS 3.1: Nếu audio không nhận diện được (result rỗng hoặc chỉ có 1 đoạn), tự động chạy Full Video OCR
        if _ocr_engine and os.path.exists(v_path) and len(result) <= 1:
            print("⚠️ [Transcriber] Whisper không phát hiện âm thanh thoại. Đang tự động quét Full Video OCR toàn bộ khung hình video...")
            try:
                cmd_dur = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{v_path}"'
                res_dur = subprocess.run(cmd_dur, shell=True, capture_output=True, text=True)
                v_dur = float(res_dur.stdout.strip()) if res_dur.stdout.strip() else 0
            except Exception:
                v_dur = 0

            if v_dur > 0:
                ocr_full = []
                sample_t = 1.0
                frame_idx = 0
                while sample_t < v_dur:
                    tmp_img = os.path.join(os.path.dirname(v_path), f"ocr_full_{frame_idx}.jpg")
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

                if ocr_full:
                    print(f"[Transcriber Full OCR] Đã quét toàn bộ video và bóc tách thành công {len(ocr_full)} khối phụ đề từ màn hình!")
                    result.extend(ocr_full)
                    result.sort(key=lambda x: x['start'])

        # PASS 3: Video OCR Hardcoded Subtitle Recovery cho các khoảng hổng >= 0.8s
        if _ocr_engine and os.path.exists(v_path):
            ocr_recovered = []
            for i in range(len(result) - 1):
                curr_s = result[i]
                next_s = result[i + 1]
                gap_dur = next_s['start'] - curr_s['end']
                if gap_dur >= 0.8:
                    s_t = curr_s['end']
                    e_t = next_s['start']
                    sample_ts = s_t + 0.5
                    while sample_ts < e_t:
                        sample_t = round(sample_ts, 2)
                        tmp_img = os.path.join(os.path.dirname(v_path), f"ocr_gap_{i}_{int(sample_t*10)}.jpg")
                        cmd = f'ffmpeg -y -ss {sample_t} -i "{v_path}" -vframes 1 "{tmp_img}"'
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
                                                    'start': round(sample_t - 0.2, 3),
                                                    'end': round(min(e_t - 0.05, sample_t + 2.0), 3),
                                                    'text': txt
                                                })
                            except Exception:
                                pass
                            try:
                                os.remove(tmp_img)
                            except Exception:
                                pass
                        sample_ts += 1.0

            if ocr_recovered:
                print(f"[Transcriber OCR Pass] Đã đọc chữ từ khung hình và khôi phục thành công {len(ocr_recovered)} vế thoại Tiếng Trung bị lọt!")
                result.extend(ocr_recovered)
                result.sort(key=lambda x: x['start'])

        # Cập nhật lại số thứ tự index
        for idx, seg in enumerate(result, 1):
            seg['index'] = idx

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
        Tạo file phụ đề SRT chuẩn xác thời gian thực tế, không kéo lê bừa bãi.
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            for i, seg in enumerate(segments, 1):
                start_t = seg['start']
                end_t = seg['end']
                text_val = str(seg['text']).replace('\r\n', '\n').strip()
                safe_text = '\n'.join([line.strip() for line in text_val.split('\n') if line.strip()])

                dur = end_t - start_t
                if dur > 4.0:
                    end_t = round(start_t + max(2.0, min(3.5, len(safe_text) * 0.08)), 3)

                start_ts = Transcriber.format_timestamp(start_t)
                end_ts = Transcriber.format_timestamp(end_t)
                f.write(f"{i}\n")
                f.write(f"{start_ts} --> {end_ts}\n")
                f.write(f"{safe_text}\n\n")

        print(f"[Transcriber] Đã tạo file SRT: {output_path}")
        return output_path

    @staticmethod
    def parse_time(time_str: str) -> float:
        """Chuyển đổi định dạng SRT timestamp sang giây (float)."""
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
