import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ArrowLeft, Upload } from 'lucide-react';
import { useCreateDataset } from '@/hooks';

export function DatasetImportPage() {
  const navigate = useNavigate();
  const createMutation = useCreateDataset();
  const [file, setFile] = useState<File | null>(null);
  const [name, setName] = useState('');
  const [delimiter, setDelimiter] = useState(',');
  const [hasHeader, setHasHeader] = useState(true);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.name.endsWith('.csv')) {
      setFile(droppedFile);
      if (!name) setName(droppedFile.name.replace('.csv', ''));
    }
  }, [name]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      if (!name) setName(selectedFile.name.replace('.csv', ''));
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !name.trim()) return;

    const formData = new FormData();
    formData.append('file', file);
    formData.append('name', name);
    formData.append('delimiter', delimiter);
    formData.append('has_header', String(hasHeader));

    createMutation.mutate(formData, {
      onSuccess: (dataset) => {
        navigate(`/datasets/${dataset.dataset_id}`);
      },
    });
  };

  return (
    <div className="space-y-4 max-w-2xl">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => navigate('/datasets')}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <h1 className="text-2xl font-bold">データセットインポート</h1>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>CSVファイル</CardTitle>
          </CardHeader>
          <CardContent>
            <div
              className="border-2 border-dashed rounded-lg p-8 text-center cursor-pointer hover:border-primary transition-colors"
              onDrop={handleDrop}
              onDragOver={(e) => e.preventDefault()}
              onClick={() => document.getElementById('file-input')?.click()}
            >
              <Upload className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
              {file ? (
                <p className="text-sm">{file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)</p>
              ) : (
                <p className="text-sm text-muted-foreground">
                  CSVファイルをドラッグ&ドロップ、またはクリックして選択
                </p>
              )}
              <input
                id="file-input"
                type="file"
                accept=".csv"
                className="hidden"
                onChange={handleFileChange}
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>インポート設定</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="dataset-name">データセット名</Label>
              <Input
                id="dataset-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="データセット名"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="delimiter">区切り文字</Label>
              <Input
                id="delimiter"
                value={delimiter}
                onChange={(e) => setDelimiter(e.target.value)}
                className="w-20"
              />
            </div>
            <div className="flex items-center gap-2">
              <input
                id="has-header"
                type="checkbox"
                checked={hasHeader}
                onChange={(e) => setHasHeader(e.target.checked)}
                className="rounded"
              />
              <Label htmlFor="has-header">先頭行をヘッダとして使用</Label>
            </div>
          </CardContent>
        </Card>

        {createMutation.isError && (
          <p className="text-sm text-destructive">インポートに失敗しました。ファイルの形式を確認してください。</p>
        )}

        <div className="flex gap-2">
          <Button variant="outline" type="button" onClick={() => navigate('/datasets')}>
            キャンセル
          </Button>
          <Button type="submit" disabled={!file || !name.trim() || createMutation.isPending}>
            {createMutation.isPending ? 'インポート中...' : 'インポート'}
          </Button>
        </div>
      </form>
    </div>
  );
}
