import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { CardEditPage } from '@/pages/CardEditPage';
import { createWrapper, createMockPaginatedResponse, createMockDataset } from '@/__tests__/helpers/test-utils';

const mockNavigate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: () => ({ id: 'new' }),
  };
});

vi.mock('@/hooks', () => ({
  useCard: vi.fn(() => ({ data: null, isLoading: false })),
  useDatasets: vi.fn(() => ({ data: null })),
  useCreateCard: vi.fn(() => ({ mutate: vi.fn(), isPending: false })),
  useUpdateCard: vi.fn(() => ({ mutate: vi.fn(), isPending: false })),
  usePreviewCard: vi.fn(() => ({ mutate: vi.fn(), isPending: false })),
}));

vi.mock('@/components/card/CardEditor', () => ({
  CardEditor: ({ code, onChange }: any) => (
    <textarea data-testid="card-editor" value={code} onChange={(e) => onChange(e.target.value)} />
  ),
}));

vi.mock('@/components/card/CardPreview', () => ({
  CardPreview: () => <div data-testid="card-preview">Preview</div>,
}));

import { useCard, useDatasets } from '@/hooks';
const mockUseCard = useCard as ReturnType<typeof vi.fn>;
const mockUseDatasets = useDatasets as ReturnType<typeof vi.fn>;

describe('CardEditPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it('新規作成モードで「新規カード」を表示する', () => {
    mockUseCard.mockReturnValue({ data: null, isLoading: false } as any);
    mockUseDatasets.mockReturnValue({ data: null } as any);

    render(
      <MemoryRouter initialEntries={['/cards/new']}>
        <Routes>
          <Route path="/cards/:id" element={<CardEditPage />} />
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('新規カード')).toBeInTheDocument();
  });

  it('カード名入力フィールドがある', () => {
    mockUseCard.mockReturnValue({ data: null, isLoading: false } as any);
    mockUseDatasets.mockReturnValue({ data: null } as any);

    render(
      <MemoryRouter initialEntries={['/cards/new']}>
        <Routes>
          <Route path="/cards/:id" element={<CardEditPage />} />
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('カード名')).toBeInTheDocument();
  });

  it('データセット選択フィールドがある', () => {
    const datasets = [createMockDataset({ id: 'ds-1', name: 'Dataset 1' })];
    mockUseCard.mockReturnValue({ data: null, isLoading: false } as any);
    mockUseDatasets.mockReturnValue({
      data: createMockPaginatedResponse(datasets),
    } as any);

    render(
      <MemoryRouter initialEntries={['/cards/new']}>
        <Routes>
          <Route path="/cards/:id" element={<CardEditPage />} />
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('データセット')).toBeInTheDocument();
    expect(screen.getByText('Dataset 1')).toBeInTheDocument();
  });

  it('Pythonコードエディタがある', () => {
    mockUseCard.mockReturnValue({ data: null, isLoading: false } as any);
    mockUseDatasets.mockReturnValue({ data: null } as any);

    render(
      <MemoryRouter initialEntries={['/cards/new']}>
        <Routes>
          <Route path="/cards/:id" element={<CardEditPage />} />
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('Pythonコード')).toBeInTheDocument();
    expect(screen.getByTestId('card-editor')).toBeInTheDocument();
  });

  it('保存ボタンがある', () => {
    mockUseCard.mockReturnValue({ data: null, isLoading: false } as any);
    mockUseDatasets.mockReturnValue({ data: null } as any);

    render(
      <MemoryRouter initialEntries={['/cards/new']}>
        <Routes>
          <Route path="/cards/:id" element={<CardEditPage />} />
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByRole('button', { name: /保存/ })).toBeInTheDocument();
  });

  it('戻るボタンがある', () => {
    mockUseCard.mockReturnValue({ data: null, isLoading: false } as any);
    mockUseDatasets.mockReturnValue({ data: null } as any);

    render(
      <MemoryRouter initialEntries={['/cards/new']}>
        <Routes>
          <Route path="/cards/:id" element={<CardEditPage />} />
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    const backButtons = screen.getAllByRole('button');
    expect(backButtons.length).toBeGreaterThan(0);
  });

  it('プレビューセクションがある', () => {
    mockUseCard.mockReturnValue({ data: null, isLoading: false } as any);
    mockUseDatasets.mockReturnValue({ data: null } as any);

    render(
      <MemoryRouter initialEntries={['/cards/new']}>
        <Routes>
          <Route path="/cards/:id" element={<CardEditPage />} />
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('プレビュー')).toBeInTheDocument();
    expect(screen.getByTestId('card-preview')).toBeInTheDocument();
  });
});
