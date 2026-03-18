import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface HistoryPoint {
  date: string;
  overall: number;
  architecture: number;
  framework_depth: number;
  complexity_mgmt: number;
}

const LINES = [
  { key: 'overall', color: '#22c55e', label: 'Overall' },
  { key: 'architecture', color: '#3b82f6', label: 'Architecture' },
  { key: 'framework_depth', color: '#a855f7', label: 'Framework Depth' },
  { key: 'complexity_mgmt', color: '#f59e0b', label: 'Complexity Mgmt' },
] as const;

export default function ELOChart({ history }: { history: HistoryPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={history}>
        <XAxis
          dataKey="date"
          stroke="#6b7280"
          tick={{ fill: '#9ca3af', fontSize: 11 }}
        />
        <YAxis stroke="#6b7280" tick={{ fill: '#9ca3af', fontSize: 11 }} />
        <Tooltip
          contentStyle={{
            backgroundColor: '#1f2937',
            border: '1px solid #374151',
            borderRadius: 8,
            color: '#e5e7eb',
          }}
        />
        <Legend wrapperStyle={{ color: '#d1d5db' }} />
        {LINES.map((l) => (
          <Line
            key={l.key}
            type="monotone"
            dataKey={l.key}
            name={l.label}
            stroke={l.color}
            strokeWidth={2}
            dot={false}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
