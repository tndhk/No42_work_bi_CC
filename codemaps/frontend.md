# フロントエンド コードマップ

最終更新: 2026-02-05 (Audit Log 機能追加)
フレームワーク: React 18 + TypeScript + Vite 5
エントリポイント: `frontend/src/main.tsx`
テストカバレッジ: 64テストファイル (Unit) + 4スペック (E2E)

---

## ディレクトリ構造

```
frontend/
  playwright.config.ts                 # Playwright E2E テスト設定
  vitest.config.ts                     # Vitest 設定 (jsdom, V8 coverage, 80% threshold)
  e2e/                                 # Playwright E2E テスト
    global-setup.ts                    # バックエンド起動待機 (ヘルスチェック)
    auth.spec.ts                       # 認証フロー E2E (5テスト)
    dataset.spec.ts                    # データセット E2E (3テスト)
    card-dashboard.spec.ts             # カード+ダッシュボード E2E (4テスト)
    sharing.spec.ts                    # 共有+グループ管理 E2E (14テスト) [FR-7]
    helpers/
      login-helper.ts                  # loginViaUI() ヘルパー
      api-helper.ts                    # テストデータ CRUD ヘルパー (createShare, createGroup 追加)
    sample-data/
      test-sales.csv                   # テスト用 CSV (5行, 4列)
  src/
    main.tsx                           # ReactDOM.createRoot, StrictMode
    App.tsx                            # QueryClientProvider + RouterProvider
    routes.tsx                         # createBrowserRouter 定義 (13ルート)
    index.css                          # TailwindCSS
    vite-env.d.ts                      # Vite 型定義
    components/
      common/
        index.ts                       # barrel export
        AuthGuard.tsx                  # 認証ガード (Zustand)
        ErrorBoundary.tsx              # React ErrorBoundary
        Header.tsx                     # ヘッダー (ユーザーメニュー)
        Layout.tsx                     # Sidebar + Header + Outlet
        Sidebar.tsx                    # ナビゲーション (Transform リンク, admin 時 グループ管理+監査ログリンク表示)
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
        FilterViewSelector.tsx         # FilterView 選択/保存/上書き/削除
        ShareDialog.tsx                # ダッシュボード共有設定ダイアログ [FR-7]
        filters/
          CategoryFilter.tsx           # カテゴリフィルタ (単一/複数選択)
          DateRangeFilter.tsx          # 日付範囲フィルタ (カレンダー)
      dataset/                         # データセット関連コンポーネント (単数形)
        S3ImportForm.tsx               # S3 CSV インポートフォーム
      datasets/                        # データセット関連コンポーネント (複数形) [FR-1.3]
        SchemaChangeWarningDialog.tsx  # スキーマ変更警告ダイアログ (再取り込み時)
      transform/                       # Transform 関連コンポーネント [FR-2.1]
        TransformCodeEditor.tsx        # Monaco Editor (Python, Transform 用)
        DatasetMultiSelect.tsx         # 入力データセット複数選択
        TransformExecutionResult.tsx   # 実行結果表示 (行数, カラム, 実行時間)
        TransformExecutionHistory.tsx  # 実行履歴一覧 (ステータスバッジ, 手動/スケジュール区分)
        TransformScheduleConfig.tsx    # スケジュール設定 (Cron式 + プリセット)
      group/                           # グループ管理コンポーネント [FR-7]
        GroupCreateDialog.tsx           # グループ新規作成ダイアログ
        GroupDetailPanel.tsx            # グループ詳細 + メンバー一覧パネル
        MemberAddDialog.tsx             # メンバー追加ダイアログ
      ui/                              # shadcn/ui コンポーネント
        alert-dialog.tsx, badge.tsx, button.tsx, calendar.tsx,
        card.tsx, checkbox.tsx, dialog.tsx, dropdown-menu.tsx,
        form.tsx, input.tsx, label.tsx, popover.tsx,
        select.tsx, separator.tsx, sheet.tsx, table.tsx
    hooks/
      index.ts                         # barrel export (全 hook 再エクスポート)
      use-auth.ts                      # useLogin, useLogout, useCurrentUser
      use-cards.ts                     # useCards, useCard, CRUD + execute + preview
      use-dashboards.ts                # useDashboards, useDashboard, CRUD + clone
      use-datasets.ts                  # useDatasets, useDataset, CRUD + preview + S3 import + reimport [FR-1.3]
      use-dashboard-shares.ts          # useShares, useCreateShare, useUpdateShare, useDeleteShare [FR-7]
      use-filter-views.ts              # useFilterViews, CRUD
      use-groups.ts                    # useGroups, useGroup, CRUD + useAddMember, useRemoveMember [FR-7]
      use-transforms.ts               # useTransforms, useTransform, CRUD + execute + executions [FR-2.1]
      use-audit-logs.ts              # useAuditLogs (query, admin向け)
    lib/
      api-client.ts                    # ky ベース HTTPクライアント (JWT自動付与)
      utils.ts                         # cn() (clsx + tailwind-merge)
      layout-utils.ts                  # toRGLLayout(), fromRGLLayout()
      api/
        index.ts                       # barrel export (9 API モジュール)
        auth.ts                        # authApi
        cards.ts                       # cardsApi
        dashboards.ts                  # dashboardsApi
        datasets.ts                    # datasetsApi (reimportDryRun, reimport 追加) [FR-1.3]
        dashboard-shares.ts            # dashboardSharesApi [FR-7]
        filter-views.ts                # filterViewsApi
        groups.ts                      # groupsApi [FR-7]
        transforms.ts                  # transformsApi [FR-2.1]
        audit-logs.ts                  # auditLogsApi (list)
    pages/
      LoginPage.tsx                    # ログインフォーム
      DashboardListPage.tsx            # ダッシュボード一覧 (権限バッジ, 権限別操作ボタン表示)
      DashboardViewPage.tsx            # ダッシュボード閲覧 (ShareDialog, 権限別ボタン表示)
      DashboardEditPage.tsx            # ダッシュボード編集 (viewer リダイレクト)
      DatasetListPage.tsx              # データセット一覧
      DatasetImportPage.tsx            # CSVインポート
      DatasetDetailPage.tsx            # データセット詳細 (再取り込み+スキーマ変更警告) [FR-1.3]
      CardListPage.tsx                 # カード一覧
      CardEditPage.tsx                 # カード編集 (コードエディタ)
      TransformListPage.tsx            # Transform 一覧 (CRUD + ページネーション) [FR-2.1]
      TransformEditPage.tsx            # Transform 編集 (コード/データセット選択/スケジュール/実行/履歴) [FR-2.1]
      GroupListPage.tsx                # グループ管理 (admin専用) [FR-7]
      AuditLogListPage.tsx            # 監査ログ一覧 (admin専用、フィルタ+ページネーション)
    stores/
      auth-store.ts                    # Zustand 認証ストア
    types/
      index.ts                         # barrel export (全型 + type guards)
      api.ts                           # ApiResponse, PaginatedResponse, etc
      user.ts                          # User, UserWithGroups, GroupRef, LoginRequest, LoginResponse
      card.ts                          # Card, CardDetail, execute/preview 型
      dashboard.ts                     # Dashboard, LayoutItem, FilterDefinition, DashboardShare, Permission, SharedToType
      dataset.ts                       # Dataset, ColumnSchema, DatasetPreview, OwnerRef
      filter-view.ts                   # FilterView, FilterViewCreateRequest, FilterViewUpdateRequest
      group.ts                         # Group, GroupDetail, GroupMember, GroupCreateRequest, GroupUpdateRequest, AddMemberRequest [FR-7]
      reimport.ts                      # SchemaChange, ReimportDryRunResponse, ReimportRequest [FR-1.3]
      transform.ts                     # Transform, TransformCreateRequest, TransformUpdateRequest, TransformExecuteResponse, TransformExecution, isTransform [FR-2.1]
      audit-log.ts                     # EventType, AuditLog, AuditLogListParams
    __tests__/                         # Vitest テストスイート (64ファイル)
      setup.ts                         # jest-dom matchers, CSS mock
      vitest.d.ts                      # カスタム型定義
      helpers/
        test-utils.tsx                 # renderWithProviders, factory 関数 (createMockTransform, createMockTransformExecution 追加)
      App.test.tsx                     # App コンポーネントテスト
      types/
        type-guards.test.ts            # 全 type guard テスト
        transform-type-guards.test.ts  # Transform type guard テスト [FR-2.1]
      stores/
        auth-store.test.ts             # Zustand ストアテスト
      hooks/
        use-auth.test.ts               # 認証 hooks テスト
        use-cards.test.ts              # カード hooks テスト
        use-dashboards.test.ts         # ダッシュボード hooks テスト
        use-datasets.test.ts           # データセット hooks テスト
        use-dashboard-shares.test.ts   # 共有 hooks テスト [FR-7]
        use-filter-views.test.ts       # FilterView hooks テスト
        use-groups.test.ts             # グループ hooks テスト [FR-7]
        use-transforms.test.ts         # Transform hooks テスト [FR-2.1]
      lib/
        api-client.test.ts             # HTTP クライアントテスト
        layout-utils.test.ts           # レイアウトユーティリティテスト
        utils.test.ts                  # cn() ユーティリティテスト
        api/
          auth.test.ts                 # authApi テスト
          cards.test.ts                # cardsApi テスト
          dashboards.test.ts           # dashboardsApi テスト
          datasets.test.ts             # datasetsApi テスト
          filter-views.test.ts         # filterViewsApi テスト
          transforms.test.ts           # transformsApi テスト [FR-2.1]
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
          FilterBar.test.tsx           # フィルタバーテスト
          FilterConfigPanel.test.tsx   # フィルタ設定テスト
          FilterDefinitionForm.test.tsx # フィルタ定義フォームテスト
          FilterViewSelector.test.tsx  # FilterView セレクタテスト
          ShareDialog.test.tsx         # 共有ダイアログテスト [FR-7]
          filters/
            CategoryFilter.test.tsx    # カテゴリフィルタテスト
            DateRangeFilter.test.tsx   # 日付範囲フィルタテスト
        dataset/
          S3ImportForm.test.tsx        # S3 インポートフォームテスト
        datasets/                      # [FR-1.3]
          SchemaChangeWarningDialog.test.tsx # スキーマ変更警告ダイアログテスト
        transform/                     # [FR-2.1]
          TransformCodeEditor.test.tsx # コードエディタテスト
          DatasetMultiSelect.test.tsx   # データセット複数選択テスト
          TransformExecutionResult.test.tsx # 実行結果表示テスト
          TransformExecutionHistory.test.tsx # 実行履歴テスト
          TransformScheduleConfig.test.tsx # スケジュール設定テスト
        group/                         # グループコンポーネントテスト [FR-7]
          GroupCreateDialog.test.tsx    # グループ作成ダイアログテスト
          GroupDetailPanel.test.tsx     # グループ詳細パネルテスト
          GroupListPage.test.tsx        # グループ一覧ページテスト
          MemberAddDialog.test.tsx      # メンバー追加ダイアログテスト
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
        TransformListPage.test.tsx     # Transform 一覧テスト [FR-2.1]
        TransformEditPage.test.tsx     # Transform 編集テスト [FR-2.1]
```

