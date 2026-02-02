# バックエンド コードマップ

最終更新: 2026-02-03 (FR-7 Dashboard Sharing / Group Management)
フレームワーク: FastAPI 0.109 / Python 3.11+
エントリポイント: `backend/app/main.py`

---

## ディレクトリ構造

```
backend/
  app/
    __init__.py
    main.py                          # FastAPI アプリ初期化、CORS、レート制限
    api/
      __init__.py                    # (空)
      deps.py                        # DI: DynamoDB, S3, 認証, require_admin
      response.py                    # api_response(), paginated_response()
      routes/
        __init__.py                  # api_router 組み立て
        auth.py                      # 認証 API
        cards.py                     # カード CRUD + 実行
        dashboards.py                # ダッシュボード CRUD + clone
        dashboard_shares.py          # ダッシュボード共有 CRUD [FR-7]
        datasets.py                  # データセット CRUD + CSV インポート
        filter_views.py              # フィルタビュー (dashboard-scoped)
        filter_view_detail.py        # フィルタビュー詳細 (独立)
        groups.py                    # グループ管理 CRUD + メンバー管理 [FR-7]
        users.py                     # ユーザー検索 [FR-7]
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
      dashboard.py                   # Dashboard, LayoutItem, FilterDefinition (options付き)
      dashboard_share.py             # DashboardShare, Permission, SharedToType [FR-7]
      dataset.py                     # Dataset, ColumnSchema
      group.py                       # Group, GroupCreate, GroupUpdate, GroupMember [FR-7]
      user.py                        # User, UserInDB, UserCreate, UserUpdate
    repositories/
      __init__.py
      base.py                        # BaseRepository[T] (Generic CRUD)
      card_repository.py             # CardRepository
      dashboard_repository.py        # DashboardRepository
      dashboard_share_repository.py  # DashboardShareRepository (GSI: SharesByDashboard, SharesByTarget) [FR-7]
      dataset_repository.py          # DatasetRepository
      group_repository.py            # GroupRepository (GSI: GroupsByName) [FR-7]
      group_member_repository.py     # GroupMemberRepository (複合キー, GSI: MembersByUser) [FR-7]
      user_repository.py             # UserRepository (+ GSI email検索, scan_by_email_prefix)
    services/
      __init__.py
      card_execution_service.py      # CardExecutionService, CardCacheService
      csv_parser.py                  # CSV パース + エンコーディング検出
      dashboard_service.py           # DashboardService (参照データセット)
      dataset_service.py             # DatasetService (CSV インポート + プレビュー)
      parquet_storage.py             # ParquetConverter, ParquetReader
      permission_service.py          # PermissionService (VIEWER/EDITOR/OWNER レベル判定) [FR-7]
      type_inferrer.py               # 型推論 (int, float, bool, date, string)
  tests/
    conftest.py                      # 共通フィクスチャ
    core/                            # config, security, logging, password_policy テスト
    models/                          # common, user, dataset, card, dashboard,
                                     # dashboard_share, group テスト
    db/                              # dynamodb, s3 テスト
    repositories/                    # base, user, dataset, card, dashboard,
                                     # dashboard_share, group, group_member テスト
    services/                        # csv_parser, parquet, dataset, card_execution,
                                     # dashboard, executor_client, type_inferrer,
                                     # permission_service テスト
    api/                             # health, deps テスト
      routes/                        # auth, cards, dashboards, datasets, filter_views,
                                     # dashboard_shares, groups, users テスト
    integration/                     # 統合テスト [FR-7]
      test_permission_integration.py # パーミッション統合テスト
  requirements.txt                   # pip 依存関係
  pyproject.toml                     # ruff, mypy, pytest 設定
```

## APIレスポンスヘルパー (api/response.py)

```python
def api_response(data: Any) -> dict:
    """単体レスポンス: { "data": T }"""

def paginated_response(items, total, limit, offset) -> dict:
    """一覧レスポンス: { "data": [...], "pagination": { total, limit, offset, has_next } }"""
```

全ルートハンドラがこれらのヘルパーを使用してレスポンスをラップ。
Frontend の `ApiResponse<T>` / `PaginatedResponse<T>` 型と整合。

## API ルート

### 認証 / ヘルスチェック

| メソッド | パス | ハンドラ | 説明 | レスポンス形式 |
|----------|------|---------|------|---------------|
| GET | /api/health | main.health | ヘルスチェック | `{ status }` |
| POST | /api/auth/login | auth.login | ログイン (5/min) | api_response |
| POST | /api/auth/logout | auth.logout | ログアウト | api_response |
| GET | /api/auth/me | auth.get_me | 現在ユーザー | api_response |

### データセット

