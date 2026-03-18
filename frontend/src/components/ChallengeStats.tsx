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

function ProgressBar({ label, completed, total }: { label: string; completed: number; total: number }) {
  const pct = total > 0 ? Math.round((completed / total) * 100) : 0;
  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-300">{label}</span>
        <span className="text-gray-400">{completed}/{total}</span>
      </div>
      <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
        <div
          className="h-full bg-brand-600 rounded-full transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export default function ChallengeStats({ total, completed, byMode, byDifficulty }: ChallengeStatsProps) {
  return (
    <div className="space-y-6">
      <ProgressBar label="Overall Progress" completed={completed} total={total} />

      <div>
        <h4 className="text-sm font-semibold text-gray-400 mb-3">By Mode</h4>
        <div className="space-y-2">
          {Object.entries(byMode).map(([mode, stats]) => (
            <ProgressBar key={mode} label={mode} completed={stats.completed} total={stats.total} />
          ))}
        </div>
      </div>

      <div>
        <h4 className="text-sm font-semibold text-gray-400 mb-3">By Difficulty</h4>
        <div className="space-y-2">
          {Object.entries(byDifficulty).map(([diff, stats]) => (
            <ProgressBar key={diff} label={diff} completed={stats.completed} total={stats.total} />
          ))}
        </div>
      </div>
    </div>
  );
}
