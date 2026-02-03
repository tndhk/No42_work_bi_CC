# 開発者ガイド (CONTRIB)

最終更新: 2026-02-03
プロジェクト: 社内BI・Pythonカード MVP
フェーズ: Phase Q4 (E2E) + Q5 (クリーンアップ) + FilterView / S3 Import + Dashboard Sharing / Group Management + FilterView Visibility 実装中

> 実装進捗: 全機能の実装ステータスは [PROGRESS.md](./PROGRESS.md) を参照

---

## 1. 前提条件

開発環境に以下がインストールされていること。

| ツール | バージョン | 用途 |
|--------|-----------|------|
| Docker / Docker Compose | 最新安定版 | コンテナ実行 |
| Node.js | 20.x | フロントエンドビルド |
| Python | 3.11+ | バックエンド / Executor |
| Git | 最新安定版 | バージョン管理 |

---

## 2. リポジトリ構成

```
work_BI_ClaudeCode/
├── backend/             # FastAPI バックエンド (Python 3.11)
│   ├── app/
│   │   ├── api/         # APIルート定義
│   │   │   └── routes/  # auth, datasets, cards, dashboards, filter_views, users, groups, dashboard_shares
│   │   ├── core/        # 設定、セキュリティ、ロギング
│   │   ├── db/          # DynamoDB / S3 クライアント
│   │   ├── models/      # Pydantic モデル (user, dataset, card, dashboard, filter_view, group, dashboard_share, common)
│   │   ├── repositories/# データアクセス層 (DynamoDB CRUD: user, dataset, card, dashboard, filter_view, group, group_member, dashboard_share)
│   │   ├── services/    # ビジネスロジック層 (csv_parser, dataset, card_execution, dashboard, parquet_storage, permission, type_inferrer)
│   │   └── main.py      # アプリケーションエントリポイント
│   ├── tests/           # pytest テスト
│   │   ├── api/routes/  # APIルートテスト (test_auth, test_cards, test_dashboards, test_datasets, test_filter_views, test_s3_import, test_dashboard_shares, test_groups, test_users)
│   │   ├── api/         # test_health, test_deps
│   │   ├── core/        # test_config, test_logging, test_password_policy, test_security
│   │   ├── db/          # test_dynamodb, test_s3
│   │   ├── integration/ # test_permission_integration
│   │   ├── models/      # test_user, test_dataset, test_card, test_dashboard, test_filter_view, test_group, test_dashboard_share, test_common, test_s3_import
│   │   ├── repositories/# test_base, test_user, test_dataset, test_card, test_dashboard, test_filter_view, test_group, test_group_member, test_dashboard_share
│   │   └── services/    # test_csv_parser, test_dataset, test_card_execution, test_dashboard, test_parquet_storage, test_permission, test_type_inferrer 等
│   ├── pyproject.toml   # プロジェクト設定 (ruff, mypy, pytest)
│   ├── requirements.txt # Python依存パッケージ
│   └── Dockerfile.dev   # 開発用Dockerfile
├── frontend/            # React SPA (TypeScript / Vite)
│   ├── src/
│   │   ├── __tests__/   # Vitest テスト (53ファイル, 340+テスト)
│   │   │   ├── components/  # コンポーネントテスト
│   │   │   │   ├── card/        # CardEditor, CardPreview
│   │   │   │   ├── common/      # AuthGuard, ErrorBoundary, Header, Layout 等
│   │   │   │   ├── dashboard/   # DashboardViewer, DashboardEditor, AddCardDialog, ShareDialog, FilterBar, FilterConfigPanel, FilterDefinitionForm 等
│   │   │   │   │   └── filters/ # CategoryFilter, DateRangeFilter
│   │   │   │   ├── dataset/     # S3ImportForm
│   │   │   │   └── group/       # GroupCreateDialog, GroupDetailPanel, GroupListPage, MemberAddDialog
│   │   │   ├── hooks/       # use-auth, use-cards, use-dashboards, use-datasets, use-filter-views, use-dashboard-shares, use-groups
│   │   │   ├── lib/         # api-client, utils, layout-utils, api/*.test.ts (auth, cards, dashboards, datasets, filter-views)
│   │   │   ├── pages/       # 全9ページのテスト
│   │   │   ├── stores/      # auth-store
│   │   │   ├── types/       # type-guards
│   │   │   └── helpers/     # test-utils (共通テストユーティリティ)
│   │   ├── components/  # UIコンポーネント
│   │   │   ├── card/    # カード関連 (CardEditor, CardPreview)
│   │   │   ├── common/  # 共通 (Header, Sidebar, Layout, AuthGuard, ErrorBoundary)
│   │   │   ├── dashboard/ # ダッシュボード関連 (DashboardViewer, DashboardEditor, ShareDialog, FilterBar, FilterConfigPanel, FilterDefinitionForm)
│   │   │   │   └── filters/ # フィルタUI (CategoryFilter, DateRangeFilter)
│   │   │   ├── dataset/ # データセット関連 (S3ImportForm)
│   │   │   ├── group/   # グループ管理 (GroupCreateDialog, GroupDetailPanel, MemberAddDialog)
│   │   │   └── ui/      # shadcn/ui プリミティブ (button, input, label, dialog, calendar, checkbox, popover, select 等)
│   │   ├── hooks/       # React Query カスタムフック (7ファイル)
│   │   ├── lib/         # APIクライアント、ユーティリティ、layout-utils
│   │   │   └── api/     # APIモジュール (auth, cards, dashboards, datasets, filter-views, dashboard-shares, groups)
│   │   ├── pages/       # ページコンポーネント (10ページ)
│   │   ├── stores/      # Zustand ストア (auth-store)
│   │   ├── types/       # TypeScript型定義 (api, card, dashboard, dataset, filter-view, group, user)
│   │   ├── routes.tsx   # React Router ルート定義
│   │   └── App.tsx      # アプリケーションルート
│   ├── e2e/             # Playwright E2Eテスト (auth, dataset, card-dashboard, sharing)
│   ├── package.json     # Node.js依存パッケージ
│   └── vite.config.ts   # Vite設定 (パスエイリアス @/ = src/)
├── executor/            # Pythonコード実行サンドボックス (FastAPI)
│   ├── app/
│   │   ├── main.py      # Executorエントリポイント
│   │   ├── runner.py    # CardRunner 実行エンジン
│   │   ├── sandbox.py   # SecureExecutor (安全なコード実行)
│   │   ├── resource_limiter.py  # CPU/メモリ制限
│   │   ├── api_models.py # リクエスト/レスポンスモデル
│   │   └── models.py    # HTMLResult データモデル
│   ├── tests/           # pytest テスト
│   ├── requirements.txt # Python依存パッケージ
│   └── Dockerfile       # 本番兼用Dockerfile (非rootユーザ)
├── scripts/             # 運用スクリプト
│   ├── init_tables.py   # DynamoDB テーブル初期化
│   └── Dockerfile.init  # 初期化コンテナ用Dockerfile
├── codemaps/            # アーキテクチャマップ
│   ├── architecture.md  # システム全体のアーキテクチャ
│   ├── backend.md       # バックエンド構造マップ
│   ├── frontend.md      # フロントエンド構造マップ
│   └── data.md          # データモデルマップ
├── docs/                # プロジェクトドキュメント
│   ├── requirements.md  # 要件定義書 v0.2
│   ├── design.md        # 設計書 v0.2
│   ├── tech-spec.md     # 技術仕様書 v0.1
│   ├── api-spec.md      # API仕様書 v0.1
│   ├── data-flow.md     # データフロー定義 v0.1
│   ├── security.md      # セキュリティ実装ガイド v0.1
│   ├── deployment.md    # デプロイメントガイド v0.1
│   ├── CONTRIB.md       # 開発者ガイド (本ドキュメント)
│   └── RUNBOOK.md       # 運用ランブック
├── .reports/            # テストカバレッジレポート
├── docker-compose.yml   # ローカル開発環境定義
├── .env.example         # 環境変数テンプレート
└── .gitignore           # Git除外設定
```

