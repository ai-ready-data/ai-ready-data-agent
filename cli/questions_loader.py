"""Load question-based requirements. Questions are resolved per suite/platform."""

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# Per-suite questions: agent/suites/questions/{suite_name}.yaml; fallback default.yaml
_SUITES_QUESTIONS_DIR = Path(__file__).parent / "suites" / "questions"
_LEGACY_REGISTRY = Path(__file__).parent / "questions_registry.yaml"


def _parse_questions_list(raw: Any, factor_filter: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Parse YAML list of question items into list of question defs."""
    if not isinstance(raw, list):
        return []
    out: List[Dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        factor = item.get("factor")
        requirement = item.get("requirement")
        question = item.get("question")
        if not factor or not requirement or not question:
            continue
        if factor_filter and factor not in factor_filter:
            continue
        out.append({
            "factor": str(factor),
            "requirement": str(requirement),
            "question": str(question),
            "rubric": item.get("rubric"),
            "accepts_file": item.get("accepts_file", False),
            "file_types": item.get("file_types"),
            "file_evaluator": item.get("file_evaluator"),
        })
    return out


def get_suite_questions(
    suite_name: str,
    *,
    factor_filter: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Load questions for the given suite. Resolution order:
    1. agent/suites/questions/{suite_name}.yaml if it exists
    2. else agent/suites/questions/default.yaml
    Returns list of question defs (factor, requirement, question, rubric, ...). Empty if no file found.
    """
    suite_file = _SUITES_QUESTIONS_DIR / f"{suite_name}.yaml"
    default_file = _SUITES_QUESTIONS_DIR / "default.yaml"
    path = suite_file if suite_file.exists() else default_file
    if not path.exists():
        return []
    raw = yaml.safe_load(path.read_text())
    return _parse_questions_list(raw, factor_filter=factor_filter)


def load_questions(
    path: Optional[Path] = None,
    *,
    factor_filter: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Load question definitions from an explicit YAML path. For suite-based loading use get_suite_questions(suite_name).
    path: when None, tries agent/suites/questions/default.yaml then legacy questions_registry.yaml.
    """
    p = path
    if p is None:
        p = _SUITES_QUESTIONS_DIR / "default.yaml"
        if not p.exists():
            p = _LEGACY_REGISTRY
    if not p.exists():
        return []
    raw = yaml.safe_load(p.read_text())
    return _parse_questions_list(raw, factor_filter=factor_filter)
