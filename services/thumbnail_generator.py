"""
Service tạo và chỉnh sửa ảnh bìa Thumbnail Tiếng Việt tự động.
Hỗ trợ cả trích xuất khung hình từ Video và biên tập từ Ảnh Bìa Gốc người dùng tải lên.
100% Cục bộ bằng FFmpeg & Pillow (PIL) - Tốn 0 Token API.
"""
import os
import math
import subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from config import FFMPEG_PATH


class ThumbnailGenerator:
    """Tạo và biên tập ảnh Thumbnail chuẩn 1080p sang trọng, thay thế chính xác vị trí chữ Trung - Việt."""

    @staticmethod
    def capture_frame(video_path: str, output_path: str, timestamp_sec: float = 3.0) -> str:
        """
        Trích xuất 1 khung hình từ video tại mốc thời gian chỉ định bằng FFmpeg.
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        hours = int(timestamp_sec // 3600)
        minutes = int((timestamp_sec % 3600) // 60)
        secs = timestamp_sec % 60
        time_str = f"{hours:02d}:{minutes:02d}:{secs:06.3f}"

        cmd = [
            FFMPEG_PATH,
            "-ss", time_str,
            "-i", video_path,
            "-vframes", "1",
            "-q:v", "2",
            "-y", output_path
        ]
        subprocess.run(cmd, capture_output=True, check=False)

        # Fallback nếu ở mốc timestamp_sec không lấy được (vd video ngắn hơn)
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            cmd_fallback = [
                FFMPEG_PATH,
                "-ss", "00:00:01.000",
                "-i", video_path,
                "-vframes", "1",
                "-q:v", "2",
                "-y", output_path
            ]
            subprocess.run(cmd_fallback, capture_output=True, check=False)

        return output_path

    @staticmethod
    def get_default_font(font_size: int):
        """Lấy font chữ hệ thống hỗ trợ Unicode Tiếng Việt đậm nét nhất."""
        font_paths = [
            "C:\\Windows\\Fonts\\arialbd.ttf",      # Arial Bold
            "C:\\Windows\\Fonts\\segoeuib.ttf",     # Segoe UI Bold
            "C:\\Windows\\Fonts\\tahomabd.ttf",     # Tahoma Bold
            "C:\\Windows\\Fonts\\calibrib.ttf",     # Calibri Bold
            "C:\\Windows\\Fonts\\arial.ttf"
        ]
        for path in font_paths:
            if os.path.exists(path):
                try:
                    return ImageFont.truetype(path, font_size)
                except Exception:
                    continue
        return ImageFont.load_default()

    @classmethod
    def draw_bordered_text(
        cls,
        draw: ImageDraw.ImageDraw,
        xy: tuple,
        text: str,
        font: ImageFont.ImageFont,
        fill_color: tuple,
        outline_color: tuple = (0, 0, 0, 255),
        stroke_width: int = 6,
        shadow_offset: tuple = (4, 4)
    ):
        x, y = xy
        if shadow_offset:
            sx, sy = shadow_offset
            draw.text((x + sx, y + sy), text, font=font, fill=(0, 0, 0, 240))

        try:
            draw.text(
                (x, y),
                text,
                font=font,
                fill=fill_color,
                stroke_width=stroke_width,
                stroke_fill=outline_color
            )
        except Exception:
            for dx in range(-stroke_width, stroke_width + 1):
                for dy in range(-stroke_width, stroke_width + 1):
                    if dx * dx + dy * dy <= stroke_width * stroke_width:
                        draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
            draw.text((x, y), text, font=font, fill=fill_color)

    @classmethod
    def generate_thumbnail(
        cls,
        image_input_path: str,
        output_path: str,
        title_text: str = "",
        episode_text: str = "",
        sub_title_text: str = "",
        style: str = "match_original"
    ) -> str:
        """
        Tạo ảnh Thumbnail Tiếng Việt nghệ thuật thay thế chính xác vị trí chữ Trung Quốc.
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        if not os.path.exists(image_input_path):
            raise FileNotFoundError(f"Không tìm thấy ảnh đầu vào: {image_input_path}")

        img = Image.open(image_input_path).convert("RGBA")
        width, height = img.size

        if style == "raw":
            img.convert("RGB").save(output_path, "JPEG", quality=95)
            return output_path

        draw = ImageDraw.Draw(img)

        line1 = episode_text.strip().upper() if episode_text else ""
        line2 = title_text.strip().upper() if title_text else ""
        line3 = sub_title_text.strip().upper() if sub_title_text else ""

        # Nếu line2 dài mà line3 trống, tự động tách line2 thành 2 dòng (Hàng Cyan + Hàng Yellow)
        if line2 and not line3:
            if "," in line2:
                parts = line2.split(",", 1)
                line2 = parts[0].strip()
                line3 = parts[1].strip()
            elif " - " in line2:
                parts = line2.split(" - ", 1)
                line2 = parts[0].strip()
                line3 = parts[1].strip()
            else:
                words = line2.split()
                if len(words) >= 6:
                    mid = len(words) // 2
                    line2 = " ".join(words[:mid])
                    line3 = " ".join(words[mid:])

        # -------------------------------------------------------------
        # 1. DÒNG 1 (GÓC TRÊN BÊN TRÁI - CHỮ ĐỎ VIỀN ĐEN TRONG NGOẶC 【...】)
        # -------------------------------------------------------------
        if line1:
            if not line1.startswith("【") and not line1.startswith("["):
                line1_text = f"【{line1}】"
            else:
                line1_text = line1

            font_size_1 = max(int(width * 0.048), 24)
            font1 = cls.get_default_font(font_size_1)

            # Vị trí góc trên bên trái (Top Left)
            pos_x1 = int(width * 0.05)
            pos_y1 = int(height * 0.04)

            cls.draw_bordered_text(
                draw,
                (pos_x1, pos_y1),
                line1_text,
                font1,
                fill_color=(255, 51, 51, 255),  # Màu Đỏ Tươi #FF3333
                outline_color=(0, 0, 0, 255),
                stroke_width=max(4, int(font_size_1 * 0.09))
            )

        # -------------------------------------------------------------
        # 2. DÒNG 2 (HÀNG DƯỚI 1 - CHỮ XANH CYAN #00E5FF VIỀN ĐEN DÀY)
        # -------------------------------------------------------------
        if line2:
            max_w = int(width * 0.94)
            font_size_2 = int(width * 0.054)

            font2 = cls.get_default_font(font_size_2)
            bbox2 = font2.getbbox(line2)
            w2 = bbox2[2] - bbox2[0]

            # Co font nếu vượt quá chiều rộng ảnh
            if w2 > max_w:
                font_size_2 = int(font_size_2 * (max_w / w2))
                font2 = cls.get_default_font(max(font_size_2, 18))
                bbox2 = font2.getbbox(line2)
                w2 = bbox2[2] - bbox2[0]

            pos_x2 = (width - w2) // 2
            pos_y2 = int(height * 0.67) if line3 else int(height * 0.74)

            cls.draw_bordered_text(
                draw,
                (pos_x2, pos_y2),
                line2,
                font2,
                fill_color=(0, 229, 255, 255),  # Màu Xanh Cyan #00E5FF
                outline_color=(0, 0, 0, 255),
                stroke_width=max(6, int(font_size_2 * 0.11))
            )

        # -------------------------------------------------------------
        # 3. DÒNG 3 (HÀNG DƯỚI 2 - CHỮ VÀNG #FFEA00 VIỀN ĐEN DÀY)
        # -------------------------------------------------------------
        if line3:
            max_w = int(width * 0.94)
            font_size_3 = int(width * 0.050)

            font3 = cls.get_default_font(font_size_3)
            bbox3 = font3.getbbox(line3)
            w3 = bbox3[2] - bbox3[0]

            if w3 > max_w:
                font_size_3 = int(font_size_3 * (max_w / w3))
                font3 = cls.get_default_font(max(font_size_3, 18))
                bbox3 = font3.getbbox(line3)
                w3 = bbox3[2] - bbox3[0]

            pos_x3 = (width - w3) // 2
            pos_y3 = int(height * 0.81)

            cls.draw_bordered_text(
                draw,
                (pos_x3, pos_y3),
                line3,
                font3,
                fill_color=(255, 234, 0, 255),  # Màu Vàng Nổi #FFEA00
                outline_color=(0, 0, 0, 255),
                stroke_width=max(6, int(font_size_3 * 0.11))
            )

        # Lưu ảnh đầu ra
        final_img = img.convert("RGB")
        final_img.save(output_path, "JPEG", quality=95)
        print(f"[ThumbnailGenerator] Đã tạo ảnh bìa thay thế vị trí chuẩn Trung-Việt: {output_path}")
        return output_path