## ルーティング

| パス | ページ | 認証 | 説明 |
|------|--------|------|------|
| `/login` | LoginPage | 不要 | ログイン |
| `/` | (redirect) | 必要 | `/dashboards` へリダイレクト |
| `/dashboards` | DashboardListPage | 必要 | ダッシュボード一覧 (権限バッジ表示) |
| `/dashboards/:id` | DashboardViewPage | 必要 | ダッシュボード閲覧 (owner: 共有ボタン表示) |
| `/dashboards/:id/edit` | DashboardEditPage | 必要 | ダッシュボード編集 (viewer はリダイレクト) |
| `/datasets` | DatasetListPage | 必要 | データセット一覧 |
| `/datasets/import` | DatasetImportPage | 必要 | CSVインポート |
| `/datasets/:id` | DatasetDetailPage | 必要 | データセット詳細 (再取り込みボタン) [FR-1.3] |
| `/cards` | CardListPage | 必要 | カード一覧 |
| `/cards/:id` | CardEditPage | 必要 | カード編集 (new/既存) |
| `/transforms` | TransformListPage | 必要 | Transform 一覧 [FR-2.1] |
| `/transforms/:id` | TransformEditPage | 必要 | Transform 編集 (new/既存) [FR-2.1] |
| `/admin/groups` | GroupListPage | 必要 | グループ管理 (admin 専用, Sidebar から遷移) [FR-7] |
| `/admin/audit-logs` | AuditLogListPage | 必要 | 監査ログ閲覧 (admin 専用, Sidebar から遷移) |

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
              |     +-- useAuthStore (store) -- user.role チェック
              |     +-- 常時表示: ダッシュボード, データセット, Transform, カード
              |     +-- admin の場合: グループ管理 (/admin/groups) + 監査ログ (/admin/audit-logs) リンクを追加表示
              +-- Outlet --> 各ページ
