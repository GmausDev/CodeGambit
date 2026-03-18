"""Submissions API router.

POST /api/submissions          — create submission, trigger async pipeline
GET  /api/submissions/{id}     — get submission with evaluation (polling)
POST /api/submissions/{id}/socratic-answers — submit answers to Socratic questions
"""

import asyncio
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session, get_session
from app.models.challenge import Challenge
from app.models.elo_history import SocraticAnswers
from app.models.evaluation import Evaluation
from app.models.submission import Submission
from app.models.user import UserProfile
from app.schemas.evaluation import EvaluationOut
from app.schemas.submission import SubmissionCreate, SubmissionOut
from app.services.evaluator import ClaudeEvaluator

logger = logging.getLogger(__name__)

router = APIRouter()


class SubmissionWithEvaluation(BaseModel):
    submission: SubmissionOut
    evaluation: EvaluationOut | None = None
    socratic_questions: list[dict] | None = None


class SocraticAnswersRequest(BaseModel):
    answers: list[str]


class SocraticAnswersResponse(BaseModel):
    submission_id: int
    status: str
    message: str


# --- Endpoints ---


@router.post("/submissions", response_model=SubmissionOut, status_code=201)
async def create_submission(
    body: SubmissionCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    """Create a submission and trigger the async evaluation pipeline."""
    # Validate challenge exists
    result = await session.execute(
        select(Challenge).where(Challenge.id == body.challenge_id)
    )
    challenge = result.scalar_one_or_none()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    # Validate mode
    if body.mode not in ("socratic", "adversarial", "collaborative"):
        raise HTTPException(
            status_code=400,
            detail="Mode must be one of: socratic, adversarial, collaborative",
        )

    # Create submission
    submission = Submission(
        challenge_id=body.challenge_id,
        code=body.code,
        mode=body.mode,
        status="pending",
    )
    session.add(submission)
    await session.commit()
    await session.refresh(submission)

    # Trigger async pipeline
    background_tasks.add_task(run_evaluation_pipeline, submission.id)

    return submission


@router.get("/submissions/{submission_id}", response_model=SubmissionWithEvaluation)
async def get_submission(
    submission_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get submission with its evaluation (for polling)."""
    result = await session.execute(
        select(Submission).where(Submission.id == submission_id)
    )
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    # Get evaluation if exists
    eval_result = await session.execute(
        select(Evaluation).where(Evaluation.submission_id == submission_id)
    )
    evaluation = eval_result.scalar_one_or_none()

    # Get Socratic questions if applicable
    socratic_questions = None
    if submission.mode == "socratic":
        sa_result = await session.execute(
            select(SocraticAnswers).where(
                SocraticAnswers.submission_id == submission_id
            )
        )
        sa = sa_result.scalar_one_or_none()
        if sa and sa.questions:
            socratic_questions = sa.questions

    return SubmissionWithEvaluation(
        submission=SubmissionOut.model_validate(submission),
        evaluation=EvaluationOut.model_validate(evaluation) if evaluation else None,
        socratic_questions=socratic_questions,
    )


@router.post(
    "/submissions/{submission_id}/socratic-answers",
    response_model=SocraticAnswersResponse,
)
async def submit_socratic_answers(
    submission_id: int,
    body: SocraticAnswersRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    """Submit answers to Socratic questions for phase 2 evaluation."""
    # Validate submission exists and is Socratic mode
    result = await session.execute(
        select(Submission).where(Submission.id == submission_id)
    )
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    if submission.mode != "socratic":
        raise HTTPException(
            status_code=400, detail="Socratic answers only apply to Socratic mode"
        )

    # Get existing Socratic record with questions
    sa_result = await session.execute(
        select(SocraticAnswers).where(
            SocraticAnswers.submission_id == submission_id
        )
    )
    sa = sa_result.scalar_one_or_none()
    if not sa or not sa.questions:
        raise HTTPException(
            status_code=400,
            detail="No Socratic questions found. Wait for initial evaluation to complete.",
        )
    if sa.answers:
        raise HTTPException(
            status_code=400, detail="Socratic answers already submitted"
        )

    # Save answers
    sa.answers = body.answers
    await session.commit()

    # Trigger phase 2 evaluation in background
    background_tasks.add_task(
        run_socratic_phase2, submission_id
    )

    return SocraticAnswersResponse(
        submission_id=submission_id,
        status="evaluating",
        message="Answers received. Evaluation in progress.",
    )


# --- Background pipeline ---


async def run_evaluation_pipeline(submission_id: int) -> None:
    """Async pipeline: validate -> execute in sandbox -> AI evaluate -> save."""
    async with async_session() as session:
        try:
            # 1. Load submission and challenge
            result = await session.execute(
                select(Submission).where(Submission.id == submission_id)
            )
            submission = result.scalar_one_or_none()
            if not submission:
                logger.error("Submission %d not found in pipeline", submission_id)
                return

            if submission.status != "pending":
                return

            # 2. Update status to running
            submission.status = "running"
            await session.commit()

            # 3. Load challenge
            ch_result = await session.execute(
                select(Challenge).where(Challenge.id == submission.challenge_id)
            )
            challenge = ch_result.scalar_one_or_none()
            if not challenge:
                submission.status = "error"
                await session.commit()
                logger.error(
                    "Challenge %s not found for submission %d",
                    submission.challenge_id,
                    submission_id,
                )
                return

            # 4. Execute code in sandbox (import dynamically to avoid circular deps)
            execution_result = await _execute_in_sandbox(
                submission.code, challenge, session, submission
            )

            # 5. AI evaluation
            submission.status = "evaluating"
            await session.commit()

            evaluator = ClaudeEvaluator(settings)
            eval_result = await evaluator.evaluate(
                challenge, submission, execution_result
            )

            # 6. Save evaluation
            evaluation = Evaluation(
                submission_id=submission_id,
                overall_score=eval_result.overall_score,
                architecture_score=eval_result.architecture_score,
                framework_depth_score=eval_result.framework_depth_score,
                complexity_mgmt_score=eval_result.complexity_mgmt_score,
                feedback_summary=eval_result.feedback_summary,
                strengths=eval_result.strengths,
                improvements=eval_result.improvements,
                mode_specific_feedback=eval_result.mode_specific_feedback,
                raw_ai_response=eval_result.raw_ai_response,
                model_used=eval_result.model_used,
                tokens_used=eval_result.tokens_used,
            )
            session.add(evaluation)

            # 7. For Socratic mode, generate and save questions
            if submission.mode == "socratic":
                questions = await evaluator.generate_socratic_questions(
                    challenge, submission.code, execution_result
                )
                sa = SocraticAnswers(
                    submission_id=submission_id,
                    questions=questions,
                )
                session.add(sa)

            # 8. ELO update
            try:
                from app.services.elo import ELOService

                elo_service = ELOService()
                user_result = await session.execute(
                    select(UserProfile).where(UserProfile.id == 1)
                )
                user = user_result.scalar_one_or_none()
                if user:
                    test_pass_rate = 1.0 if execution_result.get("exit_code") == 0 else 0.0
                    ai_scores = {
                        "overall": eval_result.overall_score,
                        "architecture": eval_result.architecture_score,
                        "framework_depth": eval_result.framework_depth_score,
                        "complexity_mgmt": eval_result.complexity_mgmt_score,
                    }
                    await elo_service.update_elo(
                        session=session,
                        user=user,
                        submission_id=submission_id,
                        challenge_elo=challenge.elo_target,
                        test_pass_rate=test_pass_rate,
                        ai_scores=ai_scores,
                    )
                    logger.info("ELO updated for submission %d", submission_id)

                    # Check if this is the user's first completed submission for this challenge
                    existing = await session.execute(
                        select(func.count(Submission.id)).where(
                            Submission.challenge_id == submission.challenge_id,
                            Submission.status == "completed",
                        )
                    )
                    if existing.scalar() == 0:
                        user.challenges_completed += 1
            except Exception:
                logger.exception("ELO update failed for submission %d (non-fatal)", submission_id)

            # 9. Update status
            submission.status = "completed"
            await session.commit()
            logger.info("Submission %d completed successfully", submission_id)

        except Exception:
            logger.exception("Pipeline failed for submission %d", submission_id)
            try:
                submission.status = "error"
                await session.commit()
            except Exception:
                logger.exception(
                    "Failed to set error status for submission %d", submission_id
                )


async def run_socratic_phase2(submission_id: int) -> None:
    """Phase 2: evaluate Socratic answers and update the evaluation."""
    async with async_session() as session:
        try:
            result = await session.execute(
                select(Submission).where(Submission.id == submission_id)
            )
            submission = result.scalar_one_or_none()
            if not submission:
                return

            ch_result = await session.execute(
                select(Challenge).where(Challenge.id == submission.challenge_id)
            )
            challenge = ch_result.scalar_one_or_none()
            if not challenge:
                return

            sa_result = await session.execute(
                select(SocraticAnswers).where(
                    SocraticAnswers.submission_id == submission_id
                )
            )
            sa = sa_result.scalar_one_or_none()
            if not sa or not sa.answers:
                return

            evaluator = ClaudeEvaluator(settings)
            eval_result = await evaluator.evaluate_socratic_answers(
                challenge, submission.code, sa.questions, sa.answers
            )

            # Save answer evaluation on the SocraticAnswers record
            sa.answer_evaluation = eval_result.raw_ai_response
            await session.commit()

            # Update the main evaluation with Socratic Q&A scores
            ev_result = await session.execute(
                select(Evaluation).where(Evaluation.submission_id == submission_id)
            )
            evaluation = ev_result.scalar_one_or_none()
            if evaluation:
                evaluation.overall_score = eval_result.overall_score
                evaluation.architecture_score = eval_result.architecture_score
                evaluation.framework_depth_score = eval_result.framework_depth_score
                evaluation.complexity_mgmt_score = eval_result.complexity_mgmt_score
                evaluation.feedback_summary = eval_result.feedback_summary
                evaluation.strengths = eval_result.strengths
                evaluation.improvements = eval_result.improvements
                evaluation.mode_specific_feedback = (
                    eval_result.mode_specific_feedback
                    or "Socratic Q&A evaluation complete."
                )
                evaluation.raw_ai_response = eval_result.raw_ai_response
                evaluation.model_used = eval_result.model_used
                await session.commit()

                # ELO recalculation with updated scores
                try:
                    from app.services.elo import ELOService

                    elo_service = ELOService()
                    user_result = await session.execute(
                        select(UserProfile).where(UserProfile.id == 1)
                    )
                    user = user_result.scalar_one_or_none()
                    if user:
                        ch_for_elo = await session.execute(
                            select(Challenge).where(Challenge.id == submission.challenge_id)
                        )
                        challenge_for_elo = ch_for_elo.scalar_one_or_none()
                        if challenge_for_elo:
                            test_pass_rate = (
                                1.0 if submission.sandbox_exit_code == 0 else 0.0
                            )
                            ai_scores = {
                                "overall": eval_result.overall_score,
                                "architecture": eval_result.architecture_score,
                                "framework_depth": eval_result.framework_depth_score,
                                "complexity_mgmt": eval_result.complexity_mgmt_score,
                            }
                            await elo_service.update_elo(
                                session=session,
                                user=user,
                                submission_id=submission_id,
                                challenge_elo=challenge_for_elo.elo_target,
                                test_pass_rate=test_pass_rate,
                                ai_scores=ai_scores,
                            )
                            await session.commit()
                            logger.info(
                                "ELO recalculated for Socratic phase 2, submission %d",
                                submission_id,
                            )
                except Exception:
                    logger.exception(
                        "ELO recalculation failed for Socratic phase 2, submission %d (non-fatal)",
                        submission_id,
                    )

            logger.info(
                "Socratic phase 2 complete for submission %d", submission_id
            )

        except Exception:
            logger.exception(
                "Socratic phase 2 failed for submission %d", submission_id
            )


async def _execute_in_sandbox(
    code: str,
    challenge: Challenge,
    session: AsyncSession,
    submission: Submission,
) -> dict:
    """Execute code in sandbox. Falls back to a stub if sandbox service is unavailable."""
    try:
        from app.services.sandbox import ExecutionResult, execute_code

        exec_result: ExecutionResult = await asyncio.to_thread(
            execute_code,
            code=code,
            timeout=settings.SANDBOX_TIMEOUT,
            memory_limit=settings.SANDBOX_MEMORY_LIMIT,
        )
        result = {
            "stdout": exec_result.stdout,
            "stderr": exec_result.stderr,
            "exit_code": exec_result.exit_code,
            "execution_time_ms": exec_result.execution_time_ms,
        }
        submission.sandbox_stdout = exec_result.stdout
        submission.sandbox_stderr = exec_result.stderr
        submission.sandbox_exit_code = exec_result.exit_code
        submission.execution_time_ms = exec_result.execution_time_ms
        await session.commit()
        return result
    except ImportError:
        logger.warning("Sandbox service not available; using stub execution result")
        stub = {
            "stdout": "",
            "stderr": "",
            "exit_code": 0,
            "execution_time_ms": 0,
        }
        submission.sandbox_stdout = ""
        submission.sandbox_stderr = ""
        submission.sandbox_exit_code = 0
        submission.execution_time_ms = 0
        await session.commit()
        return stub
    except Exception as e:
        logger.error("Sandbox execution failed: %s", e)
        stub = {
            "stdout": "",
            "stderr": str(e),
            "exit_code": 1,
            "execution_time_ms": 0,
        }
        submission.sandbox_stderr = str(e)
        submission.sandbox_exit_code = 1
        submission.execution_time_ms = 0
        await session.commit()
        return stub
