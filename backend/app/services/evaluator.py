"""Claude AI evaluation service.

Routes submissions to mode-specific evaluation and returns structured scores.
Falls back to mock evaluation when ANTHROPIC_API_KEY is not configured.
"""

import json
import logging
import random
from dataclasses import dataclass

from app.config import Settings
from app.models.challenge import Challenge
from app.models.submission import Submission
from app.services.prompts.adversarial import evaluate_fixes_prompt
from app.services.prompts.collaborative import evaluate_final_prompt, evaluate_step_prompt
from app.services.prompts.socratic import evaluate_answers_prompt, generate_questions_prompt

logger = logging.getLogger(__name__)

EVAL_MODEL = "claude-sonnet-4-6"
HINT_MODEL = "claude-haiku-4-5-20251001"


@dataclass
class EvaluationResult:
    overall_score: int
    architecture_score: int
    framework_depth_score: int
    complexity_mgmt_score: int
    feedback_summary: str
    strengths: list[str]
    improvements: list[str]
    mode_specific_feedback: str | None
    raw_ai_response: dict | None
    model_used: str | None
    tokens_used: int | None


class ClaudeEvaluator:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = None
        if settings.ANTHROPIC_API_KEY:
            try:
                import anthropic

                self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
            except ImportError:
                logger.warning("anthropic package not installed; using mock mode")

    async def evaluate(
        self,
        challenge: Challenge,
        submission: Submission,
        execution_result: dict,
    ) -> EvaluationResult:
        """Route to mode-specific evaluation and return structured scores."""
        mode = submission.mode

        if mode == "socratic":
            return await self._evaluate_socratic_code(
                challenge, submission.code, execution_result
            )
        elif mode == "adversarial":
            original_code = challenge.starter_code or ""
            return await self._evaluate_adversarial(
                challenge, original_code, submission.code, execution_result
            )
        elif mode == "collaborative":
            return await self._evaluate_collaborative_final(
                challenge, [], submission.code, execution_result
            )
        else:
            return await self._evaluate_generic(
                challenge, submission.code, execution_result
            )

    async def generate_socratic_questions(
        self,
        challenge: Challenge,
        code: str,
        execution_result: dict,
    ) -> list[dict]:
        """Phase 1 of Socratic mode: generate probing questions."""
        system, user = generate_questions_prompt(challenge, code, execution_result)

        if not self.client:
            return _mock_socratic_questions()

        raw = await self._call_claude(system, user, model=EVAL_MODEL)
        parsed = _parse_json_response(raw)
        return parsed.get("questions", _mock_socratic_questions())

    async def evaluate_socratic_answers(
        self,
        challenge: Challenge,
        code: str,
        questions: list[dict],
        answers: list[str],
    ) -> EvaluationResult:
        """Phase 2 of Socratic mode: evaluate developer's answers."""
        system, user = evaluate_answers_prompt(challenge, code, questions, answers)

        if not self.client:
            return _mock_evaluation("socratic")

        raw = await self._call_claude(system, user, model=EVAL_MODEL)
        parsed = _parse_json_response(raw)
        return _result_from_parsed(parsed, raw, "socratic")

    async def evaluate_collaborative_step(
        self,
        challenge: Challenge,
        step_info: dict,
        step_code: str,
        execution_result: dict,
    ) -> dict:
        """Evaluate a single step in collaborative mode."""
        system, user = evaluate_step_prompt(challenge, step_info, step_code, execution_result)

        if not self.client:
            return _mock_step_evaluation()

        raw = await self._call_claude(system, user, model=EVAL_MODEL)
        return _parse_json_response(raw)

    # --- Internal evaluation methods ---

    async def _evaluate_socratic_code(
        self, challenge: Challenge, code: str, execution_result: dict
    ) -> EvaluationResult:
        """Evaluate Socratic submission code quality (before Q&A phase)."""
        system, user = generate_questions_prompt(challenge, code, execution_result)

        if not self.client:
            return _mock_evaluation("socratic")

        raw = await self._call_claude(system, user, model=EVAL_MODEL)
        parsed = _parse_json_response(raw)
        # For initial code evaluation, return a preliminary result
        return EvaluationResult(
            overall_score=parsed.get("overall_score", 65),
            architecture_score=parsed.get("architecture_score", 65),
            framework_depth_score=parsed.get("framework_depth_score", 65),
            complexity_mgmt_score=parsed.get("complexity_mgmt_score", 65),
            feedback_summary=parsed.get(
                "feedback_summary",
                "Socratic questions generated. Submit answers for full evaluation.",
            ),
            strengths=parsed.get("strengths", []),
            improvements=parsed.get("improvements", []),
            mode_specific_feedback="Awaiting Socratic Q&A for full evaluation.",
            raw_ai_response=parsed,
            model_used=EVAL_MODEL,
            tokens_used=None,
        )

    async def _evaluate_adversarial(
        self,
        challenge: Challenge,
        original_code: str,
        user_code: str,
        execution_result: dict,
    ) -> EvaluationResult:
        system, user = evaluate_fixes_prompt(
            challenge, original_code, user_code, execution_result
        )

        if not self.client:
            return _mock_evaluation("adversarial")

        raw = await self._call_claude(system, user, model=EVAL_MODEL)
        parsed = _parse_json_response(raw)
        bugs_found = parsed.get("bugs_found", 0)
        bugs_total = parsed.get("bugs_total", 0)
        mode_feedback = f"Bugs found: {bugs_found}/{bugs_total}"
        if parsed.get("new_bugs_introduced"):
            mode_feedback += f". New bugs introduced: {len(parsed['new_bugs_introduced'])}"
        return _result_from_parsed(parsed, raw, "adversarial", mode_feedback)

    async def _evaluate_collaborative_final(
        self,
        challenge: Challenge,
        all_steps: list[dict],
        final_code: str,
        execution_result: dict,
    ) -> EvaluationResult:
        system, user = evaluate_final_prompt(
            challenge, all_steps, final_code, execution_result
        )

        if not self.client:
            return _mock_evaluation("collaborative")

        raw = await self._call_claude(system, user, model=EVAL_MODEL)
        parsed = _parse_json_response(raw)
        step_score = parsed.get("step_progression_score", 0)
        final_score = parsed.get("final_solution_score", 0)
        mode_feedback = (
            f"Step progression: {step_score}/100, Final solution: {final_score}/100"
        )
        return _result_from_parsed(parsed, raw, "collaborative", mode_feedback)

    async def _evaluate_generic(
        self, challenge: Challenge, code: str, execution_result: dict
    ) -> EvaluationResult:
        """Fallback for unknown modes."""
        return _mock_evaluation("generic")

    async def _call_claude(
        self, system: str, user: str, model: str = EVAL_MODEL
    ) -> str:
        """Call Claude API asynchronously."""
        try:
            response = await self.client.messages.create(
                model=model,
                max_tokens=2048,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            return response.content[0].text
        except Exception as e:
            logger.error("Claude API call failed: %s", e)
            raise


# --- Helper functions ---


def _parse_json_response(raw: str) -> dict:
    """Parse JSON from Claude's response, handling markdown code blocks."""
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first and last lines (code fence markers)
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.warning("Failed to parse Claude response as JSON: %s...", text[:200])
        return {}


def _result_from_parsed(
    parsed: dict,
    raw: str | dict,
    mode: str,
    mode_feedback: str | None = None,
) -> EvaluationResult:
    return EvaluationResult(
        overall_score=parsed.get("overall_score", 60),
        architecture_score=parsed.get("architecture_score", 60),
        framework_depth_score=parsed.get("framework_depth_score", 60),
        complexity_mgmt_score=parsed.get("complexity_mgmt_score", 60),
        feedback_summary=parsed.get("feedback_summary", f"{mode} evaluation complete."),
        strengths=parsed.get("strengths", []),
        improvements=parsed.get("improvements", []),
        mode_specific_feedback=mode_feedback or parsed.get("mode_specific_feedback"),
        raw_ai_response=parsed,
        model_used=EVAL_MODEL,
        tokens_used=None,
    )


def _clamp_score(score: int) -> int:
    """Clamp a score to the 0-100 range."""
    return min(100, max(0, score))


def _mock_evaluation(mode: str) -> EvaluationResult:
    """Return reasonable mock evaluation when API key is not configured."""
    base = random.randint(60, 80)
    return EvaluationResult(
        overall_score=base,
        architecture_score=_clamp_score(base + random.randint(-10, 10)),
        framework_depth_score=_clamp_score(base + random.randint(-10, 10)),
        complexity_mgmt_score=_clamp_score(base + random.randint(-10, 10)),
        feedback_summary=(
            f"Mock evaluation ({mode} mode). "
            "Configure ANTHROPIC_API_KEY for real AI evaluation."
        ),
        strengths=["Code compiles and runs", "Reasonable structure"],
        improvements=["Consider edge cases", "Add error handling"],
        mode_specific_feedback=f"Mock {mode} mode feedback.",
        raw_ai_response={"mock": True, "mode": mode},
        model_used="mock",
        tokens_used=0,
    )


def _mock_socratic_questions() -> list[dict]:
    return [
        {
            "question": "What design pattern did you use and why?",
            "category": "architecture",
            "difficulty": "intermediate",
        },
        {
            "question": "How would your solution handle an empty input?",
            "category": "edge_cases",
            "difficulty": "basic",
        },
        {
            "question": "What are the time and space complexity trade-offs in your approach?",
            "category": "performance",
            "difficulty": "advanced",
        },
    ]


def _mock_step_evaluation() -> dict:
    score = random.randint(60, 85)
    return {
        "step_score": score,
        "requirements_met": ["Basic structure implemented"],
        "requirements_missed": [],
        "code_quality_notes": "Mock evaluation — configure API key for real feedback.",
        "suggestion": "Continue to the next step.",
    }
