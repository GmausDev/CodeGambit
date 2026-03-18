import { useEffect, useState, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import MonacoEditor from '../components/MonacoEditor';
import { userApi, challengeApi, submissionApi } from '../services/api';

type Phase = 'loading' | 'start' | 'challenge' | 'submitting' | 'result' | 'complete';

interface ChallengeDetail {
  id: string;
  title: string;
  description: string;
  difficulty: string;
  starter_code?: string;
  mode: string;
}

interface FinalResults {
  elo_overall: number;
  elo_architecture: number;
  elo_framework_depth: number;
  elo_complexity_mgmt: number;
}

export default function Calibration() {
  const navigate = useNavigate();
  const [phase, setPhase] = useState<Phase>('loading');
  const [step, setStep] = useState(0);
  const totalSteps = 10;
  const [challenge, setChallenge] = useState<ChallengeDetail | null>(null);
  const [code, setCode] = useState('');
  const [lastScore, setLastScore] = useState<number | null>(null);
  const [finalResults, setFinalResults] = useState<FinalResults | null>(null);
  const [error, setError] = useState('');
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Clean up polling on unmount
  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  // Check if already calibrated on mount
  useEffect(() => {
    const controller = new AbortController();
    async function check() {
      try {
        const res = await userApi.getProfile({ signal: controller.signal });
        if (res.data.calibration_complete) {
          setPhase('complete');
          setFinalResults({
            elo_overall: res.data.elo_overall,
            elo_architecture: res.data.elo_architecture,
            elo_framework_depth: res.data.elo_framework_depth,
            elo_complexity_mgmt: res.data.elo_complexity_mgmt,
          });
        } else {
          setPhase('start');
        }
      } catch {
        if (!controller.signal.aborted) {
          setPhase('start');
        }
      }
    }
    check();
    return () => controller.abort();
  }, []);

  const loadChallenge = useCallback(async (calStep: number) => {
    try {
      const calRes = await userApi.calibrate(calStep);
      const data = calRes.data;

      if (data.status === 'calibration_complete') {
        setFinalResults({
          elo_overall: data.elo_overall,
          elo_architecture: data.elo_architecture,
          elo_framework_depth: data.elo_framework_depth,
          elo_complexity_mgmt: data.elo_complexity_mgmt,
        });
        setPhase('complete');
        return;
      }

      if (data.status === 'already_complete') {
        setPhase('complete');
        return;
      }

      if (data.status === 'no_challenge') {
        setError('No challenge available for this calibration step.');
        return;
      }

      // Load the full challenge detail
      const detail = await challengeApi.get(data.challenge_id);
      setChallenge(detail.data);
      setCode(detail.data.starter_code ?? '');
      setStep(data.calibration_step);
      setLastScore(null);
      setPhase('challenge');
    } catch {
      setError('Failed to load calibration challenge.');
    }
  }, []);

  const handleStart = () => {
    setPhase('loading');
    loadChallenge(0);
  };

  const handleSubmit = async () => {
    if (!challenge) return;
    if (pollRef.current) clearInterval(pollRef.current);
    setPhase('submitting');
    try {
      const res = await submissionApi.submit({
        challenge_id: challenge.id,
        code,
        mode: challenge.mode ?? 'socratic',
      });
      const submissionId: number = res.data.id;

      // Poll for completion using setInterval
      const MAX_POLLS = 150;
      let polls = 0;
      pollRef.current = setInterval(async () => {
        polls++;
        if (polls > MAX_POLLS) {
          if (pollRef.current) clearInterval(pollRef.current);
          pollRef.current = null;
          setError('Evaluation timed out. Please try again.');
          setPhase('challenge');
          return;
        }
        try {
          const { data: sub } = await submissionApi.get(submissionId);
          const submission = sub.submission ?? sub;
          if (submission.status === 'completed') {
            if (pollRef.current) clearInterval(pollRef.current);
            pollRef.current = null;
            const score = sub.evaluation?.overall_score ?? submission.elo_delta ?? 0;
            setLastScore(score);
            setPhase('result');
            return;
          }
          if (submission.status === 'failed' || submission.status === 'error') {
            if (pollRef.current) clearInterval(pollRef.current);
            pollRef.current = null;
            setError('Evaluation failed. Please try again.');
            setPhase('challenge');
            return;
          }
        } catch {
          if (pollRef.current) clearInterval(pollRef.current);
          pollRef.current = null;
          setError('Submission failed. Please try again.');
          setPhase('challenge');
        }
      }, 2000);
    } catch {
      setError('Submission failed. Please try again.');
      setPhase('challenge');
    }
  };

  const handleNext = () => {
    const nextStep = step + 1;
    if (nextStep >= totalSteps) {
      setPhase('loading');
      loadChallenge(nextStep);
    } else {
      setPhase('loading');
      loadChallenge(nextStep);
    }
  };

  const progressPct = Math.round(((phase === 'complete' ? totalSteps : step) / totalSteps) * 100);

  if (error) {
    return (
      <div className="max-w-2xl mx-auto mt-16 text-center">
        <p className="text-red-400 mb-4">{error}</p>
        <button
          onClick={() => { setError(''); setPhase('start'); }}
          className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-gray-200 rounded-lg transition-colors"
        >
          Try Again
        </button>
      </div>
    );
  }

  if (phase === 'loading' || phase === 'submitting') {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400 animate-pulse">
          {phase === 'submitting' ? 'Evaluating submission...' : 'Loading...'}
        </div>
      </div>
    );
  }

  if (phase === 'start') {
    return (
      <div className="max-w-2xl mx-auto mt-16">
        <h2 className="text-2xl font-bold mb-4">Calibration</h2>
        <div className="bg-gray-800 rounded-xl p-8 border border-gray-700">
          <p className="text-gray-400 mb-6">
            Complete 10 challenges across 5 difficulty bands to determine your initial skill
            rating. Each challenge tests a different aspect of your LangChain expertise.
          </p>
          <button
            onClick={handleStart}
            className="px-6 py-3 bg-brand-600 hover:bg-brand-700 text-white rounded-lg transition-colors font-medium"
          >
            Start Calibration
          </button>
        </div>
      </div>
    );
  }

  if (phase === 'complete') {
    return (
      <div className="max-w-2xl mx-auto mt-16">
        <h2 className="text-2xl font-bold mb-4">Calibration Complete</h2>
        {/* Progress bar full */}
        <div className="mb-6">
          <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
            <div className="h-full bg-brand-600 rounded-full w-full" />
          </div>
          <p className="text-sm text-gray-400 mt-1">10 of 10 challenges completed</p>
        </div>
        {finalResults && (
          <div className="bg-gray-800 rounded-xl p-8 border border-gray-700 space-y-4">
            <h3 className="text-lg font-semibold text-gray-200 mb-4">Your Initial Ratings</h3>
            {[
              { label: 'Overall', value: finalResults.elo_overall },
              { label: 'Architecture', value: finalResults.elo_architecture },
              { label: 'Framework Depth', value: finalResults.elo_framework_depth },
              { label: 'Complexity Mgmt', value: finalResults.elo_complexity_mgmt },
            ].map((r) => (
              <div key={r.label} className="flex items-center justify-between p-3 bg-gray-900 rounded-lg border border-gray-700">
                <span className="text-gray-300">{r.label}</span>
                <span className="text-brand-500 font-mono font-semibold">{r.value}</span>
              </div>
            ))}
            <button
              onClick={() => navigate('/')}
              className="mt-4 w-full px-6 py-3 bg-brand-600 hover:bg-brand-700 text-white rounded-lg transition-colors font-medium"
            >
              Go to Dashboard
            </button>
          </div>
        )}
      </div>
    );
  }

  if (phase === 'result') {
    return (
      <div className="max-w-2xl mx-auto mt-16">
        <h2 className="text-2xl font-bold mb-4">Challenge {step + 1} of {totalSteps}</h2>
        {/* Progress bar */}
        <div className="mb-6">
          <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-brand-600 rounded-full transition-all"
              style={{ width: `${Math.round(((step + 1) / totalSteps) * 100)}%` }}
            />
          </div>
        </div>
        <div className="bg-gray-800 rounded-xl p-8 border border-gray-700 text-center">
          <h3 className="text-lg font-semibold text-gray-200 mb-2">Submission Evaluated</h3>
          {lastScore !== null && (
            <p className="text-3xl font-mono font-bold text-brand-500 mb-4">
              {lastScore > 0 ? '+' : ''}{lastScore}
            </p>
          )}
          <button
            onClick={handleNext}
            className="px-6 py-3 bg-brand-600 hover:bg-brand-700 text-white rounded-lg transition-colors font-medium"
          >
            {step + 1 >= totalSteps ? 'See Results' : 'Next Challenge'}
          </button>
        </div>
      </div>
    );
  }

  // phase === 'challenge'
  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold">Challenge {step + 1} of {totalSteps}</h2>
        <span className="text-sm text-gray-400">{challenge?.difficulty}</span>
      </div>

      {/* Progress bar */}
      <div className="mb-4">
        <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-brand-600 rounded-full transition-all"
            style={{ width: `${progressPct}%` }}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 flex-1 min-h-0">
        {/* Briefing */}
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 overflow-auto">
          <h3 className="text-sm font-semibold text-gray-400 mb-2">{challenge?.title}</h3>
          <pre className="text-gray-300 text-sm whitespace-pre-wrap font-sans">
            {challenge?.description}
          </pre>
        </div>

        {/* Editor */}
        <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden flex flex-col">
          <div className="flex-1 min-h-[300px]">
            <MonacoEditor value={code} onChange={setCode} />
          </div>
          <div className="p-3 border-t border-gray-700">
            <button
              onClick={handleSubmit}
              className="w-full px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white rounded-lg transition-colors font-medium text-sm"
            >
              Submit Solution
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
