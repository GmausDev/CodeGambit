import { useState, useCallback } from 'react';
import clsx from 'clsx';

interface SocraticQuestionnaireProps {
  questions: string[];
  onSubmit: (answers: Record<number, string>) => void;
  evaluation?: string | null;
}

export default function SocraticQuestionnaire({
  questions,
  onSubmit,
  evaluation,
}: SocraticQuestionnaireProps) {
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [submitted, setSubmitted] = useState(false);

  const handleChange = useCallback((index: number, value: string) => {
    setAnswers((prev) => ({ ...prev, [index]: value }));
  }, []);

  const handleSubmit = useCallback(() => {
    setSubmitted(true);
    onSubmit(answers);
  }, [answers, onSubmit]);

  const allAnswered = questions.every((_, i) => answers[i]?.trim());

  return (
    <div className="flex flex-col gap-4 h-full overflow-auto">
      <h3 className="text-sm font-semibold text-gray-300">
        Socratic Questions
      </h3>
      <p className="text-xs text-gray-500">
        Reflect on your solution by answering these questions.
      </p>

      <div className="flex flex-col gap-4">
        {questions.map((question, i) => (
          <div key={i} className="flex flex-col gap-1.5">
            <label htmlFor={`answer-${i}`} className="text-sm text-gray-300">
              <span className="text-gray-500 font-mono mr-1.5">{i + 1}.</span>
              {question}
            </label>
            <textarea
              id={`answer-${i}`}
              value={answers[i] ?? ''}
              onChange={(e) => handleChange(i, e.target.value)}
              disabled={submitted}
              rows={3}
              className={clsx(
                'w-full rounded-lg border bg-gray-950 px-3 py-2 text-sm text-gray-200',
                'placeholder-gray-600 resize-none focus:outline-none focus:ring-2',
                submitted
                  ? 'border-gray-700 opacity-40 cursor-not-allowed bg-gray-900'
                  : 'border-gray-700 focus:ring-brand-500 focus:border-brand-500'
              )}
              placeholder="Your answer..."
            />
            {!submitted && (
              <span className="text-xs text-gray-600">Aim for 2-3 sentences</span>
            )}
          </div>
        ))}
      </div>

      {!submitted && (
        <button
          onClick={handleSubmit}
          disabled={!allAnswered}
          className={clsx(
            'w-full py-2 px-4 rounded-lg font-medium text-sm transition-colors',
            allAnswered
              ? 'bg-brand-600 hover:bg-brand-500 text-white cursor-pointer'
              : 'bg-gray-700 text-gray-500 cursor-not-allowed'
          )}
        >
          Submit Answers
        </button>
      )}

      {/* Evaluation of answers */}
      {evaluation && (
        <div className="bg-gray-800/50 rounded-lg border border-gray-700/50 p-3">
          <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
            Feedback on Your Answers
          </h4>
          <div className="text-sm text-gray-300 whitespace-pre-wrap">
            {evaluation}
          </div>
        </div>
      )}
    </div>
  );
}
