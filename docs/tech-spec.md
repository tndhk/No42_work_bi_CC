# 社内BI・Pythonカード 技術仕様書 v0.1

## 1. 技術スタック

### 1.1 フロントエンド

| 項目 | 技術 | バージョン | 理由 |
|------|------|-----------|------|
| フレームワーク | React | 18.x | 安定性、エコシステム |
| 言語 | TypeScript | 5.x | 型安全性 |
| ビルドツール | Vite | 5.x | 高速ビルド |
| UIライブラリ | shadcn/ui | latest | カスタマイズ性、軽量 |
| スタイリング | Tailwind CSS | 3.x | ユーティリティファースト |
| 状態管理（サーバ） | TanStack Query | 5.x | キャッシュ、再検証 |
| 状態管理（クライアント） | Zustand | 4.x | 軽量、シンプル |
| ルーティング | React Router | 6.x | 標準的 |
| フォーム | React Hook Form | 7.x | パフォーマンス |
| バリデーション | Zod | 3.x | TypeScript統合 |
| グリッドレイアウト | react-grid-layout | 1.x | ドラッグ&ドロップ対応 |
| コードエディタ | Monaco Editor | latest | VSCode互換 |
| 日付操作 | date-fns | 3.x | 軽量、Tree-shaking |
| HTTPクライアント | ky | 1.x | 軽量、モダン |

### 1.2 バックエンド（API）

| 項目 | 技術 | バージョン | 理由 |
|------|------|-----------|------|
| フレームワーク | FastAPI | 0.109.x | 高速、型ヒント、OpenAPI |
| 言語 | Python | 3.11 | 安定性、パフォーマンス |
| ASGI | Uvicorn | 0.27.x | 高速 |
| DynamoDB | aioboto3 | 12.x | 非同期対応 |
| S3 | aioboto3 | 12.x | 非同期対応 |
| Parquet | PyArrow | 15.x | 高速、メモリ効率 |
| DataFrame | Pandas | 2.2.x | 標準的 |
| JWT | python-jose | 3.x | JWT実装 |
| パスワードハッシュ | passlib[bcrypt] | 1.7.x | bcrypt対応 |
| バリデーション | Pydantic | 2.x | FastAPI統合 |
| 設定管理 | pydantic-settings | 2.x | 環境変数管理 |
| ログ | structlog | 24.x | 構造化ログ |
| Vertex AI | google-cloud-aiplatform | 1.x | Gemini API |

### 1.3 Python実行基盤

| 項目 | 技術 | バージョン | 理由 |
|------|------|-----------|------|
| 言語 | Python | 3.11 | APIと統一 |
| DataFrame | Pandas | 2.2.x | 標準的 |
| Parquet | PyArrow | 15.x | Parquet読み書き |
| 可視化 | Plotly | 5.x | インタラクティブ |
| 可視化 | Matplotlib | 3.8.x | 静的グラフ |
| 可視化 | Seaborn | 0.13.x | 統計可視化 |
| 数値計算 | NumPy | 1.26.x | 基本ライブラリ |

### 1.4 インフラ（AWS）

| 項目 | 技術 | 設定 |
|------|------|------|
| コンテナ | ECS Fargate | API: 0.5 vCPU / 1GB, Executor: 1-2 vCPU / 2-4GB |
| データベース | DynamoDB | オンデマンドキャパシティ |
| ストレージ | S3 | Standard、バージョニング有効 |
| CDN | CloudFront | 静的アセット配信 |
| スケジューラ | EventBridge Scheduler | cron形式 |
| ロードバランサ | ALB | HTTPS終端 |
| 証明書 | ACM | 自動更新 |
| シークレット | Secrets Manager | API認証情報等 |
| ログ | CloudWatch Logs | 30日保持 |

### 1.5 ローカル開発

| 項目 | 技術 | バージョン |
|------|------|-----------|
| コンテナ | Docker | 24.x |
| オーケストレーション | docker-compose | 2.x |
| DynamoDB | DynamoDB Local | latest |
| S3互換 | MinIO | latest |

---

## 2. プロジェクト構成