```

### ページ --> コンポーネント

```
DashboardListPage
  +-- useDashboards, useCreateDashboard, useDeleteDashboard
  +-- LoadingSpinner, Pagination, ConfirmDialog
  +-- ui/table, ui/dialog, ui/button, ui/input, ui/badge
  +-- dashboard.my_permission による表示制御:
  |     owner  -> Eye + Pencil + Trash (全操作)
  |     editor -> Eye + Pencil (閲覧+編集)
  |     viewer -> Eye のみ (閲覧のみ)
  +-- Badge で my_permission を表示 (owner=default, 他=secondary)

DashboardViewPage
  +-- useDashboard, useExecuteCard
  +-- useFilterViews, useCreateFilterView, useUpdateFilterView, useDeleteFilterView
  +-- FilterBar (フィルタ適用 UI)
  |     +-- CategoryFilter (filters/)
  |     +-- DateRangeFilter (filters/)
  +-- FilterViewSelector (FilterView 選択/保存/上書き/削除)
  +-- ShareDialog (owner のみ表示, 共有設定ダイアログ) [FR-7]
  |     +-- useShares, useCreateShare, useUpdateShare, useDeleteShare
  |     +-- 共有タイプ (user/group), 共有先ID, 権限 (viewer/editor) を管理
  +-- DashboardViewer (filterValues 対応)
  |     +-- ResponsiveGridLayout (react-grid-layout)
  |     +-- toRGLLayout (lib/layout-utils)
  |     +-- CardContainer (iframe sandbox, filterApplied)
  |     +-- LoadingSpinner
  +-- my_permission による表示制御:
        owner  -> 編集ボタン + 共有ボタン
        editor -> 編集ボタンのみ
        viewer -> ボタンなし

