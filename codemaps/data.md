# データモデルとスキーマ コードマップ

最終更新: 2026-02-05 17:00 JST (Codemap refresh)
データベース: DynamoDB (NoSQL) + S3 (Parquet)

---

## DynamoDB テーブル一覧

テーブルプレフィックス: `bi_` (設定可能)
BillingMode: PAY_PER_REQUEST (全テーブル)
テーブル総数: 11

| テーブル名 | PK | SK | GSI | 用途 |
|-----------|-----|-----|-----|------|
| bi_users | userId (S) | - | UsersByEmail (email) | ユーザー |
| bi_datasets | datasetId (S) | - | DatasetsByOwner (ownerId + createdAt) | データセット |
| bi_cards | cardId (S) | - | CardsByOwner (ownerId + createdAt) | カード |
| bi_dashboards | dashboardId (S) | - | DashboardsByOwner (ownerId + createdAt) | ダッシュボード |
| bi_filter_views | filterViewId (S) | - | FilterViewsByDashboard (dashboardId + createdAt) | フィルタービュー |
| bi_transforms | transformId (S) | - | TransformsByOwner (ownerId) | Transform定義 [FR-2.1] |
| bi_transform_executions | transformId (S) | startedAt (N) | - (GSI なし) | Transform実行履歴 [FR-2.1] |
| bi_groups | groupId (S) | - | GroupsByName (name) | グループ [FR-7] |
| bi_group_members | groupId (S) | userId (S) | MembersByUser (userId) | グループメンバー [FR-7] |
| bi_dashboard_shares | shareId (S) | - | SharesByDashboard (dashboardId), SharesByTarget (sharedToId) | ダッシュボード共有 [FR-7] |
| bi_audit_logs | logId (S) | timestamp (N) | LogsByUser (userId + timestamp), LogsByTarget (targetId + timestamp) | 監査ログ |

---

## DynamoDB スキーマ詳細

### bi_users

| 属性 | 型 | DynamoDB型 | 説明 |
|------|-----|-----------|------|
| userId | PK | S | UUID |
| email | GSI-PK | S | メールアドレス (一意) |
| hashedPassword | - | S | bcrypt ハッシュ |
| role | - | S | ロール ("user" / "admin", デフォルト "user") |
| createdAt | - | N | UNIX タイムスタンプ |
| updatedAt | - | N | UNIX タイムスタンプ |

GSI: `UsersByEmail` (PK: email, Projection: ALL)

### bi_datasets

| 属性 | 型 | DynamoDB型 | 説明 |
|------|-----|-----------|------|
| datasetId | PK | S | ds_XXXXXXXXXXXX 形式 |
| name | - | S | 表示名 |
| description | - | S | 説明 (nullable) |
| sourceType | - | S | "csv" |
| rowCount | - | N | 行数 |
| columnCount | - | N | 列数 |
| schema | - | L(M) | ColumnSchema のリスト |
| ownerId | GSI-PK | S | オーナー ID |
| s3Path | - | S | S3 パス |
| partitionColumn | - | S | パーティション列名 (nullable) |
| sourceConfig | - | M | ソース設定 (nullable) |
| lastImportAt | - | N | 最終インポート日時 |
| lastImportBy | - | S | 最終インポートユーザー |
| createdAt | GSI-SK | N | UNIX タイムスタンプ |
| updatedAt | - | N | UNIX タイムスタンプ |

GSI: `DatasetsByOwner` (PK: ownerId, SK: createdAt, Projection: ALL)

### bi_cards

| 属性 | 型 | DynamoDB型 | 説明 |
|------|-----|-----------|------|
| cardId | PK | S | UUID |
| name | - | S | 表示名 |
| code | - | S | Python コード |
| description | - | S | 説明 (nullable) |
| datasetId | - | S | 対象データセット ID (nullable) |
| datasetIds | - | L(S) | 複数データセット ID (nullable) |
| params | - | M | カードパラメータ (nullable) |
| usedColumns | - | L(S) | 使用列 (nullable) |
| filterApplicable | - | BOOL | フィルタ適用可否 (nullable) |
| ownerId | GSI-PK | S | オーナー ID |
| createdAt | GSI-SK | N | UNIX タイムスタンプ |
| updatedAt | - | N | UNIX タイムスタンプ |

