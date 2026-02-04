import Editor from '@monaco-editor/react';

interface TransformCodeEditorProps {
  code: string;
  onChange: (code: string) => void;
}

export function TransformCodeEditor({ code, onChange }: TransformCodeEditorProps) {
  return (
    <div className="border rounded-md overflow-hidden h-[500px]">
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
