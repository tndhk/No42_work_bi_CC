import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import { TransformScheduleConfig } from '@/components/transform/TransformScheduleConfig';

describe('TransformScheduleConfig', () => {
  const defaultProps = {
    scheduleCron: '',
    scheduleEnabled: false,
    onCronChange: vi.fn(),
    onEnabledChange: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it('スケジュール有効チェックボックスを表示する', () => {
    render(<TransformScheduleConfig {...defaultProps} />);
    expect(screen.getByText('スケジュール実行を有効にする')).toBeInTheDocument();
    expect(screen.getByRole('checkbox')).toBeInTheDocument();
  });

  it('チェックOFF時はcron入力欄を表示しない', () => {
    render(<TransformScheduleConfig {...defaultProps} scheduleEnabled={false} />);
    expect(screen.queryByText('Cron式')).not.toBeInTheDocument();
  });

  it('チェックON時にcron入力欄を表示する', () => {
    render(<TransformScheduleConfig {...defaultProps} scheduleEnabled={true} />);
    expect(screen.getByText('Cron式')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('0 0 * * *')).toBeInTheDocument();
  });

  it('cron入力変更時にonCronChangeが呼ばれる', () => {
    const onCronChange = vi.fn();
    render(<TransformScheduleConfig {...defaultProps} scheduleEnabled={true} onCronChange={onCronChange} />);

    fireEvent.change(screen.getByPlaceholderText('0 0 * * *'), { target: { value: '*/5 * * * *' } });
    expect(onCronChange).toHaveBeenCalledWith('*/5 * * * *');
  });

  it('プリセットボタンクリックでcron値が設定される', () => {
    const onCronChange = vi.fn();
    render(<TransformScheduleConfig {...defaultProps} scheduleEnabled={true} onCronChange={onCronChange} />);

    fireEvent.click(screen.getByText('毎時'));
    expect(onCronChange).toHaveBeenCalledWith('0 * * * *');

    fireEvent.click(screen.getByText('毎日 0:00'));
    expect(onCronChange).toHaveBeenCalledWith('0 0 * * *');
  });

  it('有効/無効トグルでonEnabledChangeが呼ばれる', () => {
    const onEnabledChange = vi.fn();
    render(<TransformScheduleConfig {...defaultProps} onEnabledChange={onEnabledChange} />);

    fireEvent.click(screen.getByRole('checkbox'));
    expect(onEnabledChange).toHaveBeenCalledWith(true);
  });
});
