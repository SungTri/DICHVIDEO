"""
Service dịch thuật EN → VI sử dụng LLM API.
"""
import json
import urllib.request
import urllib.error


class Translator:
    @staticmethod
    def contains_chinese(text: str) -> bool:
        import re
        return bool(re.search(r"[一-鿿]", str(text)))

    """Dịch văn bản từ ngôn ngữ nguồn bất kỳ sang tiếng Việt."""

    def __init__(self):
        self._initialized_langs = set()

    def initialize(self, from_lang: str) -> bool:
        """
        Khởi tạo ngôn ngữ (đã vô hiệu hóa Argos).
        """
        self._initialized_langs.add(from_lang.lower())
        return True

    def translate_text(self, text: str, from_lang: str = "en") -> str:
        """
        Dịch offline. Đã vô hiệu hóa, chỉ trả về text gốc.
        """
        return text

    # ==================== BATCH CHUNKING HELPERS ====================

    BATCH_SIZE = 45  # Số đoạn tối đa gửi trong 1 lần gọi API

    # Mapping tên ngôn ngữ đầy đủ cho prompt
    _LANG_NAMES = {
        "en": "English", "zh": "Chinese", "ja": "Japanese", "ko": "Korean",
        "fr": "French", "de": "German", "es": "Spanish", "ru": "Russian",
        "pt": "Portuguese", "it": "Italian", "th": "Thai", "ar": "Arabic",
    }

    def _build_prompt(self, input_data, json_module, from_lang="en", context_prompt=None):
        """Tạo prompt dịch thuật chuyên nghiệp chuẩn lồng tiếng khớp thời lượng, dịch thoát nghĩa tự nhiên theo ngữ cảnh hành động."""
        lang_name = self._LANG_NAMES.get(from_lang, from_lang.upper())
        
        context_str = ""
        if context_prompt and isinstance(context_prompt, str) and context_prompt.strip():
            context_str = f"\n- NGỮ CẢNH BỔ SUNG TỪ NGƯỜI DÙNG: {context_prompt.strip()}\n"

        # Định dạng danh sách đầu vào có kèm mốc thời lượng và giới hạn số từ lồng tiếng
        formatted_inputs = []
        for s in input_data:
            start_t = s.get('start', 0)
            end_t = s.get('end', 0)
            dur = max(0.5, round(end_t - start_t, 2)) if end_t > start_t else 2.0
            # Tốc độ đọc tự nhiên tiếng Việt ~ 3.5 từ/giây
            max_words = max(3, int(dur * 3.5))
            formatted_inputs.append({
                "index": s['index'],
                "source_text": s.get('text', ''),
                "time_limit_sec": dur,
                "max_vietnamese_words": max_words
            })
            
        return f"""Bạn là AI chuyên gia biên dịch và lồng tiếng phụ đề video phim ảnh, hoạt hình, đời sống, vlog từ {lang_name} sang Tiếng Việt.

NHIỆM VỤ TỐI THƯỢNG:
Dịch toàn bộ danh sách câu thoại đầu vào sang Tiếng Việt CÔ ĐỌNG, SÚC TÍCH, THOÁT NGHĨA TỰ NHIÊN, VỪA KHÍT THỜI LƯỢNG NÓI VÀ ĐÚNG HÀNH ĐỘNG THỰC TẾ TRONG VIDEO.

CÁC NGUYÊN TẮC BẮT BUỘC KHÔNG ĐƯỢC VI PHẠM:
1. BẢO TOÀN 100% SỐ LƯỢNG ENTRY/INDEX:
   - Số lượng câu đầu ra PHẢI BẰNG CHÍNH XÁC số lượng câu đầu vào (Input count = Output count).
   - Tuyệt đối không được bỏ sót, xóa bỏ, gộp hay chia nhỏ bất kỳ index nào.
   - Các câu ngắn, tiếng cảm thán: "Ừ", "À", "Hả?", "Này!", "Ồ", "Ừm", "..." VẪN PHẢI GIỮ VÀ DỊCH.
2. DỊCH THOÁT NGHĨA THEO HÀNH ĐỘNG THỰC TẾ & TÊN NHÂN VẬT:
   - Tên nhân vật hoạt hình: 'Doro' (bé Doro), STT nghe nhầm thành '剁肉' / '小剁肉' ➔ Bắt buộc dịch là 'Doro' hoặc 'bé Doro'.
   - Cụm từ thành ngữ / khẩu ngữ '安家' (An gia):
     * Khi video nói về xúc đất, chậu cây, trồng hoa/cây cảnh ➔ '安家' mang nghĩa ẩn dụ trồng vào chậu mới. BẮT BUỘC DỊCH THOÁT NGHĨA LÀ 'sang chậu', 'trồng chậu mới', 'trồng cây' (Tuyệt đối KHÔNG dịch thô cứng/máy móc từng chữ thành 'làm nhà', 'xây nhà').
     * Ví dụ: "今天我们一起给小剁肉安家吧" ➔ "Hôm nay cùng sang chậu cho bé Doro nhé" (hoặc "Hôm nay cùng trồng chậu mới cho bé Doro nhé").
   - Các từ đồng âm:
     * '躲雨' (trú mưa/trốn mưa) ➔ STT nghe nhầm thành '夺鱼' (bắt cá).
     * '猫咪' / '小猫' (mèo) ➔ STT nghe nhầm thành '毛衣' (áo len).
   - AI PHẢI PHÂN TÍCH TOÀN BỘ MẠCH CÂU CHUYỆN LIÊN KẾT GIỮA CÁC CÂU để dịch tự nhiên, mượt mà và chuẩn ngữ cảnh nhất.
3. NGUYÊN TẮC CÔ ĐỌNG VỪA KHÍT THỜI GIAN LỒNG TIẾNG (DUBBING PACING):
   - Bản dịch tiếng Việt BẮT BUỘC PHẢI NGẮN GỌN, SÚC TÍCH, DỄ ĐỌC NHANH, KHÔNG VƯỢT QUÁ số từ 'max_vietnamese_words'.
   - Tuyệt đối KHÔNG dịch rườm rà, dài dòng, thêm thắt từ ngữ thừa thãi.
4. VĂN PHONG TỰ NHIÊN, CHUẨN ĐIỆN ẢNH:
   - Dịch mượt mà, xưng hô phù hợp ngữ cảnh, sửa lỗi chính tả phát âm STT.
5. MỖI BẢN DỊCH LÀ 1 DÒNG DUY NHẤT:
   - Không chèn ký tự xuống dòng (\n) trong trường text.
6. DỊCH SẠCH 100% SANG TIẾNG VIỆT:
   - Tuyệt đối không để sót chữ {lang_name} gốc trong bản dịch.{context_str}

Danh sách phụ đề đầu vào:
{json_module.dumps(formatted_inputs, ensure_ascii=False, indent=2)}

BẮT BUỘC TRẢ VỀ: Chỉ trả về duy nhất 1 JSON Array hợp lệ gồm các object có đúng 2 key: "index" (int) và "text" (string, bản dịch tiếng Việt súc tích ngắn gọn). Tuyệt đối không thêm lời giải thích hay bọc mã."""

    def _parse_api_response(self, raw_text, json_module):
        """Phân tích JSON trả về từ API, hỗ trợ cả dạng array và object."""
        # Làm sạch markdown block markers
        if raw_text.startswith("```"):
            lines = raw_text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].strip() == "```":
                lines = lines[:-1]
            raw_text = "\n".join(lines).strip()

        translated_list = json_module.loads(raw_text)

        # Nếu API trả về Object thay vì Array, bóc tách mảng bên trong
        if isinstance(translated_list, dict):
            for val in translated_list.values():
                if isinstance(val, list):
                    translated_list = val
                    break

        return {
            int(item["index"]): str(item["text"]).strip()
            for item in translated_list
            if isinstance(item, dict) and "index" in item and "text" in item
        }

    def _call_gemini(self, input_data, json_module, urllib_request, GEMINI_API_KEY, from_lang="en", context_prompt=None, model_name="gemini-flash-lite-latest"):
        """Gọi Gemini API cho một batch nhỏ."""
        prompt = self._build_prompt(input_data, json_module, from_lang, context_prompt)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        req_payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json"}
        }
        req = urllib_request.Request(
            url,
            data=json_module.dumps(req_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib_request.urlopen(req, timeout=90) as response:
            res_body = json_module.loads(response.read().decode("utf-8"))
        raw_text = res_body["candidates"][0]["content"]["parts"][0]["text"].strip()
        return self._parse_api_response(raw_text, json_module)

    def _call_github(self, input_data, json_module, urllib_request, GITHUB_TOKEN, from_lang="en", context_prompt=None):
        """Gọi GitHub Models API (GPT-4o-mini) cho một batch nhỏ."""
        prompt = self._build_prompt(input_data, json_module, from_lang, context_prompt)
        url = "https://models.inference.ai.azure.com/chat/completions"
        req_payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
            "temperature": 0.2
        }
        req = urllib_request.Request(
            url,
            data=json_module.dumps(req_payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {GITHUB_TOKEN}"
            },
            method="POST"
        )
        with urllib_request.urlopen(req, timeout=90) as response:
            res_body = json_module.loads(response.read().decode("utf-8"))
        raw_text = res_body["choices"][0]["message"]["content"].strip()
        return self._parse_api_response(raw_text, json_module)

    def _call_sambanova(self, input_data, json_module, urllib_request, SAMBANOVA_API_KEY, from_lang="en", context_prompt=None):
        """Gọi SambaNova API (Llama 3.3 70B) cho một batch nhỏ."""
        prompt = self._build_prompt(input_data, json_module, from_lang, context_prompt)
        url = "https://api.sambanova.ai/v1/chat/completions"
        req_payload = {
            "model": "Meta-Llama-3.3-70B-Instruct",
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
            "temperature": 0.2
        }
        req = urllib_request.Request(
            url,
            data=json_module.dumps(req_payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {SAMBANOVA_API_KEY}"
            },
            method="POST"
        )
        with urllib_request.urlopen(req, timeout=90) as response:
            res_body = json_module.loads(response.read().decode("utf-8"))
        raw_text = res_body["choices"][0]["message"]["content"].strip()
        return self._parse_api_response(raw_text, json_module)

    def _call_groq(self, input_data, json_module, urllib_request, GROQ_API_KEY, from_lang="en", context_prompt=None):
        """Gọi Groq API (Llama 3.3 70B) cho một batch nhỏ."""
        prompt = self._build_prompt(input_data, json_module, from_lang, context_prompt)
        url = "https://api.groq.com/openai/v1/chat/completions"
        req_payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
            "temperature": 0.2
        }
        req = urllib_request.Request(
            url,
            data=json_module.dumps(req_payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {GROQ_API_KEY}"
            },
            method="POST"
        )
        with urllib_request.urlopen(req, timeout=90) as response:
            res_body = json_module.loads(response.read().decode("utf-8"))
        raw_text = res_body["choices"][0]["message"]["content"].strip()
        return self._parse_api_response(raw_text, json_module)

    # ==================== MAIN TRANSLATE METHOD ====================

    def translate_segments(self, segments: list, from_lang: str = "en", progress_callback=None, context_prompt: str | None = None) -> list:
        """
        Dịch tất cả các segments phụ đề sử dụng LLM API.
        """
        from_lang = from_lang.lower()

        import json
        import urllib.request
        import urllib.error
        from config import GEMINI_API_KEY, GROQ_API_KEY, GITHUB_TOKEN, SAMBANOVA_API_KEY

        total = len(segments)
        if total == 0:
            return []

        # Xây dựng danh sách các API khả dụng theo thứ tự ưu tiên
        api_providers = []
        
        if GEMINI_API_KEY and from_lang != "vi":
            g_keys = [k.strip() for k in GEMINI_API_KEY.split(",") if k.strip()]
            g_models = ["gemini-flash-lite-latest", "gemini-1.5-flash-latest", "gemini-flash-lite-latest"]
            for m_name in g_models:
                for idx, key in enumerate(g_keys):
                    p_name = f"Gemini {m_name} (Key {idx+1})" if len(g_keys) > 1 else f"Gemini {m_name}"
                    api_providers.append((
                        p_name,
                        lambda batch, fl=from_lang, ctx=context_prompt, k=key, m=m_name: self._call_gemini(batch, json, urllib.request, k, fl, ctx, m)
                    ))

        def add_providers(key_str, name, call_func):
            if not key_str or from_lang == "vi": return
            keys = [k.strip() for k in key_str.split(",") if k.strip()]
            for idx, key in enumerate(keys):
                provider_name = f"{name} (Key {idx+1})" if len(keys) > 1 else name
                api_providers.append((provider_name, lambda batch, fl=from_lang, ctx=context_prompt, k=key: call_func(batch, json, urllib.request, k, fl, ctx)))

        add_providers(GITHUB_TOKEN, "GitHub GPT-4o-mini", self._call_github)
        add_providers(SAMBANOVA_API_KEY, "SambaNova Llama 3.1", self._call_sambanova)
        add_providers(GROQ_API_KEY, "Groq Llama 3.3", self._call_groq)

        # Chia segments thành các batch nhỏ
        batches = []
        for i in range(0, total, self.BATCH_SIZE):
            batches.append(segments[i:i + self.BATCH_SIZE])
            
        total_batches = len(batches)
        print(f"📦 [Translator] Chia {total} đoạn thành {total_batches} batch (mỗi batch ~{self.BATCH_SIZE} đoạn).")

        # Dict lưu kết quả dịch theo index
        trans_results = {}
        completed_batches = 0

        # Thử dịch qua từng API provider
        for api_name, api_call in api_providers:
            # Lọc ra các batch chưa dịch xong hoàn toàn
            remaining_batches = []
            for batch in batches:
                has_untranslated = any(seg["index"] not in trans_results for seg in batch)
                if has_untranslated:
                    remaining_batches.append(batch)

            if not remaining_batches:
                break  # Tất cả đã dịch xong

            print(f"✨ [Translator] Đang dịch {len(remaining_batches)} batch bằng {api_name}...")
            api_failed = False

            for batch_idx, batch in enumerate(remaining_batches):
                # Chỉ gửi những đoạn chưa có kết quả
                untranslated = [seg for seg in batch if seg["index"] not in trans_results]
                if not untranslated:
                    continue

                input_data = [{"index": seg["index"], "text": seg["text"]} for seg in untranslated]

                import time
                max_retries = 3
                retry_count = 0
                success = False

                while retry_count <= max_retries:
                    try:
                        batch_result = api_call(input_data)
                        trans_results.update(batch_result)
                        completed_batches += 1
                        print(f"  ✅ Batch {batch_idx + 1}/{len(remaining_batches)} ({len(batch_result)} đoạn) — {api_name}")

                        if progress_callback:
                            progress_callback(len(trans_results) / total * 90)  # Giữ 10% cho assembly
                        
                        time.sleep(0.5)  # Nghỉ 3 giây cơ bản để tránh Rate Limit
                        success = True
                        break

                    except Exception as e:
                        error_msg = str(e).lower()
                        if "429" in error_msg or "too many requests" in error_msg or "rate limit" in error_msg:
                            retry_count += 1
                            if retry_count <= max_retries:
                                sleep_time = 15 * retry_count  # Chờ 15s, 30s, 45s
                                print(f"  ⏳ Kẹt Rate Limit ({api_name}), chờ {sleep_time}s rồi thử lại lần {retry_count}/{max_retries}...")
                                time.sleep(sleep_time)
                            else:
                                print(f"  ⚠️ Batch {batch_idx + 1}/{len(remaining_batches)} thất bại ({api_name}) sau {max_retries} lần thử lại do kẹt Rate Limit.")
                                api_failed = True # Key đã hết Quota hoặc bị chặn, chuyển sang API khác
                                break
                        else:
                            retry_count += 1
                            if retry_count <= max_retries:
                                print(f"  ⚠️ Lỗi ({api_name}): {str(e)}. Thử lại lần {retry_count}/{max_retries}...")
                                time.sleep(0.5)
                            else:
                                print(f"  ❌ Batch {batch_idx + 1}/{len(remaining_batches)} thất bại ({api_name}): {str(e)} sau {max_retries} lần thử lại.")
                                if "401" in error_msg or "403" in error_msg or "unauthorized" in error_msg or "forbidden" in error_msg:
                                    api_failed = True # Key chết hoặc hết Quota, bỏ qua API này
                                break
                            
                if api_failed:
                    break  # Key lỗi, chuyển sang API tiếp theo
                # Nếu chỉ là lỗi 1 batch, vòng lặp for batch_idx sẽ tiếp tục chạy batch tiếp theo

            if not api_failed:
                # API này dịch thành công tất cả batch
                print(f"✅ [Translator] Dịch hoàn tất bằng {api_name} ({len(trans_results)}/{total} đoạn).")
                break

        missing_segs = [seg for seg in segments if seg["index"] not in trans_results or self.contains_chinese(trans_results.get(seg["index"], ""))]
        if missing_segs:
            print(f"🧹 [Translator] Phát hiện {len(missing_segs)} đoạn chưa có bản dịch. Bắt đầu Vòng Quét Vét AI 100%...")
            for i in range(0, len(missing_segs), 15):
                sub_batch = missing_segs[i:i + 15]
                input_data = [{"index": seg["index"], "text": seg["text"]} for seg in sub_batch]
                for k_idx, k_val in enumerate(g_keys):
                    try:
                        sweep_res = self._call_gemini(input_data, json, urllib.request, k_val, from_lang, context_prompt, "gemini-flash-lite-latest")
                        if sweep_res:
                            trans_results.update(sweep_res)
                            print(f"  ✅ Quét vét xong {len(sweep_res)} đoạn bằng Key {k_idx + 1}")
                            break
                    except Exception:
                        continue

        # Lắp ráp kết quả cuối cùng theo đúng thứ tự
        zh_map = {"嗯": "Ừm", "啊": "À", "哦": "Ồ", "呃": "Hả", "呀": "Nè", "哈": "Ha", "哇": "Oa", "唉": "Haizz", "喂": "Alo", "好的": "Được rồi"}
        for seg in segments:
            idx = seg["index"]
            curr_text = trans_results.get(idx, "").strip()
            if not curr_text or self.contains_chinese(curr_text):
                orig = seg.get("text", "").strip()
                if orig in zh_map:
                    trans_results[idx] = zh_map[orig]

        translated_segments = []
        for seg in segments:
            translated_text = trans_results.get(seg["index"], seg["text"])
            translated_segments.append({
                'index': seg['index'],
                'start': seg['start'],
                'end': seg['end'],
                'original_text': seg['text'],
                'text': translated_text
            })

        if progress_callback:
            progress_callback(100)

        print(f"🎉 [Translator] Hoàn tất dịch {len(translated_segments)} đoạn sang tiếng Việt!")
        return translated_segments
