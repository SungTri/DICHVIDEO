"""
Service dịch thuật EN → VI sử dụng LLM API.
"""
import json
import urllib.request
import urllib.error


class Translator:
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

    BATCH_SIZE = 20  # Số đoạn tối đa gửi trong 1 lần gọi API

    # Mapping tên ngôn ngữ đầy đủ cho prompt
    _LANG_NAMES = {
        "en": "English", "zh": "Chinese", "ja": "Japanese", "ko": "Korean",
        "fr": "French", "de": "German", "es": "Spanish", "ru": "Russian",
        "pt": "Portuguese", "it": "Italian", "th": "Thai", "ar": "Arabic",
    }

    def _build_prompt(self, input_data, json_module, from_lang="en", context_prompt=None):
        """Tạo prompt dịch thuật chung cho mọi API, tự động nhận dạng ngôn ngữ nguồn."""
        lang_name = self._LANG_NAMES.get(from_lang, from_lang.upper())
        
        context_str = ""
        if context_prompt and isinstance(context_prompt, str) and context_prompt.strip():
            context_str = f"\n5. NGỮ CẢNH BỔ SUNG TỪ NGƯỜI DÙNG: {context_prompt.strip()}\n"
            
        return f"""You are a professional video translator and editor.
Your task is to translate the following {lang_name} subtitle segments into natural, fluent Vietnamese.

CRITICAL REQUIREMENTS:
1. Translating for video presentations or advertisements, so keep the tone engaging, professional, and natural.
2. Follow standard Vietnamese grammar and sentence flow (do not translate word-for-word, reorganize sentences if necessary).
3. Automatically correct any obvious speech-to-text transcription errors in the input based on the general context.
4. Do not drop or add segment lines. The output MUST contain the exact same list of indexes.
5. Translate EVERYTHING into Vietnamese. Do NOT leave any original {lang_name} characters or words untranslated in the output (except globally recognized English brand names). The final text MUST be 100% Vietnamese.{context_str}

Input subtitle JSON:
{json_module.dumps(input_data, ensure_ascii=False, indent=2)}

You MUST output ONLY a valid JSON array of objects, containing two keys: 'index' (int) and 'text' (string, the translated Vietnamese text). Do not wrap the JSON in code blocks (such as ```json) or add any extra text or conversational filler."""

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
            item["index"]: item["text"]
            for item in translated_list
            if isinstance(item, dict) and "index" in item and "text" in item
        }

    def _call_gemini(self, input_data, json_module, urllib_request, GEMINI_API_KEY, from_lang="en", context_prompt=None):
        """Gọi Gemini API cho một batch nhỏ."""
        prompt = self._build_prompt(input_data, json_module, from_lang, context_prompt)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
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
            api_providers.append(("Gemini", lambda batch, fl=from_lang, ctx=context_prompt: self._call_gemini(batch, json, urllib.request, GEMINI_API_KEY, fl, ctx)))
        if GITHUB_TOKEN and from_lang != "vi":
            api_providers.append(("GitHub GPT-4o-mini", lambda batch, fl=from_lang, ctx=context_prompt: self._call_github(batch, json, urllib.request, GITHUB_TOKEN, fl, ctx)))
        if SAMBANOVA_API_KEY and from_lang != "vi":
            api_providers.append(("SambaNova Llama 3.1", lambda batch, fl=from_lang, ctx=context_prompt: self._call_sambanova(batch, json, urllib.request, SAMBANOVA_API_KEY, fl, ctx)))
        if GROQ_API_KEY and from_lang != "vi":
            api_providers.append(("Groq Llama 3.3", lambda batch, fl=from_lang, ctx=context_prompt: self._call_groq(batch, json, urllib.request, GROQ_API_KEY, fl, ctx)))

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
                        
                        time.sleep(3)  # Nghỉ 3 giây cơ bản để tránh Rate Limit
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
                                print(f"  ⚠️ Batch {batch_idx + 1}/{len(remaining_batches)} thất bại ({api_name}) sau {max_retries} lần thử lại.")
                                break
                        else:
                            print(f"  ⚠️ Batch {batch_idx + 1}/{len(remaining_batches)} thất bại ({api_name}): {str(e)}")
                            break
                            
                if not success:
                    api_failed = True
                    break  # Chuyển sang API tiếp theo

            if not api_failed:
                # API này dịch thành công tất cả batch
                print(f"✅ [Translator] Dịch hoàn tất bằng {api_name} ({len(trans_results)}/{total} đoạn).")
                break

        missing_indices = [seg["index"] for seg in segments if seg["index"] not in trans_results]
        if missing_indices:
            print(f"⚠️ [Translator] Còn {len(missing_indices)} đoạn chưa dịch được. Giữ nguyên text gốc.")

        # Lắp ráp kết quả cuối cùng theo đúng thứ tự
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
