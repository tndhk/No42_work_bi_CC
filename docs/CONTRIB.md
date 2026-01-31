# 開発者ガイド (CONTRIB)

**最終更新:** 2026-01-31
**プロジェクト:** 社内BI・Pythonカード MVP

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
│   │   ├── api/         # APIルート定義 (auth, datasets, cards, dashboards)
│   │   ├── core/        # 設定、セキュリティ、ロギング
│   │   ├── db/          # DynamoDB / S3 クライアント
│   │   ├── models/      # Pydantic モデル
│   │   ├── repositories/# データアクセス層 (DynamoDB CRUD)
│   │   ├── services/    # ビジネスロジック層
│   │   └── main.py      # アプリケーションエントリポイント
│   ├── tests/           # pytest テスト
│   ├── pyproject.toml   # プロジェクト設定
│   ├── requirements.txt # Python依存パッケージ
│   └── Dockerfile.dev   # 開発用Dockerfile
├── frontend/            # React SPA (TypeScript / Vite)
│   ├── src/
│   │   ├── components/  # UIコンポーネント
│   │   │   ├── card/    # カード関連 (CardEditor, CardPreview)
│   │   │   ├── common/  # 共通 (Header, Sidebar, Layout, AuthGuard)
│   │   │   ├── dashboard/ # ダッシュボード関連
│   │   │   ├── dataset/ # データセット関連
│   │   │   └── ui/      # shadcn/ui プリミティブ
│   │   ├── hooks/       # React Query カスタムフック
│   │   ├── lib/         # APIクライアント、ユーティリティ
│   │   ├── pages/       # ページコンポーネント
│   │   ├── stores/      # Zustand ストア (auth-store)
│   │   ├── types/       # TypeScript型定義
│   │   ├── routes.tsx   # React Router ルート定義
│   │   └── App.tsx      # アプリケーションルート
│   ├── package.json     # Node.js依存パッケージ
│   └── Dockerfile.dev   # 開発用Dockerfile
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
├── docs/                # プロジェクトドキュメント
│   ├── requirements.md  # 要件定義書
│   ├── design.md        # 設計書
│   ├── tech-spec.md     # 技術仕様書
│   ├── api-spec.md      # API仕様書
│   ├── data-flow.md     # データフロー定義
│   ├── security.md      # セキュリティ実装ガイド
│   ├── deployment.md    # デプロイメントガイド
│   ├── CONTRIB.md       # 開発者ガイド (本ドキュメント)
│   └── RUNBOOK.md       # 運用ランブック
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
| `JWT_SECRET_KEY` | (テンプレート値) | JWT署名キー。**本番環境では必ず変更すること** (最低32文字) |
| `JWT_ALGORITHM` | `HS256` | JWT署名アルゴリズム |
| `JWT_EXPIRE_MINUTES` | `1440` | JWTトークン有効期限 (分) |

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
| `EXECUTOR_TIMEOUT_TRANSFORM` | `300` | Transform実行タイムアウト (秒) |
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

| コマンド | 説明 |
|---------|------|
| `npm run dev` | 開発サーバを起動 (Vite、ホットリロード有効、ポート3000) |
| `npm run build` | TypeScript型チェック後にプロダクションビルドを生成 |
| `npm run preview` | ビルド済みアプリケーションのプレビューサーバを起動 |
| `npm run test` | Vitest でテストを実行 (ウォッチモード) |
| `npm run test:coverage` | カバレッジ付きでテストを実行 |
| `npm run lint` | ESLint による静的解析 (TypeScript/TSX対象) |
| `npm run typecheck` | TypeScript型チェックのみ実行 (ビルドなし) |

### 5.2 バックエンド (Python)

`backend/` ディレクトリで実行するコマンド。

| コマンド | 説明 |
|---------|------|
| `pytest` | テストを実行 |
| `pytest --cov=app` | カバレッジ付きでテストを実行 |
| `pytest --cov=app --cov-report=html` | HTML形式のカバレッジレポートを生成 |
| `ruff check app/ tests/` | Ruff によるリンティング |
| `ruff format app/ tests/` | Ruff によるコードフォーマット |
| `mypy app/` | 型チェック |
| `uvicorn app.main:app --reload` | 開発サーバ起動 |

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
| `scripts/init_tables.py` | DynamoDB テーブル作成 (bi_users, bi_datasets, bi_cards, bi_dashboards) |

---

## 6. テスト手順

### 6.1 バックエンドテスト

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