```
work_BI/
├── docs/                          # ドキュメント
│   ├── requirements.md
│   ├── design.md
│   ├── tech-spec.md
│   └── api-spec.md
├── frontend/                      # フロントエンド
│   ├── src/
│   │   ├── components/
│   │   │   ├── common/           # 共通コンポーネント
│   │   │   ├── dashboard/        # Dashboard関連
│   │   │   ├── dataset/          # Dataset関連
│   │   │   ├── transform/        # Transform関連
│   │   │   ├── card/             # Card関連
│   │   │   └── chatbot/          # Chatbot関連
│   │   ├── hooks/                # カスタムフック
│   │   ├── lib/                  # ユーティリティ
│   │   ├── pages/                # ページコンポーネント
│   │   ├── stores/               # Zustandストア
│   │   ├── types/                # 型定義
│   │   └── App.tsx
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── Dockerfile
├── backend/                       # バックエンド（API）
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/           # APIルート
│   │   │   │   ├── auth.py
│   │   │   │   ├── users.py
│   │   │   │   ├── groups.py
│   │   │   │   ├── datasets.py
│   │   │   │   ├── transforms.py
│   │   │   │   ├── cards.py
│   │   │   │   ├── dashboards.py
│   │   │   │   ├── filter_views.py
│   │   │   │   └── chatbot.py
│   │   │   └── deps.py           # 依存性注入
│   │   ├── core/
│   │   │   ├── config.py         # 設定
│   │   │   ├── security.py       # 認証・認可
│   │   │   └── logging.py        # ログ設定
│   │   ├── db/
│   │   │   ├── dynamodb.py       # DynamoDB接続
│   │   │   └── s3.py             # S3接続
│   │   ├── models/               # Pydanticモデル
│   │   │   ├── user.py
│   │   │   ├── group.py
│   │   │   ├── dataset.py
│   │   │   ├── transform.py
│   │   │   ├── card.py
│   │   │   ├── dashboard.py
│   │   │   └── filter_view.py
│   │   ├── services/             # ビジネスロジック
│   │   │   ├── dataset_service.py
│   │   │   ├── transform_service.py
│   │   │   ├── card_service.py
│   │   │   ├── dashboard_service.py
│   │   │   ├── executor_service.py
│   │   │   └── chatbot_service.py
│   │   └── main.py               # エントリポイント
│   ├── tests/
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── Dockerfile
├── executor/                      # Python実行基盤
│   ├── app/
│   │   ├── runner.py             # 実行エンジン
│   │   ├── sandbox.py            # サンドボックス
│   │   └── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── infra/                         # インフラ（Terraform）
│   ├── modules/
│   │   ├── ecs/
│   │   ├── dynamodb/
│   │   ├── s3/
│   │   └── networking/
│   ├── environments/
│   │   ├── dev/
│   │   ├── staging/
│   │   └── prod/
│   └── main.tf
├── docker-compose.yml             # ローカル開発用
├── docker-compose.override.yml
├── .env.example
├── .gitignore
└── README.md
```

---

## 3. 設定値

### 3.1 環境変数

```bash
# 共通
ENV=local|staging|production

# API
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
API_DEBUG=false

# 認証
JWT_SECRET_KEY=your-secret-key-min-32-chars
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440  # 24時間
PASSWORD_MIN_LENGTH=8

# DynamoDB
DYNAMODB_ENDPOINT=http://localhost:8000  # ローカルのみ
DYNAMODB_REGION=ap-northeast-1
DYNAMODB_TABLE_PREFIX=bi_

# S3
S3_ENDPOINT=http://localhost:9000  # ローカルのみ
S3_REGION=ap-northeast-1
S3_BUCKET_DATASETS=bi-datasets
S3_BUCKET_STATIC=bi-static
S3_ACCESS_KEY=minioadmin  # ローカルのみ
S3_SECRET_KEY=minioadmin  # ローカルのみ

# Vertex AI
VERTEX_AI_PROJECT_ID=your-project-id
VERTEX_AI_LOCATION=asia-northeast1
VERTEX_AI_MODEL=gemini-1.5-pro

# 実行基盤
EXECUTOR_ENDPOINT=http://executor:8080
EXECUTOR_TIMEOUT_CARD=10
EXECUTOR_TIMEOUT_TRANSFORM=300
EXECUTOR_MAX_CONCURRENT_CARDS=10
EXECUTOR_MAX_CONCURRENT_TRANSFORMS=5

# ログ
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### 3.2 リソース制限

**Card実行:**
```yaml
cpu: 1024        # 1 vCPU
memory: 2048     # 2 GB
timeout: 10      # 10秒
disk: 1024       # 1 GB
```

**Transform実行:**
```yaml
cpu: 2048        # 2 vCPU
memory: 4096     # 4 GB
timeout: 300     # 5分
disk: 10240      # 10 GB
```

### 3.3 レート制限

```yaml
# API全体
global:
  requests_per_minute: 1000
  requests_per_user_per_minute: 100

# Chatbot
chatbot:
  requests_per_user_per_minute: 5
  requests_per_dashboard_per_minute: 10

# カード実行
card_execution:
  requests_per_dashboard_per_minute: 60
