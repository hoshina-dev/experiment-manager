"""Tests for calculation_service — input extraction and eval."""

import pytest

from app.services.calculation_service import _eval_calculations, _extract_inputs
from fastapi import HTTPException


# ---------------------------------------------------------------------------
# _extract_inputs
# ---------------------------------------------------------------------------

def test_extract_inputs_uses_value_over_default() -> None:
    state = {"workerForm": {"questions": [
        {"id": "x", "value": 5.0, "default": 1.0}
    ]}}
    assert _extract_inputs(state) == {"x": 5.0}


def test_extract_inputs_falls_back_to_default() -> None:
    state = {"workerForm": {"questions": [
        {"id": "x", "default": 3.0}
    ]}}
    assert _extract_inputs(state) == {"x": 3.0}


def test_extract_inputs_falls_back_to_config_default() -> None:
    state = {"workerForm": {"questions": [
        {"id": "x", "type": "number", "config": {"default": 3.0}}
    ]}}
    assert _extract_inputs(state) == {"x": 3.0}


def test_extract_inputs_skips_missing_id() -> None:
    state = {"workerForm": {"questions": [{"default": 1.0}]}}
    assert _extract_inputs(state) == {}


def test_extract_inputs_skips_none_value() -> None:
    state = {"workerForm": {"questions": [{"id": "x"}]}}
    assert _extract_inputs(state) == {}


def test_extract_inputs_no_worker_form() -> None:
    assert _extract_inputs({}) == {}


# ---------------------------------------------------------------------------
# _eval_calculations
# ---------------------------------------------------------------------------

def test_eval_basic_arithmetic() -> None:
    result = _eval_calculations({"a": 10, "b": 3}, {"c": "a + b"})
    assert result == {"c": 13}


def test_eval_chained_expressions() -> None:
    result = _eval_calculations(
        {"tray_mass": 100.0, "tray_sam": 120.0, "tray_ctrl": 115.0},
        {
            "sample_mass":  "tray_sam - tray_mass",
            "sample_error": "tray_sam - tray_ctrl",
            "moisture_pct": "round(1000 * (sample_error / sample_mass)) / 10",
        },
    )
    assert result["sample_mass"] == 20.0
    assert result["sample_error"] == 5.0
    assert result["moisture_pct"] == 25.0


def test_eval_math_module_available() -> None:
    result = _eval_calculations({"x": 4.0}, {"r": "math.sqrt(x)"})
    assert result["r"] == 2.0


def test_eval_raises_422_on_division_by_zero() -> None:
    with pytest.raises(HTTPException) as exc_info:
        _eval_calculations({"a": 1, "b": 0}, {"r": "a / b"})
    assert exc_info.value.status_code == 422
    assert "Division by zero" in exc_info.value.detail
    assert "'r'" in exc_info.value.detail


def test_eval_raises_422_on_undefined_variable() -> None:
    with pytest.raises(HTTPException) as exc_info:
        _eval_calculations({}, {"r": "missing_var + 1"})
    assert exc_info.value.status_code == 422
    assert "Undefined variable" in exc_info.value.detail
    assert "'r'" in exc_info.value.detail


def test_eval_raises_422_on_dunder_injection() -> None:
    with pytest.raises(HTTPException) as exc_info:
        _eval_calculations({}, {"r": "().__class__.__bases__[0].__subclasses__()"})
    assert exc_info.value.status_code == 422
    assert "dunder" in exc_info.value.detail


def test_eval_raises_422_on_generic_error() -> None:
    with pytest.raises(HTTPException) as exc_info:
        _eval_calculations({}, {"r": "math.sqrt(-1)"})  # raises ValueError, not caught above
    assert exc_info.value.status_code == 422
    assert "Calculation error" in exc_info.value.detail
    assert "'r'" in exc_info.value.detail


def test_eval_raises_422_on_infinite_result() -> None:
    with pytest.raises(HTTPException) as exc_info:
        _eval_calculations({}, {"r": "math.nan"})  # nan is non-finite
    assert exc_info.value.status_code == 422
    assert "Non-finite" in exc_info.value.detail


def test_eval_later_expression_references_earlier() -> None:
    result = _eval_calculations({"x": 5}, {"doubled": "x * 2", "quadrupled": "doubled * 2"})
    assert result["quadrupled"] == 20


def test_eval_empty_calculations_returns_empty() -> None:
    assert _eval_calculations({"x": 1}, {}) == {}


def test_eval_ternary_expression() -> None:
    result = _eval_calculations({"flag": 1}, {"label": "100 if flag == 1 else 0"})
    assert result["label"] == 100
