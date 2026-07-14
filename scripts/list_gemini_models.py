"""Liệt kê các model Gemini đang khả dụng cho API key trong .env.

Vì sao cần script này: Google thường xuyên thêm/bỏ model (model cũ bị "retire",
đổi tên, v.v.) - khi `main.py` báo lỗi kiểu "model not found" / "404" từ Gemini,
chạy script này để xem danh sách model THẬT SỰ đang dùng được ngay bây giờ,
rồi tự chọn 1 cái cập nhật vào `GEMINI_MODEL` trong `.env`.

Cách chạy:
    uv run python scripts/list_gemini_models.py
    (hoặc `python scripts/list_gemini_models.py` nếu đã cài dependency thủ công)

Yêu cầu: đã điền GEMINI_API_KEY trong .env (không cần bật ENABLE_AI_SCORING).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Cho phép chạy trực tiếp script này (không qua `python -m`) mà vẫn import được `src`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from google import genai  # noqa: E402

from src.utils.config import get_settings  # noqa: E402


def main() -> None:
    settings = get_settings()

    if not settings.gemini_api_key:
        print("Chưa có GEMINI_API_KEY trong .env - điền vào rồi chạy lại script này.")
        return

    client = genai.Client(api_key=settings.gemini_api_key)

    print(f"Model đang cấu hình trong .env (GEMINI_MODEL): {settings.gemini_model}")
    print()
    print("Model hỗ trợ generate_content (dùng được cho AI scorer của bot):")
    print("-" * 70)

    supported: list[str] = []
    for model in client.models.list():
        if "generateContent" in (model.supported_actions or []):
            supported.append(model.name)
            print(f"  {model.name}")

    print("-" * 70)

    if not supported:
        print("Không tìm thấy model nào hỗ trợ generateContent - kiểm tra lại API key.")
        return

    print()
    print("=> Copy 1 tên model ở trên (bỏ prefix 'models/' nếu có) vào GEMINI_MODEL trong .env")
    print('   Ví dụ: GEMINI_MODEL=gemini-3.1-flash-lite')


if __name__ == "__main__":
    main()
