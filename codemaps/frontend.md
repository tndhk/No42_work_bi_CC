# フロントエンド コードマップ

**最終更新:** 2026-02-01 (Phase Q4 E2E + Q5 + フィルタ機能)
**フレームワーク:** React 18 + TypeScript + Vite 5
**エントリポイント:** `frontend/src/main.tsx`
**テストカバレッジ:** 83.07% (statements) / 42テストファイル / 262テスト (Unit) + 3スペック / 12テスト (E2E)

---

## ディレクトリ構造

```
frontend/
  playwright.config.ts                 # Playwright E2E テスト設定 [NEW]
  vitest.config.ts                     # Vitest 設定 (jsdom, V8 coverage, 80% threshold)
  e2e/                                 # Playwright E2E テスト [NEW]
    global-setup.ts                    # バックエンド起動待機 (ヘルスチェック)
    auth.spec.ts                       # 認証フロー E2E (5テスト)
    dataset.spec.ts                    # データセット E2E (3テスト)
    card-dashboard.spec.ts             # カード+ダッシュボード E2E (4テスト)
    helpers/
      login-helper.ts                  # loginViaUI() ヘルパー
      api-helper.ts                    # テストデータ CRUD ヘルパー
    sample-data/
      test-sales.csv                   # テスト用 CSV (5行, 4列)
  src/
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
        DashboardEditor.tsx            # グリッドレイアウト編集 (react-grid-layout)
        DashboardViewer.tsx            # ダッシュボード表示 (react-grid-layout)
        FilterBar.tsx                  # フィルタバー (閲覧モード)
        FilterConfigPanel.tsx          # フィルタ設定パネル (編集モード)
        FilterDefinitionForm.tsx       # フィルタ定義フォーム
        filters/
          CategoryFilter.tsx           # カテゴリフィルタ (単一/複数選択)
          DateRangeFilter.tsx          # 日付範囲フィルタ (カレンダー)
      ui/                              # shadcn/ui コンポーネント
        alert-dialog.tsx, badge.tsx, button.tsx, calendar.tsx,
        card.tsx, checkbox.tsx, dialog.tsx, dropdown-menu.tsx,
        form.tsx, input.tsx, label.tsx, popover.tsx,
        select.tsx, separator.tsx, sheet.tsx, table.tsx
    hooks/
      index.ts                         # barrel export
      use-auth.ts                      # useLogin, useLogout, useCurrentUser
      use-cards.ts                     # useCards, useCard, CRUD + execute + preview
      use-dashboards.ts                # useDashboards, useDashboard, CRUD + clone
      use-datasets.ts                  # useDatasets, useDataset, CRUD + preview
    lib/
      api-client.ts                    # ky ベース HTTPクライアント (JWT自動付与)
      utils.ts                         # cn() (clsx + tailwind-merge)
      layout-utils.ts                  # toRGLLayout(), fromRGLLayout()
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
    __tests__/                         # Vitest テストスイート
      setup.ts                         # jest-dom matchers, CSS mock
      vitest.d.ts                      # カスタム型定義
      helpers/
        test-utils.tsx                 # renderWithProviders, factory 関数
      App.test.tsx                     # App コンポーネントテスト
      types/
        type-guards.test.ts            # 全 type guard テスト
      stores/
        auth-store.test.ts             # Zustand ストアテスト
      hooks/
        use-auth.test.ts               # 認証 hooks テスト
        use-cards.test.ts              # カード hooks テスト
        use-dashboards.test.ts         # ダッシュボード hooks テスト
        use-datasets.test.ts           # データセット hooks テスト
      lib/
        api-client.test.ts             # HTTP クライアントテスト
        layout-utils.test.ts           # レイアウトユーティリティテスト
        utils.test.ts                  # cn() ユーティリティテスト
        api/
          auth.test.ts                 # authApi テスト
          cards.test.ts                # cardsApi テスト
          dashboards.test.ts           # dashboardsApi テスト
          datasets.test.ts             # datasetsApi テスト
      components/
        common/
          AuthGuard.test.tsx           # 認証ガードテスト
          ConfirmDialog.test.tsx        # 確認ダイアログテスト
          ErrorBoundary.test.tsx        # ErrorBoundary テスト
          Header.test.tsx              # ヘッダーテスト
          Layout.test.tsx              # レイアウトテスト
          LoadingSpinner.test.tsx       # ローディングテスト
          Pagination.test.tsx           # ページネーションテスト
          Sidebar.test.tsx             # サイドバーテスト
        card/
          CardEditor.test.tsx          # Monaco Editor テスト
          CardPreview.test.tsx         # プレビューテスト
        dashboard/
          AddCardDialog.test.tsx       # カード追加ダイアログテスト
          CardContainer.test.tsx       # iframe sandbox テスト
          DashboardEditor.test.tsx     # グリッド編集テスト
          DashboardViewer.test.tsx     # ダッシュボード表示テスト
          FilterBar.test.tsx           # フィルタバーテスト (7テスト)
          FilterConfigPanel.test.tsx   # フィルタ設定テスト (6テスト)
          FilterDefinitionForm.test.tsx # フィルタ定義フォームテスト (6テスト)
          filters/
            CategoryFilter.test.tsx    # カテゴリフィルタテスト (10テスト)
            DateRangeFilter.test.tsx   # 日付範囲フィルタテスト (6テスト)
      pages/
        LoginPage.test.tsx             # ログインページテスト
        DashboardListPage.test.tsx     # ダッシュボード一覧テスト
        DashboardViewPage.test.tsx     # ダッシュボード閲覧テスト
        DashboardEditPage.test.tsx     # ダッシュボード編集テスト
        DatasetListPage.test.tsx       # データセット一覧テスト
        DatasetImportPage.test.tsx     # CSVインポートテスト
        DatasetDetailPage.test.tsx     # データセット詳細テスト
        CardListPage.test.tsx          # カード一覧テスト
        CardEditPage.test.tsx          # カード編集テスト
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
  +-- FilterBar (フィルタ適用 UI)
  |     +-- CategoryFilter (filters/)
  |     +-- DateRangeFilter (filters/)
  +-- DashboardViewer (filterValues 対応)
        +-- ResponsiveGridLayout (react-grid-layout)
        +-- toRGLLayout (lib/layout-utils)
        +-- CardContainer (iframe sandbox, filterApplied)
        +-- LoadingSpinner

DashboardEditPage
  +-- useDashboard, useUpdateDashboard
  +-- DashboardEditor
  |     +-- ResponsiveGridLayout (react-grid-layout)
  |     +-- toRGLLayout, fromRGLLayout (lib/layout-utils)
  |     +-- X icon (lucide-react)
  +-- AddCardDialog
  |     +-- useCards
  +-- FilterConfigPanel (フィルタ定義管理)
        +-- FilterDefinitionForm
        +-- dashboardsApi.getReferencedDatasets()
        +-- datasetsApi.getColumnValues()

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

## レイアウトユーティリティ (lib/layout-utils.ts)

DashboardEditor/DashboardViewer と react-grid-layout 間の型変換ブリッジ:

| 関数 | 入力 | 出力 | 用途 |
|------|------|------|------|
| `toRGLLayout()` | `LayoutItem[]` | `Layout[]` (RGL) | 表示用変換 (card_id -> i) |
| `fromRGLLayout()` | `Layout[]` (RGL) | `LayoutItem[]` | 保存用変換 (i -> card_id) |

## ダッシュボードグリッドレイアウト

DashboardEditor / DashboardViewer は `react-grid-layout` の `Responsive` + `WidthProvider` を使用:

```
ResponsiveGridLayout
  breakpoints: { lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 }
  cols: layout.columns (default: 12)
  rowHeight: layout.row_height (default: 100)
  compactType: "vertical"

