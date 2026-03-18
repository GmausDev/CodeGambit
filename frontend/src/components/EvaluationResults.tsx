import { useState, useEffect } from 'react';
import clsx from 'clsx';

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

interface EvaluationResultsProps {
  evaluation: Evaluation;
  referenceSolution?: string | null;
}

function scoreColor(score: number): string {
  if (score >= 70) return 'bg-green-500';
  if (score >= 40) return 'bg-yellow-500';
  return 'bg-red-500';
}

function scoreTextColor(score: number): string {
  if (score >= 70) return 'text-green-400';
  if (score >= 40) return 'text-yellow-400';
  return 'text-red-400';
}

interface ScoreBarProps {
  label: string;
  score: number;
}

function scoreLabel(score: number): string {
  if (score > 80) return 'Excellent';
  if (score > 60) return 'Good';
  if (score > 40) return 'Fair';
  return 'Needs Work';
}

function ScoreBar({ label, score }: ScoreBarProps) {
  const [animate, setAnimate] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setAnimate(true), 100);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="flex flex-col gap-1">
      <div className="flex justify-between text-xs">
        <span className="text-gray-400">{label}</span>
        <span className="flex items-center gap-1.5">
          <span className="text-gray-500">{scoreLabel(score)}</span>
          <span className={scoreTextColor(score)}>{score}</span>
        </span>
      </div>
      <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden">
        <div
          className={clsx('h-full rounded-full transition-all duration-1000 ease-out', scoreColor(score))}
          style={{ width: animate ? `${Math.min(score, 100)}%` : '0%' }}
        />
      </div>
    </div>
  );
}

export default function EvaluationResults({
  evaluation,
  referenceSolution,
}: EvaluationResultsProps) {
  const [showReference, setShowReference] = useState(false);

  return (
    <div className="flex flex-col gap-4 h-full overflow-auto">
      {/* Overall score */}
      <div className="text-center py-3">
        <div className={clsx('text-4xl font-bold', scoreTextColor(evaluation.overall_score))}>
          {evaluation.overall_score}
        </div>
        <div className="text-xs text-gray-500 mt-1">Overall Score</div>
      </div>

      {/* Dimension scores */}
      <div className="flex flex-col gap-3">
        <ScoreBar label="Architecture" score={evaluation.architecture_score} />
        <ScoreBar label="Framework Depth" score={evaluation.framework_depth_score} />
        <ScoreBar label="Complexity Mgmt" score={evaluation.complexity_mgmt_score} />
      </div>

      {/* Feedback summary */}
      <div className="text-sm text-gray-300 bg-gray-800/50 rounded-lg p-3 border border-gray-700/50">
        {evaluation.feedback_summary}
      </div>

      {/* Strengths */}
      {evaluation.strengths.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
            Strengths
          </h4>
          <ul className="space-y-1">
            {evaluation.strengths.map((s, i) => (
              <li key={i} className="text-sm text-green-400 flex gap-2">
                <span className="shrink-0">+</span>
                <span>{s}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Improvements */}
      {evaluation.improvements.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
            Areas for Improvement
          </h4>
          <ul className="space-y-1">
            {evaluation.improvements.map((imp, i) => (
              <li key={i} className="text-sm text-yellow-400 flex gap-2">
                <span className="shrink-0">-</span>
                <span>{imp}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Mode-specific feedback */}
      {evaluation.mode_specific_feedback && (
        <div className="text-sm text-gray-400 italic border-l-2 border-gray-600 pl-3">
          {evaluation.mode_specific_feedback}
        </div>
      )}

      {/* Reference solution toggle */}
      {referenceSolution && (
        <div>
          <button
            onClick={() => setShowReference(!showReference)}
            className="text-xs text-brand-400 hover:text-brand-300 transition-colors"
          >
            {showReference ? 'Hide' : 'Show'} Reference Solution
          </button>
          {showReference && (
            <pre className="mt-2 text-xs bg-gray-950 rounded-lg border border-gray-700 p-3 overflow-auto max-h-60 text-gray-300 font-mono">
              {referenceSolution}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}
