import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { challengeApi, submissionApi } from '../services/api';
import MonacoEditor from '../components/MonacoEditor';
import ChallengeBriefing from '../components/ChallengeBriefing';
import SubmissionFlow from '../components/SubmissionFlow';
import EvaluationResults from '../components/EvaluationResults';
import SocraticQuestionnaire from '../components/SocraticQuestionnaire';

interface Challenge {
  id: string;
  title: string;
  description: string;
  difficulty: string;
  mode: string;
  domain: string;
  category: string;
  tags: string[];
  starter_code: string | null;
  constraints: Record<string, unknown> | string[];
  expected_concepts: string[];
  reference_solution: string | null;
  buggy_code?: string;
  steps?: Array<{ id: string; title: string; description: string }>;
  socratic_questions?: string[];
  estimated_minutes?: number;
}

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

type MobilePanel = 'brief' | 'editor' | 'results';

export default function ChallengeIDE() {
  const { id } = useParams<{ id: string }>();
  const [challenge, setChallenge] = useState<Challenge | null>(null);
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  const [referenceSolution, setReferenceSolution] = useState<string | null>(null);
  const [socraticAnswerEval, setSocraticAnswerEval] = useState<string | null>(null);
  const [submissionId, setSubmissionId] = useState<number | null>(null);
  const [dynamicSocraticQuestions, setDynamicSocraticQuestions] = useState<string[] | null>(null);
  const [activeStep, setActiveStep] = useState(0);
  const [activePanel, setActivePanel] = useState<MobilePanel>('editor');

  // Fetch challenge data
  useEffect(() => {
    if (!id) return;
    const controller = new AbortController();

    setLoading(true);
    challengeApi
      .get(id, { signal: controller.signal })
      .then(({ data }) => {
        setChallenge(data);
        // Set initial editor content based on mode
        if (data.mode === 'adversarial' && data.buggy_code) {
          setCode(data.buggy_code);
        } else {
          setCode(data.starter_code ?? '');
        }
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          setError('Failed to load challenge');
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      });

    return () => controller.abort();
  }, [id]);

  // Fetch reference solution when evaluation completes
  useEffect(() => {
    if (!evaluation || !id) return;
    const controller = new AbortController();
    challengeApi
      .getReference(id, { signal: controller.signal })
      .then(({ data }) => setReferenceSolution(data.reference_solution ?? null))
      .catch(() => {
        /* reference may not be available */
      });
    return () => controller.abort();
  }, [evaluation, id]);

  const handleResult = useCallback((result: SubmissionResult) => {
    setSubmissionId(result.id);
    if (result.evaluation) {
      setEvaluation(result.evaluation);
    }
    if (result.socratic_questions && result.socratic_questions.length > 0) {
      setDynamicSocraticQuestions(
        result.socratic_questions.map((q) =>
          typeof q === 'string' ? q : q.question
        )
      );
    }
  }, []);

  const handleSocraticSubmit = useCallback(
    async (answers: Record<number, string>) => {
      if (!submissionId) return;
      const answerList = Object.keys(answers)
        .sort((a, b) => Number(a) - Number(b))
        .map((k) => answers[Number(k)]);
      try {
        setSocraticAnswerEval('Submitting answers for evaluation...');
        await submissionApi.submitSocraticAnswers(submissionId, answerList);
        setSocraticAnswerEval(
          'Your answers have been submitted. Evaluation in progress — results will update automatically.'
        );
      } catch {
        setSocraticAnswerEval('Failed to submit answers. Please try again.');
      }
    },
    [submissionId]
  );

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-gray-500 animate-pulse">Loading challenge...</div>
      </div>
    );
  }

  if (error || !challenge) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-red-400">{error ?? 'Challenge not found'}</div>
      </div>
    );
  }

  const isSocratic = challenge.mode === 'socratic';
  const isCollaborative = challenge.mode === 'collaborative';
  const socraticQuestions = dynamicSocraticQuestions ?? challenge.socratic_questions ?? null;
  const showSocratic = isSocratic && evaluation && socraticQuestions && socraticQuestions.length > 0;

  const briefingPanel = (
    <>
      <ChallengeBriefing challenge={challenge} />
      {isCollaborative && challenge.steps && challenge.steps[activeStep] && (
        <div className="mt-4 pt-4 border-t border-gray-700">
          <h4 className="text-xs font-semibold text-brand-400 mb-1">
            Step {activeStep + 1}: {challenge.steps[activeStep].title}
          </h4>
          <p className="text-sm text-gray-400 whitespace-pre-wrap">
            {challenge.steps[activeStep].description}
          </p>
        </div>
      )}
    </>
  );

  const editorPanel = (
    <>
      <div className="flex-1 min-h-0">
        <MonacoEditor value={code} onChange={setCode} />
      </div>
      <div className="p-3 border-t border-gray-700 bg-gray-800/30">
        <SubmissionFlow
          challengeId={challenge.id}
          code={code}
          mode={challenge.mode}
          onResult={handleResult}
        />
      </div>
    </>
  );

  const resultsPanel = (
    <>
      {!evaluation && (
        <div className="flex items-center justify-center h-full">
          <p className="text-sm text-gray-600">
            Submit your solution to see results here.
          </p>
        </div>
      )}
      {evaluation && (
        <EvaluationResults
          evaluation={evaluation}
          referenceSolution={referenceSolution}
        />
      )}
      {showSocratic && socraticQuestions && (
        <div className="border-t border-gray-700 pt-4">
          <SocraticQuestionnaire
            questions={socraticQuestions}
            onSubmit={handleSocraticSubmit}
            evaluation={socraticAnswerEval}
          />
        </div>
      )}
    </>
  );

  return (
    <div className="h-full flex flex-col -m-8">
      {/* Skip to main content */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-brand-600 focus:text-white focus:rounded"
      >
        Skip to main content
      </a>

      {/* Top bar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-700 bg-gray-800/50 shrink-0">
        <div className="flex items-center gap-3">
          <h2 className="text-sm font-semibold text-gray-200 truncate">
            {challenge.title}
          </h2>
        </div>
        {isCollaborative && challenge.steps && (
          <div className="flex items-center gap-2 text-xs text-gray-400">
            {challenge.steps.map((step, i) => (
              <button
                key={step.id}
                onClick={() => setActiveStep(i)}
                className={
                  i === activeStep
                    ? 'text-brand-400 font-medium'
                    : 'text-gray-500 hover:text-gray-300'
                }
              >
                Step {i + 1}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Mobile tab navigation */}
      <div className="lg:hidden flex border-b border-gray-700 bg-gray-800/50 shrink-0" role="tablist">
        {(['brief', 'editor', 'results'] as const).map((panel) => (
          <button
            key={panel}
            role="tab"
            aria-selected={activePanel === panel}
            onClick={() => setActivePanel(panel)}
            className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
              activePanel === panel
                ? 'text-brand-400 border-b-2 border-brand-400'
                : 'text-gray-500 hover:text-gray-300'
            }`}
          >
            {panel === 'brief' ? 'Brief' : panel === 'editor' ? 'Editor' : 'Results'}
          </button>
        ))}
      </div>

      {/* Main content */}
      <div id="main-content" className="flex-1 min-h-0">
        {/* Desktop: 3-column grid */}
        <div className="hidden lg:grid h-full grid-cols-[1fr_2fr_1fr] min-h-0">
          <div className="border-r border-gray-700 p-4 overflow-auto">
            {briefingPanel}
          </div>
          <div className="border-r border-gray-700 flex flex-col min-h-0">
            {editorPanel}
          </div>
          <div className="p-4 overflow-auto flex flex-col gap-4">
            {resultsPanel}
          </div>
        </div>

        {/* Tablet (md to lg): 2-column with collapsible briefing */}
        <div className="hidden md:flex lg:hidden h-full flex-col min-h-0">
          <details className="border-b border-gray-700 bg-gray-800/30">
            <summary className="px-4 py-2 text-sm font-medium text-gray-300 cursor-pointer hover:text-gray-100">
              Challenge Briefing
            </summary>
            <div className="px-4 pb-3 overflow-auto max-h-64">
              {briefingPanel}
            </div>
          </details>
          <div className="flex-1 grid grid-cols-[2fr_1fr] min-h-0">
            <div className="border-r border-gray-700 flex flex-col min-h-0">
              {editorPanel}
            </div>
            <div className="p-4 overflow-auto flex flex-col gap-4">
              {resultsPanel}
            </div>
          </div>
        </div>

        {/* Mobile (below md): single column with tabs */}
        <div className="flex md:hidden h-full flex-col min-h-0">
          {activePanel === 'brief' && (
            <div className="flex-1 p-4 overflow-auto">
              {briefingPanel}
            </div>
          )}
          {activePanel === 'editor' && (
            <div className="flex-1 flex flex-col min-h-0">
              {editorPanel}
            </div>
          )}
          {activePanel === 'results' && (
            <div className="flex-1 p-4 overflow-auto flex flex-col gap-4">
              {resultsPanel}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
