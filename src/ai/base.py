"""Interface cho AI provider chấm điểm project bằng LLM.

Thiết kế theo interface để sau này thay Gemini bằng OpenRouter/OpenAI chỉ cần
viết thêm 1 class implement `AIProvider`, không phải sửa code gọi nó
(`main.py` chỉ biết tới interface này, không biết Gemini/OpenAI cụ thể).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.models import AIScore, Project


class AIProvider(ABC):
    """Interface gọi LLM để đánh giá 1 project.

    Implementation KHÔNG được raise exception ra ngoài - nếu AI call lỗi
    (timeout, quota hết, JSON không parse được...), trả về None + tự log lỗi.
    Đây là tính năng optional (V3), lỗi ở đây không được làm chết pipeline chính.
    """

    @abstractmethod
    def evaluate(self, project: Project) -> AIScore | None:
        """Đánh giá 1 project bằng AI. Trả về None nếu có lỗi bất kỳ."""
