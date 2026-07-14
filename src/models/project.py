"""Domain models cho Airdrop Intelligence Bot.

Project là entity trung tâm: mọi crawler đều phải chuẩn hóa dữ liệu thô
về đúng schema này trước khi đi qua các bước tiếp theo (dedupe, score, notify).
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl, field_validator


class ProjectCategory(str, Enum):
    """Phân loại airdrop theo mảng hoạt động chính."""

    DEFI = "defi"
    NFT = "nft"
    GAMEFI = "gamefi"
    LAYER1 = "layer1"
    LAYER2 = "layer2"
    INFRA = "infra"
    SOCIAL = "social"
    DEPIN = "depin"
    AI = "ai"
    OTHER = "other"


class ProjectSource(str, Enum):
    """Nguồn crawl dữ liệu."""

    AIRDROPS_IO = "airdrops.io"
    GALXE = "galxe"
    LAYER3 = "layer3"
    ZEALY = "zealy"


class AIScore(BaseModel):
    """Kết quả chấm điểm bởi AI (V3). Optional - chỉ có khi ENABLE_AI_SCORING=true."""

    worth: int = Field(ge=0, le=100, description="Điểm đáng làm, 0-100")
    risk: int = Field(ge=0, le=100, description="Điểm rủi ro/scam, 0-100, càng cao càng rủi ro")
    time_estimate: str = Field(description="Ước lượng thời gian cần bỏ ra, vd '20 minutes'")
    capital_required: str = Field(description="Vốn cần thiết, vd '0 USD'")
    has_active_github: bool | None = Field(default=None, description="Có GitHub hoạt động không")
    network_stage: str | None = Field(default=None, description="Mainnet/Testnet/Unknown")
    strong_backers: bool | None = Field(default=None, description="VC/backer có uy tín không")
    suitable_for_low_capital: bool | None = Field(default=None)
    summary: str = Field(description="Tóm tắt đánh giá ngắn gọn bằng tiếng Việt")


class ProjectScore(BaseModel):
    """Điểm số nội bộ (V2, rule-based) - không phụ thuộc AI.

    Interface cho ProjectScorer trong src/scorer. Tách riêng khỏi AIScore
    vì đây là scoring xác định (deterministic), không tốn API call.
    """

    worth_score: int = Field(ge=0, le=100)
    reasons: list[str] = Field(default_factory=list)


class Project(BaseModel):
    """Entity chuẩn hóa cho một airdrop/quest project.

    Đây là "hợp đồng" (contract) giữa crawler và các layer phía sau
    (parser output = model này). Mọi crawler mới phải map dữ liệu thô
    về đúng schema này.
    """

    title: str = Field(min_length=1)
    website: HttpUrl | None = None
    description: str = ""
    reward: str = "Unknown"
    deadline: str = "Unknown"
    cost: str = "Unknown"
    category: ProjectCategory = ProjectCategory.OTHER
    source: ProjectSource
    source_url: HttpUrl
    tags: list[str] = Field(default_factory=list)
    published_at: datetime | None = None

    # Các field được điền thêm ở giai đoạn sau (scorer/ai), không có ở lúc parse.
    score: ProjectScore | None = None
    ai_score: AIScore | None = None

    @field_validator("title")
    @classmethod
    def normalize_title(cls, v: str) -> str:
        return " ".join(v.split()).strip()

    @property
    def dedupe_key(self) -> str:
        """Key dùng để merge project trùng nhau giữa các nguồn.

        Chuẩn hóa title (lowercase, bỏ khoảng trắng thừa) làm key chính.
        Đây là giải pháp đơn giản cho V1; có thể nâng cấp lên fuzzy-match sau.
        """
        return self.title.lower().strip()

    @property
    def unique_id(self) -> str:
        """ID ổn định để lưu vào history.json (không đổi qua các lần crawl)."""
        return self.dedupe_key