DashboardEditPage
  +-- useDashboard, useUpdateDashboard
  +-- viewer 権限の場合 /dashboards/:id へリダイレクト
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

DatasetDetailPage [FR-1.3 拡張]
  +-- useDataset, useDatasetPreview, useReimportDryRun, useReimportDataset
  +-- SchemaChangeWarningDialog (components/datasets/)
  |     +-- スキーマ変更検出時に警告表示、force 再取り込み確認
  +-- LoadingSpinner

TransformListPage [FR-2.1]
  +-- useTransforms, useDeleteTransform
  +-- LoadingSpinner, Pagination, ConfirmDialog
  +-- ui/table, ui/button
  +-- 一覧表示: 名前, 入力データセット数, オーナー, 更新日時

TransformEditPage [FR-2.1]
  +-- useTransform, useCreateTransform, useUpdateTransform, useExecuteTransform, useDatasets
  +-- TransformCodeEditor (Monaco Editor, Python)
  +-- DatasetMultiSelect (入力データセット複数選択)
  +-- TransformScheduleConfig (Cron式, プリセット, 有効/無効切替)
  +-- TransformExecutionResult (行数, カラム, 実行時間, 出力データセットリンク)
  +-- TransformExecutionHistory (実行履歴一覧)
  |     +-- useTransformExecutions
  |     +-- ステータスバッジ (success/failed/running)
  |     +-- 手動実行 / スケジュール実行 区分表示
  +-- 2カラムレイアウト: 左=設定+コード, 右=結果+履歴

