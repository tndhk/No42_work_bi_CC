import Editor from '@monaco-editor/react';

interface CardEditorProps {
  code: string;
  onChange: (code: string) => void;
}

export function CardEditor({ code, onChange }: CardEditorProps) {
  return (
    <div className="border rounded-md overflow-hidden" style={{ height: 400 }}>
      <Editor
        defaultLanguage="python"
        value={code}
        onChange={(value) => onChange(value || '')}
        theme="vs-dark"
        options={{
          minimap: { enabled: false },
          fontSize: 14,
          tabSize: 4,
          wordWrap: 'on',
          scrollBeyondLastLine: false,
          automaticLayout: true,
        }}
      />
    </div>
  );
}
