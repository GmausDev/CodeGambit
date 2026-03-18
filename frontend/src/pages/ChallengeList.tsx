import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { challengeApi } from '../services/api';
import clsx from 'clsx';

interface Challenge {
  id: string;
  title: string;
  difficulty: string;
  mode: string;
  domain: string;
  tags: string[];
  elo_band?: number;
  elo_target?: number;
}

const DIFFICULTY_COLORS: Record<string, string> = {
  beginner: 'bg-green-500/20 text-green-400 border-green-700',
  intermediate: 'bg-blue-500/20 text-blue-400 border-blue-700',
  advanced: 'bg-yellow-500/20 text-yellow-400 border-yellow-700',
  expert: 'bg-orange-500/20 text-orange-400 border-orange-700',
  master: 'bg-red-500/20 text-red-400 border-red-700',
};

const MODE_ICONS: Record<string, string> = {
  socratic: '💬',
  adversarial: '⚔️',
  collaborative: '🤝',
};

export default function ChallengeList() {
  const navigate = useNavigate();
  const [challenges, setChallenges] = useState<Challenge[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [diffFilter, setDiffFilter] = useState('');
  const [modeFilter, setModeFilter] = useState('');

  useEffect(() => {
    const controller = new AbortController();
    async function load() {
      try {
        const res = await challengeApi.list({ signal: controller.signal });
        setChallenges(res.data.challenges ?? []);
      } catch {
        if (!controller.signal.aborted) {
          setError('Failed to load challenges. Please try again later.');
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

  const filtered = challenges.filter((c) => {
    if (diffFilter && c.difficulty !== diffFilter) return false;
    if (modeFilter && c.mode !== modeFilter) return false;
    if (search) {
      const q = search.toLowerCase();
      return (
        c.title.toLowerCase().includes(q) ||
        c.tags?.some((t) => t.toLowerCase().includes(q))
      );
    }
    return true;
  });

  const difficulties = [...new Set(challenges.map((c) => c.difficulty))];
  const modes = [...new Set(challenges.map((c) => c.mode))];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400 animate-pulse">Loading challenges...</div>
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

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Challenge Library</h2>

      {/* Filter bar */}
      <div className="bg-gray-800 rounded-xl p-4 border border-gray-700 mb-6">
        <div className="flex flex-wrap items-center gap-4">
          <input
            type="text"
            placeholder="Search challenges..."
            aria-label="Search challenges"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="flex-1 min-w-[200px] px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-gray-100 placeholder-gray-500 text-sm focus:outline-none focus:border-brand-600"
          />
          <select
            value={diffFilter}
            onChange={(e) => setDiffFilter(e.target.value)}
            aria-label="Filter by difficulty"
            className="select-dark px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-gray-300 text-sm focus:outline-none focus:border-brand-600"
          >
            <option value="">All Difficulties</option>
            {difficulties.map((d) => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>
          <select
            value={modeFilter}
            onChange={(e) => setModeFilter(e.target.value)}
            aria-label="Filter by mode"
            className="select-dark px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-gray-300 text-sm focus:outline-none focus:border-brand-600"
          >
            <option value="">All Modes</option>
            {modes.map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Challenge grid */}
      {filtered.length === 0 ? (
        <div className="text-center text-gray-500 py-12">
          {challenges.length === 0
            ? 'No challenges available yet.'
            : 'No challenges match your filters.'}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((c) => (
            <button
              key={c.id}
              onClick={() => navigate(`/challenge/${c.id}`)}
              aria-label={c.title}
              className="bg-gray-800 rounded-xl p-6 border border-gray-700 hover:border-brand-600 transition-colors text-left"
            >
              <div className="flex items-start justify-between mb-3">
                <h3 className="text-sm font-semibold text-gray-100 leading-tight pr-2">
                  {c.title}
                </h3>
                <span className="text-lg flex-shrink-0" title={c.mode}>
                  {MODE_ICONS[c.mode] ?? c.mode}
                </span>
              </div>
              <div className="flex items-center gap-2 mb-3">
                <span
                  className={clsx(
                    'text-xs px-2 py-0.5 rounded border',
                    DIFFICULTY_COLORS[c.difficulty] ?? 'bg-gray-700 text-gray-300 border-gray-600'
                  )}
                >
                  {c.difficulty}
                </span>
                {(c.elo_band ?? c.elo_target) && (
                  <span className="text-xs text-gray-500 font-mono">
                    ELO {c.elo_band ?? c.elo_target}
                  </span>
                )}
              </div>
              <div className="flex flex-wrap gap-1">
                {c.tags?.slice(0, 3).map((tag) => (
                  <span key={tag} className="text-xs text-gray-500 bg-gray-900 px-1.5 py-0.5 rounded">
                    {tag}
                  </span>
                ))}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
