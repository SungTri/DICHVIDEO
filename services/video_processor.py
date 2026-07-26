"""
Service xử lý video sử dụng FFmpeg.
Chèn phụ đề, trộn audio, xuất video hoàn chỉnh.
"""
import os
import sys
import subprocess
import shutil
from config import FFMPEG_PATH, FFPROBE_PATH, ORIGINAL_AUDIO_VOLUME, DUBBED_AUDIO_VOLUME


class VideoProcessor:
    """Xử lý video: chèn sub, trộn audio, xuất video."""
    _cached_encoder = None

    def __init__(self):
        pass

    @staticmethod
    def check_ffmpeg() -> bool:
        """Kiểm tra FFmpeg đã cài đặt chưa."""
        try:
            result = subprocess.run(
                [FFMPEG_PATH, '-version'],
                capture_output=True, text=True
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    @staticmethod
    def get_best_video_encoder() -> str:
        """Kiểm tra và trả về encoder tốt nhất được hỗ trợ (NVENC, QSV hoặc libx264)."""
        if VideoProcessor._cached_encoder is not None:
            return VideoProcessor._cached_encoder

        try:
            result = subprocess.run(
                [FFMPEG_PATH, '-encoders'],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                encoders_text = result.stdout
                if "h264_nvenc" in encoders_text:
                    print("⚡ [VideoProcessor] Phát hiện GPU Nvidia: Dùng phần cứng NVENC (h264_nvenc)!")
                    VideoProcessor._cached_encoder = "h264_nvenc"
                    return "h264_nvenc"
                if "h264_qsv" in encoders_text:
                    print("⚡ [VideoProcessor] Phát hiện GPU Intel: Dùng phần cứng QSV (h264_qsv)!")
                    VideoProcessor._cached_encoder = "h264_qsv"
                    return "h264_qsv"
        except Exception as e:
            print(f"[VideoProcessor] Lỗi kiểm tra encoders: {e}")
        
        print("ℹ️ [VideoProcessor] Dùng bộ mã hóa phần mềm CPU: libx264")
        VideoProcessor._cached_encoder = "libx264"
        return "libx264"

    def get_video_duration(self, video_path: str) -> float:
        """
        Lấy thời lượng video (giây).
        
        Args:
            video_path: Đường dẫn file video
            
        Returns:
            Thời lượng (giây)
        """
        cmd = [
            FFPROBE_PATH,
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            video_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Lỗi đọc thông tin video: {result.stderr}")

        return float(result.stdout.strip())

    def burn_subtitles(self, video_path: str, srt_path: str,
                       output_path: str) -> str:
        """
        Chèn phụ đề cứng (hardcoded) vào video.
        Sử dụng cách copy SRT vào cùng thư mục để tránh lỗi path trên Windows.
        
        Args:
            video_path: Đường dẫn video gốc
            srt_path: Đường dẫn file SRT
            output_path: Đường dẫn video đầu ra
            
        Returns:
            Đường dẫn video có phụ đề
        """
        # Copy SRT vào thư mục output với tên đơn giản
        work_dir = os.path.dirname(output_path)
        os.makedirs(work_dir, exist_ok=True)
        temp_srt = os.path.join(work_dir, "temp_sub.srt")
        shutil.copy2(srt_path, temp_srt)

        # Style phụ đề
        subtitle_style = (
            "FontName=Arial,"
            "FontSize=22,"
            "PrimaryColour=&H00FFFFFF,"
            "OutlineColour=&H00000000,"
            "BackColour=&H80000000,"
            "Outline=2,"
            "Shadow=1,"
            "MarginV=35,"
            "Alignment=2"
        )

        # Escape path cho FFmpeg subtitles filter trên Windows
        srt_escaped = temp_srt.replace('\\', '/').replace(':', '\\:')

        cmd = [
            FFMPEG_PATH,
            '-i', video_path,
            '-vf', f"subtitles='{srt_escaped}':force_style='{subtitle_style}'",
            '-c:a', 'copy',
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-y', '-loglevel', 'warning',
            output_path
        ]

        print(f"[VideoProcessor] Đang chèn phụ đề...")
        result = subprocess.run(cmd, capture_output=True, text=True)

        # Dọn dẹp
        if os.path.exists(temp_srt):
            os.remove(temp_srt)

        if result.returncode != 0:
            raise RuntimeError(f"Lỗi chèn phụ đề: {result.stderr}")

        return output_path


    def separate_vocals_demucs(self, video_path: str, temp_dir: str) -> str:
        """
        Sử dụng Meta Demucs để tách giọng lồng tiếng gốc, trả về đường dẫn tới file nhạc nền (no_vocals.wav).
        """
        print(f"[Demucs] Bắt đầu tách giọng gốc cho video: {video_path}")
        
        # 1. Trích xuất audio từ video gốc
        original_audio_path = os.path.join(temp_dir, "original_audio.wav")
        extract_cmd = [
            FFMPEG_PATH,
            '-i', video_path,
            '-vn',
            '-c:a', 'pcm_s16le',
            '-ar', '44100',
            '-ac', '2',
            '-y', '-loglevel', 'warning',
            original_audio_path
        ]
        
        # Tạo thư mục tạm nếu chưa có
        os.makedirs(temp_dir, exist_ok=True)
        subprocess.run(extract_cmd, check=True)
        
        # 2. Chạy Demucs tách vocal
        # --two-stems=vocals sẽ tạo ra vocals.wav (giọng nói) và no_vocals.wav (nhạc nền + tiếng động)
        demucs_out_dir = os.path.join(temp_dir, "demucs_out")
        os.makedirs(demucs_out_dir, exist_ok=True)
        
        # Tìm path của python.exe trong venv để chạy CLI của demucs trực tiếp
        python_exe = sys.executable
        demucs_cmd = [
            python_exe,
            '-m', 'demucs.separate',
            '--two-stems=vocals',
            '-o', demucs_out_dir,
            original_audio_path
        ]
        
        print(f"[Demucs] Đang tách bằng lệnh: {' '.join(demucs_cmd)}")
        result = subprocess.run(demucs_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Lỗi khi chạy Demucs tách vocal: {result.stderr or result.stdout}")
            
        # Đường dẫn mặc định của Demucs: {demucs_out_dir}/htdemucs/original_audio/no_vocals.wav
        bgm_path = os.path.join(demucs_out_dir, "htdemucs", "original_audio", "no_vocals.wav")
        if not os.path.exists(bgm_path):
            # Thử tìm kiếm bất kỳ file no_vocals.wav nào trong thư mục đầu ra phòng khi model name khác
            import glob
            found_files = glob.glob(os.path.join(demucs_out_dir, "**", "no_vocals.wav"), recursive=True)
            if found_files:
                bgm_path = found_files[0]
            else:
                raise FileNotFoundError("Không tìm thấy file nhạc nền no_vocals.wav sau khi chạy Demucs.")
                
        print(f"[Demucs] Đã tách thành công! Nhạc nền lưu tại: {bgm_path}")
        return bgm_path


    def mix_audio(self, video_path: str, dubbed_audio_path: str,
                  output_path: str, original_volume: float | None = None,
                  dubbed_volume: float | None = None) -> str:
        """
        Trộn audio gốc (giảm volume) với audio lồng tiếng.
        
        Args:
            video_path: Đường dẫn video (có audio gốc)
            dubbed_audio_path: Đường dẫn audio lồng tiếng
            output_path: Đường dẫn video đầu ra
            original_volume: Âm lượng gốc (0.0 - 1.0)
            dubbed_volume: Âm lượng lồng tiếng (0.0 - 2.0)
            
        Returns:
            Đường dẫn video có audio đã trộn
        """
        orig_vol = original_volume if original_volume is not None else ORIGINAL_AUDIO_VOLUME
        dub_vol = dubbed_volume if dubbed_volume is not None else DUBBED_AUDIO_VOLUME

        filter_audio = (
            f"[0:a]volume={orig_vol}[orig];"
            f"[1:a]volume={dub_vol}[dub];"
            f"[orig][dub]amix=inputs=2:duration=first:dropout_transition=3,volume=2[aout]"
        )

        cmd = [
            FFMPEG_PATH,
            '-i', video_path,
            '-i', dubbed_audio_path,
            '-filter_complex', filter_audio,
            '-map', '0:v',
            '-map', '[aout]',
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-movflags', '+faststart',
            '-y', '-loglevel', 'warning',
            output_path
        ]

        print(f"[VideoProcessor] Đang trộn audio...")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"Lỗi trộn audio: {result.stderr}")

        return output_path

    def export_final(self, video_path: str, srt_path: str,
                     dubbed_audio_path: str | None, output_path: str,
                     sub_color: str = "white", sub_size: int = 22,
                     sub_bg: str = "outline", sub_position: str = "bottom",
                     sub_font: str = "Arial",
                     sub_bg_color: str = "#000000",
                     sub_bg_opacity: int = 80,
                     sub_outline: bool = True,
                     sub_outline_width: float = 2.0,
                     sub_shadow: bool = True,
                     sub_margin_v_percent: float = 12.0,
                     original_volume: float | None = None,
                     dubbed_volume: float | None = None,
                     separate_vocals: bool = False,
                     progress_callback: Callable[[int, str], None] | None = None,
                     blur_bars: list[dict] | None = None) -> str:
        """
        Xuất video hoàn chỉnh: chèn phụ đề + trộn audio bằng 1 câu lệnh duy nhất
        với các cấu hình style phụ đề tùy biến và preset encode tối ưu (ultrafast).
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        if progress_callback:
            progress_callback(5)

        # Lấy kích thước video thực tế để tự động điều chỉnh cỡ chữ cho video dọc/vuông
        width, height = 1920, 1080
        try:
            cmd = [
                FFPROBE_PATH,
                '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height',
                '-of', 'csv=s=x:p=0',
                video_path
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                parts = res.stdout.strip().split('x')
                if len(parts) == 2:
                    width = int(parts[0])
                    height = int(parts[1])
        except Exception as e:
            print(f"[VideoProcessor] Lỗi lấy kích thước video: {e}")

        # Tỷ lệ aspect ratio của video
        video_ratio = width / height if height > 0 else 1.777
        
        # Nếu là video dọc hoặc vuông (AR < 1.6), tự động thu nhỏ cỡ chữ tỉ lệ thuận với chiều rộng
        actual_sub_size = sub_size
        if video_ratio < 1.6:
            actual_sub_size = max(10, int(sub_size * (video_ratio / 1.777)))
            print(f"[VideoProcessor] Phát hiện video dọc/vuông (AR: {video_ratio:.2f}). Điều chỉnh cỡ chữ từ {sub_size} xuống {actual_sub_size} để tránh tràn dòng.")

        # Tách giọng lồng tiếng gốc bằng AI Demucs nếu được yêu cầu
        no_vocals_path = None
        if separate_vocals:
            if progress_callback:
                progress_callback(10)
            try:
                temp_demucs_dir = os.path.join(os.path.dirname(output_path), f"temp_demucs_{os.path.basename(output_path).split('_')[0]}")
                no_vocals_path = self.separate_vocals_demucs(video_path, temp_demucs_dir)
            except Exception as e:
                print(f"[VideoProcessor] [Demucs Fallback] Lỗi tách giọng gốc: {e}. Sử dụng phương pháp giảm âm lượng gốc thông thường.")
                no_vocals_path = None

        # Copy SRT vào thư mục output với tên đơn giản để tránh lỗi ký tự đặc biệt hoặc space
        work_dir = os.path.dirname(output_path)
        temp_srt = os.path.join(work_dir, "temp_sub.srt")
        shutil.copy2(srt_path, temp_srt)

        # Parse màu chữ (HTML #RRGGBB sang ASS &H00BBGGRR)
        def html_to_ass_color(html_color: str, default: str = "&H00FFFFFF") -> str:
            if not html_color:
                return default
            if html_color.startswith('#'):
                rr = html_color[1:3]
                gg = html_color[3:5]
                bb = html_color[5:7]
                return f"&H00{bb}{gg}{rr}"
            color_map = {
                "white": "&H00FFFFFF",
                "yellow": "&H0000FFFF",
                "cyan": "&H00FFFF00",
                "green": "&H0000FF00",
                "magenta": "&H00FF00FF",
                "red": "&H000000FF"
            }
            return color_map.get(html_color.lower(), default)

        primary_color = html_to_ass_color(sub_color, "&H00FFFFFF")

        # Parse màu nền kèm độ mờ (BackColour &HAABBGGRR)
        bg_rgb = sub_bg_color.lstrip('#')
        if len(bg_rgb) == 6:
            rr, gg, bb = bg_rgb[0:2], bg_rgb[2:4], bg_rgb[4:6]
        else:
            rr, gg, bb = "00", "00", "00"

        # Alpha: 00 là đặc hoàn toàn, FF là trong suốt hoàn toàn
        alpha_val = 255 - int(sub_bg_opacity * 2.55)
        alpha_val = max(0, min(255, alpha_val))
        back_colour = f"&H{alpha_val:02X}{bb}{gg}{rr}"

        # Map vị trí phụ đề sang mã Alignment của ASS format
        # 2: Bottom center (mặc định), 5: Middle center, 8: Top center
        pos_map = {
            "bottom": "2",
            "center": "5",
            "top": "8"
        }
        alignment = pos_map.get(sub_position.lower(), "2")

        # Cấu hình kiểu viền / nền
        # BorderStyle: 1 (Outline + drop shadow), 3 (Opaque box)
        if sub_bg == "box":
            border_style = "3"
            outline = "0"
        elif sub_bg == "none":
            border_style = "1"
            outline = "0"
        else:  # outline hoặc custom
            border_style = "1"
            outline = str(sub_outline_width) if sub_outline else "0"

        shadow = "1.5" if sub_shadow else "0"

        # Quy đổi margin_v_percent từ UI sang ASS MarginV (dựa trên virtual height 288px của ASS)
        # 12% tương đương với 35px
        margin_v = int(sub_margin_v_percent * 2.88)
        margin_v = max(5, min(280, margin_v))

        # Style phụ đề hoàn chỉnh
        subtitle_style = (
            f"FontName={sub_font},"
            f"FontSize={actual_sub_size},"
            f"PrimaryColour={primary_color},"
            f"OutlineColour=&H00000000,"
            f"BackColour={back_colour},"
            f"BorderStyle={border_style},"
            f"Outline={outline},"
            f"Shadow={shadow},"
            f"MarginV={margin_v},"
            f"Alignment={alignment}"
        )

        # Escape path cho FFmpeg subtitles filter trên Windows
        srt_escaped = temp_srt.replace('\\', '/').replace(':', '\\:')

        orig_vol = original_volume if original_volume is not None else ORIGINAL_AUDIO_VOLUME
        dub_vol = dubbed_volume if dubbed_volume is not None else DUBBED_AUDIO_VOLUME

        # Chuẩn bị chuỗi Blur Bar filter (nếu có)
        v_in = "[0:v]"
        blur_filter = ""
        if blur_bars:
            active_bars = [b for b in blur_bars if b.get("enabled")]
            if active_bars:
                last_v_out = "[0:v]"
                for i, bar in enumerate(active_bars):
                    y_pct = float(bar.get("y_percent", 85))
                    x_pct = float(bar.get("x_percent", 0))
                    h_pct = float(bar.get("h_percent", 15))
                    w_pct = float(bar.get("w_percent", 100))
                    intensity = int(bar.get("intensity", 15))
                    
                    v_base = f"[vbase{i}]"
                    v_orig = f"[vblur_orig{i}]"
                    v_blurred = f"[vblurred{i}]"
                    v_out = f"[vpre{i}]"
                    
                    blur_filter += (
                        f"{last_v_out}split{v_base}{v_orig};"
                        f"{v_orig}crop=iw*{w_pct/100}:ih*{h_pct/100}:iw*{x_pct/100}:ih*{y_pct/100},boxblur={intensity}:1{v_blurred};"
                        f"{v_base}{v_blurred}overlay=W*{x_pct/100}:H*{y_pct/100}{v_out};"
                    )
                    last_v_out = v_out
                v_in = last_v_out

        if no_vocals_path:
            # Nhạc nền gốc tách bằng Demucs ở input 2 (nếu có dubbed_audio_path thì input 1 là dubbed)
            if dubbed_audio_path:
                filter_complex = (
                    f"{blur_filter}"
                    f"{v_in}subtitles='{srt_escaped}':force_style='{subtitle_style}'[vout];"
                    f"[2:a]volume={orig_vol}[orig];"
                    f"[1:a]volume={dub_vol}[dub];"
                    f"[orig][dub]amix=inputs=2:duration=first:dropout_transition=3[aout]"
                )
                inputs = ['-i', video_path, '-i', dubbed_audio_path, '-i', no_vocals_path]
            else:
                filter_complex = (
                    f"{blur_filter}"
                    f"{v_in}subtitles='{srt_escaped}':force_style='{subtitle_style}'[vout];"
                    f"[1:a]volume={orig_vol}[aout]"
                )
                inputs = ['-i', video_path, '-i', no_vocals_path]
        else:
            # Nhạc nền gốc của video ở input 0
            if dubbed_audio_path:
                filter_complex = (
                    f"{blur_filter}"
                    f"{v_in}subtitles='{srt_escaped}':force_style='{subtitle_style}'[vout];"
                    f"[0:a]volume={orig_vol}[orig];"
                    f"[1:a]volume={dub_vol}[dub];"
                    f"[orig][dub]amix=inputs=2:duration=first:dropout_transition=3[aout]"
                )
                inputs = ['-i', video_path, '-i', dubbed_audio_path]
            else:
                filter_complex = (
                    f"{blur_filter}"
                    f"{v_in}subtitles='{srt_escaped}':force_style='{subtitle_style}'[vout];"
                    f"[0:a]volume={orig_vol}[aout]"
                )
                inputs = ['-i', video_path]

        # Kiểm tra bộ giải mã phần cứng tốt nhất
        encoder = self.get_best_video_encoder()

        cmd = [FFMPEG_PATH] + inputs + [
            '-filter_complex', filter_complex,
            '-map', '[vout]',
            '-map', '[aout]',
            '-c:v', encoder,
        ]

        if encoder == "libx264":
            cmd.extend(['-preset', 'ultrafast', '-crf', '24'])
        else:
            # NVENC hoặc QSV hỗ trợ tăng tốc phần cứng
            cmd.extend(['-preset', 'fast'])

        cmd.extend([
            '-c:a', 'aac',
            '-b:a', '128k',
            '-movflags', '+faststart',
            '-y', '-loglevel', 'warning',
            output_path
        ])

        print(f"[VideoProcessor] Đang xuất video gộp 1 bước với Custom Style (tốc độ cao)...")
        if progress_callback:
            progress_callback(20)

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"[VideoProcessor] Lỗi xuất gộp bằng GPU ({encoder}): {result.stderr}")
            if encoder != "libx264":
                print("[VideoProcessor] Đang thử lại bằng bộ mã hóa CPU (libx264)...")
                # Xây dựng lại lệnh với libx264 cho CPU
                cmd_cpu = [FFMPEG_PATH] + inputs + [
                    '-filter_complex', filter_complex,
                    '-map', '[vout]',
                    '-map', '[aout]',
                    '-c:v', 'libx264',
                    '-preset', 'ultrafast',
                    '-crf', '24',
                    '-c:a', 'aac',
                    '-b:a', '128k',
                    '-movflags', '+faststart',
                    '-y', '-loglevel', 'warning',
                    output_path
                ]
                result = subprocess.run(cmd_cpu, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"[VideoProcessor] Lỗi kết xuất chính: {result.stderr}")
            if progress_callback:
                progress_callback(50)
            
            # Fallback nếu cách gộp bị lỗi (ví dụ video gốc không có tiếng):
            # Thử xuất chỉ chèn sub và dùng tiếng lồng độc lập (chạy trên CPU)
            print("[VideoProcessor] Thử phương án dự phòng (chỉ dùng lồng tiếng trên CPU)...")
            try:
                shutil.copy2(srt_path, temp_srt) # copy lại srt do đã bị xóa
                filter_complex_fallback = f"[0:v]subtitles='{srt_escaped}':force_style='{subtitle_style}'[vout]"
                if dubbed_audio_path:
                    cmd_fallback = [
                        FFMPEG_PATH,
                        '-i', video_path,
                        '-i', dubbed_audio_path,
                        '-filter_complex', filter_complex_fallback,
                        '-map', '[vout]',
                        '-map', '1:a',
                        '-c:v', 'libx264',
                        '-preset', 'ultrafast',
                        '-c:a', 'aac',
                        '-y', '-loglevel', 'warning',
                        output_path
                    ]
                else:
                    cmd_fallback = [
                        FFMPEG_PATH,
                        '-i', video_path,
                        '-filter_complex', filter_complex_fallback,
                        '-map', '[vout]',
                        '-map', '0:a',
                        '-c:v', 'libx264',
                        '-preset', 'ultrafast',
                        '-c:a', 'aac',
                        '-y', '-loglevel', 'warning',
                        output_path
                    ]
                result_fallback = subprocess.run(cmd_fallback, capture_output=True, text=True)
                if os.path.exists(temp_srt):
                    os.remove(temp_srt)
                if result_fallback.returncode != 0:
                    raise RuntimeError(f"Lỗi xuất dự phòng: {result_fallback.stderr}")
            except Exception as e:
                # Nếu vẫn lỗi, copy nguyên video gốc để tránh lỗi toàn bộ job
                print(f"[VideoProcessor] Lỗi xuất toàn bộ: {e}. Tiến hành copy video gốc.")
                shutil.copy2(video_path, output_path)

        # Dọn dẹp temp SRT cuối cùng sau khi hoàn tất mọi retries/fallbacks
        if os.path.exists(temp_srt):
            try:
                os.remove(temp_srt)
            except OSError:
                pass

        if progress_callback:
            progress_callback(100)

        file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
        print(f"[VideoProcessor] Đã xuất video: {output_path} ({file_size / 1024 / 1024:.1f} MB)")

        return output_path
