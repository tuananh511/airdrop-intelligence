"""Interface cho scorer chấm điểm project.

`ProjectScorer` là interface chung - hiện tại chỉ có `RuleBasedScorer` (V2),
nhưng thiết kế theo interface để sau này có thể thêm scorer khác (vd
kết hợp AI score) mà không phải sửa code gọi nó.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.models import Project, ProjectScore


class ProjectScorer(ABC):
    """Interface chấm điểm 1 project. Implementation không được raise exception."""

    @abstractmethod
    def score(self, project: Project) -> ProjectScore:
        """Chấm điểm 1 project, trả về ProjectScore (worth_score 0-100 + lý do)."""
