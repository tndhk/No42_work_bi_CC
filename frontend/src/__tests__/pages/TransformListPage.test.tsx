import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { TransformListPage } from '@/pages/TransformListPage';
import { createWrapper, createMockTransform, createMockPaginatedResponse } from '@/__tests__/helpers/test-utils';

const mockNavigate = vi.fn();
const mockDeleteMutate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return { ...actual, useNavigate: () => mockNavigate };
});

vi.mock('@/hooks', () => ({
  useTransforms: vi.fn(),
  useDeleteTransform: vi.fn(() => ({ mutate: mockDeleteMutate })),
}));

import { useTransforms } from '@/hooks';
const mockUseTransforms = useTransforms as ReturnType<typeof vi.fn>;

describe('TransformListPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it('ローディング中はスピナーを表示する', () => {
    mockUseTransforms.mockReturnValue({ data: undefined, isLoading: true } as any);

    render(<MemoryRouter><TransformListPage /></MemoryRouter>, { wrapper: createWrapper() });

    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('Transform一覧をテーブルに表示する', () => {
    const transforms = [
      createMockTransform({ id: 'tf-1', name: 'Transform 1' }),
      createMockTransform({ id: 'tf-2', name: 'Transform 2' }),
    ];

    mockUseTransforms.mockReturnValue({
      data: createMockPaginatedResponse(transforms),
      isLoading: false,
    } as any);

    render(<MemoryRouter><TransformListPage /></MemoryRouter>, { wrapper: createWrapper() });

    expect(screen.getByText('Transform 1')).toBeInTheDocument();
    expect(screen.getByText('Transform 2')).toBeInTheDocument();
  });

  it('Transformがない場合はメッセージを表示する', () => {
    mockUseTransforms.mockReturnValue({
      data: createMockPaginatedResponse([]),
      isLoading: false,
    } as any);

    render(<MemoryRouter><TransformListPage /></MemoryRouter>, { wrapper: createWrapper() });

    expect(screen.getByText('Transformがありません')).toBeInTheDocument();
  });

  it('新規作成ボタンがある', () => {
    mockUseTransforms.mockReturnValue({
      data: createMockPaginatedResponse([]),
      isLoading: false,
    } as any);

    render(<MemoryRouter><TransformListPage /></MemoryRouter>, { wrapper: createWrapper() });

    expect(screen.getByRole('button', { name: /新規作成/ })).toBeInTheDocument();
  });

  it('テーブルに入力データセット数を表示する', () => {
    const transforms = [
      createMockTransform({ id: 'tf-1', name: 'Transform 1', input_dataset_ids: ['ds-1', 'ds-2', 'ds-3'] }),
    ];

    mockUseTransforms.mockReturnValue({
      data: createMockPaginatedResponse(transforms),
      isLoading: false,
    } as any);

    render(<MemoryRouter><TransformListPage /></MemoryRouter>, { wrapper: createWrapper() });

    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('テーブルにオーナー名を表示する', () => {
    const transforms = [
      createMockTransform({ id: 'tf-1', owner: { user_id: 'u-1', name: 'Alice' } }),
    ];

    mockUseTransforms.mockReturnValue({
      data: createMockPaginatedResponse(transforms),
      isLoading: false,
    } as any);

    render(<MemoryRouter><TransformListPage /></MemoryRouter>, { wrapper: createWrapper() });

    expect(screen.getByText('Alice')).toBeInTheDocument();
  });

  it('ページネーションが表示される', () => {
    const transforms = Array.from({ length: 10 }, (_, i) =>
      createMockTransform({ id: `tf-${i}` })
    );

    mockUseTransforms.mockReturnValue({
      data: createMockPaginatedResponse(transforms, 100),
      isLoading: false,
    } as any);

    render(<MemoryRouter><TransformListPage /></MemoryRouter>, { wrapper: createWrapper() });

    expect(screen.getByText(/100件中/)).toBeInTheDocument();
  });
});
