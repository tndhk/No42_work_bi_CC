# フロントエンド コードマップ

**最終更新:** 2026-01-31
**フレームワーク:** React 18 + TypeScript + Vite 5
**エントリポイント:** `frontend/src/main.tsx`

---

## ディレクトリ構造

```
frontend/src/
  main.tsx                           # ReactDOM.createRoot, StrictMode
  App.tsx                            # QueryClientProvider + RouterProvider
  routes.tsx                         # createBrowserRouter 定義
  index.css                          # TailwindCSS
  vite-env.d.ts                      # Vite 型定義
  components/
    common/
      index.ts                       # barrel export
      AuthGuard.tsx                  # 認証ガード (Zustand)
      ErrorBoundary.tsx              # React ErrorBoundary
      Header.tsx                     # ヘッダー (ユーザーメニュー)
      Layout.tsx                     # Sidebar + Header + Outlet
      Sidebar.tsx                    # ナビゲーション
      LoadingSpinner.tsx             # ローディング
      ConfirmDialog.tsx              # 確認ダイアログ
      Pagination.tsx                 # ページネーション
    card/
      CardEditor.tsx                 # Monaco Editor (Python)
      CardPreview.tsx                # カードプレビュー
    dashboard/
      AddCardDialog.tsx              # カード追加ダイアログ
      CardContainer.tsx              # iframe sandbox (HTML描画)
      DashboardEditor.tsx            # レイアウト編集 (グリッド)
      DashboardViewer.tsx            # ダッシュボード表示
    ui/                              # shadcn/ui コンポーネント
      alert-dialog.tsx, badge.tsx, button.tsx, card.tsx,
      dialog.tsx, dropdown-menu.tsx, form.tsx, input.tsx,
      label.tsx, separator.tsx, sheet.tsx, table.tsx
  hooks/
    index.ts                         # barrel export
    use-auth.ts                      # useLogin, useLogout, useCurrentUser
    use-cards.ts                     # useCards, useCard, CRUD + execute + preview
    use-dashboards.ts                # useDashboards, useDashboard, CRUD + clone
    use-datasets.ts                  # useDatasets, useDataset, CRUD + preview
  lib/
    api-client.ts                    # ky ベース HTTPクライアント (JWT自動付与)
    utils.ts                         # cn() (clsx + tailwind-merge)
    api/
      index.ts                       # barrel export
      auth.ts                        # authApi
      cards.ts                       # cardsApi
      dashboards.ts                  # dashboardsApi
      datasets.ts                    # datasetsApi
  pages/
    LoginPage.tsx                    # ログインフォーム
    DashboardListPage.tsx            # ダッシュボード一覧
    DashboardViewPage.tsx            # ダッシュボード閲覧
    DashboardEditPage.tsx            # ダッシュボード編集
    DatasetListPage.tsx              # データセット一覧
    DatasetImportPage.tsx            # CSVインポート
    DatasetDetailPage.tsx            # データセット詳細
    CardListPage.tsx                 # カード一覧
    CardEditPage.tsx                 # カード編集 (コードエディタ)
  stores/
    auth-store.ts                    # Zustand 認証ストア
  types/
    index.ts                         # barrel export (全型 + type guards)
    api.ts                           # ApiResponse, PaginatedResponse, etc
    user.ts                          # User, LoginRequest, LoginResponse
    card.ts                          # Card, CardDetail, execute/preview 型
    dashboard.ts                     # Dashboard, LayoutItem, FilterDefinition
    dataset.ts                       # Dataset, ColumnSchema, DatasetPreview
  __tests__/                         # テスト
```

## ルーティング

| パス | ページ | 認証 | 説明 |
|------|--------|------|------|
| `/login` | LoginPage | 不要 | ログイン |
| `/` | (redirect) | 必要 | `/dashboards` へリダイレクト |
| `/dashboards` | DashboardListPage | 必要 | ダッシュボード一覧 |
| `/dashboards/:id` | DashboardViewPage | 必要 | ダッシュボード閲覧 |
| `/dashboards/:id/edit` | DashboardEditPage | 必要 | ダッシュボード編集 |
| `/datasets` | DatasetListPage | 必要 | データセット一覧 |
| `/datasets/import` | DatasetImportPage | 必要 | CSVインポート |
| `/datasets/:id` | DatasetDetailPage | 必要 | データセット詳細 |
| `/cards` | CardListPage | 必要 | カード一覧 |
| `/cards/:id` | CardEditPage | 必要 | カード編集 (new/既存) |

## コンポーネント依存関係グラフ

```
App.tsx
  +-- QueryClientProvider (@tanstack/react-query)
  +-- RouterProvider (react-router-dom)
        +-- LoginPage
        |     +-- useLogin (hook)
        |     +-- useAuthStore (store)
        |     +-- ui/card, ui/input, ui/label, ui/button
        |
        +-- AuthGuard
        |     +-- useAuthStore (store)
        |
        +-- ErrorBoundary
        |
        +-- Layout
              +-- Header
              |     +-- useAuthStore (store)
              |     +-- useLogout (hook)
              |     +-- ui/button, ui/dropdown-menu
              +-- Sidebar
              |     +-- NavLink (react-router-dom)
              +-- Outlet --> 各ページ
```