GSI: `CardsByOwner` (PK: ownerId, SK: createdAt, Projection: ALL)

### bi_dashboards

| 属性 | 型 | DynamoDB型 | 説明 |
|------|-----|-----------|------|
| dashboardId | PK | S | UUID |
| name | - | S | 表示名 |
| description | - | S | 説明 (nullable) |
| layout | - | L(M) | LayoutItem のリスト |
| filters | - | L(M) | FilterDefinition のリスト |
| defaultFilterViewId | - | S | デフォルトフィルタービュー (nullable) |
| ownerId | GSI-PK | S | オーナー ID |
| createdAt | GSI-SK | N | UNIX タイムスタンプ |
| updatedAt | - | N | UNIX タイムスタンプ |

GSI: `DashboardsByOwner` (PK: ownerId, SK: createdAt, Projection: ALL)

### bi_filter_views

| 属性 | 型 | DynamoDB型 | 説明 |
|------|-----|-----------|------|
| filterViewId | PK | S | UUID |
| dashboardId | GSI-PK | S | 対象ダッシュボード ID |
| name | - | S | ビュー名 |
| ownerId | - | S | 作成者 ID |
| filterState | - | M | フィルタ状態 |
| isShared | - | BOOL | 共有フラグ |
| isDefault | - | BOOL | デフォルトフラグ |
| createdAt | GSI-SK | N | UNIX タイムスタンプ |
| updatedAt | - | N | UNIX タイムスタンプ |

GSI: `FilterViewsByDashboard` (PK: dashboardId, SK: createdAt, Projection: ALL)

### bi_transforms [FR-2.1]

| 属性 | 型 | DynamoDB型 | 説明 |
|------|-----|-----------|------|
| transformId | PK | S | UUID |
| name | - | S | Transform名 |
| ownerId | GSI-PK | S | オーナー ID |
| inputDatasetIds | - | L(S) | 入力データセット ID のリスト (1つ以上) |
| outputDatasetId | - | S | 出力データセット ID (nullable, 実行後に設定) |
| code | - | S | Python 変換コード |
| scheduleCron | - | S | cronスケジュール式 (nullable) |
| scheduleEnabled | - | BOOL | スケジュール実行有効フラグ (デフォルト false) |
| createdAt | - | N | UNIX タイムスタンプ |
| updatedAt | - | N | UNIX タイムスタンプ |

GSI: `TransformsByOwner` (PK: ownerId, Projection: ALL)

### bi_transform_executions [FR-2.1]

複合キーテーブル (transformId + startedAt)。GSI なし。

| 属性 | 型 | DynamoDB型 | 説明 |
|------|-----|-----------|------|
| transformId | PK | S | Transform ID |
| startedAt | SK | N | 実行開始 UNIX タイムスタンプ |
| executionId | - | S | UUID (実行ごとの一意 ID) |
| status | - | S | "running" / "success" / "failed" |
| finishedAt | - | N | 実行完了 UNIX タイムスタンプ (nullable) |
| durationMs | - | N | 実行時間(ms) (nullable) |
| outputRowCount | - | N | 出力行数 (nullable) |
| outputDatasetId | - | S | 出力データセット ID (nullable) |
| error | - | S | エラーメッセージ (nullable, failed時) |
| triggeredBy | - | S | "manual" / "schedule" |

クエリパターン: transformId で PK 指定 + startedAt 降順 (ScanIndexForward=False) で最新実行を取得

### bi_audit_logs

複合キーテーブル (logId + timestamp)。GSI 2つ。

| 属性 | 型 | DynamoDB型 | 説明 |
|------|-----|-----------|------|
| logId | PK | S | log_ + uuid hex[:12] |
| timestamp | SK | N | イベント発生 UNIX タイムスタンプ |
| eventType | - | S | EventType 列挙値 (12種) |
| userId | GSI-PK | S | 操作実行ユーザーID |
| targetType | - | S | 対象リソース種別 |
| targetId | GSI-PK | S | 対象リソースID |
| details | - | M | 追加詳細情報 |
| requestId | - | S | リクエストトレース用ID (nullable) |

