interface StatGroup {
  total: number;
  completed: number;
}

interface ChallengeStatsProps {
  total: number;
  completed: number;
  byMode: Record<string, StatGroup>;
  byDifficulty: Record<string, StatGroup>;
}

const DIFFICULTY_COLORS: Record<string, string> = {
  easy: 'bg-green-500',
  medium: 'bg-blue-500',
  hard: 'bg-yellow-500',
  expert: 'bg-orange-500',
  grandmaster: 'bg-red-500',
};

function ProgressBar({
  label,
  completed,
  total,
  colorClass,
}: {
  label: string;
  completed: number;
  total: number;
  colorClass?: string;
}) {
  const pct = total > 0 ? Math.round((completed / total) * 100) : 0;
  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-300">{label}</span>
        <span className="text-gray-400">
          {completed}/{total}{total > 0 ? ` (${pct}%)` : ''}
        </span>
      </div>
      <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
        {total > 0 ? (
          <div
            className={`h-full rounded-full transition-all ${colorClass ?? 'bg-brand-600'}`}
            style={{ width: `${pct}%` }}
          />
        ) : (
          <div className="h-full w-full bg-gray-600/30 rounded-full" />
        )}
      </div>
    </div>
  );
}

export default function ChallengeStats({ total, completed, byMode, byDifficulty }: ChallengeStatsProps) {
  return (
    <div className="space-y-6">
      <ProgressBar label="Overall Progress" completed={completed} total={total} />

      {Object.keys(byMode).length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-gray-400 mb-3">By Mode</h4>
          <div className="space-y-2">
            {Object.entries(byMode).map(([mode, stats]) => (
              <ProgressBar key={mode} label={mode} completed={stats.completed} total={stats.total} />
            ))}
          </div>
        </div>
      )}

      {Object.keys(byDifficulty).length > 0 ? (
        <div>
          <h4 className="text-sm font-semibold text-gray-400 mb-3">By Difficulty</h4>
          <div className="space-y-2">
            {Object.entries(byDifficulty).map(([diff, stats]) => (
              <ProgressBar
                key={diff}
                label={diff}
                completed={stats.completed}
                total={stats.total}
                colorClass={DIFFICULTY_COLORS[diff.toLowerCase()]}
              />
            ))}
          </div>
        </div>
      ) : (
        <p className="text-sm text-gray-500">No challenges attempted yet.</p>
      )}
    </div>
  );
}
