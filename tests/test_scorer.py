from src.models import Project, ProjectSource
from src.scorer import RuleBasedScorer


def _project(**overrides) -> Project:
    base = dict(
        title="Test Project",
        source=ProjectSource.AIRDROPS_IO,
        source_url="https://airdrops.io/test",
    )
    base.update(overrides)
    return Project(**base)


def test_score_is_within_bounds():
    scorer = RuleBasedScorer()
    project = _project()
    result = scorer.score(project)
    assert 0 <= result.worth_score <= 100
    assert len(result.reasons) >= 1


def test_richer_project_scores_higher_than_sparse_project():
    scorer = RuleBasedScorer()

    sparse = _project()
    rich = _project(
        reward="100 USDC",
        deadline="2026-08-01",
        description="Actions: complete quests, refer friends, and claim reward" * 2,
        tags=["Ongoing"],
    )

    assert scorer.score(rich).worth_score > scorer.score(sparse).worth_score


def test_ended_project_scores_lower():
    scorer = RuleBasedScorer()
    ongoing = _project(tags=["Ongoing"])
    ended = _project(tags=["Ended"])

    assert scorer.score(ended).worth_score < scorer.score(ongoing).worth_score


def test_score_never_raises_on_minimal_data():
    scorer = RuleBasedScorer()
    minimal = _project(description="", tags=[])
    result = scorer.score(minimal)
    assert result.worth_score >= 0