---

## 3. 環境セットアップ

### 3.1 Docker Compose によるフルスタック起動 (推奨)

```bash
# 1. リポジトリをクローン
git clone <repository-url>
cd work_BI_ClaudeCode

# 2. 環境変数ファイルを作成
cp .env.example .env
# .env を編集して必要な値を設定 (特にJWT_SECRET_KEY)

# 3. 全サービスをビルド・起動
docker compose up --build

# バックグラウンドで起動する場合
docker compose up --build -d
```

起動後にアクセス可能なサービス:

| サービス | URL | 説明 |
|---------|-----|------|
| フロントエンド | http://localhost:3000 | React SPA |
| APIサーバ | http://localhost:8000 | FastAPI (Swagger UI: /docs) |
| Executor | http://localhost:8080 | Python実行基盤 |
| DynamoDB Local | http://localhost:8001 | DynamoDB互換ローカルDB |
| MinIO Console | http://localhost:9001 | S3互換ストレージ管理画面 |
| MinIO API | http://localhost:9000 | S3互換API |

初回起動時は `dynamodb-init` と `minio-init` コンテナが自動的にテーブルとバケットを作成します。

### 3.2 バックエンド単体での開発

```bash
cd backend

# 仮想環境を作成
python3.11 -m venv .venv
source .venv/bin/activate

# 依存パッケージをインストール
pip install -r requirements.txt

# 開発サーバを起動 (ホットリロード有効)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

注意: バックエンド単体で起動する場合、DynamoDB Local と MinIO を別途起動する必要があります。

### 3.3 フロントエンド単体での開発

```bash
cd frontend

# 依存パッケージをインストール
npm ci

# 開発サーバを起動 (ホットリロード有効)
npm run dev
```

### 3.4 Executor 単体での開発

```bash
cd executor

# 仮想環境を作成
python3.11 -m venv venv
source venv/bin/activate

