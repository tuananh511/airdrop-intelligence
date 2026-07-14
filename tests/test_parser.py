from src.models import ProjectSource
from src.parser import build_project, build_projects, merge_projects


def _raw(title: str, **overrides):
    base = {
        "title": title,
        "source_url": f"https://example.com/{title.lower().replace(' ', '-')}",
    }
    base.update(overrides)
    return base


def test_build_project_minimal():
    project = build_project(_raw("Cool Airdrop"), ProjectSource.AIRDROPS_IO)
    assert project is not None
    assert project.title == "Cool Airdrop"
    assert project.reward == "Unknown"
    assert project.source == ProjectSource.AIRDROPS_IO


def test_build_project_missing_required_field_returns_none():
    raw = {"title": "No URL Project"}  # thiếu source_url bắt buộc
    project = build_project(raw, ProjectSource.GALXE)
    assert project is None


def test_build_projects_skips_invalid_items():
    raws = [_raw("Valid One"), {"title": "Missing url"}, _raw("Valid Two")]
    projects = build_projects(raws, ProjectSource.LAYER3)
    assert len(projects) == 2
    assert {p.title for p in projects} == {"Valid One", "Valid Two"}


def test_merge_projects_deduplicates_by_title():
    a = build_project(_raw("Same Project", reward="100 USDC"), ProjectSource.AIRDROPS_IO)
    b = build_project(_raw("same project", reward="Unknown"), ProjectSource.ZEALY)

    merged = merge_projects([a, b])

    assert len(merged) == 1
    result = merged[0]
    assert result.reward == "100 USDC"  # giữ giá trị "giàu thông tin hơn"
    assert "airdrops.io" in result.tags
    assert "zealy" in result.tags


def test_merge_projects_keeps_distinct_titles_separate():
    a = build_project(_raw("Project A"), ProjectSource.AIRDROPS_IO)
    b = build_project(_raw("Project B"), ProjectSource.AIRDROPS_IO)

    merged = merge_projects([a, b])

    assert len(merged) == 2
