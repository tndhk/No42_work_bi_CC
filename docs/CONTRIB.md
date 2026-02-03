# 開発者ガイド (CONTRIB)

最終更新: 2026-02-03

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

---

## 3. 環境変数

`.env.example` を `.env` にコピーして設定。

### API設定

| 変数 | デフォルト | 説明 |
|------|-----------|------|
| `ENV` | local | 環境識別子 (local/staging/production) |
| `API_HOST` | 0.0.0.0 | APIバインドアドレス |
| `API_PORT` | 8000 | APIポート |
| `API_WORKERS` | 4 | Uvicorn ワーカー数 |
| `API_DEBUG` | false | デバッグモード |

### 認証設定

| 変数 | デフォルト | 説明 |
|------|-----------|------|
| `JWT_SECRET_KEY` | (必須) | JWT署名キー (本番: 32文字以上のランダム文字列) |
| `JWT_ALGORITHM` | HS256 | JWTアルゴリズム |
| `JWT_EXPIRE_MINUTES` | 1440 | トークン有効期限 (分、デフォルト24時間) |
| `PASSWORD_MIN_LENGTH` | 8 | パスワード最小文字数 |

### DynamoDB設定

| 変数 | デフォルト | 説明 |
|------|-----------|------|
| `DYNAMODB_ENDPOINT` | http://dynamodb-local:8000 | DynamoDBエンドポイント |
| `DYNAMODB_REGION` | ap-northeast-1 | AWSリージョン |
| `DYNAMODB_TABLE_PREFIX` | bi_ | テーブル名プレフィックス |

### S3/MinIO設定

| 変数 | デフォルト | 説明 |
|------|-----------|------|
| `S3_ENDPOINT` | http://minio:9000 | S3エンドポイント |
| `S3_REGION` | ap-northeast-1 | AWSリージョン |
| `S3_BUCKET_DATASETS` | bi-datasets | Parquetデータ格納バケット |
| `S3_BUCKET_STATIC` | bi-static | 静的ファイルバケット |
| `S3_ACCESS_KEY` | minioadmin | アクセスキー (ローカル用) |
| `S3_SECRET_KEY` | minioadmin | シークレットキー (ローカル用) |

### Vertex AI設定 (Chatbot用、オプション)

| 変数 | デフォルト | 説明 |
|------|-----------|------|
| `VERTEX_AI_PROJECT_ID` | - | GCPプロジェクトID |
| `VERTEX_AI_LOCATION` | asia-northeast1 | Vertex AIロケーション |
| `VERTEX_AI_MODEL` | gemini-1.5-pro | 使用モデル |

### Executor設定

| 変数 | デフォルト | 説明 |
|------|-----------|------|
| `EXECUTOR_ENDPOINT` | http://executor:8080 | Executorエンドポイント |
| `EXECUTOR_TIMEOUT_CARD` | 10 | カード実行タイムアウト (秒) |
| `EXECUTOR_TIMEOUT_TRANSFORM` | 300 | Transform実行タイムアウト (秒) |
| `EXECUTOR_MAX_CONCURRENT_CARDS` | 10 | カード同時実行数上限 |
| `EXECUTOR_MAX_CONCURRENT_TRANSFORMS` | 5 | Transform同時実行数上限 |

### ログ設定

| 変数 | デフォルト | 説明 |
|------|-----------|------|
| `LOG_LEVEL` | INFO | ログレベル (DEBUG/INFO/WARNING/ERROR) |
| `LOG_FORMAT` | json | ログフォーマット (json/text) |

---

## 4. 開発コマンド

### フロントエンド (frontend/)

| コマンド | 説明 |
|---------|------|
| `npm run dev` | 開発サーバ起動 (Vite HMR) |
| `npm run build` | プロダクションビルド (tsc + vite build) |
| `npm run preview` | ビルド結果プレビュー |
| `npm run test` | Vitestテスト (ウォッチモード) |
| `npm run test:coverage` | カバレッジ付きテスト (v8) |
| `npm run lint` | ESLint実行 |
| `npm run typecheck` | TypeScript型チェック (--noEmit) |
| `npm run e2e` | Playwright E2Eテスト (ヘッドレス) |
| `npm run e2e:ui` | Playwright E2Eテスト (UI モード) |
| `npm run e2e:headed` | Playwright E2Eテスト (ブラウザ表示) |
| `npm run e2e:report` | E2Eテストレポート表示 |

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
| フロントエンド | 83%+ coverage, 340+ tests |
| バックエンド | pytest pass |
| E2E | 全テストpass |

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

### DynamoDBテーブル一覧

初期化スクリプト (`scripts/init_tables.py`) で作成されるテーブル:

| テーブル名 | パーティションキー | GSI |
|-----------|-------------------|-----|
| `bi_users` | userId | UsersByEmail |
| `bi_datasets` | datasetId | DatasetsByOwner |
| `bi_cards` | cardId | CardsByOwner |
| `bi_dashboards` | dashboardId | DashboardsByOwner |
| `bi_filter_views` | filterViewId | FilterViewsByDashboard |

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
      api/              # APIルート
      core/             # 認証・設定
      db/               # DynamoDB接続
      models/           # Pydanticモデル
      repositories/     # データアクセス層
      services/         # ビジネスロジック
    tests/              # pytestテスト
  executor/             # Python Sandbox (カード/Transform実行)
  frontend/             # React SPA
    src/
      components/       # UIコンポーネント
      hooks/            # カスタムフック
      lib/              # ユーティリティ・API
      pages/            # ページコンポーネント
      types/            # TypeScript型定義
  scripts/              # 初期化スクリプト
  docs/                 # ドキュメント
  codemaps/             # アーキテクチャマップ
```

---

## 9. 関連ドキュメント

| ドキュメント | 内容 |
|-------------|------|
| `docs/requirements.md` | 要件定義 |
| `docs/design.md` | 設計書 |
| `docs/api-spec.md` | API仕様 (全エンドポイント) |
| `docs/RUNBOOK.md` | 運用ガイド |
| `docs/PROGRESS.md` | 実装進捗 |
| `docs/security.md` | セキュリティ仕様 |
| `docs/data-flow.md` | データフロー図 |
| `codemaps/` | アーキテクチャマップ |
