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
    """Tạo và biên tập ảnh Thumbnail chuẩn 1080p sang trọng, chuyên nghiệp."""

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
    def wrap_text(cls, text: str, font, max_width: int):
        """Ngắt dòng văn bản tự động để không bị tràn lề."""
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = font.getbbox(test_line)
            w = bbox[2] - bbox[0]
            if w <= max_width or not current_line:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        return lines

    @classmethod
    def generate_thumbnail(
        cls,
        image_input_path: str,
        output_path: str,
        title_text: str = "",
        episode_text: str = "",
        style: str = "banner"
    ) -> str:
        """
        Tạo ảnh Thumbnail Tiếng Việt nghệ thuật chuyên nghiệp chuẩn YouTube từ ảnh gốc/khung hình đã chụp.
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        if not os.path.exists(image_input_path):
            raise FileNotFoundError(f"Không tìm thấy ảnh đầu vào: {image_input_path}")

        img = Image.open(image_input_path).convert("RGBA")
        width, height = img.size

        # Nếu style = raw, chỉ lưu lại ảnh sạch
        if style == "raw":
            img.convert("RGB").save(output_path, "JPEG", quality=95)
            return output_path

        full_title = title_text.strip().upper() if title_text else ""
        full_ep = episode_text.strip().upper() if episode_text else ""

        # 1. Tạo dải bóng mờ đen bán trong suốt ở CẢ HAI PHÍA (Phía Trên & Phía Dưới)
        # Giúp che hoàn toàn 100% chữ Trung Quốc cũ ở cả 2 góc!
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)

        # Dải mờ phía trên (che chữ Trung Quốc góc trên ~22% chiều cao)
        top_h = int(height * 0.22)
        for y in range(top_h):
            ratio = y / top_h
            alpha = int(230 * (1.0 - math.sin(ratio * math.pi / 2)))
            overlay_draw.line([(0, y), (width, y)], fill=(0, 0, 0, min(alpha, 220)))

        # Dải mờ phía dưới (che kín 2 dòng chữ Trung Quốc phía dưới ~35% chiều cao)
        bot_h = int(height * 0.36)
        for i in range(bot_h):
            y = height - bot_h + i
            ratio = i / bot_h
            alpha = int(245 * math.sin(ratio * math.pi / 2))
            overlay_draw.line([(0, y), (width, y)], fill=(0, 0, 0, min(alpha, 240)))

        img = Image.alpha_composite(img, overlay)
        draw = ImageDraw.Draw(img)

        max_text_w = int(width * 0.90)

        # 2. Vẽ Tên Phim Tiếng Việt (Full Title) ngắt dòng đẹp mắt ở dải mờ phía dưới
        if full_title:
            # Tự động tính cỡ font phù hợp với độ dài chữ
            font_size = int(width * 0.052)
            if len(full_title) > 35:
                font_size = int(width * 0.042)
            if len(full_title) > 55:
                font_size = int(width * 0.035)

            font_title = cls.get_default_font(max(font_size, 22))
            lines = cls.wrap_text(full_title, font_title, max_text_w)

            # Tối đa 2-3 dòng
            if len(lines) > 3:
                font_size = int(font_size * 0.82)
                font_title = cls.get_default_font(max(font_size, 18))
                lines = cls.wrap_text(full_title, font_title, max_text_w)

            # Tính chiều cao tổng các dòng chữ
            line_heights = []
            for line in lines:
                bbox = font_title.getbbox(line)
                line_heights.append(bbox[3] - bbox[1])
            total_text_h = sum(line_heights) + int(font_size * 0.3) * (len(lines) - 1)

            # Vị trí vẽ ở dải mờ phía dưới
            start_y = height - bot_h + int((bot_h - total_text_h) / 2)
            if start_y < height - bot_h:
                start_y = height - bot_h + int(height * 0.03)

            current_y = start_y
            outline_w = max(3, int(font_size * 0.08))

            for line in lines:
                bbox = font_title.getbbox(line)
                l_w = bbox[2] - bbox[0]
                l_h = bbox[3] - bbox[1]
                l_x = (width - l_w) // 2

                # Vẽ bóng đổ (Drop Shadow)
                draw.text((l_x + 4, current_y + 4), line, font=font_title, fill=(0, 0, 0, 245))

                # Vẽ viền đen dày (Thick 8-direction outline)
                for dx in range(-outline_w, outline_w + 1):
                    for dy in range(-outline_w, outline_w + 1):
                        if dx * dx + dy * dy <= outline_w * outline_w:
                            draw.text((l_x + dx, current_y + dy), line, font=font_title, fill=(0, 0, 0, 255))

                # Chữ chính màu Vàng Gold Hoàng Gia (#FFD700)
                draw.text((l_x, current_y), line, font=font_title, fill=(255, 215, 0, 255))
                current_y += l_h + int(font_size * 0.3)

        # 3. Vẽ Huy Hiệu Tập Phim (Episode Badge: [ FULL ] hoặc [ TẬP 01 ])
        if full_ep:
            ep_font_size = max(int(width * 0.035), 18)
            font_ep = cls.get_default_font(ep_font_size)

            ep_text = f"{full_ep}"
            bbox_ep = font_ep.getbbox(ep_text)
            ep_w = bbox_ep[2] - bbox_ep[0]
            ep_h = bbox_ep[3] - bbox_ep[1]

            # Vẽ Huy hiệu Đỏ Nổi bật ở góc trên bên trái
            pad_x = int(width * 0.02)
            pad_y = int(height * 0.01)
            b_x1 = int(width * 0.04)
            b_y1 = int(height * 0.04)
            b_x2 = b_x1 + ep_w + pad_x * 2
            b_y2 = b_y1 + ep_h + pad_y * 2

            # Vẽ khung màu đỏ bo tròn (#DC2626)
            draw.rounded_rectangle([b_x1, b_y1, b_x2, b_y2], radius=8, fill=(220, 38, 38, 240), outline=(255, 255, 255, 255), width=2)
            # Chữ màu Trắng Nổi
            draw.text((b_x1 + pad_x, b_y1 + pad_y), ep_text, font=font_ep, fill=(255, 255, 255, 255))

        # Lưu ảnh đầu ra
        final_img = img.convert("RGB")
        final_img.save(output_path, "JPEG", quality=95)
        print(f"[ThumbnailGenerator] Đã tạo ảnh bìa nâng cấp thành công: {output_path}")
        return output_path
