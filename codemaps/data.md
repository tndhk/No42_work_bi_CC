# データモデルとスキーマ コードマップ

**最終更新:** 2026-02-01 (Phase Q4 E2E + Q5 + フィルタ機能)
**データベース:** DynamoDB (NoSQL) + S3 (Parquet)

---

## DynamoDB テーブル一覧

テーブルプレフィックス: `bi_` (設定可能)

| テーブル名 | PK | GSI | 用途 |
|-----------|-----|-----|------|
| bi_users | userId (S) | UsersByEmail (email) | ユーザー |
| bi_datasets | datasetId (S) | DatasetsByOwner (ownerId + createdAt) | データセット |
| bi_cards | cardId (S) | CardsByOwner (ownerId + createdAt) | カード |
| bi_dashboards | dashboardId (S) | DashboardsByOwner (ownerId + createdAt) | ダッシュボード |

BillingMode: PAY_PER_REQUEST (全テーブル)

---

## DynamoDB スキーマ詳細

### bi_users

| 属性 | 型 | DynamoDB型 | 説明 |
|------|-----|-----------|------|
| userId | PK | S | UUID |
| email | GSI-PK | S | メールアドレス (一意) |
| hashedPassword | - | S | bcrypt ハッシュ |
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
    created_at: datetime
    updated_at: datetime

class User:                # 公開用 (hashedPassword除外)
    id: str
    email: str
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

---

## APIレスポンスヘルパー (Backend) [NEW]

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
interface User { user_id: string; email: string; name?: string; created_at: string }
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
| `isApiErrorResponse()` | api.ts | ApiErrorResponse |
| `isPagination()` | api.ts | Pagination |

---

## エンティティ関係図

```
  User (bi_users)
    |
    +--< owns >-- Dataset (bi_datasets) ---> S3 Parquet
    |
    +--< owns >-- Card (bi_cards)
    |               |
    |               +-- dataset_id --> Dataset
    |
    +--< owns >-- Dashboard (bi_dashboards)
                    |
                    +-- layout[].card_id --> Card
                    +-- filters[] --> FilterDefinition (options --> Dataset column values)
                    +-- clone --> new Dashboard (owner=current_user)
```

## DynamoDB キーパターン (camelCase)

BaseRepository で自動変換:
- Python: `snake_case` (created_at) <--> DynamoDB: `camelCase` (createdAt)
- Python: `id` <--> DynamoDB: テーブル固有PK名 (userId, datasetId, etc.)
- Python: `datetime` <--> DynamoDB: `Number` (UNIX timestamp)

## Backend <--> Frontend レスポンスマッピング [NEW]

| Backend レスポンス | Frontend 型 | 備考 |
|-------------------|------------|------|
| `api_response(data)` | `ApiResponse<T>` | `{ data: T }` |
| `paginated_response(...)` | `PaginatedResponse<T>` | `{ data: T[], pagination: Pagination }` |
| HTTPException 4xx/5xx | `ApiErrorResponse` | `{ error: { code, message } }` |

一覧 API (GET /datasets, /cards, /dashboards) は全て `paginated_response()` を使用し、
`limit` / `offset` クエリパラメータを受け付ける (デフォルト: limit=50, offset=0)。

## 関連コードマップ

- [architecture.md](./architecture.md) - 全体アーキテクチャ
- [backend.md](./backend.md) - バックエンド構造
- [frontend.md](./frontend.md) - フロントエンド構造