```

---

## 4. データ変換仕様

### 4.1 CSV → Parquet変換

**型推論ルール:**

| CSVデータパターン | 推論される型 |
|------------------|------------|
| 整数のみ（-999〜999...） | int64 |
| 小数を含む数値 | float64 |
| true/false/True/False | bool |
| ISO 8601日付（YYYY-MM-DD） | date |
| ISO 8601日時（YYYY-MM-DDTHH:MM:SS） | datetime |
| 上記以外 | string |

**変換オプション:**
```python
class CsvImportOptions(BaseModel):
    has_header: bool = True
    delimiter: str = ","
    encoding: str = "utf-8"  # utf-8, shift_jis, cp932
    null_values: list[str] = ["", "NULL", "null", "NA", "N/A"]
    date_columns: list[str] = []  # 明示的に日付として扱う列
    datetime_columns: list[str] = []
    skip_rows: int = 0
    max_rows: int | None = None  # プレビュー用
```

### 4.2 パーティション仕様

**パーティション分割:**
- 日付カラムが指定された場合、日単位でパーティション
- パーティションキー: `YYYY-MM-DD`
- パーティションなしの場合、単一Parquetファイル

**S3パス構造:**
```
datasets/{datasetId}/
  _metadata.json           # メタデータ
  data/                    # パーティションなし
    part-0000.parquet
  partitions/              # パーティションあり
    date=2024-01-01/
      part-0000.parquet
    date=2024-01-02/
      part-0000.parquet
```

### 4.3 フィルタ適用ロジック

**カテゴリフィルタ:**
```python
# 単一選択
df = df[df[column] == value]

# 複数選択
df = df[df[column].isin(values)]

# NULL許容
if include_null:
    df = df[(df[column].isin(values)) | (df[column].isna())]
```

**日付フィルタ:**
```python
# 期間フィルタ（境界を含む）
df = df[(df[column] >= start_date) & (df[column] <= end_date)]

# パーティションプルーニング
# 日付フィルタがある場合、該当パーティションのみ読み込み
partitions_to_read = [
    p for p in all_partitions
    if start_date <= p.date <= end_date
]
```

**日付境界ルール:**
- 開始日: 00:00:00 から（含む）
- 終了日: 23:59:59 まで（含む）
- タイムゾーン: JST（Asia/Tokyo）固定

---

## 5. セキュリティ実装

### 5.1 パスワードハッシュ

```python
from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # ワークファクター
)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
```

**パスワードポリシー:**
- 最小8文字
- 英大文字、英小文字、数字を各1文字以上含む
- 連続する同一文字は3文字まで

### 5.2 JWT実装

```python
from jose import jwt
from datetime import datetime, timedelta

def create_access_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def verify_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
```

### 5.3 CSP設定

```python
CSP_POLICY = {
    "default-src": ["'self'"],
    "script-src": [
        "'self'",
        "https://cdn.internal.company.com",  # 許可JSライブラリ
    ],
    "style-src": [
        "'self'",
        "'unsafe-inline'",  # Plotly等で必要
    ],
    "img-src": [
        "'self'",
        "data:",  # Base64画像
    ],
    "font-src": ["'self'"],
    "connect-src": ["'self'"],
    "frame-ancestors": ["'self'"],
    "form-action": ["'self'"],
}
```

### 5.4 iframe sandbox

```html
<iframe
  sandbox="allow-scripts"
  srcdoc="..."
  style="width: 100%; height: 100%; border: none;"
></iframe>
```

**sandbox属性:**
- `allow-scripts`: JavaScript実行を許可
- `allow-same-origin`: 削除（クロスオリジン扱い）
- その他は全て禁止

---

## 6. エラーハンドリング

### 6.1 エラーレスポンス形式

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "入力データが不正です",
    "details": {
      "field": "email",
      "reason": "メールアドレスの形式が正しくありません"
    },
    "request_id": "req_abc123"
  }
}
```

### 6.2 エラーコード一覧

| コード | HTTPステータス | 説明 |
|--------|---------------|------|
| UNAUTHORIZED | 401 | 認証が必要 |
| INVALID_TOKEN | 401 | トークンが無効 |
| TOKEN_EXPIRED | 401 | トークンが期限切れ |
| FORBIDDEN | 403 | 権限がない |
| NOT_FOUND | 404 | リソースが見つからない |
| VALIDATION_ERROR | 400 | バリデーションエラー |
| DUPLICATE_ERROR | 409 | 重複エラー |
| EXECUTION_TIMEOUT | 408 | 実行タイムアウト |
| EXECUTION_ERROR | 500 | 実行エラー |
| RATE_LIMIT_EXCEEDED | 429 | レート制限超過 |
| INTERNAL_ERROR | 500 | 内部エラー |
| SERVICE_UNAVAILABLE | 503 | サービス利用不可 |

