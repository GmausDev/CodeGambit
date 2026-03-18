import clsx from 'clsx';

interface Challenge {
  id: string;
  title: string;
  description: string;
  difficulty: string;
  mode: string;
  domain: string;
  tags: string[];
  constraints: Record<string, unknown> | string[];
  estimated_minutes?: number;
}

interface ChallengeBriefingProps {
  challenge: Challenge;
}

const difficultyColors: Record<string, string> = {
  beginner: 'bg-green-600/20 text-green-400 border-green-600/30',
  intermediate: 'bg-yellow-600/20 text-yellow-400 border-yellow-600/30',
  advanced: 'bg-orange-600/20 text-orange-400 border-orange-600/30',
  expert: 'bg-red-600/20 text-red-400 border-red-600/30',
  master: 'bg-purple-600/20 text-purple-400 border-purple-600/30',
};

const modeLabels: Record<string, string> = {
  socratic: '\uD83C\uDF93 Socratic',
  adversarial: '\u2694\uFE0F Adversarial',
  collaborative: '\uD83E\uDD1D Collaborative',
};

function renderConstraints(constraints: Record<string, unknown> | string[]): string[] {
  if (Array.isArray(constraints)) return constraints;
  // If it's an object, try to extract values
  return Object.values(constraints).flatMap((v) =>
    Array.isArray(v) ? v.map(String) : [String(v)]
  );
}

export default function ChallengeBriefing({ challenge }: ChallengeBriefingProps) {
  const constraintList = renderConstraints(challenge.constraints);

  return (
    <div className="flex flex-col gap-4 h-full overflow-auto">
      {/* Title */}
      <h2 className="text-lg font-bold text-gray-100">{challenge.title}</h2>

      {/* Badges row */}
      <div className="flex flex-wrap gap-2">
        <span
          className={clsx(
            'text-xs font-medium px-2 py-0.5 rounded border',
            difficultyColors[challenge.difficulty] ?? 'bg-gray-600/20 text-gray-400 border-gray-600/30'
          )}
        >
          {challenge.difficulty}
        </span>
        <span className="text-xs font-medium px-2 py-0.5 rounded border bg-blue-600/20 text-blue-400 border-blue-600/30">
          {modeLabels[challenge.mode] ?? challenge.mode}
        </span>
        <span className="text-xs font-medium px-2 py-0.5 rounded border bg-gray-600/20 text-gray-400 border-gray-600/30">
          {challenge.domain}
        </span>
        {challenge.estimated_minutes && (
          <span className="text-xs text-gray-500">
            ~{challenge.estimated_minutes} min
          </span>
        )}
      </div>

      {/* Tags */}
      {challenge.tags.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {challenge.tags.map((tag) => (
            <span
              key={tag}
              className="text-xs px-1.5 py-0.5 rounded bg-gray-700/50 text-gray-400"
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* Description (rendered as plain text with whitespace preserved) */}
      <div className="text-sm text-gray-300 whitespace-pre-wrap leading-relaxed">
        {challenge.description}
      </div>

      {/* Constraints */}
      {constraintList.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
            Constraints
          </h4>
          <ul className="space-y-1">
            {constraintList.map((c, i) => (
              <li key={i} className="text-sm text-gray-400 flex gap-2">
                <span className="text-gray-600">-</span>
                {c}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