AuditLogListPage (admin専用)
  +-- useAuditLogs (hook)
  +-- LoadingSpinner, Pagination
  +-- ui/table, ui/badge, ui/select
  +-- EventType フィルタ (Select コンポーネント)
  +-- イベントタイプ別バッジカラー表示

GroupListPage [FR-7]
  +-- useGroups, useDeleteGroup
  +-- LoadingSpinner, ConfirmDialog
  +-- GroupCreateDialog (グループ作成ダイアログ)
  |     +-- useCreateGroup
  +-- GroupDetailPanel (グループ詳細+メンバー管理パネル)
        +-- useGroup, useRemoveMember
        +-- MemberAddDialog (メンバー追加ダイアログ)
              +-- useAddMember

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
| `['transforms', params?]` | useTransforms | Transform 一覧 [FR-2.1] |
| `['transforms', id]` | useTransform | Transform 詳細 [FR-2.1] |
| `['transform-executions', id, params?]` | useTransformExecutions | Transform 実行履歴 [FR-2.1] |
| `['shares', dashboardId]` | useShares | ダッシュボード共有一覧 [FR-7] |
| `['groups']` | useGroups | グループ一覧 [FR-7] |
| `['groups', groupId]` | useGroup | グループ詳細 (メンバー含む) [FR-7] |
| `['audit-logs', params?]` | useAuditLogs | 監査ログ一覧 |

## API クライアント層

