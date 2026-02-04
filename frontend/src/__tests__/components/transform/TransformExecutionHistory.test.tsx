import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import { TransformExecutionHistory } from '@/components/transform/TransformExecutionHistory';

vi.mock('@/hooks', () => ({
  useTransformExecutions: vi.fn(),
}));

vi.mock('@/components/common/LoadingSpinner', () => ({
  LoadingSpinner: () => <div data-testid="loading-spinner">Loading</div>,
}));

import { useTransformExecutions } from '@/hooks';
const mockUseTransformExecutions = useTransformExecutions as ReturnType<typeof vi.fn>;

describe('TransformExecutionHistory', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it('ローディング中はスピナーを表示', () => {
    mockUseTransformExecutions.mockReturnValue({ data: undefined, isLoading: true });
    render(<TransformExecutionHistory transformId="transform-1" />);
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('実行履歴を一覧表示する', () => {
    mockUseTransformExecutions.mockReturnValue({
      data: {
        data: [
          {
            execution_id: 'exec-001',
            transform_id: 'transform-1',
            status: 'success',
            started_at: '2026-02-04T10:00:00Z',
            finished_at: '2026-02-04T10:00:05Z',
            duration_ms: 5000,
            output_row_count: 100,
            triggered_by: 'manual',
          },
        ],
      },
      isLoading: false,
    });
    render(<TransformExecutionHistory transformId="transform-1" />);
    expect(screen.getByText('success')).toBeInTheDocument();
    expect(screen.getByText('100行')).toBeInTheDocument();
    expect(screen.getByText('手動実行')).toBeInTheDocument();
  });

  it('成功ステータスを緑で表示する', () => {
    mockUseTransformExecutions.mockReturnValue({
      data: {
        data: [{
          execution_id: 'exec-001', transform_id: 'transform-1', status: 'success',
          started_at: '2026-02-04T10:00:00Z', triggered_by: 'manual',
        }],
      },
      isLoading: false,
    });
    render(<TransformExecutionHistory transformId="transform-1" />);
    const badge = screen.getByText('success');
    expect(badge.className).toContain('bg-green-100');
  });

  it('失敗ステータスを赤で表示する', () => {
    mockUseTransformExecutions.mockReturnValue({
      data: {
        data: [{
          execution_id: 'exec-002', transform_id: 'transform-1', status: 'failed',
          started_at: '2026-02-04T10:00:00Z', triggered_by: 'manual',
          error: 'SQL syntax error',
        }],
      },
      isLoading: false,
    });
    render(<TransformExecutionHistory transformId="transform-1" />);
    const badge = screen.getByText('failed');
    expect(badge.className).toContain('bg-red-100');
  });

  it('エラーメッセージを表示する', () => {
    mockUseTransformExecutions.mockReturnValue({
      data: {
        data: [{
          execution_id: 'exec-002', transform_id: 'transform-1', status: 'failed',
          started_at: '2026-02-04T10:00:00Z', triggered_by: 'manual',
          error: 'SQL syntax error',
        }],
      },
      isLoading: false,
    });
    render(<TransformExecutionHistory transformId="transform-1" />);
    expect(screen.getByText('SQL syntax error')).toBeInTheDocument();
  });

  it('実行時間を表示する', () => {
    mockUseTransformExecutions.mockReturnValue({
      data: {
        data: [{
          execution_id: 'exec-001', transform_id: 'transform-1', status: 'success',
          started_at: '2026-02-04T10:00:00Z', duration_ms: 3200, triggered_by: 'manual',
        }],
      },
      isLoading: false,
    });
    render(<TransformExecutionHistory transformId="transform-1" />);
    expect(screen.getByText('3.2s')).toBeInTheDocument();
  });

  it('実行履歴がない場合はメッセージを表示', () => {
    mockUseTransformExecutions.mockReturnValue({
      data: { data: [] },
      isLoading: false,
    });
    render(<TransformExecutionHistory transformId="transform-1" />);
    expect(screen.getByText('実行履歴がありません')).toBeInTheDocument();
  });

  it('スケジュール実行を表示する', () => {
    mockUseTransformExecutions.mockReturnValue({
      data: {
        data: [{
          execution_id: 'exec-003', transform_id: 'transform-1', status: 'success',
          started_at: '2026-02-04T10:00:00Z', triggered_by: 'schedule',
        }],
      },
      isLoading: false,
    });
    render(<TransformExecutionHistory transformId="transform-1" />);
    expect(screen.getByText('スケジュール実行')).toBeInTheDocument();
  });
});
