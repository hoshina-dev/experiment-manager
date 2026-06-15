"""Tests for calculation_service — translation, input extraction, and eval."""

import pytest

from app.services.calculation_service import (
    _eval_calculations,
    _extract_inputs,
    _translate,
)
from fastapi import HTTPException


# ---------------------------------------------------------------------------
# _translate
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("js, expected", [
    # Explicit overrides: JS Math methods → Python builtins
    ("Math.round(x)",  "round(x)"),
    ("Math.abs(x)",    "abs(x)"),
    ("Math.min(a, b)", "min(a, b)"),
    ("Math.max(a, b)", "max(a, b)"),
    # Explicit overrides: casing differences
    ("Math.PI",        "math.pi"),
    ("Math.E",         "math.e"),
    # Catch-all: any other Math.* → math.*
    ("Math.sqrt(x)",   "math.sqrt(x)"),
    ("Math.floor(x)",  "math.floor(x)"),
    ("Math.ceil(x)",   "math.ceil(x)"),
    ("Math.log(x)",    "math.log(x)"),
    ("Math.sin(x)",    "math.sin(x)"),
    # JS operators and literals
    ("a === b",        "a == b"),
    ("a !== b",        "a != b"),
    ("null",           "None"),
    ("undefined",      "None"),
    ("true",           "True"),
    ("false",          "False"),
])
def test_translate_rules(js: str, expected: str) -> None:
    assert _translate(js) == expected


def test_translate_ternary() -> None:
    assert _translate("x === 1 ? 1 : 0") == "(1) if (x == 1) else (0)"


def test_translate_combined() -> None:
    result = _translate("Math.round(1000 * (a / b)) / 10")
    assert result == "round(1000 * (a / b)) / 10"


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
            "moisture_pct": "Math.round(1000 * (sample_error / sample_mass)) / 10",
        },
    )
    assert result["sample_mass"] == 20.0
    assert result["sample_error"] == 5.0
    assert result["moisture_pct"] == 25.0


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
    result = _eval_calculations({"flag": 1}, {"label": "flag === 1 ? 100 : 0"})
    assert result["label"] == 100
