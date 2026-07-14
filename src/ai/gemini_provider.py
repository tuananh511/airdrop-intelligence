"""AIProvider implementation dùng Gemini API (`google-genai` SDK).

Yêu cầu JSON output trực tiếp từ model (response_mime_type='application/json')
thay vì parse text tự do - đáng tin cậy hơn và đúng schema `AIScore` hơn.
"""

from __future__ import annotations

import json

from google import genai
from google.genai import types
from pydantic import ValidationError

from src.ai.base import AIProvider
from src.models import AIScore, Project
from src.utils.config import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "worth": {"type": "integer", "description": "Điểm đáng làm, 0-100"},
        "risk": {"type": "integer", "description": "Điểm rủi ro/scam, 0-100"},
        "time_estimate": {"type": "string"},
        "capital_required": {"type": "string"},
        "has_active_github": {"type": "boolean"},
        "network_stage": {"type": "string"},
        "strong_backers": {"type": "boolean"},
        "suitable_for_low_capital": {"type": "boolean"},
        "summary": {"type": "string", "description": "Tóm tắt ngắn gọn bằng tiếng Việt"},
    },
    "required": ["worth", "risk", "time_estimate", "capital_required", "summary"],
}

_PROMPT_TEMPLATE = """\
Bạn là chuyên gia phân tích airdrop crypto, giúp người dùng vốn thấp đánh giá \
1 dự án airdrop có đáng tham gia hay không.

Thông tin dự án:
- Tên: {title}
- Nguồn: {source}
- Link: {source_url}
- Mô tả: {description}
- Phần thưởng: {reward}
- Deadline: {deadline}
- Chi phí: {cost}
- Tags: {tags}

Hãy đánh giá dự án này dựa trên các tiêu chí:
- Có đáng làm không (worth, 0-100, càng cao càng đáng làm)
- Có dấu hiệu scam không (risk, 0-100, càng cao càng rủi ro)
- Cần bao nhiêu thời gian để hoàn thành (time_estimate)
- Cần bao nhiêu vốn (capital_required)
- Dự án có vẻ có GitHub hoạt động không (has_active_github, true/false/null nếu không rõ)
- Đang ở giai đoạn Mainnet/Testnet/Unknown (network_stage)
- Có backer/VC uy tín không, nếu biết (strong_backers, true/false/null nếu không rõ)
- Có phù hợp với người vốn thấp không (suitable_for_low_capital)
- Tóm tắt đánh giá ngắn gọn bằng tiếng Việt (summary, 1-2 câu)

Nếu thông tin không đủ để đánh giá chắc chắn 1 tiêu chí nào đó, hãy đưa ra ước lượng \
hợp lý nhất dựa trên kinh nghiệm chung về airdrop, không được bịa số liệu cụ thể \
kiểu "$50,000 gọi vốn" nếu không có căn cứ.

Trả lời DUY NHẤT bằng JSON đúng schema đã cho, không thêm text nào khác.
"""


class GeminiProvider(AIProvider):
    """Gọi Gemini để đánh giá project. Lỗi bất kỳ -> trả về None, không raise."""

    def __init__(self) -> None:
        settings = get_settings()
        self._model = settings.gemini_model
        self._client = genai.Client(api_key=settings.gemini_api_key)

    def evaluate(self, project: Project) -> AIScore | None:
        prompt = _PROMPT_TEMPLATE.format(
            title=project.title,
            source=project.source.value,
            source_url=project.source_url,
            description=project.description or "(không có mô tả)",
            reward=project.reward,
            deadline=project.deadline,
            cost=project.cost,
            tags=", ".join(project.tags) or "(không có tag)",
        )

        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=_RESPONSE_SCHEMA,
                    temperature=0.3,
                ),
            )
            data = json.loads(response.text)
            return AIScore(**data)
        except Exception as exc:  # noqa: BLE001 - AI call lỗi không được làm chết pipeline
            logger.exception("Gemini evaluate() thất bại cho project '%s'.", project.title)

            error_text = str(exc).lower()
            if "404" in error_text or "not found" in error_text or "not_found" in error_text:
                logger.error(
                    "Lỗi trên có thể do model '%s' không còn tồn tại/bị đổi tên. "
                    "Chạy `python scripts/list_gemini_models.py` để xem danh sách model "
                    "hiện có, rồi cập nhật GEMINI_MODEL trong .env.",
                    self._model,
                )

            return None
