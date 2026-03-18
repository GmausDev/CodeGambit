"""Adversarial mode prompt templates.

Evaluates how well a developer identified and fixed bugs in intentionally buggy code.
"""

from app.models.challenge import Challenge


def evaluate_fixes_prompt(
    challenge: Challenge,
    original_buggy_code: str,
    user_code: str,
    execution_result: dict,
) -> tuple[str, str]:
    """Build system + user prompt for evaluating adversarial bug fixes.

    Returns (system_prompt, user_prompt).
    """
    system = (
        "You are an expert code reviewer evaluating a developer's ability to find "
        "and fix bugs in intentionally buggy code. Compare the original buggy code "
        "with the developer's fixed version. Assess which bugs were found, "
        "the quality of each fix, and whether any new bugs were introduced.\n\n"
        "You MUST respond with valid JSON matching this schema:\n"
        "{\n"
        '  "bugs_analysis": [\n'
        "    {\n"
        '      "bug_description": "string — what the bug was",\n'
        '      "found": true,\n'
        '      "fix_quality": "excellent | good | partial | incorrect",\n'
        '      "fix_explanation": "string"\n'
        "    }\n"
        "  ],\n"
        '  "bugs_found": 0,\n'
        '  "bugs_total": 0,\n'
        '  "new_bugs_introduced": ["string — description of any new bugs"],\n'
        '  "overall_score": 0,\n'
        '  "architecture_score": 0,\n'
        '  "framework_depth_score": 0,\n'
        '  "complexity_mgmt_score": 0,\n'
        '  "feedback_summary": "string",\n'
        '  "strengths": ["string"],\n'
        '  "improvements": ["string"]\n'
        "}\n\n"
        "All scores are 0-100. bugs_found and bugs_total are integers. "
        "Score overall based on: bugs found (40%), fix quality (40%), no regressions (20%)."
    )

    rubric_text = ""
    if challenge.rubric:
        rubric_text = f"\n\nRubric criteria: {challenge.rubric}"

    exec_summary = _format_execution_result(execution_result)

    user = (
        f"## Challenge: {challenge.title}\n\n"
        f"{challenge.description}\n"
        f"- Domain: {challenge.domain}\n"
        f"- Difficulty: {challenge.difficulty}\n"
        f"{rubric_text}\n\n"
        f"## Original Buggy Code\n\n```\n{original_buggy_code}\n```\n\n"
        f"## Developer's Fixed Code\n\n```\n{user_code}\n```\n\n"
        f"## Execution Result (of fixed code)\n\n{exec_summary}\n\n"
        "Analyze the diff between original and fixed code. "
        "Identify all bugs in the original, determine which were found and fixed, "
        "and evaluate fix quality."
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
