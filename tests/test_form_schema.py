"""Tests for form_schema helpers."""

from app.form_schema import collect_values, migrate_formula


def test_collect_values_merges_defaults() -> None:
    state = {
        "values": {"x": 5},
        "labForm": {
            "name": "Lab",
            "questions": [
                {"id": "y", "type": "number", "config": {"default": 3.0}},
            ],
        },
    }
    assert collect_values(state) == {"x": 5, "y": 3.0}


def test_migrate_formula_rewrites_question_ids() -> None:
    formula = migrate_formula(
        "round(1000 * moisture_loss / sample_mass) / 10",
        {"sample_mass"},
        {"moisture_loss"},
    )
    assert formula == "round(1000 * moisture_loss / values['sample_mass']) / 10"
