"""Tests for calculation_service — values resolution and eval."""

import pytest
from fastapi import HTTPException

from app.services.calculation_service import _eval_calculations


def test_eval_basic_arithmetic() -> None:
    values = {"a": 10, "b": 3}
    result = _eval_calculations(values, {"c": "values['a'] + values['b']"})
    assert result == {"c": 13}


def test_eval_chained_expressions() -> None:
    values = {"tray_mass": 100.0, "tray_sam": 120.0, "tray_ctrl": 115.0}
    result = _eval_calculations(
        values,
        {
            "sample_mass": "values['tray_sam'] - values['tray_mass']",
            "sample_error": "values['tray_sam'] - values['tray_ctrl']",
            "moisture_pct": "round(1000 * sample_error / sample_mass) / 10",
        },
    )
    assert result["sample_mass"] == 20.0
    assert result["sample_error"] == 5.0
    assert result["moisture_pct"] == 25.0


def test_eval_math_module_available() -> None:
    result = _eval_calculations({"x": 4.0}, {"r": "math.sqrt(values['x'])"})
    assert result["r"] == 2.0


def test_eval_list_aggregation() -> None:
    result = _eval_calculations(
        {"reading_a": [10.0, 12.0, 11.0]},
        {"avg": "round(mean(values['reading_a']), 2)"},
    )
    assert result["avg"] == 11.0


def test_eval_repeatable_measurements_formulas() -> None:
    values = {
        "sample_id": "SMP-2026-0042",
        "reading_a": [10.12, 10.08, 9.97, 10.21, 10.05, 9.94, 10.15, 10.03],
        "reading_b": [10.10, 10.11, 10.00, 10.18, 10.02, 9.98, 10.12, 10.06],
    }
    formulas = {
        "n_measurements": "len(values['reading_a'])",
        "precision": "[round(abs(a - b) / ((a + b) / 2) * 100, 3) for a, b in zip(values['reading_a'], values['reading_b'])]",
        "avg_reading_a": "round(mean(values['reading_a']), 3)",
        "avg_reading_b": "round(mean(values['reading_b']), 3)",
        "avg_precision": "round(mean(precision), 3)",
        "best_precision": "min(precision)",
        "worst_precision": "max(precision)",
        "within_spec": "mean(precision) <= 0.5",
        "run_summary": "f\"{values['sample_id']}: {len(values['reading_a'])} reads, A avg {avg_reading_a} mg / B avg {avg_reading_b} mg, avg precision {avg_precision}%\"",
    }
    result = _eval_calculations(values, formulas)
    assert result["n_measurements"] == 8
    assert result["precision"] == [
        0.198,
        0.297,
        0.3,
        0.294,
        0.299,
        0.402,
        0.296,
        0.299,
    ]
    assert result["avg_reading_a"] == 10.069
    assert result["avg_reading_b"] == 10.071
    assert result["avg_precision"] == 0.298
    assert result["best_precision"] == 0.198
    assert result["worst_precision"] == 0.402
    assert result["within_spec"] is True
    assert (
        result["run_summary"]
        == "SMP-2026-0042: 8 reads, A avg 10.069 mg / B avg 10.071 mg, avg precision 0.298%"
    )


def test_eval_raises_422_on_division_by_zero() -> None:
    with pytest.raises(HTTPException) as exc_info:
        _eval_calculations({"b": 0}, {"r": "1 / values['b']"})
    assert exc_info.value.status_code == 422
    assert "Division by zero" in exc_info.value.detail


def test_eval_raises_422_on_undefined_variable() -> None:
    with pytest.raises(HTTPException) as exc_info:
        _eval_calculations({}, {"r": "missing_var + 1"})
    assert exc_info.value.status_code == 422
    assert "Undefined variable" in exc_info.value.detail


def test_eval_raises_422_on_dunder_injection() -> None:
    with pytest.raises(HTTPException) as exc_info:
        _eval_calculations({}, {"r": "().__class__.__bases__[0].__subclasses__()"})
    assert exc_info.value.status_code == 422
    assert "dunder" in exc_info.value.detail


def test_eval_raises_422_on_generic_error() -> None:
    with pytest.raises(HTTPException) as exc_info:
        _eval_calculations({}, {"r": "math.sqrt(-1)"})
    assert exc_info.value.status_code == 422
    assert "Calculation error" in exc_info.value.detail


def test_eval_raises_422_on_infinite_result() -> None:
    with pytest.raises(HTTPException) as exc_info:
        _eval_calculations({}, {"r": "math.nan"})
    assert exc_info.value.status_code == 422
    assert "Non-finite" in exc_info.value.detail


def test_eval_later_expression_references_earlier() -> None:
    result = _eval_calculations(
        {"x": 5},
        {"doubled": "values['x'] * 2", "quadrupled": "doubled * 2"},
    )
    assert result["quadrupled"] == 20


def test_eval_empty_calculations_returns_empty() -> None:
    assert _eval_calculations({"x": 1}, {}) == {}


def test_eval_ternary_expression() -> None:
    result = _eval_calculations(
        {"flag": 1},
        {"label": "100 if values['flag'] == 1 else 0"},
    )
    assert result["label"] == 100
