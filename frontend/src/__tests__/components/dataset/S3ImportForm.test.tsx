import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, cleanup } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { S3ImportForm } from '@/components/dataset/S3ImportForm';

describe('S3ImportForm', () => {
  const mockOnSubmit = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it('renders required fields', () => {
    render(<S3ImportForm onSubmit={mockOnSubmit} />);

    expect(screen.getByLabelText(/データセット名/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/S3バケット/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/S3キー/i)).toBeInTheDocument();
  });

  it('renders optional fields', () => {
    render(<S3ImportForm onSubmit={mockOnSubmit} />);

    expect(screen.getByLabelText(/区切り文字/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/エンコーディング/i)).toBeInTheDocument();
  });

  it('submits with required fields', async () => {
    const user = userEvent.setup();
    mockOnSubmit.mockResolvedValue(undefined);

    render(<S3ImportForm onSubmit={mockOnSubmit} />);

    await user.type(screen.getByLabelText(/データセット名/i), 'test-dataset');
    await user.type(screen.getByLabelText(/S3バケット/i), 'my-bucket');
    await user.type(screen.getByLabelText(/S3キー/i), 'data/file.csv');

    await user.click(screen.getByRole('button', { name: /インポート/i }));

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          name: 'test-dataset',
          s3_bucket: 'my-bucket',
          s3_key: 'data/file.csv',
        })
      );
    });
  });

  it('shows validation errors for empty required fields', async () => {
    const user = userEvent.setup();
    render(<S3ImportForm onSubmit={mockOnSubmit} />);

    await user.click(screen.getByRole('button', { name: /インポート/i }));

    await waitFor(() => {
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });
  });

  it('shows loading state when isLoading is true', () => {
    render(<S3ImportForm onSubmit={mockOnSubmit} isLoading={true} />);

    const button = screen.getByRole('button', { name: /インポート中/i });
    expect(button).toBeDisabled();
  });

  it('submits with all optional fields', async () => {
    const user = userEvent.setup();
    mockOnSubmit.mockResolvedValue(undefined);

    render(<S3ImportForm onSubmit={mockOnSubmit} />);

    await user.type(screen.getByLabelText(/データセット名/i), 'full-test');
    await user.type(screen.getByLabelText(/S3バケット/i), 'bucket');
    await user.type(screen.getByLabelText(/S3キー/i), 'key.csv');

    // Clear and type delimiter
    const delimiterInput = screen.getByLabelText(/区切り文字/i);
    await user.clear(delimiterInput);
    await user.type(delimiterInput, '\t');

    const encodingInput = screen.getByLabelText(/エンコーディング/i);
    await user.clear(encodingInput);
    await user.type(encodingInput, 'shift_jis');

    await user.click(screen.getByRole('button', { name: /インポート/i }));

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalled();
    });
  });
});