# 依存パッケージをインストール
pip install -r requirements.txt

# 開発サーバを起動
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

---

## 4. 環境変数リファレンス

`.env.example` に定義されている全環境変数の説明。

### 基本設定

| 変数名 | デフォルト値 | 説明 |
|--------|-------------|------|
| `ENV` | `local` | 実行環境 (`local` / `staging` / `production`) |
| `API_HOST` | `0.0.0.0` | APIサーバのバインドアドレス |
| `API_PORT` | `8000` | APIサーバのポート |
| `API_WORKERS` | `4` | Uvicorn ワーカー数 |
| `API_DEBUG` | `false` | デバッグモード |

### 認証 (JWT)

| 変数名 | デフォルト値 | 説明 |
|--------|-------------|------|
| `JWT_SECRET_KEY` | (テンプレート値) | JWT署名キー。本番環境では必ず変更すること (最低32文字) |
| `JWT_ALGORITHM` | `HS256` | JWT署名アルゴリズム |
| `JWT_EXPIRE_MINUTES` | `1440` | JWTトークン有効期限 (分。デフォルト24時間) |

### パスワードポリシー

| 変数名 | デフォルト値 | 説明 |
|--------|-------------|------|
| `PASSWORD_MIN_LENGTH` | `8` | パスワード最小文字数 |

### DynamoDB

| 変数名 | デフォルト値 | 説明 |
|--------|-------------|------|
| `DYNAMODB_ENDPOINT` | `http://dynamodb-local:8000` | DynamoDBエンドポイント。本番ではAWSデフォルトを使用するため空にする |
| `DYNAMODB_REGION` | `ap-northeast-1` | AWSリージョン |
| `DYNAMODB_TABLE_PREFIX` | `bi_` | テーブル名プレフィックス |

### S3 / MinIO

| 変数名 | デフォルト値 | 説明 |
|--------|-------------|------|
| `S3_ENDPOINT` | `http://minio:9000` | S3エンドポイント。本番ではAWSデフォルトを使用するため空にする |
| `S3_REGION` | `ap-northeast-1` | AWSリージョン |
| `S3_BUCKET_DATASETS` | `bi-datasets` | データセット格納バケット (Parquetファイル) |
| `S3_BUCKET_STATIC` | `bi-static` | 静的アセット格納バケット |
| `S3_ACCESS_KEY` | `minioadmin` | S3アクセスキー (ローカル開発用。本番ではIAMロールを使用) |
| `S3_SECRET_KEY` | `minioadmin` | S3シークレットキー (ローカル開発用) |

### Vertex AI

| 変数名 | デフォルト値 | 説明 |
|--------|-------------|------|
| `VERTEX_AI_PROJECT_ID` | (未設定) | GCPプロジェクトID |
| `VERTEX_AI_LOCATION` | `asia-northeast1` | GCPリージョン |
| `VERTEX_AI_MODEL` | `gemini-1.5-pro` | 使用するLLMモデル |

### Executor (Python実行基盤)

| 変数名 | デフォルト値 | 説明 |
|--------|-------------|------|
| `EXECUTOR_ENDPOINT` | `http://executor:8080` | Executorサービスのエンドポイント |
| `EXECUTOR_TIMEOUT_CARD` | `10` | カード実行タイムアウト (秒) |
| `EXECUTOR_TIMEOUT_TRANSFORM` | `300` | Transform実行タイムアウト (秒。デフォルト5分) |
| `EXECUTOR_MAX_CONCURRENT_CARDS` | `10` | カード同時実行上限 |
| `EXECUTOR_MAX_CONCURRENT_TRANSFORMS` | `5` | Transform同時実行上限 |

### ロギング

| 変数名 | デフォルト値 | 説明 |
|--------|-------------|------|
| `LOG_LEVEL` | `INFO` | ログレベル (`DEBUG` / `INFO` / `WARNING` / `ERROR`) |
| `LOG_FORMAT` | `json` | ログフォーマット (`json` / `console`) |

---

## 5. スクリプトリファレンス

### 5.1 フロントエンド (npm scripts)

`frontend/package.json` に定義されたスクリプト。

| コマンド | 実行内容 | 説明 |
|---------|---------|------|
| `npm run dev` | `vite` | 開発サーバを起動 (ホットリロード有効、ポート3000) |
| `npm run build` | `tsc && vite build` | TypeScript型チェック後にプロダクションビルドを生成 |
| `npm run preview` | `vite preview` | ビルド済みアプリケーションのプレビューサーバを起動 |
| `npm run test` | `vitest` | Vitest でテストを実行 (ウォッチモード) |
| `npm run test:coverage` | `vitest --coverage` | カバレッジ付きでテストを実行 (@vitest/coverage-v8) |
| `npm run lint` | `eslint . --ext ts,tsx` | ESLint による静的解析 (TypeScript/TSX対象) |
| `npm run typecheck` | `tsc --noEmit` | TypeScript型チェックのみ実行 (ビルドなし) |
| `npm run e2e` | `playwright test` | Playwright E2Eテストを実行 (ヘッドレスモード) |
| `npm run e2e:ui` | `playwright test --ui` | Playwright UIモードでE2Eテストを実行 |
| `npm run e2e:headed` | `playwright test --headed` | ブラウザを表示してE2Eテストを実行 (デバッグ用) |
| `npm run e2e:report` | `playwright show-report` | 最後に実行したE2EテストのHTMLレポートを表示 |

