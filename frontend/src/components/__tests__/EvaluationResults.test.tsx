import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import EvaluationResults from '../EvaluationResults';

const sampleEvaluation = {
  overall_score: 75,
  architecture_score: 70,
  framework_depth_score: 80,
  complexity_mgmt_score: 65,
  feedback_summary: 'Good code structure with room for improvement.',
  strengths: ['Clean architecture', 'Good naming'],
  improvements: ['Add error handling', 'Consider edge cases'],
  mode_specific_feedback: 'Socratic mode: great reasoning.',
};

describe('EvaluationResults', () => {
  it('renders the overall score', () => {
    render(<EvaluationResults evaluation={sampleEvaluation} />);
    expect(screen.getByText('75')).toBeInTheDocument();
    expect(screen.getByText('Overall Score')).toBeInTheDocument();
  });

  it('renders dimension scores', () => {
    render(<EvaluationResults evaluation={sampleEvaluation} />);
    expect(screen.getByText('70')).toBeInTheDocument();
    expect(screen.getByText('80')).toBeInTheDocument();
    expect(screen.getByText('65')).toBeInTheDocument();
  });

  it('renders feedback summary', () => {
    render(<EvaluationResults evaluation={sampleEvaluation} />);
    expect(
      screen.getByText('Good code structure with room for improvement.')
    ).toBeInTheDocument();
  });

  it('renders strengths', () => {
    render(<EvaluationResults evaluation={sampleEvaluation} />);
    expect(screen.getByText('Clean architecture')).toBeInTheDocument();
    expect(screen.getByText('Good naming')).toBeInTheDocument();
  });

  it('renders improvements', () => {
    render(<EvaluationResults evaluation={sampleEvaluation} />);
    expect(screen.getByText('Add error handling')).toBeInTheDocument();
    expect(screen.getByText('Consider edge cases')).toBeInTheDocument();
  });

  it('renders mode-specific feedback', () => {
    render(<EvaluationResults evaluation={sampleEvaluation} />);
    expect(
      screen.getByText('Socratic mode: great reasoning.')
    ).toBeInTheDocument();
  });

  it('toggles reference solution visibility', () => {
    render(
      <EvaluationResults
        evaluation={sampleEvaluation}
        referenceSolution="print('solution')"
      />
    );
    // Initially hidden
    expect(screen.queryByText("print('solution')")).not.toBeInTheDocument();

    // Click to show
    fireEvent.click(screen.getByText('Show Reference Solution'));
    expect(screen.getByText("print('solution')")).toBeInTheDocument();

    // Click to hide
    fireEvent.click(screen.getByText('Hide Reference Solution'));
    expect(screen.queryByText("print('solution')")).not.toBeInTheDocument();
  });
});
