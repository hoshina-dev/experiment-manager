"""Read-only repository that loads sample and analysis data from JSON files."""

import json
from pathlib import Path

from app.models import AnalysisTemplate, SampleSummary

_DATA_DIR = Path(__file__).parent.parent.parent / "data"


def list_samples() -> list[SampleSummary]:
    raw = json.loads((_DATA_DIR / "samples.json").read_text())
    return [SampleSummary(**item) for item in raw]


def get_sample(sample_id: str) -> SampleSummary | None:
    for sample in list_samples():
        if sample.id == sample_id:
            return sample
    return None


def list_analyses(sample_id: str) -> list[AnalysisTemplate]:
    sample_dir = _DATA_DIR / sample_id
    if not sample_dir.is_dir():
        return []
    return [
        AnalysisTemplate(**json.loads(path.read_text()))
        for path in sorted(sample_dir.glob("*.json"))
    ]


def get_analysis(sample_id: str, analysis_id: str) -> AnalysisTemplate | None:
    for analysis in list_analyses(sample_id):
        if analysis.id == analysis_id:
            return analysis
    return None