GSI-1: `LogsByUser` (PK: userId, SK: timestamp, Projection: ALL)
GSI-2: `LogsByTarget` (PK: targetId, SK: timestamp, Projection: ALL)

クエリパターン:
- userId で PK 指定 + timestamp 降順 (ScanIndexForward=False) で最新ログを取得
- targetId で PK 指定 + timestamp 降順 で特定リソースのログを取得
- 全件 Scan + FilterExpression (eventType, start_date, end_date)

### bi_groups [FR-7]

| 属性 | 型 | DynamoDB型 | 説明 |
|------|-----|-----------|------|
| groupId | PK | S | UUID |
| name | GSI-PK | S | グループ名 (一意) |
| createdAt | - | N | UNIX タイムスタンプ |
| updatedAt | - | N | UNIX タイムスタンプ |

GSI: `GroupsByName` (PK: name, Projection: ALL)

### bi_group_members [FR-7]

| 属性 | 型 | DynamoDB型 | 説明 |
|------|-----|-----------|------|
| groupId | PK | S | グループ ID |
| userId | SK / GSI-PK | S | ユーザー ID (複合キー) |
| addedAt | - | N | UNIX タイムスタンプ |

PK + SK の複合キーテーブル (groupId + userId)
GSI: `MembersByUser` (PK: userId, Projection: ALL)

### bi_dashboard_shares [FR-7]

| 属性 | 型 | DynamoDB型 | 説明 |
|------|-----|-----------|------|
| shareId | PK | S | UUID |
| dashboardId | GSI-PK | S | 共有対象ダッシュボード ID |
| sharedToType | - | S | "user" または "group" |
| sharedToId | GSI-PK | S | 共有先ユーザー/グループ ID |
| permission | - | S | "owner" / "editor" / "viewer" |
| sharedBy | - | S | 共有実行ユーザー ID |
| createdAt | - | N | UNIX タイムスタンプ |

GSI-1: `SharesByDashboard` (PK: dashboardId, Projection: ALL)
GSI-2: `SharesByTarget` (PK: sharedToId, Projection: ALL)

---

## S3 ストレージ

バケット: `bi-datasets`

```
bi-datasets/
  datasets/{datasetId}/
    data/
      part-0000.parquet              # 非パーティション
    partitions/
      {column}={value}/
        part-0000.parquet            # パーティション分割
```

フォーマット: Apache Parquet (Snappy 圧縮)

Transform 実行時: 出力は新しい datasetId として `datasets/{newDatasetId}/data/` に保存される。

---

## Pydantic モデル (Backend)

### common.py

```python
class BaseResponse:
    success: bool
    data: Any | None
    error: str | None

class TimestampMixin:
    created_at: datetime   # default: now(UTC)
    updated_at: datetime   # default: now(UTC)
```

### user.py

```python
class UserCreate:
    email: EmailStr
    password: str          # min 8, 大文字/小文字/数字/特殊文字

class UserInDB:            # DB保存用 (hashedPassword含む)
    id: str
    email: str
    hashed_password: str
    role: str = "user"     # "user" / "admin"
    created_at: datetime
    updated_at: datetime

class User:                # 公開用 (hashedPassword除外)
    id: str
    email: str
    role: str = "user"     # "user" / "admin"
    created_at: datetime
    updated_at: datetime

class UserUpdate:
    password: str | None   # バリデーション付き
```

### dataset.py

```python
class ColumnSchema:
    name: str
    data_type: str         # int64, float64, bool, date, datetime, string
    nullable: bool
    description: str | None

class DatasetCreate:
    name: str
    description: str | None
    source_type: str
    partition_column: str | None

class DatasetUpdate:
    name: str | None
    description: str | None
    partition_column: str | None

class Dataset(TimestampMixin):
    id: str
    name: str
    description: str | None
    source_type: str
    row_count: int
    columns: list[ColumnSchema]   # alias="schema"
    owner_id: str | None
    s3_path: str | None
    partition_column: str | None
    source_config: dict | None
    column_count: int
    last_import_at: datetime | None
    last_import_by: str | None
```

