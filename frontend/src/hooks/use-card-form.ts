import { useState, useEffect, useCallback } from 'react';
import { useCard, useCreateCard, useUpdateCard, usePreviewCard } from './use-cards';

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
  const [previewHtml, setPreviewHtml] = useState('');

  // カードデータをフォームに反映
  useEffect(() => {
    if (card) {
      setName(card.name);
      setCode(card.code);
      setDatasetId(card.dataset?.id || '');
      setCardType(card.card_type || 'code');
    }
  }, [card]);

  const handleSave = useCallback(() => {
    if (isNew) {
      createMutation.mutate(
        { 
          name, 
          code, 
          dataset_id: cardType === 'code' ? datasetId : undefined,
          card_type: cardType,
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
        { cardId, data: { name, code, card_type: cardType } },
        {
          onSuccess: () => {
            onSaveSuccess?.(cardId);
          },
        }
      );
    }
  }, [isNew, cardId, name, code, datasetId, cardType, createMutation, updateMutation, onSaveSuccess]);

  const handlePreview = useCallback(() => {
    if (!cardId || isNew) return;
    previewMutation.mutate(
      { cardId },
      {
        onSuccess: (result) => setPreviewHtml(result.html),
      }
    );
  }, [cardId, isNew, previewMutation]);

  return {
    // フォーム状態
    name,
    code,
    datasetId,
    cardType,
    previewHtml,
    isLoading,
    isSaving: createMutation.isPending || updateMutation.isPending,
    isPreviewing: previewMutation.isPending,
    // セッター
    setName,
    setCode,
    setDatasetId,
    setCardType,
    // ハンドラ
    handleSave,
    handlePreview,
  };
}