DashboardEditor:  isDraggable=true,  isResizable=true   (編集モード)
DashboardViewer:  isDraggable=false, isResizable=false  (閲覧モード)
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
  |-- afterResponse: 401 --> clearAuth() + /login リダイレクト
  |
  +-- lib/api/auth.ts       authApi.login(), logout(), me()
  +-- lib/api/cards.ts       cardsApi.list(), get(), create(), update(), delete(), execute(), preview()
  +-- lib/api/dashboards.ts  dashboardsApi.list(), get(), create(), update(), delete(), clone(), getReferencedDatasets()
  +-- lib/api/datasets.ts    datasetsApi.list(), get(), create(FormData), update(), delete(), preview(), getColumnValues()
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
`alert-dialog`, `badge`, `button`, `calendar`, `card`, `checkbox`, `dialog`, `dropdown-menu`, `form`, `input`, `label`, `popover`, `select`, `separator`, `sheet`, `table`

## E2E テスト (Playwright) [NEW]

### 構成

| ファイル | テスト数 | 対象 |
|---------|---------|------|
| `auth.spec.ts` | 5 | 未認証リダイレクト、バリデーション、認証失敗、ログイン/ログアウト、ログイン済リダイレクト |
| `dataset.spec.ts` | 3 | CSVインポート+詳細確認、一覧+削除、プレビュー表示 |
| `card-dashboard.spec.ts` | 4 | カード作成、ダッシュボード作成+閲覧、一覧閲覧、カード削除 |