### ページ --> コンポーネント

```
DashboardListPage
  +-- useDashboards, useCreateDashboard, useDeleteDashboard
  +-- LoadingSpinner, Pagination, ConfirmDialog
  +-- ui/table, ui/dialog, ui/button, ui/input

DashboardViewPage
  +-- useDashboard, useExecuteCard
  +-- DashboardViewer
        +-- CardContainer (iframe sandbox)
        +-- LoadingSpinner

DashboardEditPage
  +-- useDashboard, useUpdateDashboard
  +-- DashboardEditor
  +-- AddCardDialog
        +-- useCards

CardEditPage
  +-- useCard, useCreateCard, useUpdateCard, usePreviewCard, useDatasets
  +-- CardEditor (Monaco Editor)
  +-- CardPreview
        +-- CardContainer (iframe sandbox)

DatasetListPage
  +-- useDatasets, useDeleteDataset
  +-- LoadingSpinner, Pagination, ConfirmDialog

DatasetImportPage
  +-- useCreateDataset

DatasetDetailPage
  +-- useDataset, useDatasetPreview
```

## 状態管理

### Zustand ストア (`stores/auth-store.ts`)

```typescript
interface AuthState {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  setAuth(token, user): void;
  clearAuth(): void;
}
```

### React Query キー設計

| クエリキー | hook | 説明 |
|-----------|------|------|
| `['auth', 'me']` | useCurrentUser | 現在ユーザー |
| `['dashboards', params?]` | useDashboards | ダッシュボード一覧 |
| `['dashboards', id]` | useDashboard | ダッシュボード詳細 |
| `['datasets', params?]` | useDatasets | データセット一覧 |
| `['datasets', id]` | useDataset | データセット詳細 |
| `['datasets', id, 'preview', limit?]` | useDatasetPreview | プレビュー |
| `['cards', params?]` | useCards | カード一覧 |
| `['cards', id]` | useCard | カード詳細 |

## API クライアント層

```
lib/api-client.ts (ky ベース)
  |-- beforeRequest: JWT トークン自動付与
  |-- afterResponse: 401 → clearAuth() + /login リダイレクト
  |
  +-- lib/api/auth.ts       authApi.login(), logout(), me()
  +-- lib/api/cards.ts       cardsApi.list(), get(), create(), update(), delete(), execute(), preview()
  +-- lib/api/dashboards.ts  dashboardsApi.list(), get(), create(), update(), delete(), clone()
  +-- lib/api/datasets.ts    datasetsApi.list(), get(), create(FormData), update(), delete(), preview()
```

## hooks 一覧

### use-auth.ts
| hook | 種別 | 説明 |
|------|------|------|
| `useLogin()` | mutation | ログイン (setAuth + invalidate) |
| `useLogout()` | mutation | ログアウト (clearAuth + clear) |
| `useCurrentUser()` | query | 現在ユーザー取得 |

### use-cards.ts
| hook | 種別 | 説明 |
|------|------|------|
| `useCards(params?)` | query | カード一覧 |
| `useCard(cardId)` | query | カード詳細 |
| `useCreateCard()` | mutation | カード作成 |
| `useUpdateCard()` | mutation | カード更新 |
| `useDeleteCard()` | mutation | カード削除 |
| `useExecuteCard()` | mutation | カード実行 |
| `usePreviewCard()` | mutation | カードプレビュー |

### use-dashboards.ts
| hook | 種別 | 説明 |
|------|------|------|
| `useDashboards(params?)` | query | ダッシュボード一覧 |
| `useDashboard(id)` | query | ダッシュボード詳細 |
| `useCreateDashboard()` | mutation | ダッシュボード作成 |
| `useUpdateDashboard()` | mutation | ダッシュボード更新 |
| `useDeleteDashboard()` | mutation | ダッシュボード削除 |
| `useCloneDashboard()` | mutation | ダッシュボードクローン |

### use-datasets.ts
| hook | 種別 | 説明 |
|------|------|------|
| `useDatasets(params?)` | query | データセット一覧 |
| `useDataset(id)` | query | データセット詳細 |
| `useDatasetPreview(id, limit?)` | query | データプレビュー |
| `useCreateDataset()` | mutation | CSV インポート |
| `useUpdateDataset()` | mutation | データセット更新 |
| `useDeleteDataset()` | mutation | データセット削除 |

## カード描画セキュリティ

`CardContainer.tsx` で生成される iframe:
- `sandbox="allow-scripts"` (フォーム、ナビゲーション、popups 禁止)
- CSP: `default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data: blob:`
- `srcDoc` で HTML 直接注入 (外部URL無し)

## UI コンポーネント (shadcn/ui)

Radix UI + Tailwind CSS ベース:
`alert-dialog`, `badge`, `button`, `card`, `dialog`, `dropdown-menu`, `form`, `input`, `label`, `separator`, `sheet`, `table`

## 関連コードマップ

- [architecture.md](./architecture.md) - 全体アーキテクチャ
- [backend.md](./backend.md) - バックエンド構造
- [data.md](./data.md) - データモデル詳細
