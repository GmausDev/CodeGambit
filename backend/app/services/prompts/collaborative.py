"""Collaborative mode prompt templates.

Evaluates a developer's step-by-step guided implementation.
"""

from app.models.challenge import Challenge


def evaluate_step_prompt(
    challenge: Challenge,
    step_info: dict,
    step_code: str,
    execution_result: dict,
) -> tuple[str, str]:
    """Build system + user prompt for evaluating a single collaborative step.

    Returns (system_prompt, user_prompt).
    """
    step_number = step_info.get("step_number", 1)
    step_description = step_info.get("description", "")
    step_requirements = step_info.get("requirements", [])

    system = (
        "You are an expert code reviewer evaluating one step of a guided, "
        "collaborative coding exercise. Focus on whether the developer met the "
        "step's requirements and whether their incremental approach is sound.\n\n"
        "You MUST respond with valid JSON matching this schema:\n"
        "{\n"
        '  "step_score": 0,\n'
        '  "requirements_met": ["string — requirement that was met"],\n'
        '  "requirements_missed": ["string — requirement that was missed"],\n'
        '  "code_quality_notes": "string",\n'
        '  "suggestion": "string — hint or guidance for next step"\n'
        "}\n\n"
        "step_score is 0-100."
    )

    reqs_text = ""
    if step_requirements:
        reqs_text = "\n\nStep requirements:\n" + "\n".join(
            f"- {r}" for r in step_requirements
        )

    exec_summary = _format_execution_result(execution_result)

    user = (
        f"## Challenge: {challenge.title}\n\n"
        f"{challenge.description}\n\n"
        f"## Step {step_number}: {step_description}\n"
        f"{reqs_text}\n\n"
        f"## Developer's Code for This Step\n\n```\n{step_code}\n```\n\n"
        f"## Execution Result\n\n{exec_summary}\n\n"
        f"Evaluate whether step {step_number} requirements are met and the code quality."
    )

    return system, user


def evaluate_final_prompt(
    challenge: Challenge,
    all_steps: list[dict],
    final_code: str,
    execution_result: dict,
) -> tuple[str, str]:
    """Build system + user prompt for holistic evaluation of collaborative submission.

    The final score weights: 60% step progression, 40% final solution.

    Returns (system_prompt, user_prompt).
    """
    system = (
        "You are an expert code reviewer providing a holistic evaluation of a "
        "developer's collaborative coding exercise. The developer built their "
        "solution step-by-step with guidance. Evaluate both their incremental "
        "progress and the final result.\n\n"
        "You MUST respond with valid JSON matching this schema:\n"
        "{\n"
        '  "step_progression_score": 0,\n'
        '  "final_solution_score": 0,\n'
        '  "overall_score": 0,\n'
        '  "architecture_score": 0,\n'
        '  "framework_depth_score": 0,\n'
        '  "complexity_mgmt_score": 0,\n'
        '  "feedback_summary": "string",\n'
        '  "strengths": ["string"],\n'
        '  "improvements": ["string"]\n'
        "}\n\n"
        "All scores are 0-100. overall_score should be calculated as: "
        "60% * step_progression_score + 40% * final_solution_score."
    )

    rubric_text = ""
    if challenge.rubric:
        rubric_text = f"\n\nRubric criteria: {challenge.rubric}"

    steps_text = ""
    for step in all_steps:
        step_num = step.get("step_number", "?")
        step_score = step.get("step_score", "not evaluated")
        step_code = step.get("step_code", "")[:500]
        steps_text += (
            f"\n### Step {step_num} (score: {step_score})\n"
            f"```\n{step_code}\n```\n"
        )

    exec_summary = _format_execution_result(execution_result)

    user = (
        f"## Challenge: {challenge.title}\n\n"
        f"{challenge.description}\n"
        f"- Domain: {challenge.domain}\n"
        f"- Difficulty: {challenge.difficulty}\n"
        f"{rubric_text}\n\n"
        f"## Step-by-Step Progression\n{steps_text}\n\n"
        f"## Final Code\n\n```\n{final_code}\n```\n\n"
        f"## Final Execution Result\n\n{exec_summary}\n\n"
        "Provide a holistic evaluation. Weight: 60% step progression, 40% final solution."
    )

    return system, user


def _format_execution_result(execution_result: dict) -> str:
    if not execution_result:
        return "No execution result available."
    parts = []
    if execution_result.get("exit_code") is not None:
        parts.append(f"Exit code: {execution_result['exit_code']}")
    if execution_result.get("stdout"):
        parts.append(f"Stdout:\n```\n{execution_result['stdout'][:2000]}\n```")
    if execution_result.get("stderr"):
        parts.append(f"Stderr:\n```\n{execution_result['stderr'][:2000]}\n```")
    if execution_result.get("execution_time_ms") is not None:
        parts.append(f"Execution time: {execution_result['execution_time_ms']}ms")
    return "\n".join(parts) if parts else "Execution completed with no output."