### テストヘルパー

| ヘルパー | ファイル | 用途 |
|---------|---------|------|
| `loginViaUI(page, email, password)` | login-helper.ts | UI 経由でログインして /dashboards へ遷移 |
| `getAccessToken(email, password)` | api-helper.ts | API 経由でアクセストークン取得 |
| `createDataset(token, name, csv)` | api-helper.ts | API 経由でデータセット作成 |
| `createCard(token, name, datasetId, code?)` | api-helper.ts | API 経由でカード作成 |
| `createDashboard(token, name, cardIds?)` | api-helper.ts | API 経由でダッシュボード作成 |
| `deleteDataset/Card/Dashboard(token, id)` | api-helper.ts | API 経由で各リソース削除 |
| `cleanupTestData(token, cleanup)` | api-helper.ts | テストデータ一括削除 (Dashboard->Card->Dataset順) |

### テストデータ管理

- テストユーザ: `e2e@example.com` / `Test@1234` (`scripts/seed_test_user.py` で作成)
- `beforeEach`: loginViaUI() でログイン + cleanup トラッキング初期化
- `afterEach`: cleanupTestData() で作成したリソースを逆順削除
- サンプルCSV: `e2e/sample-data/test-sales.csv` (date, product, amount, quantity)

### Playwright 設定

- `testDir`: `./e2e`
- `baseURL`: `http://localhost:3000`
- `workers`: 1 (DynamoDB Local 共有のため)
- `fullyParallel`: false
- `timeout`: 60s (Docker 環境考慮)
- `globalSetup`: バックエンド /api/health ポーリング (最大30回, 2秒間隔)
- ブラウザ: Chromium のみ
- 失敗時: screenshot, video (retain-on-failure), trace (on-first-retry)

## ユニットテストインフラストラクチャ

### 設定 (vitest.config.ts)
- 環境: jsdom
- セットアップ: `src/__tests__/setup.ts` (jest-dom matchers, CSS mock)
- カバレッジ: V8 provider, 80% threshold (lines/functions/branches/statements)
- 除外: `src/main.tsx`, `*.d.ts`, `__tests__/**`

### テストユーティリティ (helpers/test-utils.tsx)

| ユーティリティ | 用途 |
|---------------|------|
| `createTestQueryClient()` | retry無効・gcTime=0 の QueryClient |
| `renderWithProviders(ui, opts?)` | QueryClient + MemoryRouter ラッパー |
| `createWrapper(queryClient?)` | renderHook 用ラッパー |
| `setupAuthState(token, user)` | Zustand ストアに認証状態設定 |
| `clearAuthState()` | 認証状態クリア |
| `createMockUser(overrides?)` | User ファクトリ |
| `createMockDataset(overrides?)` | Dataset ファクトリ |
| `createMockCard(overrides?)` | Card ファクトリ |
| `createMockDashboard(overrides?)` | Dashboard ファクトリ |
| `createMockPaginatedResponse(items, total?)` | PaginatedResponse ファクトリ |

### テストカバレッジマトリクス

| 対象カテゴリ | テストファイル数 | テスト対象 |
|-------------|-----------------|-----------|
| App | 1 | App.test.tsx |
| Types | 1 | type-guards.test.ts |
| Stores | 1 | auth-store.test.ts |
| Hooks | 4 | use-auth, use-cards, use-dashboards, use-datasets |
| Lib | 3 | api-client, layout-utils, utils |
| Lib/API | 4 | auth, cards, dashboards, datasets |
| Components/common | 8 | AuthGuard, ConfirmDialog, ErrorBoundary, Header, Layout, LoadingSpinner, Pagination, Sidebar |
| Components/card | 2 | CardEditor, CardPreview |
| Components/dashboard | 7 | AddCardDialog, CardContainer, DashboardEditor, DashboardViewer, FilterBar, FilterConfigPanel, FilterDefinitionForm |
| Components/dashboard/filters | 2 | CategoryFilter, DateRangeFilter |
| Pages | 9 | Login, DashboardList/View/Edit, DatasetList/Import/Detail, CardList/Edit |
| **合計 (Unit)** | **42** | **83.07% statement coverage** |

## 関連コードマップ

- [architecture.md](./architecture.md) - 全体アーキテクチャ
- [backend.md](./backend.md) - バックエンド構造
- [data.md](./data.md) - データモデル詳細
