import { describe, it, expect, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { Sidebar } from '@/components/common/Sidebar';

describe('Sidebar', () => {
  afterEach(() => {
    cleanup();
  });
  it('BI Toolテキストを表示する', () => {
    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>
    );

    expect(screen.getByText('BI Tool')).toBeInTheDocument();
  });

  it('ダッシュボードリンクを表示する', () => {
    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>
    );

    const link = screen.getByRole('link', { name: /ダッシュボード/ });
    expect(link).toBeInTheDocument();
  });

  it('データセットリンクを表示する', () => {
    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>
    );

    const link = screen.getByRole('link', { name: /データセット/ });
    expect(link).toBeInTheDocument();
  });

  it('カードリンクを表示する', () => {
    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>
    );

    const link = screen.getByRole('link', { name: /カード/ });
    expect(link).toBeInTheDocument();
  });

  it('正しいパスへのリンクを持つ', () => {
    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>
    );

    const dashboardLink = screen.getByRole('link', { name: /ダッシュボード/ });
    expect(dashboardLink).toHaveAttribute('href', '/dashboards');

    const datasetLink = screen.getByRole('link', { name: /データセット/ });
    expect(datasetLink).toHaveAttribute('href', '/datasets');

    const cardLink = screen.getByRole('link', { name: /カード/ });
    expect(cardLink).toHaveAttribute('href', '/cards');
  });
});
