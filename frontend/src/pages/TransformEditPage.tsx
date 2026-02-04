import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ArrowLeft, Save, Play } from 'lucide-react';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { useTransform, useCreateTransform, useUpdateTransform, useExecuteTransform, useDatasets } from '@/hooks';
import { TransformCodeEditor } from '@/components/transform/TransformCodeEditor';
import { DatasetMultiSelect } from '@/components/transform/DatasetMultiSelect';
import { TransformExecutionResult } from '@/components/transform/TransformExecutionResult';
import { TransformExecutionHistory } from '@/components/transform/TransformExecutionHistory';
import { TransformScheduleConfig } from '@/components/transform/TransformScheduleConfig';
import type { TransformExecuteResponse } from '@/types';

const DEFAULT_CODE = `import pandas as pd

# datasets: list[pd.DataFrame] - 入力データセットのリスト
# result: pd.DataFrame - 出力データフレーム

df = datasets[0]
result = df
`;

export function TransformEditPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const isNew = id === 'new';
  const { data: transform, isLoading } = useTransform(isNew ? '' : id!);
  const { data: datasetsData } = useDatasets({ limit: 100 });
  const createMutation = useCreateTransform();
  const updateMutation = useUpdateTransform();
  const executeMutation = useExecuteTransform();
  const isSaving = createMutation.isPending || updateMutation.isPending;

  const [name, setName] = useState('');
  const [code, setCode] = useState(DEFAULT_CODE);
  const [inputDatasetIds, setInputDatasetIds] = useState<string[]>([]);
  const [scheduleCron, setScheduleCron] = useState('');
  const [scheduleEnabled, setScheduleEnabled] = useState(false);
  const [executionResult, setExecutionResult] = useState<TransformExecuteResponse | null>(null);

  useEffect(() => {
    if (transform) {
      setName(transform.name);
      setCode(transform.code);
      setInputDatasetIds(transform.input_dataset_ids);
      setScheduleCron(transform.schedule_cron || '');
      setScheduleEnabled(transform.schedule_enabled || false);
    }
  }, [transform]);

  const handleSave = () => {
    const formData = {
      name, code, input_dataset_ids: inputDatasetIds,
      schedule_cron: scheduleCron || undefined,
      schedule_enabled: scheduleEnabled,
    };
    if (isNew) {
      createMutation.mutate(formData, {
        onSuccess: (newTransform) => navigate(`/transforms/${newTransform.id}`),
      });
    } else {
      updateMutation.mutate({ transformId: id!, data: formData }, {
        onSuccess: () => navigate('/transforms'),
      });
    }
  };

  const handleExecute = () => {
    if (!id || isNew) return;
    executeMutation.mutate(id, {
      onSuccess: (result) => {
        setExecutionResult(result);
        queryClient.invalidateQueries({ queryKey: ['transform-executions', id] });
      },
    });
  };

  if (!isNew && isLoading) {
    return <div className="flex justify-center py-12"><LoadingSpinner size="lg" /></div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => navigate('/transforms')}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <h1 className="text-2xl font-bold">{isNew ? '新規Transform' : 'Transform編集'}</h1>
        <div className="ml-auto flex gap-2">
          {!isNew && (
            <Button variant="outline" onClick={handleExecute} disabled={executeMutation.isPending}>
              <Play className="h-4 w-4 mr-2" />
              実行
            </Button>
          )}
          <Button onClick={handleSave} disabled={isSaving}>
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
                <Label>Transform名</Label>
                <Input value={name} onChange={(e) => setName(e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label>入力データセット</Label>
                <DatasetMultiSelect
                  datasets={datasetsData?.data || []}
                  selectedIds={inputDatasetIds}
                  onChange={setInputDatasetIds}
                />
              </div>
              <div className="space-y-2">
                <Label>スケジュール</Label>
                <TransformScheduleConfig
                  scheduleCron={scheduleCron}
                  scheduleEnabled={scheduleEnabled}
                  onCronChange={setScheduleCron}
                  onEnabledChange={setScheduleEnabled}
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Pythonコード</CardTitle>
            </CardHeader>
            <CardContent>
              <TransformCodeEditor code={code} onChange={setCode} />
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>実行結果</CardTitle>
            </CardHeader>
            <CardContent>
              <TransformExecutionResult result={executionResult} />
            </CardContent>
          </Card>

          {!isNew && (
            <Card>
              <CardHeader>
                <CardTitle>実行履歴</CardTitle>
              </CardHeader>
              <CardContent>
                <TransformExecutionHistory transformId={id!} />
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
