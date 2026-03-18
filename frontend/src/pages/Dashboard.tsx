import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { userApi } from '../services/api';
import SkillRadar from '../components/SkillRadar';
import ELOChart from '../components/ELOChart';
import ChallengeStats from '../components/ChallengeStats';

interface Profile {
  display_name: string;
  elo_overall: number;
  elo_architecture: number;
  elo_framework_depth: number;
  elo_complexity_mgmt: number;
  calibration_complete: boolean;
  challenges_completed: number;
  total_submissions: number;
}

interface EloHistoryRecord {
  dimension: string;
  elo_after: number;
  created_at: string;
}

interface HistoryPoint {
  date: string;
  overall: number;
  architecture: number;
  framework_depth: number;
  complexity_mgmt: number;
}

function buildHistory(records: EloHistoryRecord[]): HistoryPoint[] {
  const byDate = new Map<string, HistoryPoint>();
  for (const r of records) {
    const date = r.created_at.slice(0, 10);
    if (!byDate.has(date)) {
      byDate.set(date, { date, overall: 1200, architecture: 1200, framework_depth: 1200, complexity_mgmt: 1200 });
    }
    const point = byDate.get(date)!;
    const dim = r.dimension as keyof Omit<HistoryPoint, 'date'>;
    if (dim in point) {
      point[dim] = r.elo_after;
    }
  }
  return Array.from(byDate.values()).sort((a, b) => a.date.localeCompare(b.date));
}

interface StatGroup {
  total: number;
  completed: number;
}

interface Stats {
  total: number;
  completed: number;
  byMode: Record<string, StatGroup>;
  byDifficulty: Record<string, StatGroup>;
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [history, setHistory] = useState<HistoryPoint[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    async function load() {
      try {
        const [profileRes, historyRes, statsRes] = await Promise.all([
          userApi.getProfile({ signal: controller.signal }),
          userApi.getEloHistory({ signal: controller.signal }),
          userApi.getStats({ signal: controller.signal }),
        ]);
        setProfile(profileRes.data);
        setHistory(buildHistory(historyRes.data));
        setStats(statsRes.data);
      } catch {
        if (!controller.signal.aborted) {
          setError('Failed to load dashboard data');
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }
    load();
    return () => controller.abort();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400 animate-pulse">Loading dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-red-400">{error}</div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Unable to load profile. Is the backend running?</div>
      </div>
    );
  }

  if (!profile.calibration_complete) {
    return (
      <div className="max-w-lg mx-auto mt-16 text-center">
        <h2 className="text-2xl font-bold mb-4">Welcome to CodeGambit</h2>
        <p className="text-gray-400 mb-6">
          Complete the calibration challenges to determine your initial skill ratings.
        </p>
        <button
          onClick={() => navigate('/calibration')}
          className="px-6 py-3 bg-brand-600 hover:bg-brand-700 text-white rounded-lg transition-colors font-medium"
        >
          Start Calibration
        </button>
      </div>
    );
  }

  const elo = {
    overall: profile.elo_overall,
    architecture: profile.elo_architecture,
    framework_depth: profile.elo_framework_depth,
    complexity_mgmt: profile.elo_complexity_mgmt,
  };

  return (
    <div>
      <div className="flex items-baseline justify-between mb-6">
        <h2 className="text-2xl font-bold">Welcome back, {profile.display_name}</h2>
        <span className="text-brand-500 font-mono text-lg font-semibold">
          ELO {profile.elo_overall}
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <h3 className="text-lg font-semibold text-gray-300 mb-4">Skill Radar</h3>
          <div className="h-64">
            <SkillRadar elo={elo} />
          </div>
        </div>
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <h3 className="text-lg font-semibold text-gray-300 mb-4">ELO History</h3>
          <div className="h-64">
            {history.length > 0 ? (
              <ELOChart history={history} />
            ) : (
              <div className="h-full flex items-center justify-center text-gray-500">
                No history yet — complete some challenges!
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <h3 className="text-lg font-semibold text-gray-300 mb-4">Challenge Progress</h3>
          {stats ? (
            <ChallengeStats {...stats} />
          ) : (
            <div className="text-gray-500 text-sm">Stats unavailable</div>
          )}
        </div>
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <h3 className="text-lg font-semibold text-gray-300 mb-4">Recent Submissions</h3>
          <div className="text-gray-500 text-sm">
            {profile.total_submissions > 0
              ? `${profile.total_submissions} submissions total`
              : 'No submissions yet. Start a challenge!'}
          </div>
        </div>
      </div>
    </div>
  );
}
