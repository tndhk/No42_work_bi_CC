# バックエンド コードマップ

**最終更新:** 2026-01-31 (Phase Q3 Frontend Test Expansion 完了後)
**フレームワーク:** FastAPI 0.109 / Python 3.11+
**エントリポイント:** `backend/app/main.py`

---

## ディレクトリ構造

```
backend/
  app/
    __init__.py
    main.py                          # FastAPI アプリ初期化、CORS、レート制限
    api/
      __init__.py                    # (空)
      deps.py                        # DI: DynamoDB, S3, 認証
      routes/
        __init__.py                  # api_router 組み立て
        auth.py                      # 認証 API
        cards.py                     # カード CRUD + 実行
        dashboards.py                # ダッシュボード CRUD
        datasets.py                  # データセット CRUD + CSV インポート
    core/
      __init__.py
      config.py                      # Settings (pydantic-settings)
      logging.py                     # structlog 設定
      password_policy.py             # パスワードポリシー
      security.py                    # JWT + bcrypt
    db/
      __init__.py
      dynamodb.py                    # DynamoDB 接続 (aioboto3)
      s3.py                          # S3 接続 (aioboto3)
    models/
      __init__.py
      common.py                      # BaseResponse, TimestampMixin
      card.py                        # Card, CardCreate, CardUpdate
      dashboard.py                   # Dashboard, LayoutItem, FilterDefinition
      dataset.py                     # Dataset, ColumnSchema
      user.py                        # User, UserInDB, UserCreate
    repositories/
      __init__.py
      base.py                        # BaseRepository[T] (Generic CRUD)
      card_repository.py             # CardRepository
      dashboard_repository.py        # DashboardRepository
      dataset_repository.py          # DatasetRepository
      user_repository.py             # UserRepository (+ GSI email検索)
    services/
      __init__.py
      card_execution_service.py      # CardExecutionService, CardCacheService
      csv_parser.py                  # CSV パース + エンコーディング検出
      dashboard_service.py           # DashboardService (参照データセット)
      dataset_service.py             # DatasetService (CSV インポート + プレビュー)
      parquet_storage.py             # ParquetConverter, ParquetReader
      type_inferrer.py               # 型推論 (int, float, bool, date, string)
  tests/                             # pytest テスト (29ファイル)
    conftest.py                      # 共通フィクスチャ
    core/                            # config, security, logging, password_policy テスト
    models/                          # common, user, dataset, card, dashboard テスト
    db/                              # dynamodb, s3 テスト
    repositories/                    # base, user, dataset, card, dashboard テスト
    services/                        # csv_parser, parquet, dataset, card_execution,
                                     # dashboard, executor_client, type_inferrer テスト
    api/                             # health, routes テスト
  requirements.txt                   # pip 依存関係
  pyproject.toml                     # ruff, mypy, pytest 設定
```

## API ルート

| メソッド | パス | ハンドラ | 説明 |
|----------|------|---------|------|
| GET | /api/health | main.health | ヘルスチェック |
| POST | /api/auth/login | auth.login | ログイン (レート制限 5/min) |
| POST | /api/auth/logout | auth.logout | ログアウト |
| GET | /api/auth/me | auth.get_me | 現在ユーザー取得 |
| GET | /api/datasets | datasets.list_datasets | データセット一覧 |
| POST | /api/datasets | datasets.create_dataset | CSV インポート (multipart) |
| GET | /api/datasets/:id | datasets.get_dataset | データセット詳細 |
| PUT | /api/datasets/:id | datasets.update_dataset | データセット更新 |
| DELETE | /api/datasets/:id | datasets.delete_dataset | データセット削除 |
| GET | /api/datasets/:id/preview | datasets.get_dataset_preview | データプレビュー |
| GET | /api/cards | cards.list_cards | カード一覧 |
| POST | /api/cards | cards.create_card | カード作成 |
| GET | /api/cards/:id | cards.get_card | カード詳細 |
| PUT | /api/cards/:id | cards.update_card | カード更新 |
| DELETE | /api/cards/:id | cards.delete_card | カード削除 |
| POST | /api/cards/:id/preview | cards.preview_card | プレビュー実行 (キャッシュ無し) |
| POST | /api/cards/:id/execute | cards.execute_card | カード実行 (キャッシュ有) |
| GET | /api/dashboards | dashboards.list_dashboards | ダッシュボード一覧 |
| POST | /api/dashboards | dashboards.create_dashboard | ダッシュボード作成 |
| GET | /api/dashboards/:id | dashboards.get_dashboard | ダッシュボード詳細 |
| PUT | /api/dashboards/:id | dashboards.update_dashboard | ダッシュボード更新 |
| DELETE | /api/dashboards/:id | dashboards.delete_dashboard | ダッシュボード削除 |
| GET | /api/dashboards/:id/referenced-datasets | dashboards.get_referenced_datasets | 参照データセット |

