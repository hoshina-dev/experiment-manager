"""Pydantic models for request validation and response serialisation."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

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
    type: str
    label: str
    description: str | None = None
    required: bool = False


class FormDoc(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str
    description: str | None = None
    questions: list[FormQuestion]


class Calculation(BaseModel):
    model_config = ConfigDict(extra="allow")

    formula: str
    result: Any = None


class ExperimentTemplateSummary(BaseModel):
    id: UUID
    lineage_id: UUID
    name: str
    description: str | None = None
    version: int
    is_current: bool


class ExperimentTemplatesResponse(BaseModel):
    sample_id: UUID
    experiments: list[ExperimentTemplateSummary]


class ExperimentTemplateHistoryResponse(BaseModel):
    lineage_id: UUID
    versions: list[ExperimentTemplateSummary]


class ExperimentTemplateDetail(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: UUID
    lineage_id: UUID
    name: str
    description: str | None = None
    version: int
    is_current: bool


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

    name: str = Field(min_length=1)
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

    name: str = Field(min_length=1)
    description: str | None = None


# ---------------------------------------------------------------------------
# Analysis template (create / update)
# ---------------------------------------------------------------------------


_PROXIMATE_EXAMPLE: dict[str, Any] = {
    "name": "Proximate Analysis",
    "description": "Determine moisture, ash, volatile matter, and fixed carbon content",
    "clientForm": {
        "name": "Client Intake",
        "questions": [],
    },
    "labForm": {
        "name": "Proximate Analysis Form",
        "description": "Record masses at each stage of the proximate analysis procedure.",
        "questions": [
            {
                "id": "crucible_mass",
                "type": "number",
                "label": "Crucible mass (g)",
                "required": True,
                "config": {"min": 0, "max": 200, "step": 0.001, "default": 20.0},
            },
            {
                "id": "sample_mass",
                "type": "number",
                "label": "Sample mass (g)",
                "required": True,
                "config": {"min": 0, "max": 10, "step": 0.001, "default": 1.0},
            },
            {
                "id": "mass_after_moisture",
                "type": "number",
                "label": "Mass after moisture drying at 105°C (g)",
                "required": True,
                "config": {"min": 0, "max": 200, "step": 0.001, "default": 20.8},
            },
            {
                "id": "mass_after_volatile",
                "type": "number",
                "label": "Mass after volatile matter removal at 900°C (g)",
                "required": True,
                "config": {"min": 0, "max": 200, "step": 0.001, "default": 20.5},
            },
            {
                "id": "mass_after_ash",
                "type": "number",
                "label": "Mass after ashing at 750°C (g)",
                "required": True,
                "config": {"min": 0, "max": 200, "step": 0.001, "default": 20.1},
            },
        ],
    },
    "calculations": {
        "moisture_loss": {
            "formula": "values['crucible_mass'] + values['sample_mass'] - values['mass_after_moisture']",
        },
        "volatile_loss": {
            "formula": "values['mass_after_moisture'] - values['mass_after_volatile']",
        },
        "ash_mass": {
            "formula": "values['mass_after_ash'] - values['crucible_mass']",
        },
        "moisture_pct": {
            "formula": "round(1000 * moisture_loss / values['sample_mass']) / 10",
        },
        "volatile_pct": {
            "formula": "round(1000 * volatile_loss / values['sample_mass']) / 10",
        },
        "ash_pct": {
            "formula": "round(1000 * ash_mass / values['sample_mass']) / 10",
        },
        "fixed_carbon_pct": {
            "formula": "round(10 * (100 - moisture_pct - volatile_pct - ash_pct)) / 10",
        },
    },
}


class ExperimentTemplateCreate(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": _PROXIMATE_EXAMPLE})

    name: str
    description: str | None = None
    clientForm: FormDoc
    labForm: FormDoc
    calculations: dict[str, Calculation]


class ExperimentTemplateUpdate(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": _PROXIMATE_EXAMPLE})

    name: str
    description: str | None = None
    clientForm: FormDoc
    labForm: FormDoc
    calculations: dict[str, Calculation]


# ---------------------------------------------------------------------------
# Experiment (create / read)
# ---------------------------------------------------------------------------


class ExperimentCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "exp_id": "7b1e39a5-86e2-433f-a194-397061316cb6",
                "sample_id": "a1b2c3d4-0002-0002-0002-000000000002",
                "lineage_id": "dd949e81-22ea-46b0-aa04-c0c80d22a9a2",
            }
        }
    )

    exp_id: UUID
    sample_id: UUID
    lineage_id: UUID


_EXPERIMENT_UPDATE_EXAMPLE: dict[str, Any] = {
    "example": {
        "clientForm": {
            "name": "Client Intake",
            "questions": [],
        },
        "labForm": {
            "name": "Proximate Analysis Form",
            "questions": [
                {
                    "id": "crucible_mass",
                    "type": "number",
                    "label": "Crucible mass (g)",
                    "required": True,
                    "config": {"min": 0, "max": 200, "step": 0.001, "default": 20.0},
                },
                {
                    "id": "sample_mass",
                    "type": "number",
                    "label": "Sample mass (g)",
                    "required": True,
                    "config": {"min": 0, "max": 10, "step": 0.001, "default": 1.0},
                },
            ],
        },
        "calculations": {
            "moisture_loss": {
                "formula": "values['crucible_mass'] + values['sample_mass'] - values['mass_after_moisture']",
            },
        },
        "values": {
            "crucible_mass": 21.354,
            "sample_mass": 1.001,
            "mass_after_moisture": 22.247,
            "mass_after_volatile": 21.891,
            "mass_after_ash": 21.501,
        },
    }
}


class ExperimentUpdate(BaseModel):
    model_config = ConfigDict(json_schema_extra=_EXPERIMENT_UPDATE_EXAMPLE)

    clientForm: FormDoc
    labForm: FormDoc
    calculations: dict[str, Calculation]
    values: dict[str, Any] = Field(default_factory=dict)


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


# ---------------------------------------------------------------------------
# PDF template
# ---------------------------------------------------------------------------


class PdfTemplateBody(BaseModel):
    components: list[Any]


class PdfTemplateResponse(BaseModel):
    template_id: UUID
    is_current: bool
    components: list[Any]
    updated_at: datetime


class ReportStatusResponse(BaseModel):
    status: str


class ReportDownloadResponse(BaseModel):
    url: str
    expires_in: int