### card.py

```python
class CardCreate:
    name: str
    code: str
    description: str | None
    dataset_ids: list[str] | None
    dataset_id: str | None
    params: dict | None

class CardUpdate:
    name: str | None
    code: str | None
    description: str | None
    dataset_ids: list[str] | None
    dataset_id: str | None
    params: dict | None

class Card(TimestampMixin):
    id: str
    name: str
    code: str
    description: str | None
    dataset_ids: list[str] | None
    dataset_id: str | None
    params: dict | None
    used_columns: list[str] | None
    filter_applicable: bool | None
    owner_id: str | None
```

### dashboard.py

```python
class FilterDefinition:
    id: str
    type: str
    column: str
    label: str
    multi_select: bool = False
    options: list[str] | None = None    # カテゴリフィルタ選択肢

class LayoutItem:
    card_id: str
    x: int (>= 0)
    y: int (>= 0)
    w: int (>= 1)
    h: int (>= 1)

class DashboardCreate:
    name: str
    description: str | None
    layout: list[LayoutItem] | None
    filters: list[FilterDefinition] | None

class DashboardUpdate:
    name: str | None
    description: str | None
    layout: list[LayoutItem] | None
    filters: list[FilterDefinition] | None

class Dashboard(TimestampMixin):
    id: str
    name: str
    description: str | None
    layout: list[LayoutItem] | None
    owner_id: str | None
    filters: list[FilterDefinition] | None
    default_filter_view_id: str | None
```

### filter_view.py

```python
class FilterViewCreate:
    name: str              # min_length=1, 空白バリデーション
    filter_state: dict[str, Any]
    is_shared: bool = False
    is_default: bool = False

class FilterViewUpdate:
    name: str | None       # min_length=1, 空白バリデーション
    filter_state: dict[str, Any] | None
    is_shared: bool | None
    is_default: bool | None

class FilterView(TimestampMixin):
    id: str
    dashboard_id: str
    name: str
    owner_id: str
    filter_state: dict[str, Any]
    is_shared: bool = False
    is_default: bool = False
```

### transform.py [FR-2.1]

```python
class TransformCreate:
    name: str              # min_length=1, 空白バリデーション
    input_dataset_ids: list[str]  # min_length=1
    code: str              # min_length=1, 空白バリデーション
    schedule_cron: str | None     # croniter バリデーション
    schedule_enabled: bool = False

class TransformUpdate:
    name: str | None       # min_length=1, 空白バリデーション
    input_dataset_ids: list[str] | None  # min_length=1
    code: str | None       # min_length=1, 空白バリデーション
    schedule_cron: str | None     # croniter バリデーション
    schedule_enabled: bool | None

class Transform(TimestampMixin):
    id: str
    name: str
    owner_id: str
    input_dataset_ids: list[str]  # min_length=1
    output_dataset_id: str | None
    code: str
    schedule_cron: str | None
    schedule_enabled: bool = False
```

### transform_execution.py [FR-2.1]

```python
class TransformExecution:
    execution_id: str
    transform_id: str
    status: str            # "running" | "success" | "failed"
    started_at: datetime
    finished_at: datetime | None
    duration_ms: float | None
    output_row_count: int | None
    output_dataset_id: str | None
    error: str | None
    triggered_by: str      # "manual" | "schedule"
```

### schema_change.py [FR-1.3]

```python
class SchemaChangeType(str, Enum):
    ADDED = "added"
    REMOVED = "removed"
    TYPE_CHANGED = "type_changed"
    NULLABLE_CHANGED = "nullable_changed"

class SchemaChange:
    column_name: str
    change_type: SchemaChangeType
    old_value: str | None
    new_value: str | None

class SchemaCompareResult:
    has_changes: bool
    changes: list[SchemaChange]
```

### audit_log.py

