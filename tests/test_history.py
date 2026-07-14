from pathlib import Path

from src.models import Project, ProjectSource
from src.utils.history import filter_new_projects, load_history, save_history


def _project(title: str) -> Project:
    return Project(
        title=title,
        source=ProjectSource.AIRDROPS_IO,
        source_url=f"https://airdrops.io/{title.lower()}",
    )


def test_filter_new_projects_excludes_seen_ones():
    projects = [_project("Alpha"), _project("Beta"), _project("Gamma")]
    history = {"beta"}  # "Beta".dedupe_key == "beta"

    new_projects = filter_new_projects(projects, history)

    titles = {p.title for p in new_projects}
    assert titles == {"Alpha", "Gamma"}


def test_filter_new_projects_empty_history_returns_all():
    projects = [_project("Alpha"), _project("Beta")]
    assert filter_new_projects(projects, set()) == projects


def test_save_and_load_history_roundtrip(tmp_path: Path):
    history_file = tmp_path / "history.json"
    original = {"alpha", "beta", "gamma"}

    save_history(original, path=history_file)
    loaded = load_history(path=history_file)

    assert loaded == original


def test_load_history_missing_file_returns_empty_set(tmp_path: Path):
    missing_file = tmp_path / "does_not_exist.json"
    assert load_history(path=missing_file) == set()
