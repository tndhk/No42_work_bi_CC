import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, cleanup, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SchemaChangeWarningDialog } from '@/components/datasets/SchemaChangeWarningDialog';
import type { SchemaChange } from '@/types/reimport';

describe('SchemaChangeWarningDialog', () => {
  afterEach(() => {
    cleanup();
  });

  const mockChanges: SchemaChange[] = [
    {
      column_name: 'new_column',
      change_type: 'added',
      old_value: null,
      new_value: 'TEXT',
    },
    {
      column_name: 'old_column',
      change_type: 'removed',
      old_value: 'INTEGER',
      new_value: null,
    },
    {
      column_name: 'type_column',
      change_type: 'type_changed',
      old_value: 'TEXT',
      new_value: 'INTEGER',
    },
    {
      column_name: 'nullable_column',
      change_type: 'nullable_changed',
      old_value: 'NOT NULL',
      new_value: 'NULL',
    },
  ];

  it('ダイアログが開いている時に変更一覧がテーブルで表示される', () => {
    render(
      <SchemaChangeWarningDialog
        open={true}
        changes={mockChanges}
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />
    );

    // テーブルが表示されることを確認
    const table = screen.getByRole('table');
    expect(table).toBeInTheDocument();

    // 各カラム名が表示されることを確認
    expect(screen.getByText('new_column')).toBeInTheDocument();
    expect(screen.getByText('old_column')).toBeInTheDocument();
    expect(screen.getByText('type_column')).toBeInTheDocument();
    expect(screen.getByText('nullable_column')).toBeInTheDocument();
  });

  it('「続行」ボタンをクリックするとonConfirmが呼ばれる', async () => {
    const user = userEvent.setup();
    const mockOnConfirm = vi.fn();

    render(
      <SchemaChangeWarningDialog
        open={true}
        changes={mockChanges}
        onConfirm={mockOnConfirm}
        onCancel={vi.fn()}
      />
    );

    const confirmButton = screen.getByRole('button', { name: '続行' });
    await user.click(confirmButton);

    expect(mockOnConfirm).toHaveBeenCalledTimes(1);
  });

  it('「キャンセル」ボタンをクリックするとonCancelが呼ばれる', async () => {
    const user = userEvent.setup();
    const mockOnCancel = vi.fn();

    render(
      <SchemaChangeWarningDialog
        open={true}
        changes={mockChanges}
        onConfirm={vi.fn()}
        onCancel={mockOnCancel}
      />
    );

    const cancelButton = screen.getByRole('button', { name: 'キャンセル' });
    await user.click(cancelButton);

    expect(mockOnCancel).toHaveBeenCalledTimes(1);
  });

  it('変更タイプごとに適切なラベルが表示される', () => {
    render(
      <SchemaChangeWarningDialog
        open={true}
        changes={mockChanges}
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />
    );

    // 変更タイプのラベルが日本語で表示されることを確認
    expect(screen.getByText('追加')).toBeInTheDocument();
    expect(screen.getByText('削除')).toBeInTheDocument();
    expect(screen.getByText('型変更')).toBeInTheDocument();
    expect(screen.getByText('NULL許容変更')).toBeInTheDocument();
  });

  it('old_value/new_valueが適切に表示される', () => {
    render(
      <SchemaChangeWarningDialog
        open={true}
        changes={mockChanges}
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />
    );

    screen.getByRole('table');

    // added: old_value=null, new_value=TEXT
    const addedRow = screen.getByText('new_column').closest('tr');
    expect(addedRow).toBeInTheDocument();
    expect(within(addedRow!).getByText('TEXT')).toBeInTheDocument();

    // removed: old_value=INTEGER, new_value=null
    const removedRow = screen.getByText('old_column').closest('tr');
    expect(removedRow).toBeInTheDocument();
    expect(within(removedRow!).getByText('INTEGER')).toBeInTheDocument();

    // type_changed: old_value=TEXT, new_value=INTEGER
    const typeChangedRow = screen.getByText('type_column').closest('tr');
    expect(typeChangedRow).toBeInTheDocument();
    // TEXTとINTEGERが両方表示される(型変更)
    const typeChangedCells = within(typeChangedRow!).getAllByRole('cell');
    const cellTexts = typeChangedCells.map((cell) => cell.textContent);
    expect(cellTexts).toContain('TEXT');
    expect(cellTexts.some((text) => text?.includes('INTEGER'))).toBe(true);

    // nullable_changed: old_value=NOT NULL, new_value=NULL
    const nullableRow = screen.getByText('nullable_column').closest('tr');
    expect(nullableRow).toBeInTheDocument();
    expect(within(nullableRow!).getByText('NOT NULL')).toBeInTheDocument();
    // NULL は複数箇所で表示される可能性があるため、行内で確認
    const nullableCells = within(nullableRow!).getAllByRole('cell');
    const nullableCellTexts = nullableCells.map((cell) => cell.textContent);
    expect(nullableCellTexts.some((text) => text === 'NULL')).toBe(true);
  });

  it('open=falseの時はダイアログが表示されない', () => {
    render(
      <SchemaChangeWarningDialog
        open={false}
        changes={mockChanges}
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />
    );

    expect(screen.queryByRole('table')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '続行' })).not.toBeInTheDocument();
  });

  it('変更が空配列の場合でもダイアログは表示される', () => {
    render(
      <SchemaChangeWarningDialog
        open={true}
        changes={[]}
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />
    );

    // ダイアログ自体は表示される
    expect(screen.getByRole('button', { name: '続行' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'キャンセル' })).toBeInTheDocument();
  });
});
