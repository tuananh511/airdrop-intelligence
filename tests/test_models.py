from src.models import Project, ProjectCategory, ProjectSource


def test_project_creation_minimal():
    project = Project(
        title="  Test   Project  ",
        source=ProjectSource.GALXE,
        source_url="https://galxe.com/test",
    )
    assert project.title == "Test Project"
    assert project.category == ProjectCategory.OTHER
    assert project.dedupe_key == "test project"
    assert project.unique_id == "test project"


def test_dedupe_key_case_insensitive():
    a = Project(title="ABC Airdrop", source=ProjectSource.LAYER3, source_url="https://a.com")
    b = Project(title="abc airdrop", source=ProjectSource.ZEALY, source_url="https://b.com")
    assert a.dedupe_key == b.dedupe_key


def test_title_required():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Project(title="", source=ProjectSource.GALXE, source_url="https://x.com")
