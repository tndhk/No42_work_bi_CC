# 社内BI・Pythonカード API詳細仕様書 v0.1

Last Updated: 2026-02-03

## 1. 概要

### 1.1 ベースURL

```
# ローカル
http://localhost:8000/api

# 本番
https://bi.internal.company.com/api
```

### 1.2 認証

全てのAPIエンドポイント（`/api/auth/login`を除く）は認証が必要。

```http
Authorization: Bearer <jwt_token>
```

### 1.3 共通レスポンス形式

成功時:
```json
{
  "data": { ... },
  "meta": {
    "request_id": "req_abc123"
  }
}
```

エラー時:
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "エラーメッセージ",
    "details": { ... }
  },
  "meta": {
    "request_id": "req_abc123"
  }
}
```

### 1.4 ページネーション

```json
{
  "data": [ ... ],
  "pagination": {
    "total": 100,
    "limit": 20,
    "offset": 0,
    "has_next": true
  }
}
```

---

## 2. 認証 API

### POST /api/auth/login

ログイン

Request:
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

Response (200):
```json
{
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 86400,
    "user": {
      "user_id": "user_abc123",
      "email": "user@example.com",
      "name": "山田太郎"
    }
  }
}
```

Errors:
- `401 INVALID_CREDENTIALS`: メールアドレスまたはパスワードが正しくありません

---

### POST /api/auth/logout

ログアウト

Response (200):
```json
{
  "data": {
    "message": "ログアウトしました"
  }
}
```

---

### GET /api/auth/me

現在のユーザ情報取得

Response (200):
```json
{
  "data": {
    "user_id": "user_abc123",
    "email": "user@example.com",
    "name": "山田太郎",
    "groups": [
      {
        "group_id": "group_xyz",
        "name": "データ分析チーム"
      }
    ],
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

---

## 3. Users API

Last Updated: 2026-02-03

認証: JWT Bearer (全エンドポイント)

### GET /api/users

メールアドレスでユーザを検索する。共有ダイアログ等でのユーザ検索用途を想定。

Query Parameters:

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|-----|------|-----------|------|
| q | string | No | "" | メール検索文字列 (部分一致)。空文字の場合は空配列を返す |
| limit | integer | No | 20 | 取得件数 (1-100) |

Response (200):
```json
{
  "data": [
    {
      "id": "user_abc123",
      "email": "user@example.com",
      "role": "user"
    }
  ]
}
```

- `q` が空文字またはスペースのみの場合、`data` は空配列 `[]` を返す
- レスポンスにページネーション情報は含まれない (`api_response` 形式)
- `role` の値は `"admin"` または `"user"`

---

## 4. Groups API

Last Updated: 2026-02-03

認証: JWT Bearer (全エンドポイント)
認可: 全エンドポイントに admin 権限が必要 (`require_admin`)。
admin 以外のユーザーがアクセスした場合は `403 Forbidden` ("Admin access required") が返る。

Group モデル:

| フィールド | 型 | 説明 |
|-----------|-----|------|
| id | string | グループID (`group_` + 12桁hex) |
| name | string | グループ名 |
| created_at | string (ISO 8601) | 作成日時 |
| updated_at | string (ISO 8601) | 更新日時 |

GroupMember モデル:

| フィールド | 型 | 説明 |
|-----------|-----|------|
| group_id | string | グループID |
| user_id | string | ユーザーID |
| added_at | string (ISO 8601) | 追加日時 |

---

### GET /api/groups

グループ一覧取得 (全件取得、ページネーションなし)

認可: admin のみ

Response (200):
```json
{
  "data": [
    {
      "id": "group_xyz",
      "name": "データ分析チーム",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-10T00:00:00Z"
    }
  ]
}
```

- レスポンスにページネーション情報は含まれない (`api_response` 形式)
- 内部では `GroupRepository.list_all()` により DynamoDB テーブルを scan して全件取得

Errors:
- `401 Unauthorized`: 認証トークンが無効または未指定
- `403 Forbidden`: admin 権限がありません ("Admin access required")

---

### POST /api/groups

グループ作成

認可: admin のみ

Request:
```json
{
  "name": "マーケティングチーム"
}
```

- `name`: 必須。1文字以上 (`min_length=1`)。空白のみは不可。

Response (201):
```json
{
  "data": {
    "id": "group_new123abc456",
    "name": "マーケティングチーム",
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": "2024-01-15T10:00:00Z"
  }
}
```

内部では `GroupRepository.get_by_name()` により GroupsByName GSI を使用して名前の重複チェックを行う。

Errors:
- `401 Unauthorized`: 認証トークンが無効または未指定
- `403 Forbidden`: admin 権限がありません ("Admin access required")
- `409 Conflict`: 同名のグループが既に存在します ("Group name already exists")
- `422 Unprocessable Entity`: バリデーションエラー (name が空文字 / 未指定)

---

### GET /api/groups/{groupId}

グループ詳細取得 (メンバー一覧を含む)

認可: admin のみ

Response (200):
```json
{
  "data": {
    "id": "group_xyz",
    "name": "データ分析チーム",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-10T00:00:00Z",
    "members": [
      {
        "group_id": "group_xyz",
        "user_id": "user_abc123",
        "added_at": "2024-01-05T00:00:00Z"
      }
    ]
  }
}
```

- `members` は GroupMember モデルの配列。`GroupMemberRepository.list_members()` で取得される。
- メンバーにはユーザーの `email` や `name` は含まれない (user_id のみ)。

Errors:
- `401 Unauthorized`: 認証トークンが無効または未指定
- `403 Forbidden`: admin 権限がありません ("Admin access required")
- `404 Not Found`: グループが見つかりません ("Group not found")

---

### PUT /api/groups/{groupId}

グループ更新

認可: admin のみ

Request:
```json
{
  "name": "データ分析チーム（更新）"
}
```

- `name`: 任意。指定する場合は1文字以上 (`min_length=1`)。空白のみは不可。

Response (200):

更新後の Group モデル全フィールドを返す。

```json
{
  "data": {
    "id": "group_xyz",
    "name": "データ分析チーム（更新）",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-15T10:00:00Z"
  }
}
```

内部では名前変更時に `GroupRepository.get_by_name()` で重複チェックを行う (自グループは除外)。

Errors:
- `401 Unauthorized`: 認証トークンが無効または未指定
- `403 Forbidden`: admin 権限がありません ("Admin access required")
- `404 Not Found`: グループが見つかりません ("Group not found")
- `409 Conflict`: 同名のグループが既に存在します ("Group name already exists")
- `422 Unprocessable Entity`: バリデーションエラー (name が空文字)

---

### DELETE /api/groups/{groupId}

グループ削除

認可: admin のみ

Response (204): No Content

Errors:
- `401 Unauthorized`: 認証トークンが無効または未指定
- `403 Forbidden`: admin 権限がありません ("Admin access required")
- `404 Not Found`: グループが見つかりません ("Group not found")

---

### POST /api/groups/{groupId}/members

メンバー追加

認可: admin のみ

Request:
```json
{
  "user_id": "user_def456"
}
```

Response (201):

GroupMember モデルを返す。

```json
{
  "data": {
    "group_id": "group_xyz",
    "user_id": "user_def456",
    "added_at": "2024-01-15T10:00:00Z"
  }
}
```

Errors:
- `401 Unauthorized`: 認証トークンが無効または未指定
- `403 Forbidden`: admin 権限がありません ("Admin access required")
- `404 Not Found`: グループが見つかりません ("Group not found")

---

### DELETE /api/groups/{groupId}/members/{userId}

メンバー削除

認可: admin のみ

Response (204): No Content

Errors:
- `401 Unauthorized`: 認証トークンが無効または未指定
- `403 Forbidden`: admin 権限がありません ("Admin access required")
- `404 Not Found`: グループが見つかりません ("Group not found")

---

## 5. Datasets API

### GET /api/datasets

Dataset一覧取得

Query Parameters:
| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|-----|------|-----------|------|
| limit | integer | No | 20 | 取得件数 |
| offset | integer | No | 0 | オフセット |
| owner | string | No | - | 所有者ID（自分のみ: me） |

Response (200):
```json
{
  "data": [
    {
      "dataset_id": "ds_abc123",
      "name": "売上データ2024",
      "source_type": "local_csv",
      "row_count": 50000,
      "column_count": 15,
      "owner": {
        "user_id": "user_abc123",
        "name": "山田太郎"
      },
      "created_at": "2024-01-01T00:00:00Z",
      "last_import_at": "2024-01-15T10:00:00Z"
    }
  ],
  "pagination": { ... }
}
```

---

### POST /api/datasets

Dataset作成（Local CSV取り込み）

Request (multipart/form-data):
| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| file | File | Yes | CSVファイル |
| name | string | Yes | Dataset名 |
| has_header | boolean | No | ヘッダ有無（デフォルト: true） |
| delimiter | string | No | 区切り文字（デフォルト: ,） |
| encoding | string | No | 文字コード（デフォルト: utf-8） |
| partition_column | string | No | パーティションカラム（日付型） |

Response (201):
```json
{
  "data": {
    "dataset_id": "ds_new123",
    "name": "売上データ2024",
    "source_type": "local_csv",
    "schema": [
      { "name": "date", "type": "date", "nullable": false },
      { "name": "category", "type": "string", "nullable": true },
      { "name": "amount", "type": "int64", "nullable": false }
    ],
    "row_count": 50000,
    "column_count": 3,
    "s3_path": "datasets/ds_new123/data/",
    "partition_column": "date",
    "owner": {
      "user_id": "user_abc123",
      "name": "山田太郎"
    },
    "created_at": "2024-01-15T10:00:00Z",
    "last_import_at": "2024-01-15T10:00:00Z"
  }
}
```

Errors:
- `400 VALIDATION_ERROR`: CSVファイルが必要です
- `400 VALIDATION_ERROR`: ファイルサイズが上限を超えています（100MB）
- `400 VALIDATION_ERROR`: CSVの解析に失敗しました

---

### POST /api/datasets/s3-import

S3 CSV取り込み

Request:
```json
{
  "name": "売上データS3",
  "s3_bucket": "my-data-bucket",
  "s3_key": "data/sales.csv",
  "has_header": true,
  "delimiter": ",",
  "encoding": "utf-8",
  "partition_column": "date"
}
```

Response (201):
```json
{
  "data": {
    "dataset_id": "ds_s3_123",
    "name": "売上データS3",
    "source_type": "s3_csv",
    "source_config": {
      "s3_bucket": "my-data-bucket",
      "s3_key": "data/sales.csv"
    },
    "schema": [ ... ],
    "row_count": 100000,
    "column_count": 10,
    "created_at": "2024-01-15T10:00:00Z"
  }
}
```

Errors:
- `400 VALIDATION_ERROR`: S3バケットまたはキーが不正です
- `403 FORBIDDEN`: S3へのアクセス権限がありません

---

### GET /api/datasets/{datasetId}

Dataset詳細取得

Response (200):
```json
{
  "data": {
    "dataset_id": "ds_abc123",
    "name": "売上データ2024",
    "source_type": "local_csv",
    "source_config": null,
    "schema": [
      { "name": "date", "type": "date", "nullable": false },
      { "name": "category", "type": "string", "nullable": true },
      { "name": "amount", "type": "int64", "nullable": false }
    ],
    "row_count": 50000,
    "column_count": 3,
    "s3_path": "datasets/ds_abc123/data/",
    "partition_column": "date",
    "owner": {
      "user_id": "user_abc123",
      "name": "山田太郎"
    },
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-10T00:00:00Z",
    "last_import_at": "2024-01-15T10:00:00Z",
    "last_import_by": {
      "user_id": "user_abc123",
      "name": "山田太郎"
    }
  }
}
```

---

### PUT /api/datasets/{datasetId}

Dataset更新（メタデータのみ）

Request:
```json
{
  "name": "売上データ2024（更新）",
  "partition_column": "order_date"
}
```

Response (200):
```json
{
  "data": {
    "dataset_id": "ds_abc123",
    "name": "売上データ2024（更新）",
    "updated_at": "2024-01-15T10:00:00Z"
  }
}
```

Errors:
- `403 FORBIDDEN`: このDatasetを編集する権限がありません

---

### DELETE /api/datasets/{datasetId}

Dataset削除

Response (204): No Content

Errors:
- `403 FORBIDDEN`: このDatasetを削除する権限がありません
- `409 CONFLICT`: このDatasetは他のCard/Transformで使用されています

---

### POST /api/datasets/{datasetId}/import

再取り込み

Request:
```json
{
  "force": false
}
```

Response (200):
```json
{
  "data": {
    "dataset_id": "ds_abc123",
    "import_status": "completed",
    "row_count": 55000,
    "column_count": 3,
    "schema_changes": [
      {
        "type": "column_added",
        "column": "discount",
        "new_type": "float64"
      }
    ],
    "last_import_at": "2024-01-15T10:00:00Z"
  }
}
```

Response (200) スキーマ変更検知時:
```json
{
  "data": {
    "dataset_id": "ds_abc123",
    "import_status": "pending_confirmation",
    "schema_changes": [
      {
        "type": "column_removed",
        "column": "old_column"
      }
    ],
    "message": "スキーマに変更があります。続行しますか？"
  }
}
```

forceをtrueで再リクエストすると強制的に取り込み

---

### GET /api/datasets/{datasetId}/preview

プレビュー取得

Query Parameters:
| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|-----|------|-----------|------|
| limit | integer | No | 100 | 取得行数（1-1000） |

Response (200):
```json
{
  "data": {
    "columns": ["date", "category", "amount"],
    "rows": [
      ["2024-01-01", "電子機器", 15000],
      ["2024-01-01", "衣料品", 8000],
      ["2024-01-02", "電子機器", 22000]
    ],
    "total_rows": 50000,
    "preview_rows": 100
  }
}
```

---

## 6. Transforms API

### GET /api/transforms

Transform一覧取得

Query Parameters:
| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|-----|------|-----------|------|
| limit | integer | No | 20 | 取得件数 |
| offset | integer | No | 0 | オフセット |
| owner | string | No | - | 所有者ID |

Response (200):
```json
{
  "data": [
    {
      "transform_id": "tf_abc123",
      "name": "売上集計Transform",
      "input_datasets": [
        { "dataset_id": "ds_abc123", "name": "売上データ" }
      ],
      "output_dataset": {
        "dataset_id": "ds_output123",
        "name": "売上集計結果"
      },
      "schedule": "0 0 * * *",
      "last_execution": {
        "status": "success",
        "executed_at": "2024-01-15T00:00:00Z",
        "duration_ms": 5000
      },
      "owner": {
        "user_id": "user_abc123",
        "name": "山田太郎"
      },
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "pagination": { ... }
}
```

---

### POST /api/transforms

Transform作成

Request:
```json
{
  "name": "売上集計Transform",
  "input_dataset_ids": ["ds_abc123", "ds_def456"],
  "code": "def transform(inputs, params):\n    sales = inputs['ds_abc123']\n    return sales.groupby('category').sum()",
  "params": {},
  "schedule": "0 0 * * *"
}
```

Response (201):
```json
{
  "data": {
    "transform_id": "tf_new123",
    "name": "売上集計Transform",
    "input_datasets": [
      { "dataset_id": "ds_abc123", "name": "売上データ" }
    ],
    "output_dataset": null,
    "code": "def transform(inputs, params):\n    ...",
    "params": {},
    "schedule": "0 0 * * *",
    "created_at": "2024-01-15T10:00:00Z"
  }
}
```

Errors:
- `400 VALIDATION_ERROR`: コードにtransform関数が定義されていません
- `400 VALIDATION_ERROR`: 入力Datasetが見つかりません

---

### GET /api/transforms/{transformId}

Transform詳細取得

Response (200):
```json
{
  "data": {
    "transform_id": "tf_abc123",
    "name": "売上集計Transform",
    "input_datasets": [
      { "dataset_id": "ds_abc123", "name": "売上データ" }
    ],
    "output_dataset": {
      "dataset_id": "ds_output123",
      "name": "売上集計結果"
    },
    "code": "def transform(inputs, params):\n    sales = inputs['ds_abc123']\n    return sales.groupby('category').sum()",
    "params": {},
    "schedule": "0 0 * * *",
    "owner": {
      "user_id": "user_abc123",
      "name": "山田太郎"
    },
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-10T00:00:00Z"
  }
}
```

---

### PUT /api/transforms/{transformId}

Transform更新

Request:
```json
{
  "name": "売上集計Transform（更新）",
  "code": "def transform(inputs, params):\n    ...",
  "schedule": null
}
```

Response (200):
```json
{
  "data": {
    "transform_id": "tf_abc123",
    "name": "売上集計Transform（更新）",
    "updated_at": "2024-01-15T10:00:00Z"
  }
}
```

---

### DELETE /api/transforms/{transformId}

Transform削除

Response (204): No Content

---

### POST /api/transforms/{transformId}/execute

手動実行

Request:
```json
{
  "params": {}
}
```

Response (202):
```json
{
  "data": {
    "execution_id": "exec_abc123",
    "transform_id": "tf_abc123",
    "status": "running",
    "started_at": "2024-01-15T10:00:00Z"
  }
}
```

Response (200) 完了時（ポーリングまたはWebSocket）:
```json
{
  "data": {
    "execution_id": "exec_abc123",
    "transform_id": "tf_abc123",
    "status": "success",
    "output_dataset": {
      "dataset_id": "ds_output123",
      "name": "売上集計結果",
      "row_count": 100
    },
    "started_at": "2024-01-15T10:00:00Z",
    "finished_at": "2024-01-15T10:00:05Z",
    "duration_ms": 5000
  }
}
```

Errors:
- `408 EXECUTION_TIMEOUT`: 実行がタイムアウトしました
- `500 EXECUTION_ERROR`: 実行中にエラーが発生しました

---

### GET /api/transforms/{transformId}/executions

実行履歴取得

Query Parameters:
| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|-----|------|-----------|------|
| limit | integer | No | 20 | 取得件数 |
| offset | integer | No | 0 | オフセット |

Response (200):
```json
{
  "data": [
    {
      "execution_id": "exec_abc123",
      "status": "success",
      "started_at": "2024-01-15T10:00:00Z",
      "finished_at": "2024-01-15T10:00:05Z",
      "duration_ms": 5000,
      "output_row_count": 100,
      "error": null
    },
    {
      "execution_id": "exec_def456",
      "status": "failed",
      "started_at": "2024-01-14T10:00:00Z",
      "finished_at": "2024-01-14T10:00:03Z",
      "duration_ms": 3000,
      "output_row_count": null,
      "error": "KeyError: 'invalid_column'"
    }
  ],
  "pagination": { ... }
}
```

---

## 7. Cards API

### GET /api/cards

Card一覧取得

Query Parameters:
| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|-----|------|-----------|------|
| limit | integer | No | 20 | 取得件数 |
| offset | integer | No | 0 | オフセット |
| owner | string | No | - | 所有者ID |

Response (200):
```json
{
  "data": [
    {
      "card_id": "card_abc123",
      "name": "月別売上グラフ",
      "dataset": {
        "dataset_id": "ds_abc123",
        "name": "売上データ"
      },
      "used_columns": ["date", "amount"],
      "filter_applicable": ["category", "date"],
      "owner": {
        "user_id": "user_abc123",
        "name": "山田太郎"
      },
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "pagination": { ... }
}
```

---

### POST /api/cards

Card作成

Request:
```json
{
  "name": "月別売上グラフ",
  "dataset_id": "ds_abc123",
  "code": "def render(dataset, filters, params):\n    import plotly.express as px\n    fig = px.bar(dataset, x='date', y='amount')\n    return HTMLResult(html=fig.to_html())",
  "params": {}
}
```

Response (201):
```json
{
  "data": {
    "card_id": "card_new123",
    "name": "月別売上グラフ",
    "dataset": {
      "dataset_id": "ds_abc123",
      "name": "売上データ"
    },
    "code": "def render(dataset, filters, params):\n    ...",
    "params": {},
    "created_at": "2024-01-15T10:00:00Z"
  }
}
```

Errors:
- `400 VALIDATION_ERROR`: コードにrender関数が定義されていません
- `400 VALIDATION_ERROR`: Datasetが見つかりません

---

### GET /api/cards/{cardId}

Card詳細取得

Response (200):
```json
{
  "data": {
    "card_id": "card_abc123",
    "name": "月別売上グラフ",
    "dataset": {
      "dataset_id": "ds_abc123",
      "name": "売上データ"
    },
    "code": "def render(dataset, filters, params):\n    ...",
    "params": {},
    "used_columns": ["date", "amount"],
    "filter_applicable": ["category", "date"],
    "owner": {
      "user_id": "user_abc123",
      "name": "山田太郎"
    },
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-10T00:00:00Z"
  }
}
```

---

### PUT /api/cards/{cardId}

Card更新

Request:
```json
{
  "name": "月別売上グラフ（更新）",
  "code": "def render(dataset, filters, params):\n    ..."
}
```

Response (200):
```json
{
  "data": {
    "card_id": "card_abc123",
    "name": "月別売上グラフ（更新）",
    "updated_at": "2024-01-15T10:00:00Z"
  }
}
```

---

### DELETE /api/cards/{cardId}

Card削除

Response (204): No Content

Errors:
- `409 CONFLICT`: このCardは他のDashboardで使用されています

---

### POST /api/cards/{cardId}/preview

プレビュー実行

Request:
```json
{
  "filters": {
    "category": ["電子機器"],
    "date": {
      "start": "2024-01-01",
      "end": "2024-01-31"
    }
  }
}
```

Response (200):
```json
{
  "data": {
    "card_id": "card_abc123",
    "html": "<div id='plotly-chart'>...</div>",
    "execution_time_ms": 500,
    "input_row_count": 1000,
    "filtered_row_count": 150
  }
}
```

Errors:
- `408 EXECUTION_TIMEOUT`: 実行がタイムアウトしました
- `500 EXECUTION_ERROR`: 実行中にエラーが発生しました

---

### POST /api/cards/{cardId}/execute

カード実行（Dashboard用）

Request:
```json
{
  "filters": {
    "category": ["電子機器"],
    "date": {
      "start": "2024-01-01",
      "end": "2024-01-31"
    }
  },
  "use_cache": true
}
```

Response (200):
```json
{
  "data": {
    "card_id": "card_abc123",
    "html": "<div id='plotly-chart'>...</div>",
    "cached": true,
    "execution_time_ms": 50
  }
}
```

---

## 8. Dashboards API

### GET /api/dashboards

Dashboard一覧取得

Query Parameters:
| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|-----|------|-----------|------|
| limit | integer | No | 20 | 取得件数 |
| offset | integer | No | 0 | オフセット |
| owner | string | No | - | 所有者ID |
| shared | boolean | No | - | 共有されたもののみ |

Response (200):
```json
{
  "data": [
    {
      "dashboard_id": "dash_abc123",
      "name": "売上ダッシュボード",
      "card_count": 5,
      "owner": {
        "user_id": "user_abc123",
        "name": "山田太郎"
      },
      "my_permission": "owner",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-10T00:00:00Z"
    }
  ],
  "pagination": { ... }
}
```

---

### POST /api/dashboards

Dashboard作成

Request:
```json
{
  "name": "新規ダッシュボード"
}
```

Response (201):
```json
{
  "data": {
    "dashboard_id": "dash_new123",
    "name": "新規ダッシュボード",
    "layout": {
      "cards": [],
      "columns": 12,
      "row_height": 100
    },
    "filters": [],
    "owner": {
      "user_id": "user_abc123",
      "name": "山田太郎"
    },
    "created_at": "2024-01-15T10:00:00Z"
  }
}
```

---

### GET /api/dashboards/{dashboardId}

Dashboard詳細取得

Response (200):
```json
{
  "data": {
    "dashboard_id": "dash_abc123",
    "name": "売上ダッシュボード",
    "layout": {
      "cards": [
        {
          "card_id": "card_abc123",
          "x": 0,
          "y": 0,
          "w": 6,
          "h": 4
        },
        {
          "card_id": "card_def456",
          "x": 6,
          "y": 0,
          "w": 6,
          "h": 4
        }
      ],
      "columns": 12,
      "row_height": 100
    },
    "filters": [
      {
        "id": "filter_category",
        "type": "category",
        "column": "category",
        "label": "カテゴリ",
        "multi_select": true
      },
      {
        "id": "filter_date",
        "type": "date_range",
        "column": "date",
        "label": "期間"
      }
    ],
    "default_filter_view_id": "fv_abc123",
    "owner": {
      "user_id": "user_abc123",
      "name": "山田太郎"
    },
    "my_permission": "owner",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-10T00:00:00Z"
  }
}
```

---

### PUT /api/dashboards/{dashboardId}

Dashboard更新

Request:
```json
{
  "name": "売上ダッシュボード（更新）",
  "layout": {
    "cards": [
      { "card_id": "card_abc123", "x": 0, "y": 0, "w": 12, "h": 4 }
    ],
    "columns": 12,
    "row_height": 100
  },
  "filters": [
    {
      "id": "filter_category",
      "type": "category",
      "column": "category",
      "label": "カテゴリ",
      "multi_select": true
    }
  ]
}
```

Response (200):
```json
{
  "data": {
    "dashboard_id": "dash_abc123",
    "name": "売上ダッシュボード（更新）",
    "updated_at": "2024-01-15T10:00:00Z"
  }
}
```

---

### DELETE /api/dashboards/{dashboardId}

Dashboard削除

Response (204): No Content

---

### POST /api/dashboards/{dashboardId}/clone

Dashboard複製

Request:
```json
{
  "name": "売上ダッシュボード（コピー）"
}
```

Response (201):
```json
{
  "data": {
    "dashboard_id": "dash_clone123",
    "name": "売上ダッシュボード（コピー）",
    "created_at": "2024-01-15T10:00:00Z"
  }
}
```

---

### GET /api/dashboards/{dashboardId}/referenced-datasets

参照Dataset一覧取得

Response (200):
```json
{
  "data": [
    {
      "dataset_id": "ds_abc123",
      "name": "売上データ",
      "row_count": 50000,
      "owner": {
        "user_id": "user_abc123",
        "name": "山田太郎"
      },
      "used_by_cards": ["card_abc123", "card_def456"]
    }
  ]
}
```

---

## 9. Dashboard Shares API

Last Updated: 2026-02-03

認証: JWT Bearer (全エンドポイント)
認可: 全エンドポイントでダッシュボードのオーナーのみが操作可能。オーナー以外のユーザがアクセスした場合は 403 を返す。

DashboardShare モデル:

| フィールド | 型 | 説明 |
|-----------|-----|------|
| id | string | 共有ID (`share_` + 12桁hex) |
| dashboard_id | string | 対象ダッシュボードID |
| shared_to_type | string | 共有先種別: `"user"` または `"group"` |
| shared_to_id | string | 共有先ユーザID またはグループID |
| permission | string | 権限: `"owner"`, `"editor"`, `"viewer"` のいずれか |
| shared_by | string | 共有作成者のユーザID (文字列) |
| created_at | string (ISO 8601) | 作成日時 |

注意: `shared_by` はユーザIDの文字列であり、ネストしたオブジェクトではない。
`shared_to` もネストオブジェクトではなく、`shared_to_type` と `shared_to_id` のフラットフィールドで表現される。
DashboardShare には `updated_at` フィールドは存在しない。

---

### GET /api/dashboards/{dashboard_id}/shares

共有一覧取得

認可: ダッシュボードのオーナーのみ

Response (200):
```json
{
  "data": [
    {
      "id": "share_abc123def456",
      "dashboard_id": "dash_abc123",
      "shared_to_type": "user",
      "shared_to_id": "user_def456",
      "permission": "viewer",
      "shared_by": "user_abc123",
      "created_at": "2024-01-10T00:00:00Z"
    },
    {
      "id": "share_def456ghi789",
      "dashboard_id": "dash_abc123",
      "shared_to_type": "group",
      "shared_to_id": "group_xyz",
      "permission": "editor",
      "shared_by": "user_abc123",
      "created_at": "2024-01-11T00:00:00Z"
    }
  ]
}
```

Errors:
- `403 FORBIDDEN`: Only dashboard owner can manage shares
- `404 NOT_FOUND`: Dashboard not found

---

### POST /api/dashboards/{dashboard_id}/shares

共有追加

認可: ダッシュボードのオーナーのみ

Request:
```json
{
  "shared_to_type": "user",
  "shared_to_id": "user_ghi789",
  "permission": "viewer"
}
```

リクエストフィールド:
| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| shared_to_type | string | Yes | `"user"` または `"group"` |
| shared_to_id | string | Yes | 共有先ユーザID またはグループID |
| permission | string | Yes | `"owner"`, `"editor"`, `"viewer"` のいずれか |

重複チェック: 同一 dashboard_id + shared_to_type + shared_to_id の組み合わせが既に存在する場合、409 を返す。
内部では `DashboardShareRepository.find_share()` により SharesByDashboard GSI を使用して重複を検出する。

Response (201):
```json
{
  "data": {
    "id": "share_new123abc456",
    "dashboard_id": "dash_abc123",
    "shared_to_type": "user",
    "shared_to_id": "user_ghi789",
    "permission": "viewer",
    "shared_by": "user_abc123",
    "created_at": "2024-01-15T10:00:00Z"
  }
}
```

Errors:
- `403 FORBIDDEN`: Only dashboard owner can manage shares
- `404 NOT_FOUND`: Dashboard not found
- `409 CONFLICT`: Share already exists
- `422 VALIDATION_ERROR`: リクエストボディのバリデーションエラー (shared_to_type / permission の不正な値など)

---

### PUT /api/dashboards/{dashboard_id}/shares/{share_id}

共有権限更新

認可: ダッシュボードのオーナーのみ

Request:
```json
{
  "permission": "editor"
}
```

リクエストフィールド:
| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| permission | string | Yes | `"owner"`, `"editor"`, `"viewer"` のいずれか |

Response (200):
```json
{
  "data": {
    "id": "share_abc123def456",
    "dashboard_id": "dash_abc123",
    "shared_to_type": "user",
    "shared_to_id": "user_def456",
    "permission": "editor",
    "shared_by": "user_abc123",
    "created_at": "2024-01-10T00:00:00Z"
  }
}
```

Errors:
- `403 FORBIDDEN`: Only dashboard owner can manage shares
- `404 NOT_FOUND`: Dashboard not found / Share not found
- `422 VALIDATION_ERROR`: リクエストボディのバリデーションエラー

---

### DELETE /api/dashboards/{dashboard_id}/shares/{share_id}

共有削除

認可: ダッシュボードのオーナーのみ

Response (204): No Content

Errors:
- `403 FORBIDDEN`: Only dashboard owner can manage shares
- `404 NOT_FOUND`: Dashboard not found / Share not found

---

## 10. FilterViews API

### GET /api/dashboards/{dashboardId}/filter-views

FilterView一覧取得

Response (200):
```json
{
  "data": [
    {
      "filter_view_id": "fv_abc123",
      "name": "Q1分析ビュー",
      "filter_state": {
        "category": ["電子機器", "衣料品"],
        "date": {
          "start": "2024-01-01",
          "end": "2024-03-31"
        }
      },
      "is_shared": true,
      "is_default": true,
      "owner": {
        "user_id": "user_abc123",
        "name": "山田太郎"
      },
      "created_at": "2024-01-05T00:00:00Z"
    }
  ]
}
```

---

### POST /api/dashboards/{dashboardId}/filter-views

FilterView作成

Request:
```json
{
  "name": "Q2分析ビュー",
  "filter_state": {
    "category": ["電子機器"],
    "date": {
      "start": "2024-04-01",
      "end": "2024-06-30"
    }
  },
  "is_shared": true
}
```

Response (201):
```json
{
  "data": {
    "filter_view_id": "fv_new123",
    "name": "Q2分析ビュー",
    "filter_state": { ... },
    "is_shared": true,
    "is_default": false,
    "created_at": "2024-01-15T10:00:00Z"
  }
}
```

---

### GET /api/filter-views/{filterViewId}

FilterView詳細取得

Response (200):
```json
{
  "data": {
    "filter_view_id": "fv_abc123",
    "dashboard_id": "dash_abc123",
    "name": "Q1分析ビュー",
    "filter_state": {
      "category": ["電子機器", "衣料品"],
      "date": {
        "start": "2024-01-01",
        "end": "2024-03-31"
      }
    },
    "is_shared": true,
    "is_default": true,
    "owner": {
      "user_id": "user_abc123",
      "name": "山田太郎"
    },
    "created_at": "2024-01-05T00:00:00Z",
    "updated_at": "2024-01-10T00:00:00Z"
  }
}
```

---

### PUT /api/filter-views/{filterViewId}

FilterView更新

Request:
```json
{
  "name": "Q1分析ビュー（更新）",
  "filter_state": {
    "category": ["電子機器"],
    "date": {
      "start": "2024-01-01",
      "end": "2024-03-31"
    }
  },
  "is_default": true
}
```

Response (200):
```json
{
  "data": {
    "filter_view_id": "fv_abc123",
    "name": "Q1分析ビュー（更新）",
    "updated_at": "2024-01-15T10:00:00Z"
  }
}
```

---

### DELETE /api/filter-views/{filterViewId}

FilterView削除

Response (204): No Content

---

## 11. Chatbot API

### POST /api/dashboards/{dashboardId}/chat

Chatbot質問

Request:
```json
{
  "message": "このダッシュボードで最も売上が高いカテゴリは何ですか？",
  "conversation_id": "conv_abc123"
}
```

`conversation_id`は会話を継続する場合に指定（省略時は新規会話）

Response (200):
```json
{
  "data": {
    "conversation_id": "conv_abc123",
    "message": "このダッシュボードのデータによると、最も売上が高いカテゴリは「電子機器」で、総売上は1,500万円です。次いで「衣料品」が800万円となっています。",
    "sources": [
      {
        "dataset_id": "ds_abc123",
        "dataset_name": "売上データ"
      }
    ]
  }
}
```

Errors:
- `429 RATE_LIMIT_EXCEEDED`: リクエスト数が上限に達しました
- `500 EXECUTION_ERROR`: AI応答の生成に失敗しました

---

## 12. Audit Logs API

### GET /api/audit-logs

監査ログ取得（管理者のみ）

Query Parameters:
| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|-----|------|-----------|------|
| limit | integer | No | 50 | 取得件数 |
| offset | integer | No | 0 | オフセット |
| event_type | string | No | - | イベント種別 |
| user_id | string | No | - | 実行者ID |
| target_id | string | No | - | 対象ID |
| start_date | string | No | - | 開始日（ISO 8601） |
| end_date | string | No | - | 終了日（ISO 8601） |

Response (200):
```json
{
  "data": [
    {
      "log_id": "log_abc123",
      "event_type": "DASHBOARD_SHARE_ADDED",
      "timestamp": "2024-01-15T10:00:00Z",
      "user": {
        "user_id": "user_abc123",
        "name": "山田太郎"
      },
      "target_type": "Dashboard",
      "target_id": "dash_abc123",
      "details": {
        "shared_to_type": "user",
        "shared_to_id": "user_def456",
        "permission": "viewer"
      }
    }
  ],
  "pagination": { ... }
}
```

イベント種別:
- `USER_LOGIN`
- `USER_LOGOUT`
- `DATASET_CREATED`
- `DATASET_IMPORTED`
- `DATASET_DELETED`
- `TRANSFORM_EXECUTED`
- `TRANSFORM_FAILED`
- `CARD_EXECUTION_FAILED`
- `DASHBOARD_CREATED`
- `DASHBOARD_DELETED`
- `DASHBOARD_SHARE_ADDED`
- `DASHBOARD_SHARE_REMOVED`
- `DASHBOARD_SHARE_UPDATED`
