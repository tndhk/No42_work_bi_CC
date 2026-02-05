import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
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
  datasets?: Dataset[];
  onNameChange: (name: string) => void;
  onCodeChange: (code: string) => void;
  onDatasetIdChange: (datasetId: string) => void;
}

export function CardEditForm({
  name,
  code,
  datasetId,
  datasets,
  onNameChange,
  onCodeChange,
  onDatasetIdChange,
}: CardEditFormProps) {
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
            <Label>データセット</Label>
            <Select value={datasetId} onValueChange={onDatasetIdChange}>
              <SelectTrigger>
                <SelectValue placeholder="選択してください" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">選択してください</SelectItem>
                {datasets?.map((ds) => (
                  <SelectItem key={ds.id} value={ds.id}>
                    {ds.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Pythonコード</CardTitle>
        </CardHeader>
        <CardContent>
          <CardEditor code={code} onChange={onCodeChange} />
        </CardContent>
      </Card>
    </div>
  );
}
