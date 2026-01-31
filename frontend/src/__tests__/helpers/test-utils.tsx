import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { render } from '@testing-library/react';
import { useAuthStore } from '@/stores/auth-store';
import type { User, Dataset, Card, Dashboard } from '@/types';

// QueryClient (retry無効、テスト高速化)
export function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  });
}

// Providers wrapper (QueryClient + Router)
export function renderWithProviders(
  ui: React.ReactElement,
  options?: { route?: string; queryClient?: QueryClient }
) {
  const queryClient = options?.queryClient || createTestQueryClient();
  const route = options?.route || '/';

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[route]}>{ui}</MemoryRouter>
    </QueryClientProvider>
  );
}

// renderHook wrapper
export function createWrapper(queryClient?: QueryClient) {
  const client = queryClient || createTestQueryClient();
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
}

// Auth state helpers
export function setupAuthState(token: string, user: User) {
  useAuthStore.getState().setAuth(token, user);
}

export function clearAuthState() {
  useAuthStore.getState().clearAuth();
}

// Factory functions
export function createMockUser(overrides?: Partial<User>): User {
  return {
    user_id: 'test-user-id',
    email: 'test@example.com',
    created_at: '2026-01-01T00:00:00Z',
    ...overrides,
  };
}

export function createMockDataset(overrides?: Partial<Dataset>): Dataset {
  return {
    dataset_id: 'test-dataset-id',
    name: 'Test Dataset',
    source_type: 'csv',
    row_count: 100,
    column_count: 5,
    owner: { user_id: 'owner-id', name: 'Test Owner' },
    created_at: '2026-01-01T00:00:00Z',
    ...overrides,
  };
}

export function createMockCard(overrides?: Partial<Card>): Card {
  return {
    card_id: 'test-card-id',
    name: 'Test Card',
    dataset: {
      dataset_id: 'dataset-1',
      name: 'Test Dataset',
    },
    owner: { user_id: 'owner-id', name: 'Test Owner' },
    created_at: '2026-01-01T00:00:00Z',
    ...overrides,
  };
}

export function createMockDashboard(overrides?: Partial<Dashboard>): Dashboard {
  return {
    dashboard_id: 'test-dashboard-id',
    name: 'Test Dashboard',
    card_count: 3,
    owner: { user_id: 'owner-id', name: 'Test Owner' },
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...overrides,
  };
}

export function createMockPaginatedResponse<T>(items: T[], total = items.length) {
  return {
    data: items,
    pagination: {
      total,
      limit: items.length,
      offset: 0,
      has_next: false,
    },
  };
}
