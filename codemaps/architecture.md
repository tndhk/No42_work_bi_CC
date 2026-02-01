# 全体アーキテクチャ コードマップ

**最終更新:** 2026-02-01 (Phase Q4 E2E + Q5 + フィルタ機能)
**プロジェクト:** BI Tool (社内BI・Pythonカード MVP)
**ステージ:** MVP

---

## システム構成図

```
                       +------------------+
                       |   ブラウザ (SPA)  |
                       |  React + Vite    |
                       |  :3000           |
                       +--------+---------+
                                |
                          HTTP (REST API)
                                |
                       +--------+---------+
                       |   API サーバ     |
                       |  FastAPI         |
                       |  :8000           |
                       +---+---------+----+
                           |         |
              +------------+    +----+-----------+
              |                 |                 |
     +--------+------+  +------+------+  +-------+-------+
     |  DynamoDB     |  |    S3       |  |   Executor    |
     |  (メタデータ) |  | (Parquet)   |  |  (Python実行) |
     |  :8001        |  | MinIO :9000 |  |  :8080        |
     +---------------+  +-------------+  +---------------+
```

## サービス一覧

| サービス | 技術 | ポート | 役割 | ヘルスチェック |
|----------|------|--------|------|---------------|
| frontend | React 18 + Vite 5 + TypeScript | 3000 | SPA フロントエンド | - |
| api (backend) | FastAPI 0.109 + Python 3.11 | 8000 | REST API サーバ | GET /api/health |
| executor | FastAPI 0.109 + Python 3.11 | 8080 | Python コード安全実行 | GET /health |
| dynamodb-local | Amazon DynamoDB Local | 8001 | NoSQL メタデータ保存 | curl localhost:8000 |
| minio | MinIO (S3互換) | 9000/9001 | オブジェクトストレージ | /minio/health/live |
| dynamodb-init | Python + boto3 | - | テーブル初期化 (oneshot) | - |
| minio-init | MinIO Client | - | バケット初期化 (oneshot) | - |

## docker-compose サービス起動順序

```
dynamodb-local (healthy) -+-> dynamodb-init
                          |
minio (healthy) ----------+--> minio-init
                          |
                          +--> executor (healthy)
                          |
                          +--> api (healthy) --> frontend
```

全サービスに healthcheck が設定されており、`depends_on: condition: service_healthy` で
依存サービスの起動完了を待機してから起動する構成。

## ディレクトリ構造

```
work_BI_ClaudeCode/
  backend/             # FastAPI バックエンド
    app/
      api/             # ルーター、依存性注入、レスポンスヘルパー
      core/            # 設定、セキュリティ、ログ
      db/              # DynamoDB / S3 接続
      models/          # Pydantic モデル
      repositories/    # DynamoDB リポジトリ (CRUD)
      services/        # ビジネスロジック
    tests/             # pytest テスト (37ファイル)
  frontend/            # React SPA
    src/
      components/      # UI コンポーネント
      hooks/           # React Query hooks
      lib/             # API クライアント、ユーティリティ
      pages/           # ページコンポーネント
      stores/          # Zustand ストア
      types/           # TypeScript 型定義
      __tests__/       # Vitest テスト (42ファイル, 262テスト, 83.07% coverage)
    e2e/               # Playwright E2E テスト (3スペック, 12テスト) [NEW]
    playwright.config.ts  # E2E テスト設定 [NEW]
    vitest.config.ts   # ユニットテスト設定
  executor/            # Python 実行サンドボックス
    app/               # FastAPI アプリ
    tests/             # pytest テスト (7ファイル)
  scripts/             # 初期化・ユーティリティスクリプト
    init_tables.py     # DynamoDB テーブル作成
    seed_test_user.py  # E2E テストユーザ作成 [NEW]
  codemaps/            # アーキテクチャ・コードマップ
  docs/                # 設計ドキュメント (9ファイル)
  docker-compose.yml   # ローカル開発環境 (ヘルスチェック付き)
```

## サービス間通信

