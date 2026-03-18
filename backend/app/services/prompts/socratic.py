"""Socratic mode prompt templates.

Phase 1: Generate probing questions about the developer's code.
Phase 2: Evaluate the depth and accuracy of their answers.
"""

from app.models.challenge import Challenge


def generate_questions_prompt(
    challenge: Challenge, code: str, execution_result: dict
) -> tuple[str, str]:
    """Build system + user prompt for generating Socratic questions.

    Returns (system_prompt, user_prompt).
    """
    system = (
        "You are an expert code reviewer conducting a Socratic evaluation. "
        "Your goal is to generate probing questions that test whether the developer "
        "truly understands the design decisions, trade-offs, and implications of their code. "
        "Questions should range from architectural reasoning to edge-case awareness.\n\n"
        "You MUST respond with valid JSON matching this schema:\n"
        "{\n"
        '  "questions": [\n'
        "    {\n"
        '      "question": "string — the question to ask",\n'
        '      "category": "architecture | correctness | edge_cases | performance | trade_offs",\n'
        '      "difficulty": "basic | intermediate | advanced"\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        "Generate 3-5 questions. Ensure at least one question about architecture "
        "and one about edge cases or trade-offs."
    )

    rubric_text = ""
    if challenge.rubric:
        rubric_text = f"\n\nRubric criteria: {challenge.rubric}"

    concepts_text = ""
    if challenge.expected_concepts:
        concepts_text = f"\n\nExpected concepts: {', '.join(challenge.expected_concepts)}"

    exec_summary = _format_execution_result(execution_result)

    user = (
        f"## Challenge: {challenge.title}\n\n"
        f"{challenge.description}\n"
        f"- Domain: {challenge.domain}\n"
        f"- Difficulty: {challenge.difficulty}\n"
        f"{rubric_text}{concepts_text}\n\n"
        f"## Developer's Code\n\n```\n{code}\n```\n\n"
        f"## Execution Result\n\n{exec_summary}\n\n"
        "Generate probing Socratic questions about this submission."
    )

    return system, user


def evaluate_answers_prompt(
    challenge: Challenge,
    code: str,
    questions: list[dict],
    answers: list[str],
) -> tuple[str, str]:
    """Build system + user prompt for evaluating Socratic answers.

    Returns (system_prompt, user_prompt).
    """
    system = (
        "You are an expert code reviewer evaluating a developer's understanding "
        "of their own code through their answers to Socratic questions. "
        "Score each answer on depth of understanding and technical accuracy.\n\n"
        "You MUST respond with valid JSON matching this schema:\n"
        "{\n"
        '  "answer_evaluations": [\n'
        "    {\n"
        '      "question_index": 0,\n'
        '      "depth_score": 0,\n'
        '      "accuracy_score": 0,\n'
        '      "feedback": "string"\n'
        "    }\n"
        "  ],\n"
        '  "overall_score": 0,\n'
        '  "architecture_score": 0,\n'
        '  "framework_depth_score": 0,\n'
        '  "complexity_mgmt_score": 0,\n'
        '  "feedback_summary": "string",\n'
        '  "strengths": ["string"],\n'
        '  "improvements": ["string"]\n'
        "}\n\n"
        "All scores are 0-100. depth_score and accuracy_score per answer are 0-100."
    )

    qa_text = ""
    for i, q in enumerate(questions):
        q_text = q.get("question", q) if isinstance(q, dict) else q
        a_text = answers[i] if i < len(answers) else "(no answer provided)"
        qa_text += f"\n### Q{i + 1}: {q_text}\n**Answer:** {a_text}\n"

    user = (
        f"## Challenge: {challenge.title}\n\n"
        f"{challenge.description}\n\n"
        f"## Developer's Code\n\n```\n{code}\n```\n\n"
        f"## Questions & Answers\n{qa_text}\n\n"
        "Evaluate the depth and accuracy of each answer, then provide overall scores."
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
