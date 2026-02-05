import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ArrowLeft, Save, Play } from 'lucide-react';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { useDatasets } from '@/hooks';
import { CardPreview } from '@/components/card/CardPreview';
import { CardEditForm } from '@/components/card/CardEditForm';
import { useCardForm } from '@/hooks/use-card-form';

export function CardEditPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isNew = id === 'new';
  const { data: datasetsData } = useDatasets({ limit: 100 });

  const {
    name,
    code,
    datasetId,
    previewHtml,
    isLoading,
    isSaving,
    isPreviewing,
    setName,
    setCode,
    setDatasetId,
    handleSave,
    handlePreview,
  } = useCardForm({
    cardId: id,
    isNew,
    onSaveSuccess: (savedCardId) => {
      if (isNew) {
        navigate(`/cards/${savedCardId}`);
      } else {
        navigate('/cards');
      }
    },
  });

  if (!isNew && isLoading) {
    return <div className="flex justify-center py-12"><LoadingSpinner size="lg" /></div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => navigate('/cards')}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <h1 className="text-2xl font-bold">{isNew ? '新規カード' : 'カード編集'}</h1>
        <div className="ml-auto flex gap-2">
          {!isNew && (
            <Button variant="outline" onClick={handlePreview} disabled={isPreviewing}>
              <Play className="h-4 w-4 mr-2" />
              プレビュー
            </Button>
          )}
          <Button onClick={handleSave} disabled={isSaving}>
            <Save className="h-4 w-4 mr-2" />
            保存
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <CardEditForm
          name={name}
          code={code}
          datasetId={datasetId}
          datasets={datasetsData?.data}
          onNameChange={setName}
          onCodeChange={setCode}
          onDatasetIdChange={setDatasetId}
        />

        <div>
          <Card>
            <CardHeader>
              <CardTitle>プレビュー</CardTitle>
            </CardHeader>
            <CardContent>
              <CardPreview html={previewHtml} isLoading={isPreviewing} />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