### 5.2 バックエンド (Python)

`backend/` ディレクトリで実行するコマンド。

| コマンド | 説明 |
|---------|------|
| `pytest` | テストを実行 |
| `pytest --cov=app` | カバレッジ付きでテストを実行 |
| `pytest --cov=app --cov-report=html` | HTML形式のカバレッジレポートを生成 (`htmlcov/`) |
| `pytest --cov=app --cov-report=term-missing` | 未カバー行付きでカバレッジ表示 |
| `ruff check app/ tests/` | Ruff によるリンティング (line-length: 100) |
| `ruff format app/ tests/` | Ruff によるコードフォーマット |
| `mypy app/` | 型チェック (strict モード) |
| `uvicorn app.main:app --reload` | 開発サーバ起動 (ホットリロード有効) |

### 5.3 Executor (Python)

`executor/` ディレクトリで実行するコマンド。

| コマンド | 説明 |
|---------|------|
| `pytest` | テストを実行 |
| `pytest --cov=app` | カバレッジ付きでテストを実行 |
| `uvicorn app.main:app --host 0.0.0.0 --port 8080` | 開発サーバ起動 |

### 5.4 Docker Compose

プロジェクトルートで実行するコマンド。

| コマンド | 説明 |
|---------|------|
| `docker compose up --build` | 全サービスをビルドして起動 |
| `docker compose up --build -d` | バックグラウンドで起動 |
| `docker compose down` | 全サービスを停止 |
| `docker compose down -v` | 全サービスを停止しボリュームも削除 (データリセット) |
| `docker compose logs -f api` | APIサーバのログをフォロー |
| `docker compose logs -f executor` | Executorのログをフォロー |
| `docker compose restart api` | APIサーバのみ再起動 |

### 5.5 初期化スクリプト

| スクリプト | 説明 |
|-----------|------|
| `scripts/init_tables.py` | DynamoDB テーブル作成 (10テーブル: bi_users, bi_groups, bi_group_members, bi_datasets, bi_transforms, bi_cards, bi_dashboards, bi_dashboard_shares, bi_filter_views, bi_audit_logs) |
| `scripts/seed_test_user.py` | E2Eテスト用ユーザ作成 (e2e@example.com / Test@1234) - DynamoDB Localに直接挿入 |

---

## 6. テスト手順

### 6.1 フロントエンドテスト

現在のテスト状況 (FR-7 Dashboard Sharing / Group Management 実装時点):

| メトリクス | 値 |
|-----------|-----|
| テストファイル数 | 53 |
| テストケース数 | 340+ |
| Statements カバレッジ | 83.07% |
| テストフレームワーク | Vitest 1.x + @testing-library/react 14.x |
| テスト環境 | jsdom |

```bash
cd frontend

# ウォッチモードでテスト実行
npm run test

# カバレッジ付き (単発実行)
npm run test:coverage

# 特定ファイルのみ
npx vitest src/__tests__/stores/auth-store.test.ts

# 特定ディレクトリ配下のみ
npx vitest src/__tests__/pages/

# UIモードで実行 (@vitest/ui)
npx vitest --ui
```

テスト構成 (53ファイル):

| テストカテゴリ | ファイル数 | 対象 |
|---------------|-----------|------|
| `__tests__/pages/` | 9 | LoginPage, DashboardListPage, DashboardViewPage (+ FilterView統合), DashboardEditPage, DatasetListPage, DatasetDetailPage, DatasetImportPage, CardListPage, CardEditPage |
| `__tests__/components/common/` | 8 | AuthGuard, ErrorBoundary, ConfirmDialog, Header, Sidebar, Layout, LoadingSpinner, Pagination |
| `__tests__/components/dashboard/` | 9 | DashboardViewer, DashboardEditor, AddCardDialog, CardContainer, ShareDialog, FilterBar, FilterConfigPanel, FilterDefinitionForm, FilterViewSelector (+ 可視性ルール) |
| `__tests__/components/dashboard/filters/` | 2 | CategoryFilter, DateRangeFilter |
| `__tests__/components/dataset/` | 1 | S3ImportForm |
| `__tests__/components/card/` | 2 | CardEditor, CardPreview |
| `__tests__/components/group/` | 4 | GroupCreateDialog, GroupDetailPanel, GroupListPage, MemberAddDialog |
| `__tests__/hooks/` | 7 | use-auth, use-cards, use-dashboards, use-datasets, use-filter-views (+ getDefaultFilterView), use-dashboard-shares, use-groups |
| `__tests__/lib/api/` | 5 | auth, cards, dashboards, datasets, filter-views |
| `__tests__/lib/` | 3 | api-client, utils, layout-utils |
| `__tests__/stores/` | 1 | auth-store |
| `__tests__/types/` | 1 | type-guards |
| `__tests__/` | 1 | App.test.tsx |