```
[Frontend :3000]
    |
    +--> GET/POST /api/auth/*      --> [Backend :8000] --> [DynamoDB]
    +--> GET/POST /api/datasets/*  --> [Backend :8000] --> [DynamoDB] + [S3/MinIO]
    +--> GET /api/datasets/:id/columns/:col/values --> [Backend :8000] --> [S3/MinIO]
    +--> GET/POST /api/cards/*     --> [Backend :8000] --> [DynamoDB]
    +--> POST /api/cards/:id/execute --> [Backend :8000]
    |                                       |
    |                                       +--> POST /execute/card --> [Executor :8080]
    |                                       +--> DynamoDB (cache)
    |                                       +--> S3 (dataset)
    +--> POST /api/dashboards/:id/clone --> [Backend :8000] --> [DynamoDB] [NEW]
```

## 認証フロー

```
1. ブラウザ --> POST /api/auth/login { email, password }
2. Backend: DynamoDB から User 取得 --> bcrypt 検証 --> JWT 発行
3. Backend: api_response() でラップ { data: { access_token, user, ... } }
4. ブラウザ: Zustand ストアに token 保存
5. 以降のリクエスト: Authorization: Bearer <JWT>
6. Backend: deps.get_current_user() で JWT 検証
```

## データフロー: CSV インポート

```
1. ブラウザ: FormData で CSV アップロード
2. Backend: CSV パース (chardet + pandas)
3. Backend: 型推論 (type_inferrer)
4. Backend: Parquet 変換 + S3 保存 (parquet_storage)
5. Backend: メタデータを DynamoDB に保存 (dataset_repository)
6. Backend: api_response() でラップして返却
```

## データフロー: カード実行

```
1. ブラウザ: POST /api/cards/:id/execute
2. Backend: DynamoDB キャッシュ確認 (card_cache)
3. キャッシュ無し --> Backend: Executor に HTTP POST
4. Executor: サンドボックス内で Python コード実行
5. Executor: render() の戻り値 (HTML) を返却
6. Backend: 結果をキャッシュ + api_response() でラップ + フロントに返却
7. ブラウザ: iframe (sandbox) で HTML 描画
```

## データフロー: ダッシュボード表示

```
1. ブラウザ: GET /api/dashboards/:id --> DashboardDetail 取得 (filters 含む)
2. FilterBar: フィルタ定義からフィルタUIを描画
3. DashboardViewer: react-grid-layout で cards レイアウト構築
4. 各 LayoutItem --> onExecuteCard(cardId, filterValues) で並列実行
5. CardContainer: iframe sandbox で HTML 描画
6. ResponsiveGridLayout: ドラッグ/リサイズ不可 (閲覧モード)
```

## APIレスポンス標準化 [NEW]

全APIルートが `api/response.py` のヘルパーを使用:

| ヘルパー | 出力形式 | 使用場面 |
|---------|---------|---------|
| `api_response(data)` | `{ "data": T }` | 単体リソース取得、作成、更新 |
| `paginated_response(items, total, limit, offset)` | `{ "data": [...], "pagination": {...} }` | 一覧取得 (datasets, cards, dashboards) |

ページネーションオブジェクト: `{ total, limit, offset, has_next }`

## 主要依存ライブラリ

### Backend (Python)
| ライブラリ | バージョン | 用途 |
|-----------|-----------|------|
| fastapi | 0.109.0 | Web フレームワーク |
| pydantic | 2.5.0 | データバリデーション |
| aioboto3 | 12.3.0 | 非同期 AWS SDK |
| pandas | 2.2.0 | データ処理 |
| pyarrow | 15.0.0 | Parquet 変換 |
| python-jose | 3.3.0 | JWT |
| bcrypt | 4.1.3 | パスワードハッシュ |
| slowapi | 0.1.9 | レート制限 |
| chardet | 5.2.0 | エンコーディング検出 |
| structlog | 24.1.0 | 構造化ログ |

