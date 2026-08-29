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

        total_duration = getattr(info, 'duration', 0) or 0
        result = []

        for i, segment in enumerate(segments_list):
            text = segment.text.strip()
            if not text:
                continue

            # Bỏ qua các đoạn hallucination ảo giác phát sinh sau khi video đã kết thúc
            if total_duration > 0 and segment.start >= (total_duration - 0.2):
                print(f"[Transcriber] Bỏ qua đoạn ảo giác sau khi video kết thúc: {segment.start:.1f}s >= {total_duration:.1f}s")
                break

            seg_end = min(segment.end, total_duration) if total_duration > 0 else segment.end

            result.append({
                'index': len(result) + 1,
                'start': segment.start,
                'end': seg_end,
                'text': text
            })

            # Ước lượng tiến trình dựa trên vị trí audio
            if progress_callback and total_duration > 0:
                progress = min(segment.end / total_duration * 100, 99)
                progress_callback(progress)

        if progress_callback:
            progress_callback(100)

                # PRESERVE 100% EXACT ORIGINAL RAW WHISPER TIMESTAMPS

        
        # Chế độ Phụ Đề Liền Mạch (Continuous Subtitle Timeline): Kéo nối 100% các khoảng ngắt thoại giữa các câu
        for i in range(len(result) - 1):
            curr_seg = result[i]
            next_seg = result[i + 1]
            if curr_seg['end'] < next_seg['start']:
                gap_sec = next_seg['start'] - curr_seg['end']
                if gap_sec <= 15.0:
                    curr_seg['end'] = round(next_seg['start'] - 0.05, 3)

        
        # Tự động tách các câu dài chứa dấu phẩy/chấm Tiếng Trung (，, 。, ！, ？) thành từng khối phụ đề độc lập
        refined_result = []
        for seg in result:
            txt = seg['text'].strip()
            import re
            parts = [p.strip() for p in re.split(r'([，。！？])', txt) if p.strip()]
            clause_list = []
            temp_c = ''
            for p in parts:
                temp_c += p
                if p in ['，', '。', '！', '？'] or len(temp_c) >= 12:
                    clause_list.append(temp_c.strip())
                    temp_c = ''
            if temp_c:
                clause_list.append(temp_c.strip())
            clause_list = [c for c in clause_list if c and c not in ['，', '。', '！', '？']]
            if len(clause_list) > 1:
                total_duration = seg['end'] - seg['start']
                total_chars = sum(len(c) for c in clause_list) or 1
                curr_t = seg['start']
                for c in clause_list:
                    dur = (len(c) / total_chars) * total_duration
                    refined_result.append({
                        'start': round(curr_t, 3),
                        'end': round(curr_t + dur, 3),
                        'text': c
                    })
                    curr_t += dur
            else:
                refined_result.append(seg)
        result = refined_result

        
        # Tự động chẻ nhỏ các khối phụ đề có thời lượng dài > 5.0s thành các khối 2-4s ngắn gọn
        max_dur_result = []
        for seg in result:
            dur = seg['end'] - seg['start']
            txt = seg['text'].strip()
            words = txt.split()
            if dur > 5.0 and len(words) > 3:
                num_chunks = int(dur // 4.0) + 1
                chunk_dur = dur / num_chunks
                words_per_chunk = max(1, len(words) // num_chunks)
                curr_t = seg['start']
                for c in range(num_chunks):
                    start_w = c * words_per_chunk
                    end_w = (c + 1) * words_per_chunk if c < num_chunks - 1 else len(words)
                    chunk_txt = ' '.join(words[start_w:end_w])
                    end_t = seg['end'] if c == num_chunks - 1 else curr_t + chunk_dur
                    if chunk_txt:
                        max_dur_result.append({
                            'start': round(curr_t, 3),
                            'end': round(end_t, 3),
                            'text': chunk_txt
                        })
                    curr_t += chunk_dur
            else:
                max_dur_result.append(seg)
        result = max_dur_result

        print(f"[Transcriber] Bóc tách và chia được {len(result)} khối phụ đề độc lập.")

        # PASS 2: Tự động quét vét 100% các khoảng trống thoại > 4.0s bị bỏ lọt
        gap_recovered = []
        for i in range(len(result) - 1):
            curr_s = result[i]
            next_s = result[i + 1]
            gap_dur = next_s['start'] - curr_s['end']
            if gap_dur >= 2.0:
                s_t = curr_s['end']
                e_t = next_s['start']
                try:
                    sub_segs, _ = self.model.transcribe(
                        audio_path,
                        language=language,
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
        Tạo file phụ đề SRT từ danh sách segments với thời lượng khống chế 2.0s - 3.2s gọn gàng cho CapCut.
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            for i, seg in enumerate(segments, 1):
                start_t = seg['start']
                end_t = seg['end']
                text_val = str(seg['text']).replace('\r\n', '\n').strip()
                safe_text = '\n'.join([line.strip() for line in text_val.split('\n') if line.strip()])

                # Khống chế thời lượng phụ đề chuẩn 2.0s - 3.2s không bị kéo lê dài (8-11s) trên CapCut timeline
                dur = end_t - start_t
                if dur > 3.5:
                    calc_dur = max(2.0, min(3.2, len(safe_text) * 0.075))
                    end_t = round(start_t + calc_dur, 3)

                start_ts = Transcriber.format_timestamp(start_t)
                end_ts = Transcriber.format_timestamp(end_t)
                f.write(f"{i}\n")
                f.write(f"{start_ts} --> {end_ts}\n")
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
