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
import type { Dataset } from '@/types';

interface CardEditFormProps {
  name: string;
  code: string;
  datasetId: string;
  cardType: 'code' | 'text';
  datasets?: Dataset[];
  onNameChange: (name: string) => void;
  onCodeChange: (code: string) => void;
  onDatasetIdChange: (datasetId: string) => void;
  onCardTypeChange: (cardType: 'code' | 'text') => void;
}

export function CardEditForm({
  name,
  code,
  datasetId,
  cardType,
  datasets,
  onNameChange,
  onCodeChange,
  onDatasetIdChange,
  onCardTypeChange,
}: CardEditFormProps) {
  const isTextCard = cardType === 'text';

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
          )}
        </CardContent>
      </Card>

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