## 依存関係グラフ

```
main.py
  +-- core/config.py (settings)
  +-- core/logging.py (setup_logging)
  +-- api/routes/__init__.py (api_router)
        +-- routes/auth.py
        |     +-- api/deps.py
        |     +-- core/security.py
        |     +-- repositories/user_repository.py
        |     +-- models/user.py
        +-- routes/cards.py
        |     +-- api/deps.py
        |     +-- models/card.py, user.py
        |     +-- repositories/card_repository.py, dataset_repository.py
        |     +-- services/card_execution_service.py
        |     +-- core/config.py
        +-- routes/dashboards.py
        |     +-- api/deps.py
        |     +-- models/dashboard.py, user.py
        |     +-- repositories/dashboard_repository.py
        |     +-- services/dashboard_service.py
        +-- routes/datasets.py
              +-- api/deps.py
              +-- models/dataset.py, user.py
              +-- repositories/dataset_repository.py
              +-- services/dataset_service.py
```

### コア依存

```
api/deps.py
  +-- core/config.py (settings)
  +-- core/security.py (decode_access_token)
  +-- repositories/user_repository.py
  +-- models/user.py

core/security.py
  +-- core/config.py (settings)
  +-- bcrypt, jose (外部)
```

### リポジトリ依存

```
repositories/base.py
  +-- pydantic.BaseModel (Generic[T])

repositories/*_repository.py
  +-- repositories/base.py (BaseRepository)
  +-- core/config.py (table_prefix)
  +-- models/*
```

### サービス依存

```
services/card_execution_service.py
  +-- core/config.py (executor_url, cache_ttl)
  +-- httpx (Executor HTTP呼び出し)

services/dataset_service.py
  +-- services/csv_parser.py
  +-- services/parquet_storage.py
  +-- services/type_inferrer.py
  +-- repositories/dataset_repository.py
  +-- core/config.py

services/dashboard_service.py
  +-- repositories/card_repository.py
  +-- repositories/dataset_repository.py
  +-- models/dashboard.py, card.py, dataset.py

services/csv_parser.py
  +-- chardet, pandas (外部)

services/parquet_storage.py
  +-- pyarrow, pandas (外部)

services/type_inferrer.py
  +-- pandas (外部)
  +-- models/dataset.py (ColumnSchema)
```

## DI (依存性注入)

`api/deps.py` が提供する Depends:

| 関数 | 返却値 | 用途 |
|------|--------|------|
| `get_dynamodb_resource()` | aioboto3 DynamoDB resource | 全テーブル操作 |
| `get_s3_client()` | aioboto3 S3 client | Parquet 読み書き |
| `get_current_user()` | User | JWT 認証 (HTTPBearer) |

## BaseRepository パターン

```python
class BaseRepository(Generic[T]):
    # snake_case <--> camelCase 変換
    # datetime <--> UNIX timestamp 変換
    # CRUD: create(), get_by_id(), update(), delete()
    # aioboto3 / boto3 両対応 (_execute_db_operation)
```

各リポジトリが追加で実装:
- `UserRepository.get_by_email()` - GSI `UsersByEmail`
- `CardRepository.list_by_owner()` - GSI `CardsByOwner`
- `DashboardRepository.list_by_owner()` - GSI `DashboardsByOwner`
- `DatasetRepository.list_by_owner()` - GSI `DatasetsByOwner`

## カード実行フロー詳細

```
CardExecutionService.execute()
  1. use_cache=true --> CardCacheService.get(key)
  2. キャッシュヒット --> return CardExecutionResult(cached=true)
  3. キャッシュミス --> _execute_with_retry()
     a. httpx.AsyncClient.post(executor_url/execute/card)
     b. 5xx/接続エラー --> 指数バックオフ (0.5s * 2^n, 最大3回)
     c. 4xx --> 即座にエラー
  4. 結果を CardCacheService.set() で保存
  5. return CardExecutionResult(cached=false)
```

## セキュリティ

- **JWT**: HS256, 有効期限 24h (設定可能)
- **パスワード**: bcrypt 12ラウンド
- **パスワードポリシー**: 最低8文字, 大文字/小文字/数字/特殊文字必須
- **レート制限**: ログイン 5回/分 (slowapi)
- **CORS**: 設定可能 (デフォルト localhost:3000)

## 関連コードマップ

- [architecture.md](./architecture.md) - 全体アーキテクチャ
- [frontend.md](./frontend.md) - フロントエンド構造
- [data.md](./data.md) - データモデル詳細
