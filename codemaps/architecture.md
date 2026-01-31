# 全体アーキテクチャ コードマップ

**最終更新:** 2026-01-31 (Phase Q3 Frontend Test Expansion 完了後)
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

| サービス | 技術 | ポート | 役割 |
|----------|------|--------|------|
| frontend | React 18 + Vite 5 + TypeScript | 3000 | SPA フロントエンド |
| api (backend) | FastAPI 0.109 + Python 3.11 | 8000 | REST API サーバ |
| executor | FastAPI 0.109 + Python 3.11 | 8080 | Python コード安全実行 |
| dynamodb-local | Amazon DynamoDB Local | 8001 | NoSQL メタデータ保存 |
| minio | MinIO (S3互換) | 9000/9001 | オブジェクトストレージ |
| dynamodb-init | Python + boto3 | - | テーブル初期化 (oneshot) |
| minio-init | MinIO Client | - | バケット初期化 (oneshot) |

## ディレクトリ構造

```
work_BI_ClaudeCode/
  backend/             # FastAPI バックエンド
    app/
      api/             # ルーター、依存性注入
      core/            # 設定、セキュリティ、ログ
      db/              # DynamoDB / S3 接続
      models/          # Pydantic モデル
      repositories/    # DynamoDB リポジトリ (CRUD)
      services/        # ビジネスロジック
    tests/             # pytest テスト (29ファイル)
  frontend/            # React SPA
    src/
      components/      # UI コンポーネント
      hooks/           # React Query hooks
      lib/             # API クライアント、ユーティリティ
      pages/           # ページコンポーネント
      stores/          # Zustand ストア
      types/           # TypeScript 型定義
      __tests__/       # Vitest テスト (37ファイル, 227テスト, 83.07% coverage)
    vitest.config.ts   # テスト設定
  executor/            # Python 実行サンドボックス
    app/               # FastAPI アプリ
    tests/             # pytest テスト (6ファイル)
  scripts/             # 初期化スクリプト
  codemaps/            # アーキテクチャ・コードマップ
  docs/                # 設計ドキュメント (9ファイル)
  docker-compose.yml   # ローカル開発環境
```

## サービス間通信

```
[Frontend :3000]
    |
    +--> GET/POST /api/auth/*      --> [Backend :8000] --> [DynamoDB]
    +--> GET/POST /api/datasets/*  --> [Backend :8000] --> [DynamoDB] + [S3/MinIO]
    +--> GET/POST /api/cards/*     --> [Backend :8000] --> [DynamoDB]
    +--> POST /api/cards/:id/execute --> [Backend :8000]
                                          |
                                          +--> POST /execute/card --> [Executor :8080]
                                          +--> DynamoDB (cache)
                                          +--> S3 (dataset)
```

## 認証フロー

```
1. ブラウザ --> POST /api/auth/login { email, password }
2. Backend: DynamoDB から User 取得 --> bcrypt 検証 --> JWT 発行
3. ブラウザ: Zustand ストアに token 保存
4. 以降のリクエスト: Authorization: Bearer <JWT>
5. Backend: deps.get_current_user() で JWT 検証
```

## データフロー: CSV インポート

```
1. ブラウザ: FormData で CSV アップロード
2. Backend: CSV パース (chardet + pandas)
3. Backend: 型推論 (type_inferrer)
4. Backend: Parquet 変換 + S3 保存 (parquet_storage)
5. Backend: メタデータを DynamoDB に保存 (dataset_repository)
```

## データフロー: カード実行

```
1. ブラウザ: POST /api/cards/:id/execute
2. Backend: DynamoDB キャッシュ確認 (card_cache)
3. キャッシュ無し --> Backend: Executor に HTTP POST
4. Executor: サンドボックス内で Python コード実行
5. Executor: render() の戻り値 (HTML) を返却
6. Backend: 結果をキャッシュ + フロントに返却
7. ブラウザ: iframe (sandbox) で HTML 描画
```

## データフロー: ダッシュボード表示

```
1. ブラウザ: GET /api/dashboards/:id --> DashboardDetail 取得
2. DashboardViewer: react-grid-layout で cards レイアウト構築
3. 各 LayoutItem --> onExecuteCard(cardId) で並列実行
4. CardContainer: iframe sandbox で HTML 描画
5. ResponsiveGridLayout: ドラッグ/リサイズ不可 (閲覧モード)
```

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
| tailwindcss | 3.4.0 | CSS |
| Radix UI | 各種 | UIプリミティブ |

### Frontend (テスト)
| ライブラリ | バージョン | 用途 |
|-----------|-----------|------|
| vitest | 1.1.0 | テストランナー |
| @vitest/coverage-v8 | 1.1.0 | カバレッジ (V8) |
| @testing-library/react | 14.1.2 | React コンポーネントテスト |
| @testing-library/jest-dom | 6.1.5 | DOM マッチャー |
| @testing-library/user-event | 14.5.1 | ユーザー操作シミュレーション |
| jsdom | 23.0.1 | ブラウザ環境エミュレーション |

### Executor (Python)
| ライブラリ | バージョン | 用途 |
|-----------|-----------|------|
| fastapi | 0.109.0 | Web フレームワーク |
| pandas | 2.2.0 | データ処理 |
| plotly | 5.18.0 | チャート生成 |
| matplotlib | 3.8.2 | チャート生成 |
| seaborn | 0.13.1 | 統計可視化 |

## テストインフラストラクチャ

| 領域 | フレームワーク | テストファイル数 | カバレッジ |
|------|---------------|-----------------|-----------|
| Frontend | Vitest + Testing Library | 37 | 83.07% (statements) |
| Backend | pytest | 29 | - |
| Executor | pytest | 6 | - |

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