テストヘルパー:
- `__tests__/helpers/test-utils.tsx` -- カスタムレンダラー (QueryClient, MemoryRouter 統合)
- `__tests__/setup.ts` -- グローバルセットアップ (@testing-library/jest-dom マッチャー)
- `__tests__/vitest.d.ts` -- 型拡張

### 6.2 バックエンドテスト

```bash
cd backend
source .venv/bin/activate

# 全テスト実行
pytest

# カバレッジ付き
pytest --cov=app --cov-report=term-missing

# 特定モジュールのみ
pytest tests/api/routes/test_auth.py
pytest tests/services/test_dataset_service.py

# 詳細出力
pytest -v
```

テスト構成:

| テストディレクトリ | 対象 |
|-------------------|------|
| `tests/api/routes/` | APIエンドポイント (test_auth, test_cards, test_dashboards, test_datasets, test_filter_views, test_s3_import, test_dashboard_shares, test_groups, test_users) |
| `tests/api/` | ヘルスチェック (test_health), 依存性注入 (test_deps) |
| `tests/core/` | 設定、ロギング、パスワードポリシー、セキュリティ |
| `tests/db/` | DynamoDB / S3 クライアント |
| `tests/integration/` | 権限統合テスト (test_permission_integration) |
| `tests/models/` | Pydantic モデル (user, dataset, card, dashboard, filter_view, group, dashboard_share, common, s3_import) |
| `tests/repositories/` | リポジトリ層 (base, user, dataset, card, dashboard, filter_view, group, group_member, dashboard_share) |
| `tests/services/` | サービス層 (CSV解析、データセット、カード実行、ダッシュボード、パーミッション等) |

テストは `moto` (AWS サービスモック) と `respx` (HTTP モック) を使用しています。

### 6.3 Executor テスト

```bash
cd executor
source venv/bin/activate

# 全テスト実行
pytest

# カバレッジ付き
pytest --cov=app
```

テスト構成:

| テストファイル | 対象 |
|---------------|------|
| `tests/test_execute_api.py` | 実行APIエンドポイント |
| `tests/test_health.py` | ヘルスチェック |
| `tests/test_runner.py` | CardRunner 実行エンジン |
| `tests/test_sandbox.py` | SecureExecutor サンドボックス |
| `tests/test_resource_limiter.py` | リソース制限 |

### 6.4 E2Eテスト (Playwright)

前提条件:
- Docker Compose で全サービスが起動していること
- テストユーザがDynamoDB Localに登録されていること

```bash
# 1. Docker Compose で全サービスを起動
docker-compose up -d --build

# 2. テストユーザをSeed
python scripts/seed_test_user.py

# 3. E2Eテストを実行
cd frontend
npm run e2e

# UIモードで実行 (テストを視覚的に確認)
npm run e2e:ui

# ブラウザを表示して実行 (デバッグ用)
npm run e2e:headed

# テストレポートを表示
npm run e2e:report
```

E2Eテスト構成:

| テストスイート | テストケース | 対象 |
|---------------|------------|------|
| `e2e/auth.spec.ts` | 5 | ログイン/ログアウト、未認証リダイレクト、バリデーション、認証失敗 |
| `e2e/dataset.spec.ts` | 3 | CSVインポート、一覧表示・削除、プレビュー |
| `e2e/card-dashboard.spec.ts` | 5 | Card作成、Dashboard作成・閲覧、削除 |
| `e2e/sharing.spec.ts` | - | ダッシュボード共有、グループ管理 |

テストユーザ情報:
- Email: `e2e@example.com`
- Password: `Test@1234`
- User ID: `e2e-test-user-001`

注意事項:
- E2Eテストは`workers: 1`でシングルワーカー実行 (DynamoDB Localの共有のため)
- テストはグローバルセットアップでAPIヘルスチェックを実行してから開始
- 各テストはクリーンアップ処理で作成したデータを自動削除

### 6.5 CI統合テスト実行

全コンポーネントのテストを一括で実行するフロー:

```bash
# 1. バックエンド
cd backend && source .venv/bin/activate && pytest --cov=app && cd ..

# 2. フロントエンド
cd frontend && npm run test:coverage && cd ..

# 3. Executor
cd executor && source venv/bin/activate && pytest --cov=app && cd ..
```

カバレッジレポートは以下に出力されます:
- バックエンド: `backend/htmlcov/` (HTML) / ターミナル出力
- フロントエンド: `frontend/coverage/` (lcov)
- プロジェクト全体レポート: `.reports/`

---

## 7. アーキテクチャ概要

### 7.1 システム構成

```
  ブラウザ
    |
    v
  [Frontend - React SPA] :3000
    |
    v
  [Backend API - FastAPI] :8000
    |         |         |
    v         v         v
 [DynamoDB] [S3/MinIO] [Executor] :8080
                         |
                   Python サンドボックス
                   (pandas, plotly, matplotlib)
```

