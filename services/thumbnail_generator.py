"""
Service tạo và chỉnh sửa ảnh bìa Thumbnail Tiếng Việt tự động.
Hỗ trợ cả trích xuất khung hình từ Video và biên tập từ Ảnh Bìa Gốc người dùng tải lên.
100% Cục bộ bằng FFmpeg & Pillow (PIL) - Tốn 0 Token API.
"""
import os
import subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from config import FFMPEG_PATH


class ThumbnailGenerator:
    """Tạo và biên tập ảnh Thumbnail chuẩn 1080p."""

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
        """Lấy font chữ hệ thống hỗ trợ Unicode Tiếng Việt tốt nhất."""
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
    def generate_thumbnail(
        cls,
        image_input_path: str,
        output_path: str,
        title_text: str = "",
        episode_text: str = "",
        style: str = "banner"  # "banner", "sub_only", "raw"
    ) -> str:
        """
        Tạo ảnh Thumbnail Tiếng Việt nghệ thuật từ ảnh gốc/khung hình đã chụp.
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        if not os.path.exists(image_input_path):
            raise FileNotFoundError(f"Không tìm thấy ảnh đầu vào: {image_input_path}")

        img = Image.open(image_input_path).convert("RGBA")
        width, height = img.size

        # Đảm bảo tỉ lệ chuẩn
        draw = ImageDraw.Draw(img)

        # Nếu style = raw, chỉ lưu lại ảnh sạch
        if style == "raw":
            img.convert("RGB").save(output_path, "JPEG", quality=95)
            return output_path

        # Nếu có tiêu đề hoặc tập, vẽ dải mờ & chữ Tiếng Việt nghệ thuật
        if title_text or episode_text:
            # 1. Vẽ dải bóng mờ đen bán trong suốt ở phần trên để che bớt chữ Trung Quốc cũ
            overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            
            # Dải mờ phía trên (chiều cao ~ 22% ảnh)
            banner_h = int(height * 0.25)
            for y in range(banner_h):
                # Alpha mượt tăng dần rồi giảm dần
                alpha = int(200 * (1.0 - math_sin_factor(y / banner_h)))
                overlay_draw.line([(0, y), (width, y)], fill=(0, 0, 0, min(alpha, 180)))

            img = Image.alpha_composite(img, overlay)
            draw = ImageDraw.Draw(img)

            # 2. Chuẩn bị Tiêu đề & Tập
            full_title = title_text.strip().upper() if title_text else ""
            full_ep = episode_text.strip().upper() if episode_text else ""

            # Font size dựa trên chiều rộng ảnh
            title_font_size = int(width * 0.055)
            ep_font_size = int(width * 0.04)

            font_title = cls.get_default_font(max(title_font_size, 24))
            font_ep = cls.get_default_font(max(ep_font_size, 18))

            # Tính vị trí vẽ chữ ở góc trên giữa (Top Center)
            top_margin = int(height * 0.04)

            # Draw Title (Tên Phim - Vàng Gold nghệ thuật)
            if full_title:
                bbox = font_title.getbbox(full_title)
                t_w = bbox[2] - bbox[0]
                t_h = bbox[3] - bbox[1]
                t_x = (width - t_w) // 2
                t_y = top_margin

                # Vẽ bóng đổ (Shadow)
                draw.text((t_x + 3, t_y + 3), full_title, font=font_title, fill=(0, 0, 0, 230))
                # Vẽ viền đen (Outline)
                for dx, dy in [(-2,-2), (-2,2), (2,-2), (2,2), (0,-2), (0,2), (-2,0), (2,0)]:
                    draw.text((t_x + dx, t_y + dy), full_title, font=font_title, fill=(0, 0, 0, 255))
                # Chữ chính màu Vàng Gold sáng (FFD700)
                draw.text((t_x, t_y), full_title, font=font_title, fill=(255, 215, 0, 255))

                top_margin += t_h + int(height * 0.015)

            # Draw Episode (Tập - Trắng viền Đen)
            if full_ep:
                bbox_ep = font_ep.getbbox(full_ep)
                ep_w = bbox_ep[2] - bbox_ep[0]
                ep_x = (width - ep_w) // 2
                ep_y = top_margin

                # Vẽ viền đen
                for dx, dy in [(-2,-2), (-2,2), (2,-2), (2,2), (0,-2), (0,2), (-2,0), (2,0)]:
                    draw.text((ep_x + dx, ep_y + dy), full_ep, font=font_ep, fill=(0, 0, 0, 255))
                # Chữ màu Trắng Sáng
                draw.text((ep_x, ep_y), full_ep, font=font_ep, fill=(255, 255, 255, 255))

        # Lưu ảnh đầu ra
        final_img = img.convert("RGB")
        final_img.save(output_path, "JPEG", quality=95)
        print(f"[ThumbnailGenerator] Đã tạo ảnh bìa: {output_path}")
        return output_path


def math_sin_factor(ratio: float) -> float:
    import math
    return math.sin(ratio * math.pi / 2)
