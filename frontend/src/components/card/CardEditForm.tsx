import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { CardEditor } from './CardEditor';
import { ChartTypePicker } from './ChartTypePicker';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog';
import type { Dataset } from '@/types';
import type { ChartType } from '@/types/card';
import { useState } from 'react';

interface CardEditFormProps {
  name: string;
  code: string;
  datasetId: string;
  cardType: 'code' | 'text';
  chartType?: ChartType;
  datasets?: Dataset[];
  onNameChange: (name: string) => void;
  onCodeChange: (code: string) => void;
  onDatasetIdChange: (datasetId: string) => void;
  onCardTypeChange: (cardType: 'code' | 'text') => void;
  onChartTypeChange: (chartType: ChartType) => void;
}

export function CardEditForm({
  name,
  code,
  datasetId,
  cardType,
  chartType,
  datasets,
  onNameChange,
  onCodeChange,
  onDatasetIdChange,
  onCardTypeChange,
  onChartTypeChange,
}: CardEditFormProps) {
  const isTextCard = cardType === 'text';
  const [pendingChartType, setPendingChartType] = useState<ChartType | null>(null);
  const [hasUnsavedCode, setHasUnsavedCode] = useState(false);

  const handleChartTypeSelect = (newChartType: ChartType) => {
    // 既存のコードがある場合は確認ダイアログを表示
    if (code.trim() && code.trim() !== 'def render(dataset, filters, params):\n    import plotly.express as px\n    fig = px.bar(dataset, x=dataset.columns[0], y=dataset.columns[1])\n    return HTMLResult(html=fig.to_html())') {
      setPendingChartType(newChartType);
      setHasUnsavedCode(true);
    } else {
      onChartTypeChange(newChartType);
    }
  };

  const handleConfirmChartTypeChange = () => {
    if (pendingChartType) {
      onChartTypeChange(pendingChartType);
      setPendingChartType(null);
      setHasUnsavedCode(false);
    }
  };

  const handleCancelChartTypeChange = () => {
    setPendingChartType(null);
    setHasUnsavedCode(false);
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>基本設定</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>カード名</Label>
            <Input value={name} onChange={(e) => onNameChange(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label>カードタイプ</Label>
            <Select value={cardType} onValueChange={(value) => onCardTypeChange(value as 'code' | 'text')}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="code">コードカード (Python)</SelectItem>
                <SelectItem value="text">テキストカード (HTML/Markdown)</SelectItem>
              </SelectContent>
            </Select>
          </div>
          {!isTextCard && (
            <>
              <div className="space-y-2">
                <Label>データセット</Label>
                <Select value={datasetId} onValueChange={onDatasetIdChange}>
                  <SelectTrigger>
                    <SelectValue placeholder="選択してください" />
                  </SelectTrigger>
                  <SelectContent>
                    {datasets?.map((ds) => (
                      <SelectItem key={ds.id} value={ds.id}>
                        {ds.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>チャートタイプ</Label>
                <ChartTypePicker value={chartType} onSelect={handleChartTypeSelect} />
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <AlertDialog open={hasUnsavedCode && pendingChartType !== null} onOpenChange={(open) => !open && handleCancelChartTypeChange()}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>チャートタイプを変更しますか？</AlertDialogTitle>
            <AlertDialogDescription>
              既存のコードが上書きされます。この操作は取り消せません。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={handleCancelChartTypeChange}>キャンセル</AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirmChartTypeChange}>変更する</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <Card>
        <CardHeader>
          <CardTitle>{isTextCard ? 'HTML/Markdownコンテンツ' : 'Pythonコード'}</CardTitle>
        </CardHeader>
        <CardContent>
          {isTextCard ? (
            <Textarea
              value={code}
              onChange={(e) => onCodeChange(e.target.value)}
              placeholder="HTMLまたはMarkdownを入力してください..."
              className="font-mono min-h-[400px]"
            />
          ) : (
            <CardEditor code={code} onChange={onCodeChange} />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
