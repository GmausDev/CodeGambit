import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import SkillRadar from '../SkillRadar';

const sampleElo = {
  overall: 1200,
  architecture: 1150,
  framework_depth: 1300,
  complexity_mgmt: 1100,
};

describe('SkillRadar', () => {
  it('renders without crashing', () => {
    render(<SkillRadar elo={sampleElo} />);
    expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
  });

  it('renders with different ELO values', () => {
    const highElo = {
      overall: 1800,
      architecture: 1750,
      framework_depth: 1900,
      complexity_mgmt: 1700,
    };
    render(<SkillRadar elo={highElo} />);
    expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
  });

  it('renders with minimum ELO values', () => {
    const minElo = {
      overall: 100,
      architecture: 100,
      framework_depth: 100,
      complexity_mgmt: 100,
    };
    render(<SkillRadar elo={minElo} />);
    expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
  });
});