# 並列実行 (pytest-xdist が必要)
pytest -n auto
```

テスト構成:

| テストディレクトリ | 対象 |
|-------------------|------|
| `tests/api/routes/` | APIエンドポイント (test_auth, test_cards, test_dashboards, test_datasets) |
| `tests/api/` | ヘルスチェック |
| `tests/core/` | 設定、ロギング、パスワードポリシー、セキュリティ |
| `tests/db/` | DynamoDB / S3 クライアント |
| `tests/models/` | Pydantic モデル |
| `tests/repositories/` | リポジトリ層 |
| `tests/services/` | サービス層 (CSV解析、データセット、カード実行、ダッシュボード等) |

テストは `moto` (AWS サービスモック) と `respx` (HTTP モック) を使用しています。

### 6.2 フロントエンドテスト

```bash
cd frontend

# ウォッチモードでテスト実行
npm run test

# カバレッジ付き (単発実行)
npm run test:coverage

# 特定ファイルのみ
npx vitest src/__tests__/stores/auth-store.test.ts
```

テスト構成:

| テストファイル | 対象 |
|---------------|------|
| `src/__tests__/App.test.tsx` | アプリケーションルート |
| `src/__tests__/stores/auth-store.test.ts` | 認証ストア |
| `src/__tests__/types/type-guards.test.ts` | 型ガード |
| `src/__tests__/lib/utils.test.ts` | ユーティリティ関数 |

テストは `vitest` + `@testing-library/react` + `jsdom` を使用しています。

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

### 7.2 APIルート一覧

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
| GET | `/api/dashboards/{id}/referenced-datasets` | 参照データセット一覧 |

### 7.3 フロントエンドルート一覧

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

認証が必要なルートは `AuthGuard` コンポーネントで保護されています。

### 7.4 DynamoDB テーブル構成

| テーブル名 | パーティションキー | GSI |
|-----------|-------------------|-----|
| `bi_users` | `userId` (S) | `UsersByEmail` (email -> ALL) |
| `bi_datasets` | `datasetId` (S) | `DatasetsByOwner` (ownerId + createdAt) |
| `bi_cards` | `cardId` (S) | `CardsByOwner` (ownerId + createdAt) |
| `bi_dashboards` | `dashboardId` (S) | `DashboardsByOwner` (ownerId + createdAt) |

### 7.5 Executor サンドボックス

カードの Python コードは Executor サービス内のサンドボックスで実行されます。

**利用可能なライブラリ:**
- `pandas` (as `pd`)
- `numpy` (as `np`)
- `plotly.express` (as `px`)
- `plotly.graph_objects` (as `go`)
- `matplotlib.pyplot` (as `plt`)
- `seaborn` (as `sns`)

**ブロックされている操作:**
- ファイルI/O (`open`, `os`, `pathlib` 等)
- ネットワークアクセス (`socket`, `http`, `urllib`, `requests` 等)
- プロセス操作 (`subprocess`, `multiprocessing` 等)
- `exec`, `eval`, `compile` の直接呼び出し
- `pickle`, `marshal` によるシリアライゼーション

**リソース制限:**
- タイムアウト: 10秒 (SIGALRM)
- メモリ: 2048MB (Linux環境のみ RLIMIT_AS で制限)

---

## 8. コーディング規約

### 8.1 バックエンド (Python)

- **フォーマッタ/リンタ:** Ruff (line-length: 100, target: Python 3.11)
- **型チェック:** mypy (strict モード)
- **テストフレームワーク:** pytest (asyncio_mode: auto)
- **ドキュメント:** Google style docstring
- **命名規則:** snake_case (変数/関数)、PascalCase (クラス)

### 8.2 フロントエンド (TypeScript)

- **フォーマッタ/リンタ:** ESLint + TypeScript ESLint
- **テストフレームワーク:** Vitest + Testing Library
- **UIライブラリ:** shadcn/ui (Radix UI + Tailwind CSS)
- **状態管理:** TanStack Query (サーバ状態) + Zustand (クライアント状態)
- **命名規則:** camelCase (変数/関数)、PascalCase (コンポーネント/型)
- **パスエイリアス:** `@/` = `src/`

---

## 9. Git ワークフロー

### 9.1 ブランチ戦略

```
master (本番)
  └── feature/xxx  (機能開発)
  └── fix/xxx      (バグ修正)
  └── docs/xxx     (ドキュメント)
```

### 9.2 コミットメッセージ

```
<type>: <summary>

<body (optional)>
```

type の例: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

### 9.3 プルリクエスト

1. 機能ブランチを作成
2. 変更を実装しテストを追加
3. リンタ/型チェック/テストが通ることを確認
4. プルリクエストを作成

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
