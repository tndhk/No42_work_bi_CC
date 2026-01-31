import { createBrowserRouter, Navigate } from 'react-router-dom';
import { Layout } from '@/components/common/Layout';
import { AuthGuard } from '@/components/common/AuthGuard';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';
import { LoginPage } from '@/pages/LoginPage';
import { DashboardListPage } from '@/pages/DashboardListPage';
import { DashboardViewPage } from '@/pages/DashboardViewPage';
import { DashboardEditPage } from '@/pages/DashboardEditPage';
import { DatasetListPage } from '@/pages/DatasetListPage';
import { DatasetImportPage } from '@/pages/DatasetImportPage';
import { DatasetDetailPage } from '@/pages/DatasetDetailPage';
import { CardListPage } from '@/pages/CardListPage';
import { CardEditPage } from '@/pages/CardEditPage';

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/',
    element: (
      <AuthGuard>
        <ErrorBoundary>
          <Layout />
        </ErrorBoundary>
      </AuthGuard>
    ),
    children: [
      {
        index: true,
        element: <Navigate to="/dashboards" replace />,
      },
      {
        path: 'dashboards',
        element: <DashboardListPage />,
      },
      {
        path: 'dashboards/:id',
        element: <DashboardViewPage />,
      },
      {
        path: 'dashboards/:id/edit',
        element: <DashboardEditPage />,
      },
      {
        path: 'datasets',
        element: <DatasetListPage />,
      },
      {
        path: 'datasets/import',
        element: <DatasetImportPage />,
      },
      {
        path: 'datasets/:id',
        element: <DatasetDetailPage />,
      },
      {
        path: 'cards',
        element: <CardListPage />,
      },
      {
        path: 'cards/:id',
        element: <CardEditPage />,
      },
    ],
  },
]);