### 7.2 主要依存パッケージ

フロントエンド (frontend/package.json):

| パッケージ | バージョン | 用途 |
|-----------|-----------|------|
| react | ^18.2.0 | UIフレームワーク |
| react-router-dom | ^6.21.0 | ルーティング |
| @tanstack/react-query | ^5.17.0 | サーバ状態管理 |
| zustand | ^4.4.7 | クライアント状態管理 |
| react-hook-form | ^7.71.1 | フォーム管理 |
| zod | ^3.25.76 | バリデーション |
| react-grid-layout | ^1.4.4 | ダッシュボードグリッドレイアウト |
| @monaco-editor/react | ^4.6.0 | Pythonコードエディタ |
| ky | ^1.1.3 | HTTPクライアント |
| @radix-ui/react-checkbox | ^1.3.3 | チェックボックスUI |
| @radix-ui/react-popover | ^1.1.15 | ポップオーバーUI |
| @radix-ui/react-select | ^2.2.6 | セレクトドロップダウン |
| date-fns | ^4.1.0 | 日付フォーマット/パース |
| react-day-picker | ^9.13.0 | カレンダーUI |
| tailwind-merge | ^3.4.0 | Tailwind CSSクラスマージ |

フロントエンド devDependencies:

| パッケージ | バージョン | 用途 |
|-----------|-----------|------|
| vitest | ^1.1.0 | テストランナー |
| @vitest/coverage-v8 | ^1.1.0 | カバレッジ計測 |
| @vitest/ui | ^1.1.0 | テストUI |
| @playwright/test | ^1.58.1 | E2Eテストフレームワーク |
| @testing-library/react | ^14.1.2 | コンポーネントテスト |
| @testing-library/jest-dom | ^6.1.5 | DOMマッチャー |
| @testing-library/user-event | ^14.5.1 | ユーザインタラクションシミュレーション |
| @types/react-grid-layout | ^1.3.6 | react-grid-layout型定義 |
| typescript | ^5.3.3 | 型システム |
| vite | ^5.0.10 | ビルドツール |
| tailwindcss | ^3.4.0 | CSSフレームワーク |
| eslint | ^8.56.0 | リンター |

バックエンド (backend/requirements.txt):

| パッケージ | バージョン | 用途 |
|-----------|-----------|------|
| fastapi | 0.109.0 | Webフレームワーク |
| uvicorn | 0.27.0 | ASGIサーバ |
| pydantic | 2.5.0 | バリデーション/モデル |
| pydantic-settings | 2.1.0 | 環境変数管理 |
| structlog | 24.1.0 | 構造化ログ |
| aioboto3 | 12.3.0 | 非同期AWS SDK (DynamoDB / S3) |
| pyarrow | 15.0.0 | Parquet読み書き |
| pandas | 2.2.0 | データ操作 |
| chardet | 5.2.0 | 文字コード推定 |
| python-jose | 3.3.0 | JWT実装 |
| bcrypt | 4.1.3 | パスワードハッシュ |
| slowapi | 0.1.9 | レート制限 |
| pytest | 7.4.3 | テストフレームワーク |
| moto | 5.0.0 | AWSサービスモック |

### 7.3 APIルート一覧

すべてのAPIルートは `/api` プレフィックス配下。

| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/api/health` | ヘルスチェック |
| POST | `/api/auth/login` | ログイン (JWT発行、5回/分のレート制限) |
| POST | `/api/auth/logout` | ログアウト |
| GET | `/api/auth/me` | 現在のユーザ情報取得 |
| GET | `/api/datasets` | データセット一覧 |
| POST | `/api/datasets` | CSV取り込みによるデータセット作成 |
| GET | `/api/datasets/{id}` | データセット詳細取得 |
| PUT | `/api/datasets/{id}` | データセット更新 |
| DELETE | `/api/datasets/{id}` | データセット削除 |
| GET | `/api/datasets/{id}/preview` | データセットプレビュー (最大1000行) |
| GET | `/api/datasets/{id}/columns/{column_name}/values` | カラムのユニーク値取得 (フィルタ用) |
| GET | `/api/cards` | カード一覧 |
| POST | `/api/cards` | カード作成 |
| GET | `/api/cards/{id}` | カード詳細取得 |
| PUT | `/api/cards/{id}` | カード更新 |
| DELETE | `/api/cards/{id}` | カード削除 |
| POST | `/api/cards/{id}/preview` | カードプレビュー実行 (キャッシュなし) |
| POST | `/api/cards/{id}/execute` | カード実行 (キャッシュあり) |
| GET | `/api/dashboards` | ダッシュボード一覧 |
| POST | `/api/dashboards` | ダッシュボード作成 |
| GET | `/api/dashboards/{id}` | ダッシュボード詳細取得 |
| PUT | `/api/dashboards/{id}` | ダッシュボード更新 |
| DELETE | `/api/dashboards/{id}` | ダッシュボード削除 |
| POST | `/api/dashboards/{id}/clone` | ダッシュボードをクローン (名前に「(Copy)」を付加) |
| GET | `/api/dashboards/{id}/referenced-datasets` | 参照データセット一覧 |
| POST | `/api/datasets/s3-import` | S3からCSVを取り込みデータセット作成 |
| GET | `/api/dashboards/{id}/filter-views` | フィルタビュー一覧取得 |
| POST | `/api/dashboards/{id}/filter-views` | フィルタビュー作成 |
| GET | `/api/filter-views/{id}` | フィルタビュー詳細取得 |
| PUT | `/api/filter-views/{id}` | フィルタビュー更新 |
| DELETE | `/api/filter-views/{id}` | フィルタビュー削除 |
| GET | `/api/users` | ユーザー検索 (メール部分一致) |
| GET | `/api/groups` | グループ一覧 (管理者のみ) |
| POST | `/api/groups` | グループ作成 (管理者のみ) |
| GET | `/api/groups/{groupId}` | グループ詳細取得 (メンバー情報含む) |
| PUT | `/api/groups/{groupId}` | グループ更新 (管理者のみ) |
| DELETE | `/api/groups/{groupId}` | グループ削除 (管理者のみ) |
| POST | `/api/groups/{groupId}/members` | グループメンバー追加 (管理者のみ) |
| DELETE | `/api/groups/{groupId}/members/{userId}` | グループメンバー削除 (管理者のみ) |
| GET | `/api/dashboards/{id}/shares` | ダッシュボード共有一覧 (オーナーのみ) |
| POST | `/api/dashboards/{id}/shares` | ダッシュボード共有追加 (オーナーのみ) |
| PUT | `/api/dashboards/{id}/shares/{shareId}` | ダッシュボード共有権限更新 (オーナーのみ) |
| DELETE | `/api/dashboards/{id}/shares/{shareId}` | ダッシュボード共有削除 (オーナーのみ) |

### 7.4 フロントエンドルート一覧

| パス | コンポーネント | 説明 |
|------|---------------|------|
| `/login` | LoginPage | ログイン画面 |
| `/` | (リダイレクト) | `/dashboards` にリダイレクト |
| `/dashboards` | DashboardListPage | ダッシュボード一覧 |
| `/dashboards/:id` | DashboardViewPage | ダッシュボード閲覧 |
| `/dashboards/:id/edit` | DashboardEditPage | ダッシュボード編集 |
| `/datasets` | DatasetListPage | データセット一覧 |
| `/datasets/import` | DatasetImportPage | データセット取り込み |
| `/datasets/:id` | DatasetDetailPage | データセット詳細 |
| `/cards` | CardListPage | カード一覧 |
| `/cards/:id` | CardEditPage | カード編集 |
| `/admin/groups` | GroupListPage | グループ管理 (管理者のみ) |

認証が必要なルートは `AuthGuard` コンポーネントで保護されています。

### 7.5 DynamoDB テーブル構成

| テーブル名 | キー | GSI |
|-----------|------|-----|
| `bi_users` | PK: `userId` (S) | `UsersByEmail` (email -> ALL) |
| `bi_groups` | PK: `groupId` (S) | `GroupsByName` (name -> ALL) |
| `bi_group_members` | PK: `groupId` (S), SK: `userId` (S) | `MembersByUser` (userId -> ALL) |
| `bi_datasets` | PK: `datasetId` (S) | `DatasetsByOwner` (ownerId + createdAt) |
| `bi_transforms` | PK: `transformId` (S) | `TransformsByOwner` (ownerId + createdAt) |
| `bi_cards` | PK: `cardId` (S) | `CardsByOwner` (ownerId + createdAt) |
| `bi_dashboards` | PK: `dashboardId` (S) | `DashboardsByOwner` (ownerId + createdAt) |
| `bi_dashboard_shares` | PK: `shareId` (S) | `SharesByDashboard` (dashboardId + createdAt), `SharesByTarget` (sharedToId -> ALL) |
| `bi_filter_views` | PK: `filterViewId` (S) | `FilterViewsByDashboard` (dashboardId + createdAt) |
| `bi_audit_logs` | PK: `logId` (S) | `LogsByTimestamp`, `LogsByTarget` |

### 7.6 Executor サンドボックス

カードの Python コードは Executor サービス内のサンドボックスで実行されます。

利用可能なライブラリ:
- `pandas` (as `pd`)
- `numpy` (as `np`)
- `plotly.express` (as `px`)
- `plotly.graph_objects` (as `go`)
- `matplotlib.pyplot` (as `plt`)
- `seaborn` (as `sns`)

ブロックされている操作:
- ファイルI/O (`open`, `os`, `pathlib` 等)
- ネットワークアクセス (`socket`, `http`, `urllib`, `requests` 等)
- プロセス操作 (`subprocess`, `multiprocessing` 等)
- `exec`, `eval`, `compile` の直接呼び出し
- `pickle`, `marshal` によるシリアライゼーション

リソース制限:
- タイムアウト: 10秒 (SIGALRM)
- メモリ: 2048MB (Linux環境のみ RLIMIT_AS で制限)

---

## 8. コーディング規約

### 8.1 バックエンド (Python)

- フォーマッタ/リンタ: Ruff (line-length: 100, target: Python 3.11)
- 型チェック: mypy (strict モード、一部overrideあり: slowapi, pyarrow, aioboto3, botocore)
- テストフレームワーク: pytest (asyncio_mode: auto)
- ドキュメント: Google style docstring
- 命名規則: snake_case (変数/関数)、PascalCase (クラス)

### 8.2 フロントエンド (TypeScript)

- フォーマッタ/リンタ: ESLint + TypeScript ESLint (@typescript-eslint/eslint-plugin 6.x)
- テストフレームワーク: Vitest + Testing Library (@testing-library/react, @testing-library/user-event)
- UIライブラリ: shadcn/ui (Radix UI + Tailwind CSS)
- 状態管理: TanStack Query (サーバ状態) + Zustand (クライアント状態)
- 命名規則: camelCase (変数/関数)、PascalCase (コンポーネント/型)
- パスエイリアス: `@/` = `src/` (vite.config.ts で設定)

---

## 9. Git ワークフロー

### 9.1 ブランチ戦略

```
master (本番)
  └── feature/xxx  (機能開発)
  └── fix/xxx      (バグ修正)
  └── docs/xxx     (ドキュメント)
  └── test/xxx     (テスト追加)
