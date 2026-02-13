"""Survey step: run question-based requirements and produce question_results for the report."""

from typing import Any, Dict, List, Optional

from agent.questions_loader import load_questions


def _apply_rubric(rubric: Optional[Dict], answer: Any) -> tuple[bool, bool, bool]:
    """Return (l1_pass, l2_pass, l3_pass) from rubric. Default True when no rubric."""
    if not rubric:
        return (True, True, True)
    t = (rubric or {}).get("type") or "yes_no"
    pass_if = (rubric or {}).get("pass_if")
    if t == "yes_no":
        ok = str(answer).strip().lower() in ("yes", "y", "true", "1")
        return (ok, ok, ok)
    if t == "choice" and isinstance(pass_if, list):
        ok = str(answer).strip().lower() in [str(x).lower() for x in pass_if]
        return (ok, ok, ok)
    return (True, True, True)


def run_survey(
    questions: Optional[List[Dict[str, Any]]] = None,
    answers: Optional[Dict[str, str]] = None,
    *,
    questions_path: Optional[Any] = None,
    interactive: bool = False,
) -> List[Dict[str, Any]]:
    """
    Run survey: for each question, look up answer (keyed by requirement or "factor.requirement"), apply rubric, produce one result row.
    questions: list from load_questions(); when None, load from default registry.
    answers: dict mapping requirement key (or "factor.requirement") to user answer string. Missing key => answer "—" and pass from rubric or True.
    questions_path: optional Path to YAML; used when questions is None.
    interactive: when True and answers is empty, prompt the user interactively.
    Returns list of { factor, requirement, question_text, answer, l1_pass, l2_pass, l3_pass }.
    """
    if questions is None:
        from pathlib import Path
        path = Path(questions_path) if questions_path else None
        questions = load_questions(path)
    if not questions:
        return []
    if interactive and not answers:
        from agent.ui.console import is_interactive
        if is_interactive():
            from agent.ui.survey import interactive_survey
            answers = interactive_survey(questions)
    answers = answers or {}
    results: List[Dict[str, Any]] = []
    for q in questions:
        factor = q.get("factor", "")
        req = q.get("requirement", "")
        key = f"{factor}.{req}"
        answer = answers.get(key) or answers.get(req)
        if answer is None:
            answer = "—"
        l1, l2, l3 = _apply_rubric(q.get("rubric"), answer)
        results.append({
            "factor": factor,
            "requirement": req,
            "question_text": q.get("question", ""),
            "answer": answer,
            "l1_pass": l1,
            "l2_pass": l2,
            "l3_pass": l3,
        })
    return results
