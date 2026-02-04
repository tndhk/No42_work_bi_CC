# バックエンド コードマップ

最終更新: 2026-02-05 (Audit Log 機能追加 + 既存ルートへの監査ログ統合)
フレームワーク: FastAPI 0.109 / Python 3.11+
エントリポイント: `backend/app/main.py`

---

## ディレクトリ構造

```
backend/
  app/
    __init__.py
    main.py                          # FastAPI アプリ初期化、CORS、レート制限、スケジューラ起動
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
        datasets.py                  # データセット CRUD + CSV/S3 インポート + 再取り込み [FR-1.3]
        filter_views.py              # フィルタビュー (dashboard-scoped)
        filter_view_detail.py        # フィルタビュー詳細 (独立)
        groups.py                    # グループ管理 CRUD + メンバー管理 [FR-7]
        transforms.py                # Transform CRUD + 実行 + 実行履歴 [FR-2.1]
        audit_logs.py                # 監査ログ一覧 (admin専用)
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
      dataset.py                     # Dataset, ColumnSchema, S3ImportRequest,
                                     # ReimportDryRunResponse, ReimportRequest [FR-1.3]
      filter_view.py                 # FilterView, FilterViewCreate, FilterViewUpdate
      group.py                       # Group, GroupCreate, GroupUpdate, GroupMember [FR-7]
      schema_change.py               # SchemaChangeType, SchemaChange, SchemaCompareResult [FR-1.3]
      transform.py                   # Transform, TransformCreate, TransformUpdate [FR-2.1]
      transform_execution.py         # TransformExecution [FR-2.1]
      audit_log.py                   # AuditLog, EventType (12種類)
      user.py                        # User, UserInDB, UserCreate, UserUpdate
    repositories/
      __init__.py
      base.py                        # BaseRepository[T] (Generic CRUD)
      card_repository.py             # CardRepository
      dashboard_repository.py        # DashboardRepository
      dashboard_share_repository.py  # DashboardShareRepository (GSI: SharesByDashboard, SharesByTarget) [FR-7]
      dataset_repository.py          # DatasetRepository
      filter_view_repository.py      # FilterViewRepository (GSI: FilterViewsByDashboard)
      group_repository.py            # GroupRepository (GSI: GroupsByName) [FR-7]
      group_member_repository.py     # GroupMemberRepository (複合キー, GSI: MembersByUser) [FR-7]
      transform_repository.py        # TransformRepository (GSI: TransformsByOwner) [FR-2.1]
      transform_execution_repository.py  # TransformExecutionRepository (複合キー) [FR-2.1]
      audit_log_repository.py        # AuditLogRepository (複合キー, GSI: LogsByUser, LogsByTarget)
      user_repository.py             # UserRepository (+ GSI email検索, scan_by_email_prefix)
    services/
      __init__.py
      card_execution_service.py      # CardExecutionService, CardCacheService
      csv_parser.py                  # CSV パース + エンコーディング検出
      dashboard_service.py           # DashboardService (参照データセット)
      dataset_service.py             # DatasetService (CSV/S3 インポート + プレビュー + 再取り込み) [FR-1.3]
      parquet_storage.py             # ParquetConverter, ParquetReader
      permission_service.py          # PermissionService (VIEWER/EDITOR/OWNER レベル判定) [FR-7]
      schema_comparator.py           # compare_schemas() - スキーマ変更検知 [FR-1.3]
      transform_execution_service.py # TransformExecutionService [FR-2.1]
      transform_scheduler_service.py # TransformSchedulerService (asyncio background) [FR-2.1]
      audit_service.py               # AuditService (fire-and-forget 監査ログ記録)
      type_inferrer.py               # 型推論 (int, float, bool, date, string)
  tests/
    conftest.py                      # 共通フィクスチャ
    core/                            # config, security, logging, password_policy テスト
    models/                          # common, user, dataset, card, dashboard,
                                     # dashboard_share, group, filter_view,
                                     # s3_import, transform, audit_log テスト
    db/                              # dynamodb, s3 テスト
    repositories/                    # base, user, dataset, card, dashboard,
                                     # dashboard_share, group, group_member,
                                     # filter_view, transform, transform_execution,
                                     # audit_log テスト
    services/                        # csv_parser, parquet, dataset, card_execution,
                                     # dashboard, executor_client, type_inferrer,
                                     # permission_service, s3_import_service,
                                     # schema_comparator, transform_execution_service,
                                     # transform_scheduler_service, audit_service テスト
    api/                             # health, deps テスト
      routes/                        # auth, cards, dashboards, datasets, filter_views,
                                     # dashboard_shares, groups, users,
                                     # s3_import, transforms, audit_logs テスト
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
| POST | /api/datasets/s3-import | datasets.s3_import_dataset | S3 CSV インポート | api_response |
| GET | /api/datasets/:id | datasets.get_dataset | データセット詳細 | api_response |
| PUT | /api/datasets/:id | datasets.update_dataset | データセット更新 | api_response |
| DELETE | /api/datasets/:id | datasets.delete_dataset | データセット削除 | 204 No Content |
| GET | /api/datasets/:id/preview | datasets.get_dataset_preview | データプレビュー | api_response |
| GET | /api/datasets/:id/columns/:col/values | datasets.get_column_values | カラムユニーク値 | api_response |
| POST | /api/datasets/:id/reimport/dry-run | datasets.reimport_dry_run | 再取込ドライラン (スキーマ変更検知) [FR-1.3] | api_response |
| POST | /api/datasets/:id/reimport | datasets.reimport_execute | 再取込実行 (force対応) [FR-1.3] | api_response |

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

### フィルタビュー

prefix: `/api/dashboards/{dashboard_id}/filter-views` (dashboard-scoped)

| メソッド | パス | ハンドラ | 認可 | 説明 | レスポンス形式 |
|----------|------|---------|------|------|---------------|
| GET | /api/dashboards/:id/filter-views | filter_views.list_filter_views | VIEWER+ | フィルタビュー一覧 (可視性フィルタ付) | api_response |
| POST | /api/dashboards/:id/filter-views | filter_views.create_filter_view | VIEWER+/EDITOR+ | フィルタビュー作成 (shared=EDITOR必須) | api_response (201) |

prefix: `/api/filter-views` (独立)

| メソッド | パス | ハンドラ | 認可 | 説明 | レスポンス形式 |
|----------|------|---------|------|------|---------------|
| GET | /api/filter-views/:id | filter_view_detail.get_filter_view | owner/VIEWER+ | フィルタビュー詳細 | api_response |
| PUT | /api/filter-views/:id | filter_view_detail.update_filter_view | owner | フィルタビュー更新 (shared変更はEDITOR+) | api_response |
| DELETE | /api/filter-views/:id | filter_view_detail.delete_filter_view | owner | フィルタビュー削除 | 204 No Content |

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

### 監査ログ (Audit Log)

prefix: `/api/audit-logs` (admin only -- require_admin)

| メソッド | パス | ハンドラ | 認可 | 説明 | レスポンス形式 |
|----------|------|---------|------|------|---------------|
| GET | /api/audit-logs | audit_logs.list_audit_logs | admin | 監査ログ一覧 (フィルタ付き) | paginated_response |

フィルタパラメータ: event_type, user_id, target_id, start_date (ISO 8601), end_date (ISO 8601)
GSI 最適化: user_id 指定時は LogsByUser GSI、target_id 指定時は LogsByTarget GSI で Query を実行。

### Transform [FR-2.1]

prefix: `/api/transforms`

| メソッド | パス | ハンドラ | 認可 | 説明 | レスポンス形式 |
|----------|------|---------|------|------|---------------|
| GET | /api/transforms | transforms.list_transforms | authenticated | Transform一覧 (owner別) | paginated_response |
| POST | /api/transforms | transforms.create_transform | authenticated | Transform作成 | api_response (201) |
| GET | /api/transforms/:id | transforms.get_transform | authenticated | Transform詳細 | api_response |
| PUT | /api/transforms/:id | transforms.update_transform | owner | Transform更新 | api_response |
| DELETE | /api/transforms/:id | transforms.delete_transform | owner | Transform削除 | 204 No Content |
| POST | /api/transforms/:id/execute | transforms.execute_transform | owner | Transform手動実行 | api_response |
| GET | /api/transforms/:id/executions | transforms.list_transform_executions | authenticated | 実行履歴一覧 | paginated_response |

ヘルパー: `_check_owner_permission(transform, user_id)` -- Transform オーナー検証 (403)

### ページネーション仕様

一覧エンドポイント (datasets, cards, dashboards, transforms, executions) は共通パラメータ:

| パラメータ | 型 | デフォルト | 制約 |
|-----------|-----|----------|------|
| `limit` | int | 50 (executions: 20) | 1-100 |
| `offset` | int | 0 | >= 0 |

レスポンス: `{ data: [...], pagination: { total, limit, offset, has_next } }`

## モデル一覧

### Transform (`models/transform.py`) [FR-2.1]

| フィールド | 型 | 説明 |
|-----------|-----|------|
| id | str | Transform ID |
| name | str | Transform名 (min_length=1) |
| owner_id | str | オーナーユーザーID |
| input_dataset_ids | list[str] | 入力データセットIDリスト (min_length=1) |
| output_dataset_id | Optional[str] | 出力データセットID (実行後に設定) |
| code | str | Python変換コード (min_length=1) |
| schedule_cron | Optional[str] | cron式 (croniterで検証) |
| schedule_enabled | bool | スケジュール有効フラグ (default: False) |
| created_at | datetime | TimestampMixin |
| updated_at | datetime | TimestampMixin |

TransformCreate: name, input_dataset_ids, code, schedule_cron, schedule_enabled
TransformUpdate: 全フィールド Optional (exclude_unset)

### TransformExecution (`models/transform_execution.py`) [FR-2.1]

| フィールド | 型 | 説明 |
|-----------|-----|------|
| execution_id | str | 実行ID (UUID) |
| transform_id | str | 対応Transform ID |
| status | str | "running" / "success" / "failed" |
| started_at | datetime | 実行開始日時 |
| finished_at | Optional[datetime] | 実行完了日時 |
| duration_ms | Optional[float] | 実行時間 (ミリ秒) |
| output_row_count | Optional[int] | 出力行数 |
| output_dataset_id | Optional[str] | 出力データセットID |
| error | Optional[str] | エラーメッセージ |
| triggered_by | str | "manual" / "schedule" |

### AuditLog (`models/audit_log.py`)

| フィールド | 型 | 説明 |
|-----------|-----|------|
| log_id | str | log_ + uuid hex[:12] |
| timestamp | datetime | イベント発生日時 |
| event_type | EventType | イベント種別 (12種類) |
| user_id | str | 操作実行ユーザーID |
| target_type | str | 対象リソース種別 (user/dataset/dashboard/transform/card/email) |
| target_id | str | 対象リソースID |
| details | dict | 追加詳細情報 |
| request_id | Optional[str] | リクエストトレース用ID |

EventType (12種):
USER_LOGIN, USER_LOGOUT, USER_LOGIN_FAILED,
DASHBOARD_SHARE_ADDED, DASHBOARD_SHARE_REMOVED, DASHBOARD_SHARE_UPDATED,
DATASET_CREATED, DATASET_IMPORTED, DATASET_DELETED,
TRANSFORM_EXECUTED, TRANSFORM_FAILED, CARD_EXECUTION_FAILED

### SchemaChange (`models/schema_change.py`) [FR-1.3]

SchemaChangeType: ADDED, REMOVED, TYPE_CHANGED, NULLABLE_CHANGED
SchemaChange: column_name, change_type, old_value, new_value
SchemaCompareResult: has_changes, changes

### DashboardShare (`models/dashboard_share.py`) [FR-7]

| フィールド | 型 | 説明 |
|-----------|-----|------|
| id | str | `share_` + uuid hex[:12] |
| dashboard_id | str | 対象ダッシュボード |
| shared_to_type | SharedToType | "user" or "group" |
| shared_to_id | str | 共有先ユーザー/グループ ID |
| permission | Permission | "viewer", "editor", "owner" |
| shared_by | str | 共有を作成したユーザー ID |
| created_at | datetime | 作成日時 (updated_at なし) |

### Group / GroupMember (`models/group.py`) [FR-7]

Group: id, name, created_at, updated_at
GroupMember: group_id, user_id, added_at

### FilterView (`models/filter_view.py`)

| フィールド | 型 | 説明 |
|-----------|-----|------|
| id | str | `fv_` + uuid hex[:12] |
| dashboard_id | str | 対象ダッシュボードID |
| name | str | ビュー名 |
| owner_id | str | オーナーユーザーID |
| filter_state | dict[str, Any] | フィルタ状態 |
| is_shared | bool | 共有フラグ (default: False) |
| is_default | bool | デフォルトフラグ (default: False) |
| created_at | datetime | TimestampMixin |
| updated_at | datetime | TimestampMixin |

### Dataset (`models/dataset.py`)

主要フィールド: id, name, source_type (`csv` / `s3_csv` / `transform`), row_count, columns (alias: schema),
owner_id, s3_path, source_config, last_import_at, last_import_by
関連モデル: ColumnSchema, DatasetCreate, DatasetUpdate, S3ImportRequest, ReimportDryRunResponse, ReimportRequest

## 依存関係グラフ

```
main.py
  +-- core/config.py (settings)
  +-- core/logging.py (setup_logging)
  +-- services/transform_scheduler_service.py (条件付き起動: scheduler_enabled)  [FR-2.1]
  +-- api/routes/__init__.py (api_router)
        +-- routes/auth.py
        |     +-- api/deps.py (get_current_user)
        |     +-- api/response.py (api_response)
        |     +-- core/security.py
        |     +-- repositories/user_repository.py
        |     +-- models/user.py
        |     +-- services/audit_service.py
        +-- routes/cards.py
        |     +-- api/deps.py (get_current_user)
        |     +-- api/response.py (api_response, paginated_response)
        |     +-- models/card.py, user.py
        |     +-- repositories/card_repository.py, dataset_repository.py
        |     +-- services/card_execution_service.py
        |     +-- services/audit_service.py
        |     +-- core/config.py
        +-- routes/dashboards.py
        |     +-- api/deps.py (get_current_user)
        |     +-- api/response.py (api_response, paginated_response)
        |     +-- models/dashboard.py, user.py
        |     +-- repositories/dashboard_repository.py
        |     +-- services/dashboard_service.py
        +-- routes/datasets.py
        |     +-- api/deps.py (get_current_user, get_s3_client)
        |     +-- api/response.py (api_response, paginated_response)
        |     +-- models/dataset.py (Dataset, DatasetUpdate, S3ImportRequest,
        |     |                      ReimportDryRunResponse, ReimportRequest), user.py
        |     +-- repositories/dataset_repository.py
        |     +-- services/dataset_service.py
        |     +-- services/audit_service.py
        +-- routes/filter_views.py
        |     +-- api/deps.py (get_current_user)
        |     +-- api/response.py (api_response)
        |     +-- models/filter_view.py, dashboard_share.py (Permission), user.py
        |     +-- repositories/dashboard_repository.py, filter_view_repository.py
        |     +-- services/permission_service.py
        +-- routes/filter_view_detail.py
        |     +-- api/deps.py (get_current_user)
        |     +-- api/response.py (api_response)
        |     +-- models/filter_view.py, dashboard_share.py (Permission), user.py
        |     +-- repositories/dashboard_repository.py, filter_view_repository.py
        |     +-- services/permission_service.py
        +-- routes/dashboard_shares.py  [FR-7]
        |     +-- api/deps.py (get_current_user)
        |     +-- api/response.py (api_response)
        |     +-- models/user.py, dashboard_share.py
        |     +-- repositories/dashboard_repository.py
        |     +-- repositories/dashboard_share_repository.py
        |     +-- services/audit_service.py
        +-- routes/groups.py  [FR-7]
        |     +-- api/deps.py (require_admin)
        |     +-- api/response.py (api_response)
        |     +-- models/user.py, group.py
        |     +-- repositories/group_repository.py
        |     +-- repositories/group_member_repository.py
        +-- routes/users.py  [FR-7]
        |     +-- api/deps.py (get_current_user)
        |     +-- api/response.py (api_response)
        |     +-- models/user.py
        |     +-- repositories/user_repository.py
        +-- routes/transforms.py  [FR-2.1]
        |     +-- api/deps.py (get_current_user, get_dynamodb_resource, get_s3_client)
        |     +-- api/response.py (api_response, paginated_response)
        |     +-- models/transform.py (Transform, TransformCreate, TransformUpdate), user.py
        |     +-- repositories/transform_repository.py
        |     +-- repositories/transform_execution_repository.py
        |     +-- services/transform_execution_service.py
        |     +-- services/audit_service.py
        +-- routes/audit_logs.py
              +-- api/deps.py (require_admin)
              +-- api/response.py (paginated_response)
              +-- models/audit_log.py (EventType)
              +-- repositories/audit_log_repository.py
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

