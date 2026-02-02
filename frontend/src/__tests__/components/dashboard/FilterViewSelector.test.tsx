import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, cleanup } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import { FilterViewSelector } from '@/components/dashboard/FilterViewSelector';
import type { FilterView } from '@/types';

const mockViews: FilterView[] = [
  {
    id: 'fv_1',
    dashboard_id: 'dash_1',
    name: 'Sales View',
    owner_id: 'user_1',
    filter_state: { category: 'sales' },
    is_shared: true,
    is_default: false,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'fv_2',
    dashboard_id: 'dash_1',
    name: 'Personal View',
    owner_id: 'user_1',
    filter_state: { category: 'marketing' },
    is_shared: false,
    is_default: false,
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z',
  },
];

describe('FilterViewSelector', () => {
  const mockOnSelect = vi.fn();
  const mockOnSave = vi.fn();
  const mockOnOverwrite = vi.fn();
  const mockOnDelete = vi.fn();

  afterEach(() => {
    cleanup();
  });

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the selector button', () => {
    render(
      <FilterViewSelector
        views={mockViews}
        onSelect={mockOnSelect}
        onSave={mockOnSave}
        onOverwrite={mockOnOverwrite}
        onDelete={mockOnDelete}
      />
    );

    expect(screen.getByRole('button', { name: /ビュー/i })).toBeInTheDocument();
  });

  it('shows view list when dropdown is opened', async () => {
    const user = userEvent.setup();
    render(
      <FilterViewSelector
        views={mockViews}
        onSelect={mockOnSelect}
        onSave={mockOnSave}
        onOverwrite={mockOnOverwrite}
        onDelete={mockOnDelete}
      />
    );

    await user.click(screen.getByRole('button', { name: /ビュー/i }));

    expect(screen.getByText('Sales View')).toBeInTheDocument();
    expect(screen.getByText('Personal View')).toBeInTheDocument();
  });

  it('shows shared badge for shared views', async () => {
    const user = userEvent.setup();
    render(
      <FilterViewSelector
        views={mockViews}
        onSelect={mockOnSelect}
        onSave={mockOnSave}
        onOverwrite={mockOnOverwrite}
        onDelete={mockOnDelete}
      />
    );

    await user.click(screen.getByRole('button', { name: /ビュー/i }));

    expect(screen.getByText('共有')).toBeInTheDocument();
    expect(screen.getByText('個人')).toBeInTheDocument();
  });

  it('calls onSelect when a view is clicked', async () => {
    const user = userEvent.setup();
    render(
      <FilterViewSelector
        views={mockViews}
        onSelect={mockOnSelect}
        onSave={mockOnSave}
        onOverwrite={mockOnOverwrite}
        onDelete={mockOnDelete}
      />
    );

    await user.click(screen.getByRole('button', { name: /ビュー/i }));
    await user.click(screen.getByText('Sales View'));

    expect(mockOnSelect).toHaveBeenCalledWith(mockViews[0]);
  });

  it('shows save dialog and calls onSave', async () => {
    const user = userEvent.setup();
    mockOnSave.mockResolvedValue(undefined);

    render(
      <FilterViewSelector
        views={mockViews}
        onSelect={mockOnSelect}
        onSave={mockOnSave}
        onOverwrite={mockOnOverwrite}
        onDelete={mockOnDelete}
      />
    );

    await user.click(screen.getByRole('button', { name: /ビュー/i }));
    await user.click(screen.getByText(/名前を付けて保存/i));

    const input = screen.getByPlaceholderText(/ビュー名/i);
    await user.type(input, 'New View');
    await user.click(screen.getByRole('button', { name: /^保存$/i }));

    await waitFor(() => {
      expect(mockOnSave).toHaveBeenCalledWith('New View');
    });
  });

  it('calls onDelete when delete is clicked', async () => {
    const user = userEvent.setup();
    mockOnDelete.mockResolvedValue(undefined);

    render(
      <FilterViewSelector
        views={mockViews}
        selectedViewId="fv_1"
        onSelect={mockOnSelect}
        onSave={mockOnSave}
        onOverwrite={mockOnOverwrite}
        onDelete={mockOnDelete}
      />
    );

    await user.click(screen.getByRole('button', { name: /ビュー/i }));
    await user.click(screen.getByText(/削除/i));

    expect(mockOnDelete).toHaveBeenCalledWith('fv_1');
  });

  it('shows overwrite button when a view is selected', async () => {
    const user = userEvent.setup();
    render(
      <FilterViewSelector
        views={mockViews}
        selectedViewId="fv_1"
        onSelect={mockOnSelect}
        onSave={mockOnSave}
        onOverwrite={mockOnOverwrite}
        onDelete={mockOnDelete}
      />
    );

    await user.click(screen.getByRole('button', { name: /ビュー/i }));
    expect(screen.getByText(/上書き保存/i)).toBeInTheDocument();
  });

  it('renders empty state when no views', () => {
    render(
      <FilterViewSelector
        views={[]}
        onSelect={mockOnSelect}
        onSave={mockOnSave}
        onOverwrite={mockOnOverwrite}
        onDelete={mockOnDelete}
      />
    );

    expect(screen.getByRole('button', { name: /ビュー/i })).toBeInTheDocument();
  });
});
