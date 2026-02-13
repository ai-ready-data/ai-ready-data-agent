"""Interactive survey prompts using questionary.

When ``--survey -i`` are used together and no ``--survey-answers`` file is
provided, this module prompts the user for each question one-by-one in the
terminal.
"""

from __future__ import annotations

from typing import Any, Dict, List


# Factor display names for Rich styled output
_FACTOR_LABELS = {
    "clean": "Clean",
    "contextual": "Contextual",
    "consumable": "Consumable",
    "current": "Current",
    "correlated": "Correlated",
    "compliant": "Compliant",
}


def _requirement_label(requirement: str) -> str:
    """Turn ``'validation_at_ingestion'`` into ``'Validation at Ingestion'``."""
    return requirement.replace("_", " ").title()


def interactive_survey(questions: List[Dict[str, Any]]) -> Dict[str, str]:
    """Prompt the user for each survey question interactively.

    Parameters
    ----------
    questions:
        List of question dicts as returned by ``questions_loader``.
        Each has ``factor``, ``requirement``, ``question``, and ``rubric``.

    Returns
    -------
    dict
        Mapping of ``"factor.requirement"`` to the user's answer string.
    """
    import questionary
    from agent.ui.console import get_console

    console = get_console()
    answers = {}  # type: Dict[str, str]

    console.print()
    console.print("[header]Survey Questions[/header]")
    console.print("[muted]Answer each question below. Press Ctrl-C to abort.[/muted]")
    console.print()

    for i, q in enumerate(questions, 1):
        factor = q.get("factor", "")
        requirement = q.get("requirement", "")
        question_text = q.get("question", "")
        rubric = q.get("rubric") or {}
        rubric_type = rubric.get("type", "")
        pass_if = rubric.get("pass_if")

        factor_label = _FACTOR_LABELS.get(factor, factor.title())
        req_label = _requirement_label(requirement)

        # Show factor context
        style = "factor.%s" % factor if factor in _FACTOR_LABELS else "info"
        console.print(
            "[%s]%d. [%s] %s[/%s]" % (style, i, factor_label, req_label, style)
        )
        console.print("   %s" % question_text)

        key = "%s.%s" % (factor, requirement)

        if rubric_type == "yes_no":
            result = questionary.confirm(
                "  Your answer", default=False
            ).ask()
            # result is None if user aborts (Ctrl-C)
            if result is None:
                answers[key] = "no"
            else:
                answers[key] = "yes" if result else "no"
        elif rubric_type == "choice" and isinstance(pass_if, list) and pass_if:
            result = questionary.select(
                "  Your answer",
                choices=[str(c) for c in pass_if],
            ).ask()
            if result is None:
                answers[key] = str(pass_if[0])
            else:
                answers[key] = str(result)
        else:
            result = questionary.text("  Your answer").ask()
            answers[key] = str(result) if result else ""

        console.print()

    console.print("[pass]✓[/pass] Survey complete.")
    console.print()
    return answers

