"""
Service tổng hợp giọng nói (Text-to-Speech) sử dụng Edge TTS.
Miễn phí, chất lượng cao, hỗ trợ tiếng Việt.
Sử dụng FFmpeg trực tiếp cho xử lý audio (không dùng pydub).
"""
import os
import subprocess
import json
import asyncio
import hashlib
import edge_tts
from config import DEFAULT_VOICE, FFMPEG_PATH, FFPROBE_PATH, ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ADAM, ELEVENLABS_VOICE_BELLA


class TTSService:
    """Tổng hợp giọng nói và tạo audio lồng tiếng."""

    def __init__(self):
        pass

    async def generate_speech(self, text: str, output_path: str,
                               voice: str | None = None) -> str:
        """
        Tạo file audio từ văn bản (Đã bổ sung cơ chế Retry và Fallback Voice khi gặp lỗi server-side của Edge TTS).
        
        Args:
            text: Văn bản cần đọc
            output_path: Đường dẫn file audio đầu ra
            voice: Giọng đọc (mặc định: vi-VN-HoaiMyNeural)
            
        Returns:
            Đường dẫn file audio
        """
        voice = voice or DEFAULT_VOICE
        
        # Hỗ trợ giọng đọc ElevenLabs cao cấp
        if voice.startswith("eleven_"):
            if not ELEVENLABS_API_KEY:
                raise Exception("Không tìm thấy ELEVENLABS_API_KEY trong file config.py. Vui lòng thêm key vào config.py để sử dụng giọng này!")
            
            # Map sang ElevenLabs Voice ID
            voice_mapping = {
                "eleven_antonio": "ErXwobaYiN019PkySvjV",
                "eleven_rachel": "21m00Tcm4TlvDq8ikWAM",
                "eleven_giongbe": "xXcABhgPXUrNiSHUbNjE"
            }
            voice_id = voice_mapping.get(voice, "ErXwobaYiN019PkySvjV")
            
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            headers = {
                "xi-api-key": ELEVENLABS_API_KEY,
                "Content-Type": "application/json"
            }
            payload = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }
            
            import httpx
            try:
                with httpx.Client() as client:
                    response = client.post(url, json=payload, headers=headers, timeout=60.0)
                    if response.status_code != 200:
                        raise Exception(f"Lỗi ElevenLabs API ({response.status_code}): {response.text}")
                    with open(output_path, "wb") as f:
                        f.write(response.content)
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    return output_path
            except Exception as e:
                print(f"[TTS] Lỗi ElevenLabs: {e}. Tự động fallback về giọng Edge TTS...")
                # Fallback: Nam cho antonio, Nữ cho rachel
                voice = "vi-VN-NamMinhNeural" if "antonio" in voice else "vi-VN-HoaiMyNeural"

        max_retries = 3
        
        # Thử tải bằng giọng đọc chính được chọn
        for attempt in range(max_retries):
            try:
                communicate = edge_tts.Communicate(text, voice)
                await communicate.save(output_path)
                
                # Xác thực file tạo ra thành công và có dữ liệu
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    return output_path
            except Exception as e:
                print(f"[TTS] Lỗi tạo speech ở lần thử {attempt + 1}/{max_retries} với giọng {voice} cho text '{text[:20]}...': {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1.0 * (attempt + 1))  # Exponential backoff
        
        # Nếu bị lỗi sau max_retries, tự động chuyển sang giọng đọc còn lại (Fallback Voice) để cứu cánh
        fallback_voice = "vi-VN-NamMinhNeural" if "HoaiMy" in voice else "vi-VN-HoaiMyNeural"
        print(f"[TTS] [Fallback] Phát hiện lỗi giọng đọc '{voice}'. Tự động đổi sang giọng thay thế '{fallback_voice}' cho đoạn văn: '{text[:30]}...'")
        
        for attempt in range(2):
            try:
                communicate = edge_tts.Communicate(text, fallback_voice)
                await communicate.save(output_path)
                
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    return output_path
            except Exception as e:
                print(f"[TTS] Lỗi tạo speech ở lần thử fallback {attempt + 1}/2 với giọng {fallback_voice}: {e}")
                if attempt < 1:
                    await asyncio.sleep(1.5)
        
        raise Exception(f"Không nhận được audio từ Edge TTS sau tất cả các lần thử với cả giọng đọc chính và giọng fallback.")

    def _get_audio_duration(self, file_path: str) -> float:
        """Lấy thời lượng file audio bằng ffprobe (giây)."""
        cmd = [
            FFPROBE_PATH, '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            file_path
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return float(result.stdout.strip())
        except Exception:
            return 0.0

    def _speed_up_audio(self, input_path: str, output_path: str,
                        speed: float):
        """
        Tăng tốc audio sử dụng FFmpeg atempo filter.
        atempo chỉ hỗ trợ 0.5-2.0, nên chain nhiều filter nếu cần.
        """
        atempo_filters = []
        remaining = speed

        while remaining > 2.0:
            atempo_filters.append("atempo=2.0")
            remaining /= 2.0

        if remaining < 0.5:
            remaining = 0.5

        atempo_filters.append(f"atempo={remaining:.4f}")
        filter_str = ','.join(atempo_filters)

        cmd = [
            FFMPEG_PATH, '-i', input_path,
            '-filter:a', filter_str,
            '-y', '-loglevel', 'error',
            output_path
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            print(f"[TTS] Lỗi tăng tốc audio: {e.stderr.decode()}")

    async def generate_dubbed_audio(self, segments: list, output_dir: str,
                                     total_duration: float,
                                     voice: str | None = None,
                                     voice_speed: float = 1.0,
                                     progress_callback=None) -> str:
        """
        Tạo audio lồng tiếng hoàn chỉnh từ danh sách segments đã dịch (Tối ưu hóa chạy song song).
        """
        os.makedirs(output_dir, exist_ok=True)
        voice = voice or DEFAULT_VOICE

        total = len(segments)
        sem = asyncio.Semaphore(3)  # Giới hạn tối đa 3 request tải giọng đọc cùng lúc để tránh rate limit và lỗi rớt mạng Microsoft
        completed_count = 0

        async def process_segment(i, seg):
            nonlocal completed_count
            text = seg.get('text', '').strip()
            if not text or voice == "none":
                completed_count += 1
                if progress_callback:
                    await progress_callback(completed_count / total * 100)
                return None

            # Sử dụng MD5 hash của (text + voice) làm tên file để làm bộ nhớ đệm (cache)
            text_hash = hashlib.md5(f"{text}_{voice}".encode('utf-8')).hexdigest()
            tts_file = os.path.join(output_dir, f"tts_{text_hash}.mp3")

            try:
                # Kiểm tra cache file gốc
                if not (os.path.exists(tts_file) and os.path.getsize(tts_file) > 0):
                    # Tạo TTS audio với Semaphore giới hạn song song
                    async with sem:
                        await self.generate_speech(text, tts_file, voice)

                # Kiểm tra độ dài bằng ffprobe
                tts_duration = await asyncio.to_thread(self._get_audio_duration, tts_file)
                seg_duration = seg['end'] - seg['start']

                speed_factor = voice_speed
                adjusted_duration = tts_duration / speed_factor
                
                if adjusted_duration > seg_duration > 0.5:
                    additional_speed = adjusted_duration / seg_duration
                    speed_factor = speed_factor * additional_speed
                    speed_factor = min(speed_factor, 2.5)
                    if abs(speed_factor - voice_speed) <= 0.05:
                        speed_factor = voice_speed

                completed_count += 1
                if progress_callback:
                    await progress_callback(completed_count / total * 100)

                return {
                    'file': tts_file,
                    'start': seg['start'],
                    'speed': speed_factor
                }

            except Exception as e:
                print(f"[TTS] Lỗi tạo audio segment {i} (text: '{text[:20]}...'): {e}")
                completed_count += 1
                if progress_callback:
                    await progress_callback(completed_count / total * 100)
                return None

        # Khởi chạy song song tất cả các segments
        tasks = [process_segment(i, seg) for i, seg in enumerate(segments)]
        results = await asyncio.gather(*tasks)

        # Lọc các kết quả hợp lệ (loại bỏ None)
        tts_files = [r for r in results if r is not None]

        if not tts_files:
            # Tạo file im lặng nếu không có TTS nào
            output_path = os.path.join(output_dir, "dubbed_audio.mp3")
            cmd = [
                FFMPEG_PATH, '-f', 'lavfi', '-i',
                f'anullsrc=r=44100:cl=stereo',
                '-t', str(total_duration),
                '-c:a', 'libmp3lame', '-y', '-loglevel', 'error',
                output_path
            ]
            await asyncio.to_thread(subprocess.run, cmd, check=True, capture_output=True)
            return output_path

        # Ghép tất cả segments bằng FFmpeg
        output_path = os.path.join(output_dir, "dubbed_audio.mp3")
        await asyncio.to_thread(self._merge_tts_segments, tts_files, total_duration, output_path)

        print(f"[TTS] Đã tạo audio lồng tiếng hoàn chỉnh: {output_path}")
        return output_path

    def _merge_tts_segments(self, tts_files: list, total_duration: float,
                            output_path: str):
        """
        Ghép các TTS segments vào đúng vị trí timestamp sử dụng FFmpeg.
        Xử lý theo batch nếu quá nhiều segments để tránh command line quá dài.
        """
        BATCH_SIZE = 20  # Xử lý tối đa 20 segments mỗi batch

        if len(tts_files) <= BATCH_SIZE:
            self._merge_batch(tts_files, total_duration, output_path)
        else:
            # Chia thành batches
            batch_outputs = []
            for batch_idx in range(0, len(tts_files), BATCH_SIZE):
                batch = tts_files[batch_idx:batch_idx + BATCH_SIZE]
                batch_output = output_path + f".batch_{batch_idx}.mp3"
                self._merge_batch(batch, total_duration, batch_output)
                batch_outputs.append(batch_output)

            # Merge tất cả batches
            if len(batch_outputs) == 1:
                os.rename(batch_outputs[0], output_path)
            else:
                self._merge_audio_files(batch_outputs, total_duration, output_path)

                # Cleanup batch files
                for f in batch_outputs:
                    if os.path.exists(f):
                        try:
                            os.remove(f)
                        except OSError:
                            pass

    def _merge_batch(self, tts_files: list, total_duration: float,
                     output_path: str):
        """Ghép một batch TTS segments sử dụng FFmpeg adelay + amix."""
        # Input: silent base track + all TTS files
        inputs = [
            '-f', 'lavfi', '-i', f'anullsrc=r=44100:cl=stereo',
            '-t', str(total_duration)
        ]

        filter_parts = []
        mix_labels = ['[0:a]']

        for i, tf in enumerate(tts_files):
            inputs.extend(['-i', tf['file']])
            delay_ms = int(tf['start'] * 1000)
            
            # Tạo bộ lọc atempo nếu tốc độ khác 1.0
            speed = tf.get('speed', 1.0)
            audio_filter = ""
            if abs(speed - 1.0) > 0.01:
                atempo_filters = []
                remaining = speed
                while remaining > 2.0:
                    atempo_filters.append("atempo=2.0")
                    remaining /= 2.0
                while remaining < 0.5:
                    atempo_filters.append("atempo=0.5")
                    remaining /= 0.5
                atempo_filters.append(f"atempo={remaining:.4f}")
                audio_filter = ','.join(atempo_filters) + ","

            # Ép định dạng stereo và tăng âm lượng (volume=2.5) trước khi delay để tránh lỗi mất tiếng do định dạng mono và suy hao của amix
            filter_parts.append(
                f"[{i + 1}:a]{audio_filter}aformat=channel_layouts=stereo,volume=2.5,adelay={delay_ms}|{delay_ms}[s{i}]"
            )
            mix_labels.append(f'[s{i}]')

        n_inputs = len(tts_files) + 1
        filter_complex = '; '.join(filter_parts)
        filter_complex += f"; {''.join(mix_labels)}amix=inputs={n_inputs}:duration=longest:dropout_transition=3,volume={n_inputs}"

        cmd = [FFMPEG_PATH] + inputs + [
            '-filter_complex', filter_complex,
            '-c:a', 'libmp3lame', '-b:a', '192k',
            '-t', str(total_duration),  # Ép kết thúc ở đúng thời lượng video ở đầu ra
            '-y', '-loglevel', 'error',
            output_path
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"[TTS] FFmpeg merge error: {result.stderr[:500]}")
                # Fallback: chỉ dùng segment đầu tiên
                if tts_files:
                    import shutil
                    shutil.copy2(tts_files[0]['file'], output_path)
        except Exception as e:
            print(f"[TTS] Merge exception: {e}")

    def _merge_audio_files(self, audio_files: list, total_duration: float,
                           output_path: str):
        """Merge nhiều audio files sử dụng amix."""
        inputs = []
        labels = []
        for i, f in enumerate(audio_files):
            inputs.extend(['-i', f])
            labels.append(f'[{i}:a]')

        filter_complex = (
            f"{''.join(labels)}amix=inputs={len(audio_files)}"
            f":duration=first:dropout_transition=3,volume={len(audio_files)}"
        )

        cmd = [FFMPEG_PATH] + inputs + [
            '-filter_complex', filter_complex,
            '-c:a', 'libmp3lame', '-b:a', '192k',
            '-t', str(total_duration),
            '-y', '-loglevel', 'error',
            output_path
        ]

        subprocess.run(cmd, capture_output=True, text=True)