```
lib/api-client.ts (ky ベース)
  |-- beforeRequest: JWT トークン自動付与
  |-- afterResponse: 401 --> clearAuth() + /login リダイレクト
  |
  +-- lib/api/auth.ts              authApi.login(), logout(), me()
  +-- lib/api/cards.ts              cardsApi.list(), get(), create(), update(), delete(), execute(), preview()
  +-- lib/api/dashboards.ts         dashboardsApi.list(), get(), create(), update(), delete(), clone(), getReferencedDatasets()
  +-- lib/api/datasets.ts           datasetsApi.list(), get(), create(FormData), update(), delete(), preview(), getColumnValues(), s3Import(), reimportDryRun(), reimport() [FR-1.3]
  +-- lib/api/dashboard-shares.ts   dashboardSharesApi.list(), create(), update(), delete() [FR-7]
  +-- lib/api/filter-views.ts       filterViewsApi.list(), create(), update(), delete()
  +-- lib/api/groups.ts             groupsApi.list(), get(), create(), update(), delete(), addMember(), removeMember() [FR-7]
  +-- lib/api/transforms.ts         transformsApi.list(), get(), create(), update(), delete(), execute(), listExecutions() [FR-2.1]
  +-- lib/api/audit-logs.ts         auditLogsApi.list(params?)
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
| `useS3ImportDataset()` | mutation | S3 CSV インポート |
| `useReimportDryRun()` | mutation | 再取り込み dry-run (スキーマ変更検出) [FR-1.3] |
| `useReimportDataset()` | mutation | 再取り込み実行 (force オプション) [FR-1.3] |

### use-transforms.ts [FR-2.1]
| hook | 種別 | 説明 |
|------|------|------|
| `useTransforms(params?)` | query | Transform 一覧 |
| `useTransform(transformId)` | query | Transform 詳細 |
| `useCreateTransform()` | mutation | Transform 作成 |
| `useUpdateTransform()` | mutation | Transform 更新 |
| `useDeleteTransform()` | mutation | Transform 削除 |
| `useExecuteTransform()` | mutation | Transform 手動実行 |
| `useTransformExecutions(id, params?)` | query | Transform 実行履歴 |

### use-dashboard-shares.ts [FR-7]
| hook | 種別 | 説明 |
|------|------|------|
| `useShares(dashboardId)` | query | ダッシュボードの共有一覧を取得 |
| `useCreateShare()` | mutation | 共有追加 (shared_to_type, shared_to_id, permission) |
| `useUpdateShare()` | mutation | 共有権限更新 |
| `useDeleteShare()` | mutation | 共有削除 |

### use-groups.ts [FR-7]
| hook | 種別 | 説明 |
|------|------|------|
| `useGroups()` | query | グループ一覧 |
| `useGroup(groupId)` | query | グループ詳細 (メンバー含む) |
| `useCreateGroup()` | mutation | グループ作成 |
| `useUpdateGroup()` | mutation | グループ名更新 |
| `useDeleteGroup()` | mutation | グループ削除 |
| `useAddMember()` | mutation | グループにメンバー追加 |
| `useRemoveMember()` | mutation | グループからメンバー削除 |

### use-audit-logs.ts
| hook | 種別 | 説明 |
|------|------|------|
| `useAuditLogs(params?)` | query | 監査ログ一覧 (event_type, user_id, target_id, start_date, end_date, limit, offset) |

### use-filter-views.ts
| hook | 種別 | 説明 |
|------|------|------|
| `useFilterViews(dashboardId)` | query | FilterView 一覧 |
| `useCreateFilterView()` | mutation | FilterView 作成 |
| `useUpdateFilterView()` | mutation | FilterView 更新 |
| `useDeleteFilterView()` | mutation | FilterView 削除 |

## 型定義一覧

| ファイル | 主要な型 | 備考 |
|---------|---------|------|
| `api.ts` | ApiResponse, PaginatedResponse, PaginationParams, isApiErrorResponse, isPagination | 共通 API レスポンス型 |
| `user.ts` | User, UserWithGroups, GroupRef, LoginRequest, LoginResponse, isUser, isLoginResponse | 認証・ユーザー |
| `dataset.ts` | Dataset, DatasetDetail, ColumnSchema, OwnerRef, DatasetPreview, S3ImportRequest | データセット |
| `card.ts` | Card, CardRef, CardDetail, CardExecuteRequest, CardExecuteResponse, CardPreviewResponse, isCard | カード |
| `dashboard.ts` | Dashboard, DashboardDetail, LayoutItem, FilterDefinition, DashboardShare, Permission, SharedToType, isDashboard, isLayoutItem | ダッシュボード |
| `filter-view.ts` | FilterView, FilterViewCreateRequest, FilterViewUpdateRequest | フィルタビュー |
| `group.ts` | Group, GroupDetail, GroupMember, GroupCreateRequest, GroupUpdateRequest, AddMemberRequest | グループ [FR-7] |
| `reimport.ts` | SchemaChange, SchemaChangeType, ReimportDryRunResponse, ReimportRequest | 再取り込み [FR-1.3] |
| `transform.ts` | Transform, TransformCreateRequest, TransformUpdateRequest, TransformExecuteResponse, TransformExecution, isTransform | Transform [FR-2.1] |
| `audit-log.ts` | EventType (12種), AuditLog, AuditLogListParams | 監査ログ |

## カード描画セキュリティ

`CardContainer.tsx` で生成される iframe:
- `sandbox="allow-scripts"` (フォーム、ナビゲーション、popups 禁止)
- CSP: `default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data: blob:`
- `srcDoc` で HTML 直接注入 (外部URL無し)

## UI コンポーネント (shadcn/ui)

Radix UI + Tailwind CSS ベース:
`alert-dialog`, `badge`, `button`, `calendar`, `card`, `checkbox`, `dialog`, `dropdown-menu`, `form`, `input`, `label`, `popover`, `select`, `separator`, `sheet`, `table`

## E2E テスト (Playwright)

### 構成

| ファイル | テスト数 | 対象 |
|---------|---------|------|
| `auth.spec.ts` | 5 | 未認証リダイレクト、バリデーション、認証失敗、ログイン/ログアウト、ログイン済リダイレクト |
| `dataset.spec.ts` | 3 | CSVインポート+詳細確認、一覧+削除、プレビュー表示 |
| `card-dashboard.spec.ts` | 4 | カード作成、ダッシュボード作成+閲覧、一覧閲覧、カード削除 |
| `sharing.spec.ts` | 14 | Dashboard共有フロー, 共有ダッシュボード閲覧, 権限別操作制限, Group管理 [FR-7] |

sharing.spec.ts 内訳:
- Dashboard共有フロー (1テスト): Owner による ShareDialog からの共有追加
- 共有されたダッシュボードの閲覧 (3テスト): 一覧表示, viewer 編集/共有ボタン非表示, 閲覧可能
- 権限別操作制限 (5テスト): Viewer/Editor/Owner のボタン表示差分検証
- Group管理 (5テスト): Admin サイドバーリンク, 非Admin 非表示, 作成, メンバー追加, 削除

テストユーザー (sharing.spec.ts):
- Admin/Owner: e2e@example.com
- Viewer: e2e-viewer@example.com
- Editor: e2e-editor@example.com
- Member (非Admin): e2e-member@example.com

### テストヘルパー

| ヘルパー | ファイル | 用途 |
|---------|---------|------|
| `loginViaUI(page, email, password)` | login-helper.ts | UI 経由でログインして /dashboards へ遷移 |
| `getAccessToken(email, password)` | api-helper.ts | API 経由でアクセストークン取得 |
| `createDataset(token, name, csv)` | api-helper.ts | API 経由でデータセット作成 |
| `createCard(token, name, datasetId, code?)` | api-helper.ts | API 経由でカード作成 |
| `createDashboard(token, name, cardIds?)` | api-helper.ts | API 経由でダッシュボード作成 |
| `createShare(token, dashId, type, toId, perm)` | api-helper.ts | API 経由でダッシュボード共有作成 [FR-7] |
| `createGroup(token, name)` | api-helper.ts | API 経由でグループ作成 [FR-7] |
| `deleteDataset/Card/Dashboard(token, id)` | api-helper.ts | API 経由で各リソース削除 |
| `cleanupTestData(token, cleanup)` | api-helper.ts | テストデータ一括削除 (Share->Dashboard->Card->Dataset->Group順) |

TestDataCleanup 型 (cleanup トラッキング):
- datasetIds, cardIds, dashboardIds: 基本リソース
- shareIds: { dashboardId, shareId }[] [FR-7]
- groupIds: string[] [FR-7]

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
| `createMockTransform(overrides?)` | Transform ファクトリ [FR-2.1] |
| `createMockTransformExecution(overrides?)` | TransformExecution ファクトリ [FR-2.1] |
| `createMockPaginatedResponse(items, total?)` | PaginatedResponse ファクトリ |

### テストカバレッジマトリクス

| 対象カテゴリ | テストファイル数 | テスト対象 |
|-------------|-----------------|-----------|
| App | 1 | App.test.tsx |
| Types | 2 | type-guards, transform-type-guards [FR-2.1] |
| Stores | 1 | auth-store |
| Hooks | 8 | use-auth, use-cards, use-dashboards, use-datasets, use-dashboard-shares, use-filter-views, use-groups, use-transforms [FR-2.1] |
| Lib | 3 | api-client, layout-utils, utils |
| Lib/API | 6 | auth, cards, dashboards, datasets, filter-views, transforms [FR-2.1] |
| Components/common | 8 | AuthGuard, ConfirmDialog, ErrorBoundary, Header, Layout, LoadingSpinner, Pagination, Sidebar |
| Components/card | 2 | CardEditor, CardPreview |
| Components/dashboard | 10 | AddCardDialog, CardContainer, DashboardEditor, DashboardViewer, FilterBar, FilterConfigPanel, FilterDefinitionForm, FilterViewSelector, ShareDialog |
| Components/dashboard/filters | 2 | CategoryFilter, DateRangeFilter |
| Components/dataset | 1 | S3ImportForm |
| Components/datasets | 1 | SchemaChangeWarningDialog [FR-1.3] |
| Components/transform | 5 | TransformCodeEditor, DatasetMultiSelect, TransformExecutionResult, TransformExecutionHistory, TransformScheduleConfig [FR-2.1] |
| Components/group | 4 | GroupCreateDialog, GroupDetailPanel, GroupListPage, MemberAddDialog [FR-7] |
| Pages | 11 | Login, DashboardList/View/Edit, DatasetList/Import/Detail, CardList/Edit, TransformList/Edit [FR-2.1] |
| 合計 (Unit) | 64 | -- |

## 関連コードマップ

- [architecture.md](./architecture.md) - 全体アーキテクチャ
- [backend.md](./backend.md) - バックエンド構造
- [data.md](./data.md) - データモデル詳細
