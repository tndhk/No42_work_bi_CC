import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { DatasetImportPage } from '@/pages/DatasetImportPage';
import { createWrapper } from '@/__tests__/helpers/test-utils';

const mockNavigate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock('@/hooks', () => ({
  useCreateDataset: vi.fn(() => ({ mutate: vi.fn(), isPending: false })),
}));

describe('DatasetImportPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it('「データセットインポート」タイトルを表示する', () => {
    render(
      <MemoryRouter>
        <DatasetImportPage />
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('データセットインポート')).toBeInTheDocument();
  });

  it('ファイル選択エリアがある', () => {
    render(
      <MemoryRouter>
        <DatasetImportPage />
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText(/CSVファイルをドラッグ/)).toBeInTheDocument();
  });

  it('データセット名入力フィールドがある', () => {
    render(
      <MemoryRouter>
        <DatasetImportPage />
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('データセット名')).toBeInTheDocument();
  });

  it('インポートボタンがある', () => {
    render(
      <MemoryRouter>
        <DatasetImportPage />
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByRole('button', { name: /インポート/ })).toBeInTheDocument();
  });

  it('戻るボタンがある', () => {
    render(
      <MemoryRouter>
        <DatasetImportPage />
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    const backButtons = screen.getAllByRole('button');
    expect(backButtons.length).toBeGreaterThan(0);
  });
});