| メソッド | パス | ハンドラ | 説明 | レスポンス形式 |
|----------|------|---------|------|---------------|
| GET | /api/datasets | datasets.list_datasets | データセット一覧 | paginated_response |
| POST | /api/datasets | datasets.create_dataset | CSV インポート | api_response |
| GET | /api/datasets/:id | datasets.get_dataset | データセット詳細 | api_response |
| PUT | /api/datasets/:id | datasets.update_dataset | データセット更新 | api_response |
| DELETE | /api/datasets/:id | datasets.delete_dataset | データセット削除 | 204 No Content |
| GET | /api/datasets/:id/preview | datasets.get_dataset_preview | データプレビュー | api_response |
| GET | /api/datasets/:id/columns/:col/values | datasets.get_column_values | カラムユニーク値 | api_response |

### カード

| メソッド | パス | ハンドラ | 説明 | レスポンス形式 |
|----------|------|---------|------|---------------|
| GET | /api/cards | cards.list_cards | カード一覧 | paginated_response |
| POST | /api/cards | cards.create_card | カード作成 | api_response |
| GET | /api/cards/:id | cards.get_card | カード詳細 | api_response |
| PUT | /api/cards/:id | cards.update_card | カード更新 | api_response |
| DELETE | /api/cards/:id | cards.delete_card | カード削除 | 204 No Content |
| POST | /api/cards/:id/preview | cards.preview_card | プレビュー実行 | api_response |
| POST | /api/cards/:id/execute | cards.execute_card | カード実行 | api_response |

### ダッシュボード

| メソッド | パス | ハンドラ | 説明 | レスポンス形式 |
|----------|------|---------|------|---------------|
| GET | /api/dashboards | dashboards.list_dashboards | ダッシュボード一覧 | paginated_response |
| POST | /api/dashboards | dashboards.create_dashboard | ダッシュボード作成 | api_response |
| GET | /api/dashboards/:id | dashboards.get_dashboard | ダッシュボード詳細 | api_response |
| PUT | /api/dashboards/:id | dashboards.update_dashboard | ダッシュボード更新 | api_response |
| DELETE | /api/dashboards/:id | dashboards.delete_dashboard | ダッシュボード削除 | 204 No Content |
| POST | /api/dashboards/:id/clone | dashboards.clone_dashboard | ダッシュボード複製 | api_response |
| GET | /api/dashboards/:id/referenced-datasets | dashboards.get_referenced_datasets | 参照データセット | api_response |

### ダッシュボード共有 [FR-7]

prefix: `/api/dashboards/{dashboard_id}/shares` (dashboard-scoped)

| メソッド | パス | ハンドラ | 認可 | 説明 | レスポンス形式 |
|----------|------|---------|------|------|---------------|
| GET | /api/dashboards/:id/shares | dashboard_shares.list_shares | owner | 共有一覧取得 | api_response |
| POST | /api/dashboards/:id/shares | dashboard_shares.create_share | owner | 共有作成 (重複409) | api_response (201) |
| PUT | /api/dashboards/:id/shares/:share_id | dashboard_shares.update_share | owner | 権限レベル変更 | api_response |
| DELETE | /api/dashboards/:id/shares/:share_id | dashboard_shares.delete_share | owner | 共有削除 | 204 No Content |

ヘルパー: `_get_dashboard_as_owner(dashboard_id, current_user, dynamodb)` -- ダッシュボード存在確認 + オーナー検証 (404/403)

### グループ管理 [FR-7]

prefix: `/api/groups` (admin only -- require_admin)

| メソッド | パス | ハンドラ | 認可 | 説明 | レスポンス形式 |
|----------|------|---------|------|------|---------------|
| GET | /api/groups | groups.list_groups | admin | グループ一覧 | api_response |
| POST | /api/groups | groups.create_group | admin | グループ作成 (名前重複409) | api_response (201) |
| GET | /api/groups/:id | groups.get_group | admin | グループ詳細 (メンバー含む) | api_response |
| PUT | /api/groups/:id | groups.update_group | admin | グループ名変更 | api_response |
| DELETE | /api/groups/:id | groups.delete_group | admin | グループ削除 | 204 No Content |
| POST | /api/groups/:id/members | groups.add_member | admin | メンバー追加 | api_response (201) |
| DELETE | /api/groups/:id/members/:user_id | groups.remove_member | admin | メンバー削除 | 204 No Content |

### ユーザー検索 [FR-7]

prefix: `/api/users`

| メソッド | パス | ハンドラ | 認可 | 説明 | レスポンス形式 |
|----------|------|---------|------|------|---------------|
| GET | /api/users?q=&limit= | users.search_users | authenticated | メール部分一致検索 | api_response |

パラメータ: `q` (検索文字列, 空の場合は空配列返却), `limit` (1-100, default 20)
レスポンスフィールド: id, email, role (hashed_password は除外)

### ページネーション仕様

