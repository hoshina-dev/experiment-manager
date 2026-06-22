"""Tests for form_schema helpers."""

from app.form_schema import (collect_values, find_duplicate_question_ids,
                             migrate_formula)


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


def test_collect_values_expands_repeatable_group_child_default_to_count_list() -> None:
    # The schema documents columnar storage: one entry per repetition. A
    # child question's `config.default` should fill every slot, not collapse
    # to a bare scalar (which then breaks any formula expecting a list, e.g.
    # `len(values['reading_a'])`).
    state = {
        "labForm": {
            "name": "Lab",
            "questions": [
                {
                    "id": "measurement",
                    "type": "repeatable-group",
                    "label": "Measurements",
                    "config": {
                        "count": 3,
                        "questions": [
                            {
                                "id": "reading_a",
                                "type": "number",
                                "label": "Reading A",
                                "config": {"default": 10.0},
                            }
                        ],
                    },
                }
            ],
        },
    }
    assert collect_values(state) == {"reading_a": [10.0, 10.0, 10.0]}


def test_collect_values_does_not_override_explicitly_submitted_repeatable_values() -> None:
    state = {
        "values": {"reading_a": [1.0, 2.0, 3.0]},
        "labForm": {
            "name": "Lab",
            "questions": [
                {
                    "id": "measurement",
                    "type": "repeatable-group",
                    "label": "Measurements",
                    "config": {
                        "count": 3,
                        "questions": [
                            {
                                "id": "reading_a",
                                "type": "number",
                                "label": "Reading A",
                                "config": {"default": 10.0},
                            }
                        ],
                    },
                }
            ],
        },
    }
    assert collect_values(state) == {"reading_a": [1.0, 2.0, 3.0]}


def test_collect_values_skips_repeatable_group_child_with_no_default() -> None:
    state = {
        "labForm": {
            "name": "Lab",
            "questions": [
                {
                    "id": "measurement",
                    "type": "repeatable-group",
                    "label": "Measurements",
                    "config": {
                        "count": 3,
                        "questions": [
                            {"id": "reading_a", "type": "number", "label": "Reading A"}
                        ],
                    },
                }
            ],
        },
    }
    assert collect_values(state) == {}


def test_find_duplicate_question_ids_detects_id_used_in_both_forms() -> None:
    state = {
        "clientForm": {
            "name": "C",
            "questions": [{"id": "sample_id", "type": "string", "label": "Sample ID"}],
        },
        "labForm": {
            "name": "L",
            "questions": [{"id": "sample_id", "type": "number", "label": "Sample ID"}],
        },
    }
    assert find_duplicate_question_ids(state) == ["sample_id"]


def test_find_duplicate_question_ids_detects_repeatable_group_child_duplicate() -> None:
    state = {
        "clientForm": {"name": "C", "questions": []},
        "labForm": {
            "name": "L",
            "questions": [
                {"id": "reading_a", "type": "number", "label": "Top-level"},
                {
                    "id": "measurement",
                    "type": "repeatable-group",
                    "label": "Measurements",
                    "config": {
                        "count": 3,
                        "questions": [
                            {"id": "reading_a", "type": "number", "label": "Reading A"}
                        ],
                    },
                },
            ],
        },
    }
    assert find_duplicate_question_ids(state) == ["reading_a"]


def test_find_duplicate_question_ids_returns_empty_when_all_unique() -> None:
    state = {
        "clientForm": {
            "name": "C",
            "questions": [{"id": "sample_id", "type": "string", "label": "Sample ID"}],
        },
        "labForm": {
            "name": "L",
            "questions": [{"id": "reading_a", "type": "number", "label": "Reading A"}],
        },
    }
    assert find_duplicate_question_ids(state) == []


def test_migrate_formula_rewrites_question_ids() -> None:
    formula = migrate_formula(
        "round(1000 * moisture_loss / sample_mass) / 10",
        {"sample_mass"},
        {"moisture_loss"},
    )
    assert formula == "round(1000 * moisture_loss / values['sample_mass']) / 10"
