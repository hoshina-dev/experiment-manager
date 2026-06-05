"""Pydantic models for request validation and response serialisation."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

# ---------------------------------------------------------------------------
# Sample
# ---------------------------------------------------------------------------


class SampleSummary(BaseModel):
    id: UUID
    name: str
    description: str | None = None


class SamplesListResponse(BaseModel):
    samples: list[SampleSummary]


# ---------------------------------------------------------------------------
# Experiment template
# ---------------------------------------------------------------------------


class FormQuestion(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    label: str
    description: str | None = None
    required: bool = False
    type: str
    options: list[dict[str, Any]] | None = None
    placeholder: str | None = None


class WorkerForm(BaseModel):
    title: str | None = None
    description: str | None = None
    questions: list[FormQuestion]


class ExperimentTemplateSummary(BaseModel):
    id: UUID
    name: str
    description: str | None = None


class ExperimentTemplatesResponse(BaseModel):
    sample_id: UUID
    experiments: list[ExperimentTemplateSummary]


class ExperimentTemplateDetail(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: UUID


# ---------------------------------------------------------------------------
# Sample (create / update)
# ---------------------------------------------------------------------------


class SampleCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Coal",
                "description": "Raw coal samples for proximate and calorific analysis",
            }
        }
    )

    name: str
    description: str | None = None


class SampleUpdate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Coal",
                "description": "Raw coal samples for proximate and calorific analysis",
            }
        }
    )

    name: str
    description: str | None = None


# ---------------------------------------------------------------------------
# Analysis template (create / update)
# ---------------------------------------------------------------------------


_PROXIMATE_EXAMPLE: dict[str, Any] = {
    "title": "Proximate Analysis",
    "description": "Determine moisture, ash, volatile matter, and fixed carbon content",
    "userForm": None,
    "workerForm": {
        "title": "Proximate Analysis Form",
        "description": "Record masses at each stage of the proximate analysis procedure.",
        "questions": [
            {"id": "crucible_mass",       "type": "number", "label": "Crucible mass (g)",                               "required": True,  "min": 0, "max": 200, "step": 0.001, "default": 20.0},
            {"id": "sample_mass",         "type": "number", "label": "Sample mass (g)",                                "required": True,  "min": 0, "max": 10,  "step": 0.001, "default": 1.0},
            {"id": "mass_after_moisture", "type": "number", "label": "Mass after moisture drying at 105°C (g)",        "required": True,  "min": 0, "max": 200, "step": 0.001, "default": 20.8},
            {"id": "mass_after_volatile", "type": "number", "label": "Mass after volatile matter removal at 900°C (g)","required": True,  "min": 0, "max": 200, "step": 0.001, "default": 20.5},
            {"id": "mass_after_ash",      "type": "number", "label": "Mass after ashing at 750°C (g)",                 "required": True,  "min": 0, "max": 200, "step": 0.001, "default": 20.1},
        ],
    },
    "calculations": {
        "moisture_loss":    "crucible_mass + sample_mass - mass_after_moisture",
        "volatile_loss":    "mass_after_moisture - mass_after_volatile",
        "ash_mass":         "mass_after_ash - crucible_mass",
        "moisture_pct":     "Math.round(1000 * moisture_loss / sample_mass) / 10",
        "volatile_pct":     "Math.round(1000 * volatile_loss / sample_mass) / 10",
        "ash_pct":          "Math.round(1000 * ash_mass / sample_mass) / 10",
        "fixed_carbon_pct": "Math.round(10 * (100 - moisture_pct - volatile_pct - ash_pct)) / 10",
    },
    "template": "Moisture = {{moisture_pct}}% | Volatile Matter = {{volatile_pct}}% | Ash = {{ash_pct}}% | Fixed Carbon = {{fixed_carbon_pct}}%",
}


class ExperimentTemplateCreate(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": _PROXIMATE_EXAMPLE})

    title: str
    description: str | None = None
    userForm: dict | None = None
    workerForm: WorkerForm
    calculations: dict[str, str]
    template: str


class ExperimentTemplateUpdate(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": _PROXIMATE_EXAMPLE})

    title: str
    description: str | None = None
    userForm: dict | None = None
    workerForm: WorkerForm
    calculations: dict[str, str]
    template: str


# ---------------------------------------------------------------------------
# Experiment (create / read)
# ---------------------------------------------------------------------------


class ExperimentCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "exp_id": "7b1e39a5-86e2-433f-a194-397061316cb6",
                "sample_id": "a1b2c3d4-0002-0002-0002-000000000002",
                "template_id": "dd949e81-22ea-46b0-aa04-c0c80d22a9a2",
            }
        }
    )

    exp_id: UUID
    sample_id: UUID
    template_id: UUID


_EXPERIMENT_UPDATE_EXAMPLE: dict[str, Any] = {
    "example": {
        "workerForm": {
            "title": "Proximate Analysis Form",
            "description": "Record masses at each stage of the proximate analysis procedure.",
            "questions": [
                {"id": "crucible_mass",       "type": "number", "label": "Crucible mass (g)",                               "required": True,  "min": 0, "max": 200, "step": 0.001, "default": 20.0,  "value": 21.354},
                {"id": "sample_mass",         "type": "number", "label": "Sample mass (g)",                                "required": True,  "min": 0, "max": 10,  "step": 0.001, "default": 1.0,   "value": 1.001},
                {"id": "mass_after_moisture", "type": "number", "label": "Mass after moisture drying at 105°C (g)",        "required": True,  "min": 0, "max": 200, "step": 0.001, "default": 20.8,  "value": 22.247},
                {"id": "mass_after_volatile", "type": "number", "label": "Mass after volatile matter removal at 900°C (g)","required": True,  "min": 0, "max": 200, "step": 0.001, "default": 20.5,  "value": 21.891},
                {"id": "mass_after_ash",      "type": "number", "label": "Mass after ashing at 750°C (g)",                 "required": True,  "min": 0, "max": 200, "step": 0.001, "default": 20.1,  "value": 21.501},
            ],
        },
        "calculations": {
            "moisture_loss":    "crucible_mass + sample_mass - mass_after_moisture",
            "volatile_loss":    "mass_after_moisture - mass_after_volatile",
            "ash_mass":         "mass_after_ash - crucible_mass",
            "moisture_pct":     "Math.round(1000 * moisture_loss / sample_mass) / 10",
            "volatile_pct":     "Math.round(1000 * volatile_loss / sample_mass) / 10",
            "ash_pct":          "Math.round(1000 * ash_mass / sample_mass) / 10",
            "fixed_carbon_pct": "Math.round(10 * (100 - moisture_pct - volatile_pct - ash_pct)) / 10",
        },
        "template": "Moisture = {{moisture_pct}}% | Volatile Matter = {{volatile_pct}}% | Ash = {{ash_pct}}% | Fixed Carbon = {{fixed_carbon_pct}}%",
        "userForm": None,
    }
}


class ExperimentUpdate(BaseModel):
    model_config = ConfigDict(json_schema_extra=_EXPERIMENT_UPDATE_EXAMPLE)

    workerForm: WorkerForm
    calculations: dict[str, str]
    template: str
    userForm: dict | None = None


class ExperimentSummary(BaseModel):
    id: UUID
    sample_id: UUID
    template_id: UUID
    report_status: str | None = None
    created_at: datetime


class ExperimentDetail(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: UUID
    sample_id: UUID
    template_id: UUID
    report_status: str | None = None
    report_r2_key: str | None = None
    report_generated_at: datetime | None = None
    created_at: datetime


class ExperimentsListResponse(BaseModel):
    experiments: list[ExperimentSummary]


class ReportStatusResponse(BaseModel):
    status: str


class ReportDownloadResponse(BaseModel):
    url: str
    expires_in: int
