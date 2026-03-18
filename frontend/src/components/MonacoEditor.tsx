import Editor from '@monaco-editor/react';

interface MonacoEditorProps {
  value: string;
  onChange: (value: string) => void;
  language?: string;
  readOnly?: boolean;
  height?: string;
}

export default function MonacoEditor({
  value,
  onChange,
  language = 'python',
  readOnly = false,
  height = '100%',
}: MonacoEditorProps) {
  return (
    <Editor
      height={height}
      language={language}
      theme="vs-dark"
      value={value}
      onChange={(v) => onChange(v ?? '')}
      options={{
        readOnly,
        fontSize: 14,
        minimap: { enabled: false },
        scrollBeyondLastLine: false,
        automaticLayout: true,
        // Disable all AI / autocomplete suggestions
        quickSuggestions: false,
        suggestOnTriggerCharacters: false,
        wordBasedSuggestions: 'off',
        parameterHints: { enabled: false },
        inlineSuggest: { enabled: false },
        tabCompletion: 'off',
        // Keep helpful editing features
        autoClosingBrackets: 'always',
        autoIndent: 'full',
        matchBrackets: 'always',
        padding: { top: 12 },
      }}
    />
  );
}