```python
class EventType(str, Enum):
    USER_LOGIN = "USER_LOGIN"
    USER_LOGOUT = "USER_LOGOUT"
    USER_LOGIN_FAILED = "USER_LOGIN_FAILED"
    DASHBOARD_SHARE_ADDED = "DASHBOARD_SHARE_ADDED"
    DASHBOARD_SHARE_REMOVED = "DASHBOARD_SHARE_REMOVED"
    DASHBOARD_SHARE_UPDATED = "DASHBOARD_SHARE_UPDATED"
    DATASET_CREATED = "DATASET_CREATED"
    DATASET_IMPORTED = "DATASET_IMPORTED"
    DATASET_DELETED = "DATASET_DELETED"
    TRANSFORM_EXECUTED = "TRANSFORM_EXECUTED"
    TRANSFORM_FAILED = "TRANSFORM_FAILED"
    CARD_EXECUTION_FAILED = "CARD_EXECUTION_FAILED"

class AuditLog:
    log_id: str
    timestamp: datetime
    event_type: EventType
    user_id: str
    target_type: str
    target_id: str
    details: dict = {}
    request_id: str | None = None
```

### dashboard_share.py [FR-7]

```python
class Permission(str, Enum):
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"

class SharedToType(str, Enum):
    USER = "user"
    GROUP = "group"

class DashboardShare:
    id: str
    dashboard_id: str
    shared_to_type: SharedToType
    shared_to_id: str
    permission: Permission
    shared_by: str
    created_at: datetime

class DashboardShareCreate:
    shared_to_type: SharedToType
    shared_to_id: str
    permission: Permission

class DashboardShareUpdate:
    permission: Permission
```

### group.py [FR-7]

```python
class Group(TimestampMixin):
    id: str
    name: str

class GroupCreate:
    name: str              # min_length=1, 空白バリデーション

class GroupUpdate:
    name: str | None       # min_length=1, 空白バリデーション

class GroupMember:
    group_id: str
    user_id: str
    added_at: datetime
```

---

## APIレスポンスヘルパー (Backend)

```python
# api/response.py
def api_response(data: Any) -> Dict[str, Any]:
    """{ "data": T }"""

def paginated_response(items, total, limit, offset) -> Dict[str, Any]:
    """{ "data": [...], "pagination": { "total", "limit", "offset", "has_next" } }"""
```

全ルートの返却値をこれらのヘルパーでラップし、
Frontend の `ApiResponse<T>` / `PaginatedResponse<T>` 型と構造を統一。

---

## Executor モデル

### api_models.py

```python
class ExecuteCardRequest:
    card_id: str
    code: str
    dataset_id: str
    filters: dict = {}
    params: dict = {}
    dataset_rows: list[dict] | None   # 将来拡張用

class ExecuteCardResponse:
    html: str
    used_columns: list[str] = []
    filter_applicable: list[str] = []
    execution_time_ms: int

class ExecuteErrorResponse:
    error: str
    detail: str | None
```

### models.py

```python
@dataclass
class HTMLResult:
    html: str
    used_columns: list[str] = []
    filter_applicable: list[str] = []
```

---

## TypeScript 型定義 (Frontend)

### api.ts

```typescript
interface ApiResponse<T> { data: T; meta?: { request_id: string } }
interface ApiErrorResponse { error: { code: string; message: string; details?: Record<string, unknown> } }
interface PaginatedResponse<T> { data: T[]; pagination: Pagination }
interface Pagination { total: number; limit: number; offset: number; has_next: boolean }
interface PaginationParams { limit?: number; offset?: number }
```

### user.ts

```typescript
interface User { user_id: string; email: string; name?: string; role?: string; created_at: string }
interface UserWithGroups extends User { groups: GroupRef[] }
interface GroupRef { group_id: string; name: string }
interface LoginRequest { email: string; password: string }
interface LoginResponse { access_token: string; token_type: string; expires_in: number; user: User }
```

### dataset.ts