### 6.3 リトライポリシー

**S3アクセス:**
```python
retry_config = {
    "max_attempts": 3,
    "mode": "adaptive",  # 指数バックオフ
}
```

**DynamoDB:**
```python
retry_config = {
    "max_attempts": 3,
    "mode": "adaptive",
}
```

**Vertex AI:**
```python
retry_config = {
    "max_attempts": 2,
    "retry_codes": [429, 500, 503],
    "initial_delay": 1.0,
    "multiplier": 2.0,
    "max_delay": 10.0,
}
```

---

## 7. ログ仕様

### 7.1 ログ形式（JSON）

```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "level": "INFO",
  "logger": "app.api.routes.dashboards",
  "message": "Dashboard accessed",
  "request_id": "req_abc123",
  "user_id": "user_xyz",
  "dashboard_id": "dash_123",
  "duration_ms": 150
}
```

### 7.2 ログレベル

| レベル | 用途 |
|--------|------|
| ERROR | エラー、例外 |
| WARN | 警告（リトライ成功、レート制限接近等） |
| INFO | 通常操作（API呼び出し、実行完了等） |
| DEBUG | デバッグ情報（ローカルのみ） |

### 7.3 監査ログ

```json
{
  "event_type": "DASHBOARD_SHARE_ADDED",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "user_id": "user_xyz",
  "target_type": "Dashboard",
  "target_id": "dash_123",
  "details": {
    "shared_to_type": "Group",
    "shared_to_id": "group_abc",
    "permission": "Viewer"
  }
}
```

---

## 8. テスト戦略

### 8.1 テストレベル

| レベル | カバレッジ目標 | ツール |
|--------|--------------|--------|
| 単体テスト | 80% | pytest, vitest |
| 統合テスト | 主要フロー | pytest, Playwright |
| E2Eテスト | クリティカルパス | Playwright |

### 8.2 テストデータ

**フィクスチャ:**
```python
# tests/fixtures/datasets.py
SAMPLE_DATASET = {
    "datasetId": "test_dataset_001",
    "name": "テスト売上データ",
    "schema": [
        {"name": "date", "type": "date"},
        {"name": "category", "type": "string"},
        {"name": "amount", "type": "int64"},
    ],
    "rowCount": 1000,
}
```

**モック:**
- DynamoDB: moto
- S3: moto
- Vertex AI: unittest.mock

### 8.3 テスト実行

```bash
# バックエンド
cd backend
pytest --cov=app --cov-report=html

# フロントエンド
cd frontend
npm run test
npm run test:coverage

# E2E
cd frontend
npm run test:e2e
```

---

## 9. CI/CD

### 9.1 GitHub Actions

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  backend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r backend/requirements.txt
      - run: pytest backend/tests --cov

  frontend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: npm ci
        working-directory: frontend
      - run: npm run test
        working-directory: frontend

  build:
    needs: [backend-test, frontend-test]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t bi-api ./backend
      - run: docker build -t bi-executor ./executor
      - run: docker build -t bi-frontend ./frontend
```

### 9.2 デプロイフロー

```
develop → staging（自動デプロイ）
main → production（手動承認後デプロイ）
```

### 9.3 シークレット管理

- AWS Secrets Manager: 本番環境
- GitHub Secrets: CI/CD用
- .env.local: ローカル開発用

---

## 10. 監視・アラート

### 10.1 メトリクス

| メトリクス | 説明 | アラート閾値 |
|-----------|------|------------|
| api_request_duration_p95 | API応答時間 p95 | > 3秒 |
| api_error_rate | APIエラー率 | > 5% |
| card_execution_duration_p95 | カード実行時間 p95 | > 8秒 |
| card_execution_timeout_rate | カードタイムアウト率 | > 10% |
| transform_execution_error_rate | Transform失敗率 | > 20% |
| dynamodb_throttled_requests | DynamoDBスロットル | > 0 |

### 10.2 ダッシュボード（CloudWatch）

- API応答時間・エラー率
- カード/Transform実行状況
- ECSリソース使用率
- DynamoDB/S3メトリクス

### 10.3 アラート通知

```yaml
# SNS → Slack通知
critical:
  - api_error_rate > 10%
  - card_execution_timeout_rate > 20%
  - dynamodb_throttled_requests > 10

warning:
  - api_error_rate > 5%
  - card_execution_timeout_rate > 10%
  - api_request_duration_p95 > 3s
```
