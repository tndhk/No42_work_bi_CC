import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
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
  useCreateDataset: vi.fn(() => ({ mutate: vi.fn(), isPending: false, isError: false })),
  useS3ImportDataset: vi.fn(() => ({ mutate: vi.fn(), isPending: false, isError: false, isSuccess: false })),
}));

function renderPage() {
  return render(
    <MemoryRouter>
      <DatasetImportPage />
    </MemoryRouter>,
    { wrapper: createWrapper() }
  );
}

describe('DatasetImportPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it('renders page title', () => {
    renderPage();
    expect(screen.getByText('データセットインポート')).toBeInTheDocument();
  });

  it('renders both tab buttons', () => {
    renderPage();
    expect(screen.getByText('CSVアップロード')).toBeInTheDocument();
    expect(screen.getByText('S3インポート')).toBeInTheDocument();
  });

  it('shows CSV tab content by default', () => {
    renderPage();
    expect(screen.getByText('CSVファイル')).toBeInTheDocument();
    expect(screen.getByText(/CSVファイルをドラッグ/)).toBeInTheDocument();
  });

  it('shows dataset name input field', () => {
    renderPage();
    expect(screen.getByText('データセット名')).toBeInTheDocument();
  });

  it('shows import submit button in CSV tab', () => {
    renderPage();
    const submitButton = screen.getByRole('button', { name: /^インポート$/ });
    expect(submitButton).toBeInTheDocument();
    expect(submitButton).toHaveAttribute('type', 'submit');
  });

  it('has a back button', () => {
    renderPage();
    const backButtons = screen.getAllByRole('button');
    expect(backButtons.length).toBeGreaterThan(0);
  });

  it('switches to S3 import tab when clicked', async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByText('S3インポート'));

    // S3 form fields should be visible
    expect(screen.getByLabelText(/S3バケット/)).toBeInTheDocument();
    expect(screen.getByLabelText(/S3キー/)).toBeInTheDocument();
  });

  it('hides CSV content when S3 tab is selected', async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByText('S3インポート'));

    // CSV-specific content should not be visible
    expect(screen.queryByText(/CSVファイルをドラッグ/)).not.toBeInTheDocument();
  });

  it('switches back to CSV tab from S3 tab', async () => {
    const user = userEvent.setup();
    renderPage();

    // Switch to S3
    await user.click(screen.getByText('S3インポート'));
    // Switch back to CSV
    await user.click(screen.getByText('CSVアップロード'));

    expect(screen.getByText('CSVファイル')).toBeInTheDocument();
    expect(screen.getByText(/CSVファイルをドラッグ/)).toBeInTheDocument();
  });

  it('shows S3 card title when S3 tab is active', async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByText('S3インポート'));

    expect(screen.getByText('S3からインポート')).toBeInTheDocument();
  });
});
