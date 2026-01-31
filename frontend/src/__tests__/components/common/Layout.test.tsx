import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { Layout } from '@/components/common/Layout';
import { createWrapper } from '@/__tests__/helpers/test-utils';

vi.mock('@/components/common/Header', () => ({
  Header: () => <div data-testid="header">Header</div>,
}));

vi.mock('@/components/common/Sidebar', () => ({
  Sidebar: () => <div data-testid="sidebar">Sidebar</div>,
}));

describe('Layout', () => {
  afterEach(() => {
    cleanup();
  });

  it('HeaderとSidebarを表示する', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<div>Content</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByTestId('header')).toBeInTheDocument();
    expect(screen.getByTestId('sidebar')).toBeInTheDocument();
  });

  it('Outletでルーティングコンテンツを表示する', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<div data-testid="test-content">Test Content</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByTestId('test-content')).toBeInTheDocument();
  });
});
