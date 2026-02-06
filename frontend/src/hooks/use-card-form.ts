import { useState, useEffect, useCallback } from 'react';
import { useCard, useCreateCard, useUpdateCard, usePreviewCard } from './use-cards';
import { cardsApi } from '@/lib/api';
import { getChartTemplate } from '@/lib/chart-templates';
import type { ChartType } from '@/types/card';

const DEFAULT_CODE = `def render(dataset, filters, params):
    import plotly.express as px
    fig = px.bar(dataset, x=dataset.columns[0], y=dataset.columns[1])
    return HTMLResult(html=fig.to_html())
`;

interface UseCardFormOptions {
  cardId: string | undefined;
  isNew: boolean;
  onSaveSuccess?: (cardId: string) => void;
}

/**
 * カード編集フォームの状態と操作を管理するカスタムフック
 */
export function useCardForm({ cardId, isNew, onSaveSuccess }: UseCardFormOptions) {
  const { data: card, isLoading } = useCard(isNew ? '' : cardId || '');
  const createMutation = useCreateCard();
  const updateMutation = useUpdateCard();
  const previewMutation = usePreviewCard();

  const [name, setName] = useState('');
  const [code, setCode] = useState(DEFAULT_CODE);
  const [datasetId, setDatasetId] = useState('');
  const [cardType, setCardType] = useState<'code' | 'text'>('code');
  const [chartType, setChartType] = useState<ChartType | undefined>(undefined);
  const [previewHtml, setPreviewHtml] = useState('');
  const [isPreviewing, setIsPreviewing] = useState(false);

  // カードデータをフォームに反映
  useEffect(() => {
    if (card) {
      setName(card.name);
      setCode(card.code);
      setDatasetId(card.dataset?.id || '');
      setCardType(card.card_type || 'code');
      // paramsからchart_typeを取得
      if (card.params && 'chart_type' in card.params) {
        setChartType(card.params.chart_type as ChartType);
      } else if ('chart_type' in card && card.chart_type) {
        setChartType(card.chart_type);
      }
    }
  }, [card]);

  // チャートタイプ変更時にテンプレートコードを挿入
  const handleChartTypeChange = useCallback((newChartType: ChartType) => {
    setChartType(newChartType);
    const template = getChartTemplate(newChartType);
    setCode(template.code);
  }, []);

  const handleSave = useCallback(() => {
    const params = chartType ? { chart_type: chartType } : undefined;
    
    if (isNew) {
      createMutation.mutate(
        { 
          name, 
          code, 
          dataset_id: cardType === 'code' ? datasetId : undefined,
          card_type: cardType,
          params,
        },
        {
          onSuccess: (newCard) => {
            const savedCardId = newCard.card_id || newCard.id;
            onSaveSuccess?.(savedCardId);
          },
        }
      );
    } else if (cardId) {
      updateMutation.mutate(
        { cardId, data: { name, code, card_type: cardType, params } },
        {
          onSuccess: () => {
            onSaveSuccess?.(cardId);
          },
        }
      );
    }
  }, [isNew, cardId, name, code, datasetId, cardType, chartType, createMutation, updateMutation, onSaveSuccess]);

  const handlePreview = useCallback(async () => {
    // コードカードの場合はdataset_idが必要
    if (cardType === 'code' && !datasetId) {
      return;
    }

    setIsPreviewing(true);
    try {
      let result;
      if (isNew || !cardId) {
        // 新規カード: previewDraft APIを使用
        if (cardType === 'code') {
          result = await cardsApi.previewDraft({
            code,
            datasetId,
            filters: {},
          });
        } else {
          // テキストカードは直接HTMLを表示
          setPreviewHtml(code);
          setIsPreviewing(false);
          return;
        }
      } else {
        // 既存カード: 現在のコードを送信してプレビュー
        result = await cardsApi.preview(cardId, {
          code,
          datasetId,
          filters: {},
        });
      }
      setPreviewHtml(result.html);
    } catch (error) {
      console.error('Preview failed:', error);
      setPreviewHtml('<div style="color:red">プレビューエラーが発生しました</div>');
    } finally {
      setIsPreviewing(false);
    }
  }, [cardId, isNew, cardType, code, datasetId]);

  return {
    // フォーム状態
    name,
    code,
    datasetId,
    cardType,
    chartType,
    previewHtml,
    isLoading,
    isSaving: createMutation.isPending || updateMutation.isPending,
    isPreviewing,
    // セッター
    setName,
    setCode,
    setDatasetId,
    setCardType,
    // ハンドラ
    handleSave,
    handlePreview,
    handleChartTypeChange,
  };
}