repositories/*_repository.py (card, dashboard, dataset, user, dashboard_share,
                               group, filter_view, transform)
  +-- repositories/base.py (BaseRepository)
  +-- core/config.py (table_prefix)
  +-- models/*

repositories/group_member_repository.py  [FR-7]
  +-- core/config.py (table_prefix)
  +-- models/group.py (GroupMember)
  -- BaseRepository を継承しない (複合キー groupId + userId)

repositories/transform_execution_repository.py  [FR-2.1]
  +-- repositories/base.py (BaseRepository -- 部分的にオーバーライド)
  +-- core/config.py (table_prefix)
  +-- models/transform_execution.py
  -- 複合キー: transformId (PK) + startedAt (SK)
  -- create/update_status/list_by_transform/has_running_execution をカスタム実装
  -- _from_dynamodb_item オーバーライド (timestamp/Decimal変換)

repositories/audit_log_repository.py
  +-- repositories/base.py (BaseRepository -- 部分的にオーバーライド)
  +-- core/config.py (table_prefix)
  +-- models/audit_log.py (AuditLog, EventType)
  -- 複合キー: logId (PK) + timestamp (SK)
  -- create オーバーライド (自動タイムスタンプなし)
  -- _from_dynamodb_item オーバーライド (timestamp/Decimal変換)
  -- list_all: Scan + FilterExpression (event_type/start_date/end_date)
  -- list_by_user: GSI LogsByUser (userId + timestamp SK, ScanIndexForward=False)
  -- list_by_target: GSI LogsByTarget (targetId + timestamp SK, ScanIndexForward=False)
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
  +-- services/schema_comparator.py (compare_schemas)  [FR-1.3]
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

services/schema_comparator.py  [FR-1.3]
  +-- models/dataset.py (ColumnSchema)
  +-- models/schema_change.py (SchemaChange, SchemaChangeType, SchemaCompareResult)

services/transform_execution_service.py  [FR-2.1]
  +-- core/config.py (executor_url, transform_timeout_seconds)
  +-- httpx (Executor HTTP呼び出し: POST /execute/transform)
  +-- pandas (DataFrame変換)
  +-- models/transform.py (Transform)
  +-- models/dataset.py (ColumnSchema)
  +-- repositories/dataset_repository.py
  +-- repositories/transform_repository.py
  +-- repositories/transform_execution_repository.py
  +-- services/parquet_storage.py (ParquetConverter, ParquetReader)

services/transform_scheduler_service.py  [FR-2.1]
  +-- core/config.py (scheduler_enabled, scheduler_interval_seconds)
  +-- aioboto3 (自前でDynamoDB/S3セッション生成)
  +-- croniter (cron式評価)
  +-- repositories/transform_repository.py
  +-- repositories/transform_execution_repository.py
  +-- services/transform_execution_service.py

services/audit_service.py
  +-- models/audit_log.py (AuditLog, EventType)
  +-- repositories/audit_log_repository.py
  -- fire-and-forget: 例外は握りつぶし (ビジネスロジック非干渉)

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
- `FilterViewRepository.list_by_dashboard()` - GSI `FilterViewsByDashboard`
- `DashboardShareRepository.list_by_dashboard()` - GSI `SharesByDashboard` [FR-7]
- `DashboardShareRepository.list_by_target()` - GSI `SharesByTarget` [FR-7]
- `DashboardShareRepository.find_share()` - dashboard + shared_to_type + shared_to_id で重複検出 [FR-7]
- `GroupRepository.get_by_name()` - GSI `GroupsByName` [FR-7]
- `GroupRepository.list_all()` - Scan [FR-7]
- `TransformRepository.list_by_owner()` - GSI `TransformsByOwner` [FR-2.1]

### GroupMemberRepository [FR-7]

BaseRepository を継承しない独自実装。DynamoDB 複合キー (groupId + userId) を使用。

| メソッド | 説明 | 使用インデックス |
|----------|------|-----------------|
| `add_member(group_id, user_id)` | メンバー追加 | PK |
| `remove_member(group_id, user_id)` | メンバー削除 | PK |
| `list_members(group_id)` | グループのメンバー一覧 | PK (Query) |
| `is_member(group_id, user_id)` | メンバー所属判定 | PK (GetItem) |
| `list_groups_for_user(user_id)` | ユーザーの所属グループ一覧 | GSI `MembersByUser` |

### TransformExecutionRepository [FR-2.1]

BaseRepository を継承するがカスタム実装多数。DynamoDB 複合キー (transformId PK + startedAt SK)。

| メソッド | 説明 | 備考 |
|----------|------|------|
| `create(data, dynamodb)` | 実行レコード作成 | auto-timestamp なし、started_at を直接使用 |
| `update_status(transform_id, started_at, updates, dynamodb)` | ステータス更新 | 複合キーで特定 |
| `list_by_transform(transform_id, dynamodb, limit=20)` | 実行履歴一覧 | ScanIndexForward=False (新しい順) |
| `has_running_execution(transform_id, dynamodb)` | 実行中チェック | 直近5件を確認 |

`_from_dynamodb_item` オーバーライド: startedAt/finishedAt のタイムスタンプ変換、Decimal→int/float 変換

## Transform 実行フロー [FR-2.1]

### 手動実行 (POST /api/transforms/:id/execute)

```
routes/transforms.py -> TransformExecutionService.execute()

1. TransformExecutionRepository.create() -- status="running" レコード作成
2. DatasetRepository.get_by_id() x N -- 入力データセット取得
3. ParquetReader.read_full() x N -- S3 から Parquet 読み込み
4. _execute_with_retry() -- Executor API (POST /execute/transform) 呼び出し
   - datasets_payload: [{ data: [...records], columns: [...] }, ...]
   - リトライ: 5xx/接続エラー -> 指数バックオフ (0.5s * 2^n, 最大3回)
   - 4xx -> 即座に RuntimeError
5. pd.DataFrame(result["data"]) -- 結果をDataFrame化
6. ParquetConverter.convert_and_save() -- S3 に Parquet 保存
7. DatasetRepository.create() -- 出力 Dataset レコード作成 (source_type="transform")
8. TransformRepository.update() -- output_dataset_id を更新
9. TransformExecutionRepository.update_status() -- status="success" に更新
   (例外時: status="failed", error=str(e))
```

返却値: TransformExecutionResult(execution_id, output_dataset_id, row_count, column_names, execution_time_ms)

### スケジュール実行 (TransformSchedulerService)

```
main.py (lifespan) --> scheduler_enabled=true の場合のみ起動

TransformSchedulerService
  start() --> asyncio.create_task(_run_loop)
  stop()  --> cancel + await

_run_loop:
  while _running:
    _check_and_execute()     # 自前で aioboto3 セッション生成
    sleep(scheduler_interval_seconds)

_execute_due_transforms:
  1. Scan: scheduleEnabled=true のTransformを全件取得
  2. 各Transformに対して:
     a. schedule_cron が未設定 -> skip
     b. _is_due(cron, now) == false -> skip
        (前回実行時刻からの差分 < scheduler_interval_seconds で判定)
     c. has_running_execution() == true -> skip (重複防止)
     d. TransformExecutionService.execute(triggered_by="schedule")
```

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

## データセット再取り込みフロー [FR-1.3]

```
reimport_dry_run:
  1. DatasetRepository.get_by_id() -- 既存データセット取得
  2. source_type != "s3_csv" -> 422 エラー
  3. source_config から s3_bucket/s3_key 取得
  4. S3 から CSV 再取得 -> parse_full() + infer_schema()
  5. compare_schemas(old_schema, new_schema) -- スキーマ差分検出
  6. 返却: has_schema_changes, changes, new_row_count, new_column_count

reimport_execute:
  1-5. dry_run と同様
  6. has_changes=true かつ force=false -> 422 エラー
  7. ParquetConverter.convert_and_save() -- S3 上書き
  8. DatasetRepository.create() -- メタデータ上書き (put_item)
```

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

## ルート内ヘルパー関数

| 関数 | ファイル | 用途 |
|------|---------|------|
| `_check_owner_permission(card, user_id)` | routes/cards.py | カードオーナー権限チェック (403) |
| `_check_owner_permission(transform, user_id)` | routes/transforms.py | Transformオーナー権限チェック (403) [FR-2.1] |
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

## Settings (core/config.py)

| 設定キー | デフォルト | 説明 |
|----------|----------|------|
| env | "local" | 環境名 |
| api_host / api_port | 0.0.0.0:8000 | APIサーバー |
| jwt_secret_key | dev-secret-... | JWT署名鍵 |
| jwt_algorithm | HS256 | JWTアルゴリズム |
| jwt_expiration_hours | 24 | JWTトークン有効期限 |
| dynamodb_endpoint | None | DynamoDBエンドポイント (localstack用) |
| dynamodb_region | ap-northeast-1 | DynamoDBリージョン |
| dynamodb_table_prefix | bi_ | テーブル名プレフィックス |
| s3_endpoint | None | S3エンドポイント (localstack用) |
| s3_region | ap-northeast-1 | S3リージョン |
| s3_bucket_datasets | bi-datasets | データセット用S3バケット |
| s3_access_key / s3_secret_key | None | S3認証情報 |
| cors_origins | ["http://localhost:3000"] | CORS許可オリジン |
| max_upload_size_bytes | 104857600 (100MB) | アップロード上限 |
| executor_url | http://localhost:8001 | Executor APIベースURL |
| executor_timeout_seconds | 10 | Executorタイムアウト (カード用) |
| transform_timeout_seconds | 300 (5分) | Executorタイムアウト (Transform用) [FR-2.1] |
| cache_ttl_seconds | 3600 | カード実行キャッシュTTL |
| scheduler_enabled | False | Transformスケジューラ有効化 [FR-2.1] |
| scheduler_interval_seconds | 60 | スケジューラチェック間隔 [FR-2.1] |

## 外部依存パッケージ

### 本番

| パッケージ | バージョン | 用途 |
|-----------|----------|------|
| fastapi | 0.109.0 | Webフレームワーク |
| uvicorn | 0.27.0 | ASGIサーバー |
| pydantic | 2.5.0 | データバリデーション |
| pydantic-settings | 2.1.0 | 環境変数設定 |
| structlog | 24.1.0 | 構造化ログ |
| aioboto3 | 12.3.0 | 非同期 AWS SDK (DynamoDB, S3) |
| pyarrow | 15.0.0 | Parquet 読み書き |
| pandas | 2.2.0 | データ操作 |
| chardet | 5.2.0 | エンコーディング検出 |
| python-jose | 3.3.0 | JWT トークン |
| bcrypt | 4.1.3 | パスワードハッシュ |
| slowapi | 0.1.9 | レート制限 |
| python-multipart | 0.0.22 | ファイルアップロード |
| croniter | >=2.0.0 | cron式パース/評価 [FR-2.1] |

### 開発

| パッケージ | バージョン | 用途 |
|-----------|----------|------|
| pytest | 7.4.3 | テストフレームワーク |
| pytest-asyncio | 0.21.1 | 非同期テスト |
| pytest-cov | 4.1.0 | カバレッジ |
| httpx | 0.25.2 | テスト用HTTPクライアント / Executor呼び出し |
| respx | 0.20.2 | httpxモック |
| moto | 5.0.0 | AWSサービスモック |
| ruff | 0.1.9 | リンター/フォーマッタ |
| mypy | 1.8.0 | 型チェック |

## DynamoDB テーブル一覧

| テーブル名 | PK | SK | GSI |
|-----------|-----|-----|-----|
| bi_users | userId | - | UsersByEmail |
| bi_datasets | datasetId | - | DatasetsByOwner |
| bi_cards | cardId | - | CardsByOwner |
| bi_dashboards | dashboardId | - | DashboardsByOwner |
| bi_filter_views | filterViewId | - | FilterViewsByDashboard |
| bi_dashboard_shares | shareId | - | SharesByDashboard, SharesByTarget |
| bi_groups | groupId | - | GroupsByName |
| bi_group_members | groupId | userId | MembersByUser |
| bi_transforms | transformId | - | TransformsByOwner [FR-2.1] |
| bi_transform_executions | transformId | startedAt | - [FR-2.1] |
| bi_audit_logs | logId | timestamp | LogsByUser, LogsByTarget |

## 関連コードマップ

- [architecture.md](./architecture.md) - 全体アーキテクチャ
- [frontend.md](./frontend.md) - フロントエンド構造
- [data.md](./data.md) - データモデル詳細