```typescript
interface ColumnSchema { name: string; type: string; nullable: boolean }
interface OwnerRef { user_id: string; name: string }
interface Dataset { dataset_id: string; name: string; source_type: string; row_count: number; column_count: number; owner: OwnerRef; created_at: string; last_import_at?: string }
interface DatasetDetail extends Dataset { source_config?: Record<string, unknown> | null; schema: ColumnSchema[]; s3_path?: string; partition_column?: string; updated_at: string; last_import_by?: OwnerRef }
interface DatasetCreateRequest { file: File; name: string; has_header?: boolean; delimiter?: string; encoding?: string; partition_column?: string }
interface DatasetUpdateRequest { name?: string; partition_column?: string }
interface DatasetPreview { columns: string[]; rows: unknown[][]; total_rows: number; preview_rows: number }
```

### card.ts

```typescript
interface Card { card_id: string; name: string; dataset?: CardRef; used_columns?: string[]; filter_applicable?: string[]; owner: OwnerRef; created_at: string }
interface CardDetail extends Card { code: string; params?: Record<string, unknown>; description?: string; updated_at: string }
interface CardCreateRequest { name: string; dataset_id: string; code: string; params?: Record<string, unknown> }
interface CardUpdateRequest { name?: string; code?: string; params?: Record<string, unknown> }
interface CardExecuteRequest { filters?: Record<string, unknown>; use_cache?: boolean }
interface CardExecuteResponse { card_id: string; html: string; cached: boolean; execution_time_ms: number }
interface CardPreviewResponse { card_id: string; html: string; execution_time_ms: number; input_row_count: number; filtered_row_count: number }
```

### dashboard.ts

```typescript
interface LayoutItem { card_id: string; x: number; y: number; w: number; h: number }
interface FilterDefinition { id: string; type: 'category' | 'date_range'; column: string; label: string; multi_select?: boolean; options?: string[] }
interface DashboardLayout { cards: LayoutItem[]; columns: number; row_height: number }
interface Dashboard { dashboard_id: string; name: string; card_count: number; owner: OwnerRef; my_permission?: string; created_at: string; updated_at: string }
interface DashboardDetail extends Omit<Dashboard, 'card_count'> { layout: DashboardLayout; filters: FilterDefinition[]; default_filter_view_id?: string; description?: string }
interface DashboardCreateRequest { name: string }
interface DashboardUpdateRequest { name?: string; layout?: DashboardLayout; filters?: FilterDefinition[] }

// [FR-7] Sharing 型
type Permission = 'owner' | 'editor' | 'viewer'
type SharedToType = 'user' | 'group'
interface DashboardShare { id: string; dashboard_id: string; shared_to_type: SharedToType; shared_to_id: string; permission: Permission; shared_by: string; created_at: string }
interface ShareCreateRequest { shared_to_type: SharedToType; shared_to_id: string; permission: Permission }
interface ShareUpdateRequest { permission: Permission }
```

### group.ts [FR-7]

```typescript
interface Group { id: string; name: string; created_at: string; updated_at: string }
interface GroupDetail extends Group { members: GroupMember[] }
interface GroupMember { group_id: string; user_id: string; added_at: string }
interface GroupCreateRequest { name: string }
interface GroupUpdateRequest { name?: string }
interface AddMemberRequest { user_id: string }
```

### transform.ts [FR-2.1]

```typescript
interface Transform { id: string; name: string; owner_id: string; input_dataset_ids: string[]; output_dataset_id?: string; schedule_cron?: string; schedule_enabled?: boolean; code: string; owner: OwnerRef; created_at: string; updated_at: string }
interface TransformCreateRequest { name: string; input_dataset_ids: string[]; code: string; schedule_cron?: string; schedule_enabled?: boolean }
interface TransformUpdateRequest { name?: string; input_dataset_ids?: string[]; code?: string; schedule_cron?: string; schedule_enabled?: boolean }
interface TransformExecuteResponse { execution_id: string; output_dataset_id: string; row_count: number; column_names: string[]; execution_time_ms: number }
interface TransformExecution { execution_id: string; transform_id: string; status: 'running' | 'success' | 'failed'; started_at: string; finished_at?: string; duration_ms?: number; output_row_count?: number; output_dataset_id?: string; error?: string; triggered_by: 'manual' | 'schedule' }
```

