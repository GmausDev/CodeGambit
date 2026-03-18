import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
} from 'recharts';

interface EloScores {
  overall: number;
  architecture: number;
  framework_depth: number;
  complexity_mgmt: number;
}

export default function SkillRadar({ elo }: { elo: EloScores }) {
  const data = [
    { subject: 'Overall', value: elo.overall },
    { subject: 'Architecture', value: elo.architecture },
    { subject: 'Framework Depth', value: elo.framework_depth },
    { subject: 'Complexity Mgmt', value: elo.complexity_mgmt },
  ];

  return (
    <ResponsiveContainer width="100%" height="100%">
      <RadarChart data={data} cx="50%" cy="50%" outerRadius="70%">
        <PolarGrid stroke="#374151" />
        <PolarAngleAxis dataKey="subject" tick={{ fill: '#9ca3af', fontSize: 12 }} />
        <PolarRadiusAxis domain={[0, 2000]} tick={{ fill: '#6b7280', fontSize: 10 }} />
        <Radar
          name="ELO"
          dataKey="value"
          stroke="#22c55e"
          fill="#22c55e"
          fillOpacity={0.2}
        />
      </RadarChart>
    </ResponsiveContainer>
  );
}