```

### 9.2 コミットメッセージ

```
<type>: <summary>

<body (optional)>

Co-Authored-By: <author> (optional)
```

type の例: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

### 9.3 プルリクエスト

1. 機能ブランチを作成
2. 変更を実装しテストを追加
3. リンタ/型チェック/テストが通ることを確認
4. プルリクエストを作成

### 9.4 CI品質ゲート

PRマージ前に以下が通ることを確認:

| チェック | コマンド | 基準 |
|---------|---------|------|
| フロントエンド lint | `npm run lint` | エラー 0 |
| フロントエンド typecheck | `npm run typecheck` | エラー 0 |
| フロントエンド test | `npm run test:coverage` | 83%+ statements |
| バックエンド lint | `ruff check app/` | エラー 0 |
| バックエンド typecheck | `mypy app/` | エラー 0 |
| バックエンド test | `pytest --cov=app` | pass |

---

## 10. トラブルシューティング (開発環境)

### DynamoDB Local に接続できない

```bash
# DynamoDB Local の状態を確認
docker compose logs dynamodb-local

# テーブルが作成されているか確認
docker compose logs dynamodb-init
```

### MinIO に接続できない

```bash
# MinIO の状態を確認
docker compose logs minio

# バケットが作成されているか確認
docker compose logs minio-init

# MinIO Console で確認
# http://localhost:9001 (minioadmin / minioadmin)
```

### フロントエンドの型エラー

```bash
cd frontend
npm run typecheck
```

### バックエンドの型エラー

```bash
cd backend
mypy app/
```

### フロントエンドテストの失敗

```bash
cd frontend

# 単一テストファイルを詳細モードで実行
npx vitest src/__tests__/pages/LoginPage.test.tsx --reporter=verbose

# UIモードでデバッグ
npx vitest --ui
```

### ポートが競合する

docker-compose.yml で使用するポート:

| ポート | サービス |
|--------|---------|
| 3000 | フロントエンド (Vite) |
| 8000 | APIサーバ (FastAPI) |
| 8001 | DynamoDB Local |
| 8080 | Executor |
| 9000 | MinIO API |
| 9001 | MinIO Console |

他のプロセスがこれらのポートを使用していないか確認してください。

```bash
lsof -i :3000
lsof -i :8000
```

---

## 11. 関連ドキュメント

| ドキュメント | パス | 内容 |
|-------------|------|------|
| 要件定義書 | `docs/requirements.md` | 機能要件、非機能要件、権限モデル |
| 設計書 | `docs/design.md` | アーキテクチャ、データモデル、API設計 |
| 技術仕様書 | `docs/tech-spec.md` | 技術スタック、設定値、テスト戦略 |
| API仕様書 | `docs/api-spec.md` | 全APIエンドポイントの詳細仕様 |
| データフロー | `docs/data-flow.md` | CSV取り込み、Transform実行、カード実行フロー |
| セキュリティ | `docs/security.md` | サンドボックス、CSP、認証・認可 |
| デプロイメント | `docs/deployment.md` | AWS構成、CI/CD、Terraform |
| 運用ランブック | `docs/RUNBOOK.md` | デプロイ、監視、トラブルシューティング |
| アーキテクチャマップ | `codemaps/architecture.md` | システム全体構造の可視化 |
| フロントエンドマップ | `codemaps/frontend.md` | フロントエンド構造の可視化 |
| バックエンドマップ | `codemaps/backend.md` | バックエンド構造の可視化 |
| データモデルマップ | `codemaps/data.md` | DynamoDB/S3データ構造の可視化 |