### audit-log.ts

```typescript
type EventType = 'USER_LOGIN' | 'USER_LOGOUT' | 'USER_LOGIN_FAILED'
  | 'DASHBOARD_SHARE_ADDED' | 'DASHBOARD_SHARE_REMOVED' | 'DASHBOARD_SHARE_UPDATED'
  | 'DATASET_CREATED' | 'DATASET_IMPORTED' | 'DATASET_DELETED'
  | 'TRANSFORM_EXECUTED' | 'TRANSFORM_FAILED' | 'CARD_EXECUTION_FAILED'
interface AuditLog { log_id: string; timestamp: string; event_type: EventType; user_id: string; target_type: string; target_id: string; details: Record<string, unknown>; request_id: string | null }
interface AuditLogListParams { event_type?: EventType; user_id?: string; target_id?: string; start_date?: string; end_date?: string; limit?: number; offset?: number }
```

### reimport.ts [FR-1.3]

```typescript
type SchemaChangeType = 'added' | 'removed' | 'type_changed' | 'nullable_changed'
interface SchemaChange { column_name: string; change_type: SchemaChangeType; old_value: string | null; new_value: string | null }
interface ReimportDryRunResponse { has_schema_changes: boolean; changes: SchemaChange[]; new_row_count: number; new_column_count: number }
interface ReimportRequest { force?: boolean }
```

---

## Type Guard 関数

| 関数 | ファイル | 対象型 |
|------|---------|--------|
| `isUser()` | user.ts | User |
| `isLoginResponse()` | user.ts | LoginResponse |
| `isDataset()` | dataset.ts | Dataset |
| `isColumnSchema()` | dataset.ts | ColumnSchema |
| `isCard()` | card.ts | Card |
| `isDashboard()` | dashboard.ts | Dashboard |
| `isLayoutItem()` | dashboard.ts | LayoutItem |
| `isGroup()` | group.ts | Group |
| `isTransform()` | transform.ts | Transform |
| `isApiErrorResponse()` | api.ts | ApiErrorResponse |
| `isPagination()` | api.ts | Pagination |

---

## エンティティ関係図

```mermaid
erDiagram
    User ||--o{ Dataset : "owns"
    User ||--o{ Card : "owns"
    User ||--o{ Dashboard : "owns"
    User ||--o{ Transform : "owns"
    User }o--o{ Group : "belongs to (via GroupMember)"
    Dashboard ||--o{ DashboardShare : "shared via"
    DashboardShare }o--|| User : "shared to (user)"
    DashboardShare }o--|| Group : "shared to (group)"
    Group ||--o{ GroupMember : "has"
    GroupMember }o--|| User : "member"
    Dashboard ||--o{ LayoutItem : "contains"
    Dashboard ||--o{ FilterDefinition : "has"
    Dashboard ||--o{ FilterView : "has views"
    LayoutItem }o--|| Card : "references"
    Card }o--|| Dataset : "uses"
    Dataset ||--|| S3_Parquet : "stored in"
    Transform }o--o{ Dataset : "input (1..N)"
    Transform ||--o| Dataset : "output (0..1)"
    Transform ||--o{ TransformExecution : "execution history"
    User ||--o{ AuditLog : "audit trail"
    AuditLog }o--o| Dashboard : "target (dashboard)"
    AuditLog }o--o| Dataset : "target (dataset)"
    AuditLog }o--o| Transform : "target (transform)"
    AuditLog }o--o| Card : "target (card)"
```