一覧エンドポイント (datasets, cards, dashboards) は共通のページネーションパラメータを受け付ける:

| パラメータ | 型 | デフォルト | 制約 |
|-----------|-----|----------|------|
| `limit` | int | 50 | 1-100 |
| `offset` | int | 0 | >= 0 |

レスポンス: `{ data: [...], pagination: { total, limit, offset, has_next } }`

## 依存関係グラフ

```
main.py
  +-- core/config.py (settings)
  +-- core/logging.py (setup_logging)
  +-- api/routes/__init__.py (api_router)
        +-- routes/auth.py
        |     +-- api/deps.py (get_current_user)
        |     +-- api/response.py (api_response)
        |     +-- core/security.py
        |     +-- repositories/user_repository.py
        |     +-- models/user.py
        +-- routes/cards.py
        |     +-- api/deps.py (get_current_user)
        |     +-- api/response.py (api_response, paginated_response)
        |     +-- models/card.py, user.py
        |     +-- repositories/card_repository.py, dataset_repository.py
        |     +-- services/card_execution_service.py
        |     +-- core/config.py
        +-- routes/dashboards.py
        |     +-- api/deps.py (get_current_user)
        |     +-- api/response.py (api_response, paginated_response)
        |     +-- models/dashboard.py, user.py
        |     +-- repositories/dashboard_repository.py
        |     +-- services/dashboard_service.py
        +-- routes/datasets.py
        |     +-- api/deps.py (get_current_user)
        |     +-- api/response.py (api_response, paginated_response)
        |     +-- models/dataset.py, user.py
        |     +-- repositories/dataset_repository.py
        |     +-- services/dataset_service.py
        +-- routes/dashboard_shares.py  [FR-7]
        |     +-- api/deps.py (get_current_user)
        |     +-- api/response.py (api_response)
        |     +-- models/user.py, dashboard_share.py
        |     +-- repositories/dashboard_repository.py
        |     +-- repositories/dashboard_share_repository.py
        +-- routes/groups.py  [FR-7]
        |     +-- api/deps.py (require_admin)
        |     +-- api/response.py (api_response)
        |     +-- models/user.py, group.py
        |     +-- repositories/group_repository.py
        |     +-- repositories/group_member_repository.py
        +-- routes/users.py  [FR-7]
              +-- api/deps.py (get_current_user)
              +-- api/response.py (api_response)
              +-- models/user.py
              +-- repositories/user_repository.py
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

repositories/*_repository.py (card, dashboard, dataset, user, dashboard_share, group)
  +-- repositories/base.py (BaseRepository)
  +-- core/config.py (table_prefix)
  +-- models/*

repositories/group_member_repository.py  [FR-7]
  +-- core/config.py (table_prefix)
  +-- models/group.py (GroupMember)
  -- BaseRepository を継承しない (複合キー groupId + userId)
```

### サービス依存

```
services/card_execution_service.py
  +-- core/config.py (executor_url, cache_ttl)
  +-- httpx (Executor HTTP呼び出し)

services/dataset_service.py
  +-- services/csv_parser.py
  +-- services/parquet_storage.py (get_column_values 含む)
  +-- services/type_inferrer.py
  +-- repositories/dataset_repository.py
  +-- core/config.py

services/dashboard_service.py
  +-- repositories/card_repository.py
  +-- repositories/dataset_repository.py
  +-- models/dashboard.py, card.py, dataset.py

services/permission_service.py  [FR-7]
  +-- models/dashboard.py (Dashboard)
  +-- models/dashboard_share.py (Permission, SharedToType)
  +-- repositories/dashboard_share_repository.py
  +-- repositories/group_member_repository.py

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
| `require_admin()` | User | admin ロール必須 (get_current_user に依存, 403) [FR-7] |

### require_admin 依存性 [FR-7]

`require_admin` は `get_current_user` を内部で呼び出した上で、`current_user.role != "admin"` の場合に
HTTP 403 (Admin access required) を送出する同期関数。
groups ルートの全エンドポイントがこの依存性を使用する。

```python
def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
```

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
- `UserRepository.scan_by_email_prefix()` - Scan + FilterExpression [FR-7]
- `CardRepository.list_by_owner()` - GSI `CardsByOwner`
- `DashboardRepository.list_by_owner()` - GSI `DashboardsByOwner`
- `DatasetRepository.list_by_owner()` - GSI `DatasetsByOwner`
- `DashboardShareRepository.list_by_dashboard()` - GSI `SharesByDashboard` [FR-7]
- `DashboardShareRepository.list_by_target()` - GSI `SharesByTarget` [FR-7]
- `DashboardShareRepository.find_share()` - dashboard + shared_to_type + shared_to_id で重複検出 [FR-7]
- `GroupRepository.get_by_name()` - GSI `GroupsByName` [FR-7]
- `GroupRepository.list_all()` - Scan [FR-7]

### GroupMemberRepository [FR-7]

BaseRepository を継承しない独自実装。DynamoDB 複合キー (groupId + userId) を使用。

| メソッド | 説明 | 使用インデックス |
|----------|------|-----------------|
| `add_member(group_id, user_id)` | メンバー追加 | PK |
| `remove_member(group_id, user_id)` | メンバー削除 | PK |
| `list_members(group_id)` | グループのメンバー一覧 | PK (Query) |
| `is_member(group_id, user_id)` | メンバー所属判定 | PK (GetItem) |
| `list_groups_for_user(user_id)` | ユーザーの所属グループ一覧 | GSI `MembersByUser` |

## ダッシュボードクローン

`POST /api/dashboards/:id/clone`:
1. ソースダッシュボードを取得
2. 名前に " (Copy)" を追加
3. layout, filters, description をコピー
4. owner_id を現在ユーザーに設定
5. 新規ダッシュボードとして作成

## PermissionService [FR-7]

ダッシュボードへのアクセス権限を判定するサービス (`services/permission_service.py`)。

### 権限レベル

```
PERMISSION_LEVELS = {
    Permission.VIEWER: 1,
    Permission.EDITOR: 2,
    Permission.OWNER:  3,
}
```

### 権限判定フロー (`get_user_permission`)

```
1. dashboard.owner_id == user_id --> Permission.OWNER (即時返却)
2. DashboardShareRepository.list_by_dashboard() で全共有を取得
3. GroupMemberRepository.list_groups_for_user() でユーザーの所属グループを取得
4. 全共有をループ:
   - shared_to_type=USER かつ shared_to_id=user_id --> 該当
   - shared_to_type=GROUP かつ shared_to_id がユーザーの所属グループ --> 該当
