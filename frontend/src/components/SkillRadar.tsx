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
  const values = [elo.overall, elo.architecture, elo.framework_depth, elo.complexity_mgmt];
  const maxElo = Math.max(2000, ...values) + 100;

  const data = [
    { subject: `Overall: ${elo.overall}`, value: elo.overall },
    { subject: `Architecture: ${elo.architecture}`, value: elo.architecture },
    { subject: `Framework: ${elo.framework_depth}`, value: elo.framework_depth },
    { subject: `Complexity: ${elo.complexity_mgmt}`, value: elo.complexity_mgmt },
  ];

  return (
    <ResponsiveContainer width="100%" height="100%">
      <RadarChart data={data} cx="50%" cy="50%" outerRadius="70%">
        <PolarGrid stroke="#4b5563" />
        <PolarAngleAxis dataKey="subject" tick={{ fill: '#d1d5db', fontSize: 11 }} />
        <PolarRadiusAxis domain={[0, maxElo]} tick={{ fill: '#6b7280', fontSize: 10 }} />
        <Radar
          name="ELO"
          dataKey="value"
          stroke="#22c55e"
          fill="#22c55e"
          fillOpacity={0.2}
          animationDuration={1000}
          animationEasing="ease-out"
        />
      </RadarChart>
    </ResponsiveContainer>
  );
}
