# 開発者ガイド (CONTRIB)

最終更新: 2026-02-05

## このドキュメントについて

- 役割: 開発者向けクイックスタートガイド、開発コマンド、プロジェクト構造の説明
- 関連: 技術仕様は [tech-spec.md](tech-spec.md)、設計は [design.md](design.md)、運用は [RUNBOOK.md](RUNBOOK.md) を参照

---

## 1. 前提条件

| ツール | バージョン |
|--------|-----------|
| Docker / Docker Compose | 最新安定版 |
| Node.js | 20.x |
| Python | 3.11+ |

---

## 2. クイックスタート

```bash
# 1. 環境変数ファイル作成
cp .env.example .env

# 2. 全サービス起動
docker compose up --build
```

| サービス | URL | 説明 |
|---------|-----|------|
| フロントエンド | http://localhost:3000 | React SPA (Vite) |
| API (Swagger UI) | http://localhost:8000/docs | FastAPI |
| Executor | http://localhost:8080 | Python Sandbox |
| MinIO Console | http://localhost:9001 | S3互換ストレージ (admin: minioadmin/minioadmin) |
| DynamoDB Local | http://localhost:8001 | DynamoDB互換DB |

> docker-compose設定の詳細は [deployment.md Section 2.3](deployment.md#23-docker-composeyml) を参照

---

## 3. 環境変数

`.env.example` を `.env` にコピーして設定。

> 詳細は [tech-spec.md Section 3.1](tech-spec.md#31-環境変数) を参照

---

## 4. 開発コマンド

### フロントエンド (frontend/)

| スクリプト名 | コマンド | 目的 |
|-------------|---------|------|
| `dev` | `vite` | 開発サーバ起動 (Vite HMR) |
| `build` | `tsc && vite build` | プロダクションビルド (型チェック + バンドル) |
| `preview` | `vite preview` | ビルド結果プレビュー |
| `test` | `vitest` | Vitestテスト (ウォッチモード) |
| `test:coverage` | `vitest --coverage` | カバレッジ付きテスト (v8) |
| `lint` | `eslint . --ext ts,tsx` | ESLint実行 |
| `typecheck` | `tsc --noEmit` | TypeScript型チェック (--noEmit) |
| `e2e` | `playwright test` | Playwright E2Eテスト (ヘッドレス) |
| `e2e:ui` | `playwright test --ui` | Playwright E2Eテスト (UI モード) |
| `e2e:headed` | `playwright test --headed` | Playwright E2Eテスト (ブラウザ表示) |
| `e2e:report` | `playwright show-report` | E2Eテストレポート表示 |

### バックエンド (backend/)

| コマンド | 説明 |
|---------|------|
| `pytest` | テスト実行 |
| `pytest --cov=app` | カバレッジ付きテスト |
| `pytest -v -k "test_name"` | 特定テストのみ実行 |
| `ruff check app/` | リンティング |
| `ruff format app/` | フォーマット |
| `mypy app/` | 型チェック |
| `uvicorn app.main:app --reload` | 開発サーバ起動 |

### Docker Compose

| コマンド | 説明 |
|---------|------|
| `docker compose up --build` | 全サービス起動 |
| `docker compose up -d --build` | バックグラウンド起動 |
| `docker compose down` | 停止 |
| `docker compose down -v` | 停止 + データ削除 |
| `docker compose logs -f api` | APIログ確認 |
| `docker compose logs -f executor` | Executorログ確認 |
| `docker compose run --rm dynamodb-init` | DynamoDBテーブル再作成 |

---

## 5. テスト

### テスト基準

| コンポーネント | 基準 |
|---------------|------|
| フロントエンド | 83%+ coverage, 64 テストファイル |
| バックエンド | pytest pass |
| E2E | 全テストpass |

### フロントエンドテスト構成

テストファイルは `src/__tests__/` 以下に、ソースコードと同じディレクトリ構造で配置される。

| カテゴリ | テストファイル数 | 対象 |
|---------|-----------------|------|
| コンポーネント | 33 | card/ (2), common/ (7), dashboard/ (10), dataset/ (1), datasets/ (1), group/ (4), transform/ (5), その他 (App: 1), lib/utils系 (2) |
| hooks | 9 | use-auth, use-cards, use-dashboards, use-datasets, use-filter-views, use-groups, use-dashboard-shares, use-transforms, use-audit-logs |
| lib/api | 8 | api-client, auth, cards, dashboards, datasets, filter-views, transforms, audit-logs |
| pages | 12 | Login, DatasetList/Import/Detail, CardList/Edit, DashboardList/View/Edit, TransformList/Edit, AuditLogList |
| types | 2 | type-guards, transform-type-guards |
| stores | 1 | auth-store |

### E2Eテスト実行

```bash
# 1. 全サービス起動
docker compose up -d --build

# 2. テストユーザ作成
python scripts/seed_test_user.py

# 3. E2Eテスト実行
cd frontend && npm run e2e
```

テストユーザ: `e2e@example.com` / `Test@1234`

E2Eテストスイート:

| ファイル | 対象機能 |
|---------|---------|
| `e2e/auth.spec.ts` | ログイン・ログアウト |
| `e2e/dataset.spec.ts` | Dataset取り込み・一覧表示 |
| `e2e/card-dashboard.spec.ts` | Card作成・Dashboard操作 |
| `e2e/sharing.spec.ts` | Dashboard共有 |

### DynamoDBテーブル一覧

初期化スクリプト (`scripts/init_tables.py`) で作成されるテーブル:

> 詳細は [design.md Section 2.1](design.md#21-dynamodbテーブル設計) を参照

---

## 6. コーディング規約

### バックエンド (Python)

- フォーマッタ/リンタ: Ruff (line-length: 100, target: py311)
- 型チェック: mypy (strict, 一部 allow_untyped_defs)
- 命名: snake_case (変数/関数), PascalCase (クラス)
- テスト: pytest + asyncio_mode="auto"

### フロントエンド (TypeScript)

- リンタ: ESLint + TypeScript ESLint
- UIライブラリ: shadcn/ui (Radix UI + Tailwind CSS 3.4)
- 状態管理: TanStack Query v5 (サーバ) + Zustand v4 (クライアント)
- フォーム: React Hook Form v7 + Zod バリデーション
- コードエディタ: Monaco Editor (@monaco-editor/react)
- パスエイリアス: `@/` = `src/`
- テスト: Vitest + Testing Library + jsdom

---

## 7. Git ワークフロー

### ブランチ命名

- `feature/xxx` - 機能開発
- `fix/xxx` - バグ修正
- `docs/xxx` - ドキュメント
- `refactor/xxx` - リファクタリング

### コミットメッセージ

```
<type>: <summary>

<body (optional)>
```

type: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

### PR前チェック

```bash
# フロントエンド
cd frontend && npm run lint && npm run typecheck && npm run test:coverage

# バックエンド
cd backend && ruff check app/ && mypy app/ && pytest --cov=app
```

---

## 8. プロジェクト構造

```
work_BI_ClaudeCode/
  backend/              # FastAPI バックエンド
    app/
      api/routes/       # APIルート (auth, datasets, dashboards, cards, filter_views,
                        #   filter_view_detail, users, groups, dashboard_shares, transforms, audit_logs)
      core/             # 認証・設定 (config, auth, dependencies)
      db/               # DynamoDB接続
      models/           # Pydanticモデル (audit_log, card, common, dashboard, dashboard_share,
                        #   dataset, filter_view, group, schema_change, transform,
                        #   transform_execution, user)
      repositories/     # データアクセス層 (base + 10リポジトリ)
      services/         # ビジネスロジック
        card_execution_service.py       # Card実行
        csv_parser.py                   # CSVパーサー
        dashboard_service.py            # Dashboard操作
        dataset_service.py              # Dataset管理
        parquet_storage.py              # Parquetストレージ
        permission_service.py           # Dashboard権限チェック
        schema_comparator.py            # スキーマ変更比較
        transform_execution_service.py  # Transform実行
        transform_scheduler_service.py  # Transformスケジューラー
        type_inferrer.py                # 型推論
        audit_service.py                # 監査ログ記録サービス
    tests/              # pytestテスト
  executor/             # Python Sandbox (カード/Transform実行)
  frontend/             # React SPA
    src/
      components/       # UIコンポーネント
        card/           # Card編集 (CardEditor) ・プレビュー (CardPreview)
        common/         # 共通レイアウト・認証・エラー処理 (Layout, Sidebar, Header, AuthGuard, ErrorBoundary 等)
        dashboard/      # Dashboard閲覧・編集・フィルタ・共有 (DashboardViewer/Editor, FilterBar, ShareDialog 等)
        dataset/        # S3ImportForm
        datasets/       # SchemaChangeWarningDialog
        group/          # グループ管理 (GroupCreateDialog, GroupDetailPanel, MemberAddDialog)
        transform/      # Transform (TransformCodeEditor, DatasetMultiSelect, TransformExecutionResult, TransformExecutionHistory, TransformScheduleConfig)
        ui/             # shadcn/ui 基盤コンポーネント
      hooks/            # カスタムフック (use-auth, use-cards, use-dashboards, use-datasets, use-filter-views, use-groups, use-dashboard-shares, use-transforms, use-audit-logs)
      lib/              # ユーティリティ・APIクライアント
        api/            # RESTful APIモジュール (auth, cards, dashboards, datasets, dashboard-shares, filter-views, groups, transforms, audit-logs)
      pages/            # ページコンポーネント (13ページ)
      stores/           # Zustand ストア (auth-store)
      types/            # TypeScript型定義 (api, audit-log, card, dashboard, dataset, filter-view, group, reimport, transform, user)
    e2e/                # Playwright E2Eテスト
    __tests__/          # Vitest単体テスト (src/__tests__/)
  scripts/              # 初期化スクリプト (init_tables.py, seed_test_user.py)
  docs/                 # ドキュメント
  codemaps/             # アーキテクチャマップ
```

### フロントエンド ページ一覧

| ページ | ファイル | ルート |
|--------|---------|--------|
| ログイン | LoginPage.tsx | /login |
| Dataset一覧 | DatasetListPage.tsx | /datasets |
| Datasetインポート | DatasetImportPage.tsx | /datasets/import |
| Dataset詳細 | DatasetDetailPage.tsx | /datasets/:id |
| Card一覧 | CardListPage.tsx | /cards |
| Card編集 | CardEditPage.tsx | /cards/:id |
| Dashboard一覧 | DashboardListPage.tsx | /dashboards |
| Dashboard閲覧 | DashboardViewPage.tsx | /dashboards/:id |
| Dashboard編集 | DashboardEditPage.tsx | /dashboards/:id/edit |
| Transform一覧 | TransformListPage.tsx | /transforms |
| Transform編集 | TransformEditPage.tsx | /transforms/:id |
| グループ管理 | GroupListPage.tsx | /admin/groups |
| 監査ログ | AuditLogListPage.tsx | /admin/audit-logs |

### フロントエンド 主要依存パッケージ

| パッケージ | バージョン | 用途 |
|-----------|-----------|------|
| react | ^18.2.0 | UIフレームワーク |
| typescript | ^5.3.3 | 型安全性 |
| vite | ^5.0.10 | ビルドツール |
| @tanstack/react-query | ^5.17.0 | サーバ状態管理 |
| zustand | ^4.4.7 | クライアント状態管理 |
| react-router-dom | ^6.21.0 | ルーティング |
| react-hook-form | ^7.71.1 | フォーム管理 |
| zod | ^3.25.76 | バリデーション |
| @monaco-editor/react | ^4.6.0 | Pythonコードエディタ |
| react-grid-layout | ^1.4.4 | Dashboardグリッドレイアウト |
| ky | ^1.1.3 | HTTPクライアント |
| date-fns | ^4.1.0 | 日付操作 |
| tailwindcss | ^3.4.0 | CSSユーティリティ |

### バックエンド 主要依存パッケージ

| パッケージ | バージョン | 用途 |
|-----------|-----------|------|
| fastapi | 0.109.0 | Webフレームワーク |
| uvicorn | 0.27.0 | ASGIサーバ |
| pydantic | 2.5.0 | データバリデーション |
| pydantic-settings | 2.1.0 | 設定管理 |
| aioboto3 | 12.3.0 | 非同期AWS SDK (DynamoDB/S3) |
| pyarrow | 15.0.0 | Parquet読み書き |
| pandas | 2.2.0 | データフレーム処理 |
| python-jose | 3.3.0 | JWT認証 |
| bcrypt | 4.1.3 | パスワードハッシュ |
| croniter | >=2.0.0 | cron式パース (Transformスケジューラー) |
| structlog | 24.1.0 | 構造化ログ |
| slowapi | 0.1.9 | レート制限 |

---

## 9. 最近の主要変更

### NFR-3/4 監査ログ (2026-02-05)

追加されたバックエンド:
- `app/models/audit_log.py` -- AuditLog Pydantic モデル (EventType enum, AuditLog)
- `app/repositories/audit_log_repository.py` -- AuditLogRepository (DynamoDB CRUD, GSI Query: LogsByUser, LogsByTarget)
- `app/services/audit_service.py` -- AuditService (全12イベントタイプの記録ヘルパー)
- `app/api/routes/audit_logs.py` -- Audit Logs API (GET /api/audit-logs, admin限定)

追加されたフロントエンド:
- `src/types/audit-log.ts` -- AuditLog 型定義 (EventType, AuditLog, AuditLogListParams)
- `src/lib/api/audit-logs.ts` -- Audit Logs API クライアント
- `src/hooks/use-audit-logs.ts` -- useAuditLogs カスタムフック
- `src/pages/AuditLogListPage.tsx` -- 監査ログ一覧ページ (admin限定、イベントタイプフィルタ、ページネーション)

イベントタイプ一覧:
- `USER_LOGIN` / `USER_LOGOUT` / `USER_LOGIN_FAILED` -- 認証関連
- `DASHBOARD_SHARE_ADDED` / `DASHBOARD_SHARE_REMOVED` / `DASHBOARD_SHARE_UPDATED` -- 共有変更
- `DATASET_CREATED` / `DATASET_IMPORTED` / `DATASET_DELETED` -- Dataset操作
- `TRANSFORM_EXECUTED` / `TRANSFORM_FAILED` -- Transform実行
- `CARD_EXECUTION_FAILED` -- Card実行失敗

監査ログの特徴:
- 全APIルート (auth, cards, datasets, dashboard_shares, transforms) に AuditService を統合済み
- ログ記録の失敗はビジネスロジックに影響しない (例外は握りつぶす)
- DynamoDB GSI (LogsByUser, LogsByTarget) による効率的なクエリ
- タイムスタンプは Unix epoch (秒) で DynamoDB に格納、ISO 8601 で API レスポンス

### FR-2 Transform (2026-02-04)

2026-02-04 に完了した Transform 機能 (FR-2.1/2.2/2.3) の概要:

追加されたバックエンド:
- `app/models/transform.py` -- Transform Pydantic モデル (TransformCreate/Update/Transform)
- `app/models/transform_execution.py` -- Transform実行履歴モデル
- `app/repositories/transform_repository.py` -- TransformRepository (DynamoDB CRUD)
- `app/repositories/transform_execution_repository.py` -- 実行履歴リポジトリ
- `app/api/routes/transforms.py` -- Transforms API (CRUD + 手動実行 + 実行履歴)
- `app/services/transform_execution_service.py` -- Transform実行サービス
- `app/services/transform_scheduler_service.py` -- cron式スケジューラー

追加されたフロントエンド:
- `src/types/transform.ts` -- Transform 型定義
- `src/lib/api/transforms.ts` -- Transform API クライアント
- `src/hooks/use-transforms.ts` -- Transform カスタムフック (CRUD + 実行 + 実行履歴)
- `src/pages/TransformListPage.tsx` -- Transform 一覧ページ
- `src/pages/TransformEditPage.tsx` -- Transform 編集ページ
- `src/components/transform/TransformCodeEditor.tsx` -- Monaco コードエディタ
- `src/components/transform/DatasetMultiSelect.tsx` -- 入力Dataset複数選択
- `src/components/transform/TransformExecutionResult.tsx` -- 実行結果表示
- `src/components/transform/TransformExecutionHistory.tsx` -- 実行履歴表示
- `src/components/transform/TransformScheduleConfig.tsx` -- スケジュール設定

Transform の使い方:
1. Transform一覧ページで「新規作成」
2. 入力Datasetを1つ以上選択
3. Pythonコードを記述 (`def transform(inputs, params): ...`)
4. 「手動実行」ボタンで実行 (同期実行、300秒タイムアウト)
5. 実行結果として出力Datasetが生成される
6. (オプション) cron式を設定し、スケジュール実行を有効化

Transform モデルフィールド:
- `name` -- Transform名 (必須)
- `input_dataset_ids` -- 入力Dataset IDリスト (1つ以上必須)
- `code` -- Pythonコード (必須、`def transform(inputs, params)` を定義)
- `output_dataset_id` -- 出力Dataset ID (実行後に自動設定)
- `schedule_cron` -- cron式 (オプション、croniter でバリデーション)
- `schedule_enabled` -- スケジュール実行有効フラグ (デフォルト false)

---

## 10. 関連ドキュメント

| ドキュメント | 内容 |
|-------------|------|
| `docs/requirements.md` | 要件定義 |
| `docs/design.md` | 設計書 |
| `docs/api-spec.md` | API仕様 (全エンドポイント) |
| `docs/RUNBOOK.md` | 運用ガイド |
| `docs/PROGRESS.md` | 実装進捗 |
| `docs/security.md` | セキュリティ仕様 |
| `docs/data-flow.md` | データフロー図 |
| `docs/deployment.md` | デプロイメントガイド |
| `docs/tech-spec.md` | 技術仕様書 |
| `codemaps/` | アーキテクチャマップ |