```
  User (bi_users)
    |
    +--< owns >-- Dataset (bi_datasets) ---> S3 Parquet
    |               ^                ^
    |               |                |
    |               | (input 1..N)   | (output 0..1, 実行時に生成)
    |               |                |
    +--< owns >-- Transform (bi_transforms)
    |               |
    |               +--< history >-- TransformExecution (bi_transform_executions)
    |
    +--< owns >-- Card (bi_cards)
    |               |
    |               +-- dataset_id --> Dataset
    |
    +--< owns >-- Dashboard (bi_dashboards)
    |               |
    |               +-- layout[].card_id --> Card
    |               +-- filters[] --> FilterDefinition (options --> Dataset column values)
    |               +-- clone --> new Dashboard (owner=current_user)
    |               |
    |               +--< views >-- FilterView (bi_filter_views)
    |               |
    |               +--< shared via >-- DashboardShare (bi_dashboard_shares)
    |                                     |
    |                                     +-- shared_to_type="user"  --> User
    |                                     +-- shared_to_type="group" --> Group
    |
    +--< member of >-- GroupMember (bi_group_members)
    |                     |
    |                     +-- group_id --> Group (bi_groups)
    |
    +--< audit >-- AuditLog (bi_audit_logs)
                     +-- target_type + target_id --> Dashboard / Dataset / Transform / Card / User
```

## データフロー

### CSV インポート -> Parquet 変換
```
CSV Upload --> Backend API --> S3 (Parquet) --> Dataset レコード (DynamoDB)
                                                  |
                                                  +-- schema (列定義)
                                                  +-- s3Path (保存先)
                                                  +-- rowCount / columnCount
```

### Transform 実行 -> 新規 Dataset 生成
```
Transform 実行要求 (manual / schedule)
  |
  +-- TransformExecution レコード作成 (status="running")
  |
  +-- 入力 Dataset を S3 から読み込み (input_dataset_ids)
  |
  +-- Python コード実行 (code)
  |
  +-- 出力を新規 Dataset として S3 に保存
  |
  +-- Transform.output_dataset_id を更新
  |
  +-- TransformExecution ステータス更新 (status="success" or "failed")
```

### 再インポート (Reimport) [FR-1.3]
```
再インポート Dry Run --> スキーマ変更検知 (SchemaChange リスト返却)
  |
  +-- force=true で確定 --> 既存 Parquet 上書き --> Dataset レコード更新
```

---

## Permission モデル [FR-7]

ダッシュボードのアクセス権限は以下の順序で解決される:

```
1. Owner (ダッシュボード作成者)         --> permission = "owner"
2. DashboardShare (user 直接共有)       --> permission = "editor" | "viewer"
3. DashboardShare (group 経由共有)      --> permission = "editor" | "viewer"
4. 上記いずれにも該当しない             --> アクセス不可
```

Permission の優先度: owner > editor > viewer
複数の共有 (user + group) がある場合、最も高い権限が適用される。

## DynamoDB キーパターン (camelCase)

BaseRepository で自動変換:
- Python: `snake_case` (created_at) <--> DynamoDB: `camelCase` (createdAt)
- Python: `id` <--> DynamoDB: テーブル固有PK名 (userId, datasetId, groupId, shareId, transformId, etc.)
- Python: `datetime` <--> DynamoDB: `Number` (UNIX timestamp)

例外:
- GroupMemberRepository は BaseRepository を継承せず、独自の変換ロジックを使用 (複合キー groupId + userId を直接操作)
- TransformExecutionRepository は BaseRepository を継承するが、`create` / `_from_dynamodb_item` をオーバーライド (複合キー transformId + startedAt, Decimal 変換処理)

## Backend <--> Frontend レスポンスマッピング

| Backend レスポンス | Frontend 型 | 備考 |
|-------------------|------------|------|
| `api_response(data)` | `ApiResponse<T>` | `{ data: T }` |
| `paginated_response(...)` | `PaginatedResponse<T>` | `{ data: T[], pagination: Pagination }` |
| HTTPException 4xx/5xx | `ApiErrorResponse` | `{ error: { code, message } }` |

一覧 API (GET /datasets, /cards, /dashboards, /transforms) は全て `paginated_response()` を使用し、
`limit` / `offset` クエリパラメータを受け付ける (デフォルト: limit=50, offset=0)。

Transform 実行履歴 (GET /transforms/{id}/executions) は `api_response()` でラップ (ページネーションなし、上限20件)。

## 関連コードマップ

- [architecture.md](./architecture.md) - 全体アーキテクチャ
- [backend.md](./backend.md) - バックエンド構造
- [frontend.md](./frontend.md) - フロントエンド構造
