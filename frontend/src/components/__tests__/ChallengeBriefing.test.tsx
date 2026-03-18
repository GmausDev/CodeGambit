import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import ChallengeBriefing from '../ChallengeBriefing';

const sampleChallenge = {
  id: 'test-001',
  title: 'Test Challenge',
  description: 'Build a test system.',
  difficulty: 'intermediate',
  mode: 'socratic',
  domain: 'langchain',
  tags: ['test', 'unit'],
  constraints: ['Must use TypeScript', 'No external libs'],
};

describe('ChallengeBriefing', () => {
  it('renders the challenge title', () => {
    render(<ChallengeBriefing challenge={sampleChallenge} />);
    expect(screen.getByText('Test Challenge')).toBeInTheDocument();
  });

  it('renders difficulty badge', () => {
    render(<ChallengeBriefing challenge={sampleChallenge} />);
    expect(screen.getByText('intermediate')).toBeInTheDocument();
  });

  it('renders mode badge', () => {
    render(<ChallengeBriefing challenge={sampleChallenge} />);
    // Mode label for socratic includes emoji prefix
    expect(screen.getByText(/Socratic/)).toBeInTheDocument();
  });

  it('renders domain', () => {
    render(<ChallengeBriefing challenge={sampleChallenge} />);
    expect(screen.getByText('langchain')).toBeInTheDocument();
  });

  it('renders tags', () => {
    render(<ChallengeBriefing challenge={sampleChallenge} />);
    expect(screen.getByText('test')).toBeInTheDocument();
    expect(screen.getByText('unit')).toBeInTheDocument();
  });

  it('renders description', () => {
    render(<ChallengeBriefing challenge={sampleChallenge} />);
    expect(screen.getByText('Build a test system.')).toBeInTheDocument();
  });

  it('renders constraints', () => {
    render(<ChallengeBriefing challenge={sampleChallenge} />);
    expect(screen.getByText('Must use TypeScript')).toBeInTheDocument();
    expect(screen.getByText('No external libs')).toBeInTheDocument();
  });
});
