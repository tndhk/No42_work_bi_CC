import { describe, it, expect, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { TransformExecutionResult } from '@/components/transform/TransformExecutionResult';
import type { TransformExecuteResponse } from '@/types';

const mockResult: TransformExecuteResponse = {
  output_dataset_id: 'output-ds-1',
  row_count: 150,
  column_names: ['id', 'name', 'value'],
  execution_time_ms: 1234,
};

describe('TransformExecutionResult', () => {
  afterEach(() => {
    cleanup();
  });

  it('実行結果を表示する', () => {
    render(
      <MemoryRouter>
        <TransformExecutionResult result={mockResult} />
      </MemoryRouter>
    );
    expect(screen.getByText(/150/)).toBeInTheDocument();
    expect(screen.getByText(/1234/)).toBeInTheDocument();
  });

  it('カラム名を表示する', () => {
    render(
      <MemoryRouter>
        <TransformExecutionResult result={mockResult} />
      </MemoryRouter>
    );
    expect(screen.getByText(/id/)).toBeInTheDocument();
    expect(screen.getByText(/name/)).toBeInTheDocument();
    expect(screen.getByText(/value/)).toBeInTheDocument();
  });

  it('出力データセットへのリンクを表示する', () => {
    render(
      <MemoryRouter>
        <TransformExecutionResult result={mockResult} />
      </MemoryRouter>
    );
    const link = screen.getByRole('link');
    expect(link).toHaveAttribute('href', '/datasets/output-ds-1');
  });

  it('resultがnullの場合は何も表示しない', () => {
    const { container } = render(
      <MemoryRouter>
        <TransformExecutionResult result={null} />
      </MemoryRouter>
    );
    expect(container.firstChild).toBeNull();
  });
});
