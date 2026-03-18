import { useState, useCallback, useRef, useEffect } from 'react';
import clsx from 'clsx';
import { submissionApi } from '../services/api';

type SubmissionStep = 'idle' | 'submitting' | 'executing' | 'evaluating' | 'complete' | 'error';

interface Evaluation {
  overall_score: number;
  architecture_score: number;
  framework_depth_score: number;
  complexity_mgmt_score: number;
  feedback_summary: string;
  strengths: string[];
  improvements: string[];
  mode_specific_feedback: string | null;
}

interface SubmissionResult {
  id: number;
  status: string;
  sandbox_stdout: string | null;
  sandbox_stderr: string | null;
  evaluation?: Evaluation;
  socratic_questions?: Array<{ question: string }> | null;
}

interface SubmissionFlowProps {
  challengeId: string;
  code: string;
  mode: string;
  onResult: (result: SubmissionResult) => void;
}

const stepOrder: SubmissionStep[] = ['submitting', 'executing', 'evaluating', 'complete'];

const stepLabels: Record<string, string> = {
  submitting: 'Submitting',
  executing: 'Executing',
  evaluating: 'Evaluating',
  complete: 'Complete',
};

function statusToStep(status: string): SubmissionStep {
  switch (status) {
    case 'pending':
      return 'submitting';
    case 'running':
      return 'executing';
    case 'evaluating':
      return 'evaluating';
    case 'completed':
      return 'complete';
    case 'failed':
    case 'error':
      return 'error';
    default:
      return 'submitting';
  }
}

export default function SubmissionFlow({
  challengeId,
  code,
  mode,
  onResult,
}: SubmissionFlowProps) {
  const [step, setStep] = useState<SubmissionStep>('idle');
  const [stdout, setStdout] = useState<string | null>(null);
  const [stderr, setStderr] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Clean up polling on unmount
  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  const handleSubmit = useCallback(async () => {
    if (!code.trim()) return;

    setStep('submitting');
    setStdout(null);
    setStderr(null);
    setError(null);

    try {
      const { data } = await submissionApi.submit({
        challenge_id: challengeId,
        code,
        mode,
      });

      const submissionId: number = data.id;
      setStep('executing');

      // Poll for completion
      pollRef.current = setInterval(async () => {
        try {
          const { data: sub } = await submissionApi.get(submissionId);
          const submission = sub.submission ?? sub;
          const currentStep = statusToStep(submission.status);

          if (submission.sandbox_stdout) setStdout(submission.sandbox_stdout);
          if (submission.sandbox_stderr) setStderr(submission.sandbox_stderr);

          setStep(currentStep);

          if (currentStep === 'complete' || currentStep === 'error') {
            if (pollRef.current) clearInterval(pollRef.current);
            pollRef.current = null;
            onResult({
              id: submission.id,
              status: submission.status,
              sandbox_stdout: submission.sandbox_stdout,
              sandbox_stderr: submission.sandbox_stderr,
              evaluation: sub.evaluation,
              socratic_questions: sub.socratic_questions,
            });
          }
        } catch {
          if (pollRef.current) clearInterval(pollRef.current);
          pollRef.current = null;
          setStep('error');
          setError('Failed to check submission status');
        }
      }, 2000);
    } catch {
      setStep('error');
      setError('Failed to submit code');
    }
  }, [challengeId, code, mode, onResult]);

  const isProcessing = step !== 'idle' && step !== 'complete' && step !== 'error';
  const canSubmit = code.trim().length > 0 && !isProcessing;

  return (
    <div className="flex flex-col gap-3">
      {/* Submit button */}
      <button
        onClick={handleSubmit}
        disabled={!canSubmit}
        className={clsx(
          'w-full py-2 px-4 rounded-lg font-medium text-sm transition-colors',
          canSubmit
            ? 'bg-brand-600 hover:bg-brand-500 text-white cursor-pointer'
            : 'bg-gray-700 text-gray-500 cursor-not-allowed'
        )}
      >
        {isProcessing ? 'Processing...' : 'Submit Solution'}
      </button>

      {/* Progress steps */}
      {step !== 'idle' && (
        <div className="flex items-center gap-1">
          {stepOrder.map((s, i) => {
            const stepIdx = stepOrder.indexOf(step === 'error' ? 'complete' : step);
            const thisIdx = i;
            const isActive = step !== 'error' && thisIdx === stepIdx;
            const isDone = step !== 'error' && thisIdx < stepIdx;
            const isErr = step === 'error' && s === 'complete';

            return (
              <div key={s} className="flex items-center gap-1 flex-1">
                <div
                  className={clsx(
                    'flex items-center gap-1 text-xs',
                    isDone && 'text-green-400',
                    isActive && 'text-brand-400 font-medium',
                    isErr && 'text-red-400',
                    !isDone && !isActive && !isErr && 'text-gray-600'
                  )}
                >
                  <span
                    className={clsx(
                      'w-1.5 h-1.5 rounded-full',
                      isDone && 'bg-green-400',
                      isActive && 'bg-brand-400 animate-pulse',
                      isErr && 'bg-red-400',
                      !isDone && !isActive && !isErr && 'bg-gray-600'
                    )}
                  />
                  {stepLabels[s]}
                </div>
                {i < stepOrder.length - 1 && (
                  <div
                    className={clsx(
                      'flex-1 h-px',
                      isDone ? 'bg-green-400/40' : 'bg-gray-700'
                    )}
                  />
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Error message */}
      {error && (
        <div className="text-sm text-red-400 bg-red-900/20 border border-red-800/30 rounded-lg p-3">
          {error}
        </div>
      )}

      {/* Execution output */}
      {(stdout || stderr) && (
        <div className="bg-gray-950 rounded-lg border border-gray-700 overflow-hidden">
          <div className="text-xs font-semibold text-gray-400 px-3 py-1.5 border-b border-gray-700 bg-gray-800/50">
            Output
          </div>
          <pre className="text-xs p-3 overflow-auto max-h-40 text-gray-300 font-mono">
            {stdout}
            {stderr && (
              <span className="text-red-400">{stderr}</span>
            )}
          </pre>
        </div>
      )}
    </div>
  );
}