### Frontend (TypeScript)
| ライブラリ | バージョン | 用途 |
|-----------|-----------|------|
| react | 18.2.0 | UI フレームワーク |
| react-router-dom | 6.21.0 | ルーティング |
| @tanstack/react-query | 5.17.0 | サーバ状態管理 |
| zustand | 4.4.7 | クライアント状態管理 |
| ky | 1.1.3 | HTTP クライアント |
| @monaco-editor/react | 4.6.0 | コードエディタ |
| react-grid-layout | 1.4.4 | ダッシュボードグリッドレイアウト |
| lucide-react | 0.563.0 | アイコンライブラリ |
| zod | 3.25.76 | スキーマバリデーション |
| react-hook-form | 7.71.1 | フォーム管理 |
| date-fns | 4.1.0 | 日付フォーマット |
| react-day-picker | 9.13.0 | カレンダーUI |
| tailwindcss | 3.4.0 | CSS |
| Radix UI | 各種 | UIプリミティブ |

### Frontend (テスト)
| ライブラリ | バージョン | 用途 |
|-----------|-----------|------|
| vitest | 1.1.0 | ユニットテストランナー |
| @vitest/coverage-v8 | 1.1.0 | カバレッジ (V8) |
| @testing-library/react | 14.1.2 | React コンポーネントテスト |
| @testing-library/jest-dom | 6.1.5 | DOM マッチャー |
| @testing-library/user-event | 14.5.1 | ユーザー操作シミュレーション |
| jsdom | 23.0.1 | ブラウザ環境エミュレーション |
| @playwright/test | 1.58.1 | E2E テスト [NEW] |

### Executor (Python)
| ライブラリ | バージョン | 用途 |
|-----------|-----------|------|
| fastapi | 0.109.0 | Web フレームワーク |
| pandas | 2.2.0 | データ処理 |
| plotly | 5.18.0 | チャート生成 |
| matplotlib | 3.8.2 | チャート生成 |
| seaborn | 0.13.1 | 統計可視化 |

## テストインフラストラクチャ

| 領域 | フレームワーク | テストファイル数 | テスト数 | カバレッジ |
|------|---------------|-----------------|---------|-----------|
| Frontend (Unit) | Vitest + Testing Library | 42 | 262 | 83.07% (statements) |
| Frontend (E2E) | Playwright | 3 specs | 12 | - |
| Backend | pytest | 37 | - | - |
| Executor | pytest | 7 | - | - |

### E2E テスト構成 [NEW]

```
frontend/e2e/
  global-setup.ts          # バックエンド起動待機 (ヘルスチェック)
  auth.spec.ts             # 認証フロー (5テスト)
  dataset.spec.ts          # CSVインポート、一覧、プレビュー (3テスト)
  card-dashboard.spec.ts   # カード/ダッシュボード CRUD (4テスト)
  helpers/
    login-helper.ts        # UI 経由ログインヘルパー
    api-helper.ts          # テストデータ作成/削除 API ヘルパー
  sample-data/
    test-sales.csv         # E2E テスト用サンプル CSV
```

Playwright 設定: Chromium のみ, `workers: 1` (DynamoDB Local 共有のため順次実行), `baseURL: localhost:3000`

## 環境変数 (.env.example)

| 変数 | 用途 | デフォルト |
|------|------|-----------|
| ENV | 環境名 | local |
| JWT_SECRET_KEY | JWT 署名鍵 | (要変更) |
| DYNAMODB_ENDPOINT | DynamoDB エンドポイント | http://dynamodb-local:8000 |
| S3_ENDPOINT | S3 エンドポイント | http://minio:9000 |
| S3_BUCKET_DATASETS | データセットバケット | bi-datasets |
| EXECUTOR_ENDPOINT | Executor エンドポイント | http://executor:8080 |
| VITE_API_URL | フロントAPI URL | http://localhost:8000 |

## 関連コードマップ

- [backend.md](./backend.md) - バックエンド構造詳細
- [frontend.md](./frontend.md) - フロントエンド構造詳細
- [data.md](./data.md) - データモデルとスキーマ
