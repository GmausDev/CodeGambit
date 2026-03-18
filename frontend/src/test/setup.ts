import '@testing-library/jest-dom';
import React from 'react';

// Mock @monaco-editor/react
vi.mock('@monaco-editor/react', () => ({
  default: (props: Record<string, unknown>) => {
    const handleChange = props.onChange as ((value: string) => void) | undefined;
    return React.createElement('textarea', {
      'data-testid': 'monaco-editor',
      value: props.value as string,
      onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => handleChange?.(e.target.value),
      readOnly: props.options && (props.options as Record<string, unknown>).readOnly ? true : false,
    });
  },
}));

// Mock recharts components to avoid canvas/SVG rendering issues in jsdom
vi.mock('recharts', () => {
  const MockComponent = (props: Record<string, unknown>) =>
    React.createElement('div', { 'data-testid': props['data-testid'] || 'recharts-mock' }, props.children as React.ReactNode);

  return {
    RadarChart: MockComponent,
    Radar: MockComponent,
    PolarGrid: MockComponent,
    PolarAngleAxis: MockComponent,
    PolarRadiusAxis: MockComponent,
    ResponsiveContainer: (props: { children: React.ReactNode }) =>
      React.createElement('div', { 'data-testid': 'responsive-container' }, props.children),
    LineChart: MockComponent,
    Line: MockComponent,
    XAxis: MockComponent,
    YAxis: MockComponent,
    CartesianGrid: MockComponent,
    Tooltip: MockComponent,
    Legend: MockComponent,
  };
});
