import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ArrowLeft, Save, Play } from 'lucide-react';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { useCard, useCreateCard, useUpdateCard, usePreviewCard, useDatasets } from '@/hooks';
import { CardEditor } from '@/components/card/CardEditor';
import { CardPreview } from '@/components/card/CardPreview';

const DEFAULT_CODE = `def render(dataset, filters, params):
    import plotly.express as px
    fig = px.bar(dataset, x=dataset.columns[0], y=dataset.columns[1])
    return HTMLResult(html=fig.to_html())
`;

export function CardEditPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isNew = id === 'new';
  const { data: card, isLoading } = useCard(isNew ? '' : id!);
  const { data: datasetsData } = useDatasets({ limit: 100 });
  const createMutation = useCreateCard();
  const updateMutation = useUpdateCard();
  const previewMutation = usePreviewCard();

  const [name, setName] = useState('');
  const [code, setCode] = useState(DEFAULT_CODE);
  const [datasetId, setDatasetId] = useState('');
  const [previewHtml, setPreviewHtml] = useState('');

  useEffect(() => {
    if (card) {
      setName(card.name);
      setCode(card.code);
      setDatasetId(card.dataset?.id || '');
    }
  }, [card]);

  const handleSave = () => {
    if (isNew) {
      createMutation.mutate({ name, code, dataset_id: datasetId }, {
        onSuccess: (newCard) => navigate(`/cards/${newCard.card_id || newCard.id}`),
      });
    } else {
      updateMutation.mutate({ cardId: id!, data: { name, code } }, {
        onSuccess: () => navigate('/cards'),
      });
    }
  };

  const handlePreview = () => {
    if (!id || isNew) return;
    previewMutation.mutate({ cardId: id }, {
      onSuccess: (result) => setPreviewHtml(result.html),
    });
  };

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
            <Button variant="outline" onClick={handlePreview} disabled={previewMutation.isPending}>
              <Play className="h-4 w-4 mr-2" />
              プレビュー
            </Button>
          )}
          <Button onClick={handleSave} disabled={createMutation.isPending || updateMutation.isPending}>
            <Save className="h-4 w-4 mr-2" />
            保存
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>基本設定</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>カード名</Label>
                <Input value={name} onChange={(e) => setName(e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label>データセット</Label>
                <select
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={datasetId}
                  onChange={(e) => setDatasetId(e.target.value)}
                >
                  <option value="">選択してください</option>
                  {datasetsData?.data.map((ds) => (
                    <option key={ds.id} value={ds.id}>{ds.name}</option>
                  ))}
                </select>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Pythonコード</CardTitle>
            </CardHeader>
            <CardContent>
              <CardEditor code={code} onChange={setCode} />
            </CardContent>
          </Card>
        </div>

        <div>
          <Card>
            <CardHeader>
              <CardTitle>プレビュー</CardTitle>
            </CardHeader>
            <CardContent>
              <CardPreview html={previewHtml} isLoading={previewMutation.isPending} />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