5. 該当する共有の中で最高レベルの Permission を返却
6. 該当なし --> None (アクセス不可)
```

### 公開メソッド

| メソッド | 返却値 | 説明 |
|----------|--------|------|
| `get_user_permission(dashboard, user_id, dynamodb)` | Optional[Permission] | 最高権限レベルを取得 |
| `check_permission(dashboard, user_id, required, dynamodb)` | bool | 必要権限以上か判定 |
| `assert_permission(dashboard, user_id, required, dynamodb)` | None / 403 | 権限不足で HTTPException |

## 共有モデル [FR-7]

### DashboardShare (`models/dashboard_share.py`)

| フィールド | 型 | 説明 |
|-----------|-----|------|
| id | str | `share_` + uuid hex[:12] |
| dashboard_id | str | 対象ダッシュボード |
| shared_to_type | SharedToType | "user" or "group" |
| shared_to_id | str | 共有先ユーザー/グループ ID |
| permission | Permission | "viewer", "editor", "owner" |
| shared_by | str | 共有を作成したユーザー ID |
| created_at | datetime | 作成日時 (updated_at なし) |

### Group (`models/group.py`)

| フィールド | 型 | 説明 |
|-----------|-----|------|
| id | str | `group_` + uuid hex[:12] |
| name | str | グループ名 (ユニーク, min_length=1) |
| created_at | datetime | TimestampMixin |
| updated_at | datetime | TimestampMixin |

### GroupMember (`models/group.py`)

| フィールド | 型 | 説明 |
|-----------|-----|------|
| group_id | str | 所属グループ ID |
| user_id | str | メンバーユーザー ID |
| added_at | datetime | 追加日時 |

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

## ルート内ヘルパー関数

| 関数 | ファイル | 用途 |
|------|---------|------|
| `_check_owner_permission(card, user_id)` | routes/cards.py | カードオーナー権限チェック (403) |
| `_get_dashboard_as_owner(dashboard_id, current_user, dynamodb)` | routes/dashboard_shares.py | ダッシュボード存在 + オーナー検証 (404/403) [FR-7] |

dashboards.py, datasets.py はインラインで owner_id チェックを実施。

## セキュリティ

- JWT: HS256, 有効期限 24h (設定可能)
- パスワード: bcrypt 12ラウンド
- パスワードポリシー: 最低8文字, 大文字/小文字/数字/特殊文字必須
- レート制限: ログイン 5回/分 (slowapi)
- CORS: 設定可能 (デフォルト localhost:3000)
- ロールベースアクセス制御: user.role = "admin" | "user", require_admin 依存性で制御 [FR-7]
- ダッシュボード共有権限: VIEWER(1) < EDITOR(2) < OWNER(3) の階層型パーミッション [FR-7]

## 関連コードマップ

- [architecture.md](./architecture.md) - 全体アーキテクチャ
- [frontend.md](./frontend.md) - フロントエンド構造
- [data.md](./data.md) - データモデル詳細
