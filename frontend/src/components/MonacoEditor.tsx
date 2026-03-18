import Editor, { type Monaco } from '@monaco-editor/react';
import type { editor as monacoEditor } from 'monaco-editor';

interface MonacoEditorProps {
  value: string;
  onChange: (value: string) => void;
  language?: string;
  readOnly?: boolean;
  height?: string;
  onSubmit?: () => void;
}

export default function MonacoEditor({
  value,
  onChange,
  language = 'python',
  readOnly = false,
  height = '100%',
  onSubmit,
}: MonacoEditorProps) {
  const handleMount = (editor: monacoEditor.IStandaloneCodeEditor, monaco: Monaco) => {
    if (onSubmit) {
      editor.addAction({
        id: 'submit-code',
        label: 'Submit Code',
        keybindings: [monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter],
        run: () => onSubmit(),
      });
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 min-h-0">
        <Editor
          height={height}
          language={language}
          theme="vs-dark"
          value={value}
          onChange={(v) => onChange(v ?? '')}
          onMount={handleMount}
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
      </div>
      {onSubmit && (
        <div className="text-xs text-gray-500 px-3 py-1.5 border-t border-gray-700/50">
          Ctrl+Enter to submit
        </div>
      )}
    </div>
  );
}
