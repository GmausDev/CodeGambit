import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import MonacoEditor from '../MonacoEditor';

describe('MonacoEditor', () => {
  it('renders the editor', () => {
    render(<MonacoEditor value="test code" onChange={() => {}} />);
    const editor = screen.getByTestId('monaco-editor');
    expect(editor).toBeInTheDocument();
  });

  it('displays the provided value', () => {
    render(<MonacoEditor value="print('hello')" onChange={() => {}} />);
    const editor = screen.getByTestId('monaco-editor');
    expect(editor).toHaveValue("print('hello')");
  });

  it('calls onChange when value changes', () => {
    const handleChange = vi.fn();
    render(<MonacoEditor value="" onChange={handleChange} />);
    const editor = screen.getByTestId('monaco-editor');
    fireEvent.change(editor, { target: { value: 'new code' } });
    expect(handleChange).toHaveBeenCalledWith('new code');
  });
});
