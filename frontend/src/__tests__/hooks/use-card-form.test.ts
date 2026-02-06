import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useCardForm } from '@/hooks/use-card-form';
import { createWrapper } from '@/__tests__/helpers/test-utils';
import type { CardDetail } from '@/types';

const mockUseCard = vi.fn();
const mockCreateMutation = { mutate: vi.fn(), isPending: false };
const mockUpdateMutation = { mutate: vi.fn(), isPending: false };
const mockPreviewMutation = { mutate: vi.fn(), isPending: false };

vi.mock('@/hooks/use-cards', () => ({
  useCard: () => mockUseCard(),
  useCreateCard: () => mockCreateMutation,
  useUpdateCard: () => mockUpdateMutation,
  usePreviewCard: () => mockPreviewMutation,
}));

describe('useCardForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseCard.mockReturnValue({ data: undefined, isLoading: false });
  });

  it('新規作成モードではデフォルトコードが設定される', () => {
    const { result } = renderHook(
      () => useCardForm({ cardId: undefined, isNew: true }),
      { wrapper: createWrapper() }
    );

    expect(result.current.name).toBe('');
    expect(result.current.code).toContain('def render(dataset, filters, params):');
    expect(result.current.datasetId).toBe('');
  });

  it('編集モードでは既存カードデータを読み込む', async () => {
    const mockCard: CardDetail = {
      card_id: 'card-001',
      name: 'Test Card',
      code: 'def render(dataset, filters, params):\n    return HTMLResult("")',
      dataset: { id: 'dataset-001', name: 'Test Dataset' },
      owner: { user_id: 'owner-1', name: 'Owner' },
      created_at: '2026-01-01T00:00:00Z',
    };

    mockUseCard.mockReturnValue({ data: mockCard, isLoading: false });

    const { result } = renderHook(
      () => useCardForm({ cardId: 'card-001', isNew: false }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.name).toBe('Test Card');
      expect(result.current.code).toContain('def render');
      expect(result.current.datasetId).toBe('dataset-001');
    });
  });

  it('新規作成時にhandleSaveを呼ぶとcreateが実行される', () => {
    const onSaveSuccess = vi.fn();

    const { result } = renderHook(
      () => useCardForm({ cardId: undefined, isNew: true, onSaveSuccess }),
      { wrapper: createWrapper() }
    );

    act(() => {
      result.current.setName('New Card');
      result.current.setDatasetId('dataset-001');
    });

    act(() => {
      result.current.handleSave();
    });

    expect(mockCreateMutation.mutate).toHaveBeenCalledWith(
      {
        name: 'New Card',
        code: expect.stringContaining('def render'),
        dataset_id: 'dataset-001',
      },
      expect.any(Object)
    );
  });

  it('編集時にhandleSaveを呼ぶとupdateが実行される', async () => {
    const mockCard: CardDetail = {
      card_id: 'card-001',
      name: 'Test Card',
      code: 'original code',
      dataset: { id: 'dataset-001', name: 'Test Dataset' },
      owner: { user_id: 'owner-1', name: 'Owner' },
      created_at: '2026-01-01T00:00:00Z',
    };

    mockUseCard.mockReturnValue({ data: mockCard, isLoading: false });

    const onSaveSuccess = vi.fn();

    const { result } = renderHook(
      () => useCardForm({ cardId: 'card-001', isNew: false, onSaveSuccess }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.name).toBe('Test Card');
    });

    act(() => {
      result.current.setName('Updated Card');
      result.current.setCode('updated code');
    });

    act(() => {
      result.current.handleSave();
    });

    expect(mockUpdateMutation.mutate).toHaveBeenCalledWith(
      {
        cardId: 'card-001',
        data: {
          name: 'Updated Card',
          code: 'updated code',
        },
      },
      expect.any(Object)
    );
  });

  it('保存成功時にコールバックが呼ばれる', () => {
    const onSaveSuccess = vi.fn();
    mockCreateMutation.mutate.mockImplementation((data, options) => {
      options.onSuccess({ card_id: 'new-card-001' });
    });

    const { result } = renderHook(
      () => useCardForm({ cardId: undefined, isNew: true, onSaveSuccess }),
      { wrapper: createWrapper() }
    );

    result.current.handleSave();

    expect(onSaveSuccess).toHaveBeenCalledWith('new-card-001');
  });

  it('プレビューは編集モードでのみ実行可能', () => {
    const { result: newResult } = renderHook(
      () => useCardForm({ cardId: undefined, isNew: true }),
      { wrapper: createWrapper() }
    );

    newResult.current.handlePreview();
    expect(mockPreviewMutation.mutate).not.toHaveBeenCalled();

    const mockCard: CardDetail = {
      card_id: 'card-001',
      name: 'Test Card',
      code: 'code',
      dataset: { id: 'dataset-001', name: 'Test Dataset' },
      owner: { user_id: 'owner-1', name: 'Owner' },
      created_at: '2026-01-01T00:00:00Z',
    };

    mockUseCard.mockReturnValue({ data: mockCard, isLoading: false });

    const { result: editResult } = renderHook(
      () => useCardForm({ cardId: 'card-001', isNew: false }),
      { wrapper: createWrapper() }
    );

    editResult.current.handlePreview();
    expect(mockPreviewMutation.mutate).toHaveBeenCalledWith(
      { cardId: 'card-001' },
      expect.any(Object)
    );
  });

  it('プレビュー成功時にHTMLが設定される', () => {
    const mockCard: CardDetail = {
      card_id: 'card-001',
      name: 'Test Card',
      code: 'code',
      dataset: { id: 'dataset-001', name: 'Test Dataset' },
      owner: { user_id: 'owner-1', name: 'Owner' },
      created_at: '2026-01-01T00:00:00Z',
    };

    mockUseCard.mockReturnValue({ data: mockCard, isLoading: false });

    mockPreviewMutation.mutate.mockImplementation((data, options) => {
      options.onSuccess({ html: '<div>Preview</div>' });
    });

    const { result } = renderHook(
      () => useCardForm({ cardId: 'card-001', isNew: false }),
      { wrapper: createWrapper() }
    );

    result.current.handlePreview();

    waitFor(() => {
      expect(result.current.previewHtml).toBe('<div>Preview</div>');
    });
  });

  it('isSavingは保存中にtrueになる', () => {
    mockCreateMutation.isPending = true;

    const { result } = renderHook(
      () => useCardForm({ cardId: undefined, isNew: true }),
      { wrapper: createWrapper() }
    );

    expect(result.current.isSaving).toBe(true);
  });

  it('isPreviewingはプレビュー中にtrueになる', () => {
    const mockCard: CardDetail = {
      card_id: 'card-001',
      name: 'Test Card',
      code: 'code',
      dataset: { id: 'dataset-001', name: 'Test Dataset' },
      owner: { user_id: 'owner-1', name: 'Owner' },
      created_at: '2026-01-01T00:00:00Z',
    };

    mockUseCard.mockReturnValue({ data: mockCard, isLoading: false });
    mockPreviewMutation.isPending = true;

    const { result } = renderHook(
      () => useCardForm({ cardId: 'card-001', isNew: false }),
      { wrapper: createWrapper() }
    );

    expect(result.current.isPreviewing).toBe(true);
  });
});
