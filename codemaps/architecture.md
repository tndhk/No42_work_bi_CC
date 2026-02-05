# 全体アーキテクチャ コードマップ

最終更新: 2026-02-05 17:00 JST (Codemap refresh)
プロジェクト: BI Tool (社内BI・Pythonカード MVP)
ステージ: MVP

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
                       |  [Scheduler]     |  <-- asyncio バックグラウンドタスク
                       |  [AuditService]  |  <-- 監査ログ記録
                       +---+---------+----+
                           |         |
              +------------+----+----+-----------+
              |                 |                 |
     +--------+------+  +------+------+  +-------+-------+
     |  DynamoDB     |  |    S3       |  |   Executor    |
     | (11テーブル)  |  | (Parquet)   |  |  (Python実行) |
     |  :8001        |  | MinIO :9000 |  |  :8080        |
     +---------------+  +-------------+  +---------------+
```

## サービス一覧

| サービス | 技術 | ポート | 役割 | ヘルスチェック |
|----------|------|--------|------|---------------|
| frontend | React 18 + Vite 5 + TypeScript | 3000 | SPA フロントエンド | - |
| api (backend) | FastAPI 0.109 + Python 3.11 | 8000 | REST API サーバ + Scheduler | GET /api/health |
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
      models/          # Pydantic モデル (12ファイル)
      repositories/    # DynamoDB リポジトリ (CRUD, 11リポジトリ)
      services/        # ビジネスロジック (11サービス + AuditService)
    tests/             # pytest テスト (61テストファイル)
  frontend/            # React SPA
    src/
      components/      # UI コンポーネント (transform/ 含む)
      hooks/           # React Query hooks (use-audit-logs 含む)
      lib/             # API クライアント (audit-logs API 含む)
      pages/           # ページコンポーネント (AuditLogListPage 含む)
      stores/          # Zustand ストア
      types/           # TypeScript 型定義 (audit-log.ts 含む)
      __tests__/       # Vitest テスト (64ファイル)
    e2e/               # Playwright E2E テスト (4スペック)
    playwright.config.ts
    vitest.config.ts
  executor/            # Python 実行サンドボックス
    app/               # FastAPI アプリ
    tests/             # pytest テスト (6ファイル)
  scripts/             # 初期化・ユーティリティスクリプト
    init_tables.py     # DynamoDB テーブル作成 (11テーブル)
    seed_test_user.py  # E2E テストユーザ作成
  codemaps/            # アーキテクチャ・コードマップ
  docs/                # 設計ドキュメント (10ファイル)
  docker-compose.yml   # ローカル開発環境 (ヘルスチェック付き)
```

## サービス間通信

```
[Frontend :3000]
    |
    +--> GET/POST /api/auth/*      --> [Backend :8000] --> [DynamoDB] + [AuditLog]
    +--> GET/POST /api/datasets/*  --> [Backend :8000] --> [DynamoDB] + [S3/MinIO] + [AuditLog]
    +--> GET /api/datasets/:id/columns/:col/values --> [Backend :8000] --> [S3/MinIO]
    +--> GET/POST /api/cards/*     --> [Backend :8000] --> [DynamoDB] + [AuditLog]
    +--> POST /api/cards/:id/execute --> [Backend :8000]
    |                                       |
    |                                       +--> POST /execute/card --> [Executor :8080]
    |                                       +--> DynamoDB (cache)
    |                                       +--> S3 (dataset)
    |                                       +--> [AuditLog] (失敗時)
    +--> POST /api/dashboards/:id/clone --> [Backend :8000] --> [DynamoDB]
    +--> GET/POST /api/dashboards/:id/shares/* --> [Backend :8000] --> [DynamoDB] + [AuditLog]
    +--> GET/POST /api/groups/*    --> [Backend :8000] --> [DynamoDB]
    +--> GET /api/users?q=...      --> [Backend :8000] --> [DynamoDB]
    +--> GET/POST /api/transforms/*  --> [Backend :8000] --> [DynamoDB] + [AuditLog]
    +--> POST /api/transforms/:id/execute --> [Backend :8000]
    |                                       |
    |                                       +--> S3 (入力Dataset読込)
    |                                       +--> POST /execute/transform --> [Executor :8080]
    |                                       +--> S3 (出力Dataset保存)
    |                                       +--> DynamoDB (execution履歴 + Dataset作成)
    |                                       +--> [AuditLog] (成功/失敗)
    +--> GET /api/transforms/:id/executions --> [Backend :8000] --> [DynamoDB]
    +--> GET /api/audit-logs --> [Backend :8000] --> [DynamoDB] (admin専用)

[Scheduler (Backend内 asyncio タスク)]
    |
    +--> DynamoDB: schedule_enabled=true の Transform を scan
    +--> croniter で実行タイミング判定
    +--> TransformExecutionService.execute(triggered_by="schedule")
```

## 認証フロー

```
1. ブラウザ --> POST /api/auth/login { email, password }
2. Backend: DynamoDB から User 取得 --> bcrypt 検証 --> JWT 発行
3. Backend: api_response() でラップ { data: { access_token, user, ... } }
4. Backend: AuditService.log_user_login() (成功時) / log_user_login_failed() (失敗時)
5. ブラウザ: Zustand ストアに token 保存
6. 以降のリクエスト: Authorization: Bearer <JWT>
7. Backend: deps.get_current_user() で JWT 検証
```

## 認可レイヤー (Permission / Authorization)

### 1. ロールベース認可 (require_admin 依存性)

```
app/api/deps.py :: require_admin()

  get_current_user() で JWT を検証した後、user.role == "admin" を確認。
  admin でなければ HTTP 403 を返す。

  適用先:
    - /api/groups/*           (グループ CRUD + メンバー管理)
    - /api/audit-logs         (監査ログ閲覧)
```

グループ管理と監査ログは管理者専用操作であるため、全エンドポイントで require_admin を Depends に指定している。

### 2. ダッシュボード権限 (PermissionService)

```
app/services/permission_service.py :: PermissionService

  権限レベル (低 -> 高):
    VIEWER (1) < EDITOR (2) < OWNER (3)

  権限解決フロー (get_user_permission):
    1. dashboard.owner_id == user_id --> OWNER を即返却
    2. bi_dashboard_shares テーブルから該当ダッシュボードの全 share を取得
    3. bi_group_members テーブルからユーザが所属する全グループ ID を取得
    4. share を走査し、以下のいずれかに該当する share の権限を収集:
       - shared_to_type == USER かつ shared_to_id == user_id (直接共有)
       - shared_to_type == GROUP かつ shared_to_id がユーザ所属グループに含まれる (グループ共有)
    5. 収集した権限のうち最も高いレベルを返却 (該当なしなら None)

  メソッド:
    - get_user_permission(dashboard, user_id, dynamodb) -> Optional[Permission]
    - check_permission(dashboard, user_id, required, dynamodb) -> bool
    - assert_permission(dashboard, user_id, required, dynamodb) -> None (403 raise)
```

### ダッシュボード共有の管理

```
app/api/routes/dashboard_shares.py

  全操作はダッシュボードオーナーのみ実行可能 (_get_dashboard_as_owner で検証)。
  全操作で AuditService による監査ログ記録を実施。

  エンドポイント:
    GET    /api/dashboards/{id}/shares       -- 共有一覧取得
    POST   /api/dashboards/{id}/shares       -- 共有作成 (重複時 409) + AuditLog
    PUT    /api/dashboards/{id}/shares/{sid}  -- 権限レベル変更 + AuditLog
    DELETE /api/dashboards/{id}/shares/{sid}  -- 共有解除 + AuditLog

  共有ターゲット (SharedToType):
    - USER  -- 特定ユーザへの直接共有
    - GROUP -- グループ単位の共有
```

## 監査ログ (Audit Log)

```
app/services/audit_service.py :: AuditService

  監査ログは火-and-forget パターンで記録 (例外は握りつぶし、ビジネスロジックに影響しない)。

  記録対象イベント (EventType):
    - USER_LOGIN               -- ログイン成功
    - USER_LOGOUT              -- ログアウト
    - USER_LOGIN_FAILED        -- ログイン失敗 (email + reason)
    - DASHBOARD_SHARE_ADDED    -- ダッシュボード共有追加
    - DASHBOARD_SHARE_REMOVED  -- ダッシュボード共有削除
    - DASHBOARD_SHARE_UPDATED  -- ダッシュボード共有権限更新
    - DATASET_CREATED          -- データセット作成
    - DATASET_IMPORTED         -- データセットインポート (S3, reimport)
    - DATASET_DELETED          -- データセット削除
    - TRANSFORM_EXECUTED       -- Transform 実行成功
    - TRANSFORM_FAILED         -- Transform 実行失敗
    - CARD_EXECUTION_FAILED    -- カード実行失敗

  呼び出し元ルート:
    auth.py            --> log_user_login, log_user_logout, log_user_login_failed
    cards.py           --> log_card_execution_failed (preview/execute 失敗時)
    datasets.py        --> log_dataset_created, log_dataset_imported, log_dataset_deleted
    dashboard_shares.py --> log_dashboard_share_added/removed/updated
    transforms.py      --> log_transform_executed, log_transform_failed
```

## データフロー: CSV インポート

```
1. ブラウザ: FormData で CSV アップロード
2. Backend: CSV パース (chardet + pandas)
3. Backend: 型推論 (type_inferrer)
4. Backend: Parquet 変換 + S3 保存 (parquet_storage)
5. Backend: メタデータを DynamoDB に保存 (dataset_repository)
6. Backend: AuditService.log_dataset_created()
7. Backend: api_response() でラップして返却
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
(失敗時: AuditService.log_card_execution_failed())
```

## データフロー: Transform 実行

```
手動実行:
1. ブラウザ: POST /api/transforms/:id/execute
2. Backend: オーナー検証
3. TransformExecutionService: execution 履歴レコード作成 (status=running)
4. TransformExecutionService: 入力 Dataset を DynamoDB から取得
5. TransformExecutionService: 入力 Parquet を S3 から読込 (ParquetReader)
6. TransformExecutionService: Executor API に POST /execute/transform (リトライ付き)
7. Executor: Python コードで DataFrame 変換を実行
8. TransformExecutionService: 出力 DataFrame を Parquet に変換 + S3 保存
9. TransformExecutionService: 出力 Dataset レコードを DynamoDB に作成 (source_type="transform")
10. TransformExecutionService: Transform.output_dataset_id を更新
11. TransformExecutionService: execution 履歴を success/failed に更新
12. Backend: AuditService.log_transform_executed() / log_transform_failed()

スケジュール実行:
1. TransformSchedulerService: asyncio ループで scheduler_interval_seconds 毎にチェック
2. schedule_enabled=true の Transform を DynamoDB scan
3. croniter で実行タイミング判定 (前回実行からの差分 < interval)
4. 実行中の execution がないことを確認 (重複防止)
5. TransformExecutionService.execute(triggered_by="schedule") を呼出
```

### Transform リトライ戦略

```
- 最大リトライ: 3回
- バックオフ: 指数バックオフ (0.5s, 1s, 2s)
- リトライ対象: 接続エラー、タイムアウト、5xx エラー
- 即時失敗: 4xx クライアントエラー
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

## DynamoDB テーブル一覧 (11テーブル)

| テーブル名 | PK | SK | 主な GSI | 用途 |
|-----------|-----|-----|---------|------|
| bi_users | userId | - | UsersByEmail | ユーザ認証・プロフィール |
| bi_datasets | datasetId | - | DatasetsByOwner | データセットメタデータ |
| bi_cards | cardId | - | CardsByOwner | カード (Pythonコード + 設定) |
| bi_dashboards | dashboardId | - | DashboardsByOwner | ダッシュボード定義 |
| bi_filter_views | filterViewId | - | FilterViewsByDashboard | フィルタビュー保存 |
| bi_groups | groupId | - | GroupsByName | グループ定義 [FR-7] |
| bi_group_members | groupId | userId | MembersByUser | グループメンバーシップ [FR-7] |
| bi_dashboard_shares | shareId | - | SharesByDashboard, SharesByTarget | ダッシュボード共有設定 [FR-7] |
| bi_transforms | transformId | - | TransformsByOwner | Transform 定義 [FR-2.1] |
| bi_transform_executions | transformId | startedAt | - | Transform 実行履歴 [FR-2.1] |
| bi_audit_logs | logId | timestamp | LogsByUser, LogsByTarget | 監査ログ |

## リポジトリ一覧 (11リポジトリ)

| リポジトリ | 対象テーブル | ベースクラス | 備考 |
|-----------|-------------|-------------|------|
| UserRepository | bi_users | BaseRepository | email GSI 検索, scan_by_email_prefix |
| DatasetRepository | bi_datasets | BaseRepository | owner 別一覧 |
| CardRepository | bi_cards | BaseRepository | owner 別一覧 |
| DashboardRepository | bi_dashboards | BaseRepository | owner 別一覧 |
| FilterViewRepository | bi_filter_views | BaseRepository | dashboard 別一覧 |
| GroupRepository | bi_groups | BaseRepository | name ユニーク検証 [FR-7] |
| GroupMemberRepository | bi_group_members | (独自実装) | 複合キー操作, MembersByUser GSI [FR-7] |
| DashboardShareRepository | bi_dashboard_shares | BaseRepository | dashboard 別/target 別検索, 重複検出 [FR-7] |
| TransformRepository | bi_transforms | BaseRepository | owner 別一覧 [FR-2.1] |
| TransformExecutionRepository | bi_transform_executions | BaseRepository | 複合キー (transformId+startedAt), has_running_execution [FR-2.1] |
| AuditLogRepository | bi_audit_logs | BaseRepository | 複合キー (logId+timestamp), GSI: LogsByUser, LogsByTarget |

## サービス一覧 (12サービス)

| サービス | モジュール | 役割 |
|---------|-----------|------|
| DatasetService | dataset_service.py | CSV/S3インポート、プレビュー、再取込 |
| DashboardService | dashboard_service.py | ダッシュボード CRUD + クローン |
| CardExecutionService | card_execution_service.py | カード Python 実行 + キャッシュ |
| PermissionService | permission_service.py | ダッシュボード権限解決 |
| TransformExecutionService | transform_execution_service.py | Transform 実行オーケストレーション [FR-2.1] |
| TransformSchedulerService | transform_scheduler_service.py | asyncio cron スケジューラ [FR-2.1] |
| AuditService | audit_service.py | 監査ログ記録 (fire-and-forget) |
| CsvParser | csv_parser.py | CSV パース (chardet) |
| TypeInferrer | type_inferrer.py | カラム型推論 |
| ParquetStorage | parquet_storage.py | Parquet 変換 + S3 読み書き |
| SchemaComparator | schema_comparator.py | スキーマ変更検知 [FR-1.3] |
| setup_logging | logging.py | structlog 設定 |

## APIルーター一覧

| プレフィックス | タグ | モジュール | 認可 |
|---------------|------|-----------|------|
| /api/auth | auth | auth.py | なし (ログイン/登録) |
| /api/datasets | datasets | datasets.py | get_current_user |
| /api/dashboards | dashboards | dashboards.py | get_current_user |
| /api/cards | cards | cards.py | get_current_user |
| /api/dashboards/{id}/filter-views | filter-views | filter_views.py | get_current_user |
| /api/filter-views | filter-views | filter_view_detail.py | get_current_user |
| /api/users | users | users.py | get_current_user |
| /api/dashboards/{id}/shares | dashboard-shares | dashboard_shares.py | get_current_user + owner検証 |
| /api/groups | groups | groups.py | require_admin |
| /api/transforms | transforms | transforms.py | get_current_user + owner検証 [FR-2.1] |
| /api/audit-logs | audit-logs | audit_logs.py | require_admin |

## フロントエンド ルーティング

| パス | ページコンポーネント | 備考 |
|------|---------------------|------|
| /login | LoginPage | 認証不要 |
| /dashboards | DashboardListPage | デフォルトリダイレクト先 |
| /dashboards/:id | DashboardViewPage | |
| /dashboards/:id/edit | DashboardEditPage | |
| /datasets | DatasetListPage | |
| /datasets/import | DatasetImportPage | |
| /datasets/:id | DatasetDetailPage | |
| /cards | CardListPage | |
| /cards/:id | CardEditPage | |
| /transforms | TransformListPage | [FR-2.1] |
| /transforms/:id | TransformEditPage | [FR-2.1] |
| /admin/groups | GroupListPage | admin のみ表示 |
| /admin/audit-logs | AuditLogListPage | admin のみ表示 |

## フロントエンド Transform コンポーネント [FR-2.1]

| コンポーネント | 役割 |
|---------------|------|
| TransformListPage | Transform 一覧ページ |
| TransformEditPage | Transform 作成/編集ページ |
| TransformCodeEditor | Python コードエディタ (Monaco) |
| DatasetMultiSelect | 入力 Dataset 複数選択 |
| TransformScheduleConfig | cron スケジュール設定 |
| TransformExecutionResult | 実行結果表示 |
| TransformExecutionHistory | 実行履歴一覧 |

## スケジューラ アーキテクチャ [FR-2.1]

```
Backend API プロセス (main.py lifespan)
  |
  +--> settings.scheduler_enabled == True の場合のみ起動
  |
  +--> TransformSchedulerService
         |
         +--> asyncio.create_task(_run_loop)
         |       |
         |       +--> _check_and_execute() (毎 scheduler_interval_seconds 秒)
         |              |
         |              +--> aioboto3 セッション作成 (DynamoDB + S3)
         |              +--> schedule_enabled=true の Transform を全件 scan
         |              +--> croniter で実行判定
         |              +--> 実行中チェック (has_running_execution)
         |              +--> TransformExecutionService.execute()
         |
         +--> lifespan shutdown 時に task.cancel()

設定値:
  - SCHEDULER_ENABLED: bool (デフォルト: False)
  - SCHEDULER_INTERVAL_SECONDS: int (デフォルト: 60秒)
  - TRANSFORM_TIMEOUT_SECONDS: int (デフォルト: 300秒 = 5分)
```

## APIレスポンス標準化

全APIルートが `api/response.py` のヘルパーを使用:

| ヘルパー | 出力形式 | 使用場面 |
|---------|---------|---------|
| `api_response(data)` | `{ "data": T }` | 単体リソース取得、作成、更新 |
| `paginated_response(items, total, limit, offset)` | `{ "data": [...], "pagination": {...} }` | 一覧取得 (datasets, cards, dashboards, transforms, audit-logs) |

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
| croniter | >=2.0.0 | cron式パース (Transform スケジューラ) [FR-2.1] |
| httpx | 0.25.2 | 非同期 HTTP クライアント (Executor 呼出) |

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
| @playwright/test | 1.58.1 | E2E テスト |

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
| Frontend (Unit) | Vitest + Testing Library | 64 | - |
| Frontend (E2E) | Playwright | 4 specs | - |
| Backend | pytest | 61 | - |
| Executor | pytest | 8 | - |

### E2E テスト構成

```
frontend/e2e/
  global-setup.ts          # バックエンド起動待機 (ヘルスチェック)
  auth.spec.ts             # 認証フロー
  dataset.spec.ts          # CSVインポート、一覧、プレビュー
  card-dashboard.spec.ts   # カード/ダッシュボード CRUD
  sharing.spec.ts          # Dashboard共有フロー, Group管理 [FR-7]
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
| SCHEDULER_ENABLED | Transform スケジューラ有効化 | False [FR-2.1] |
| SCHEDULER_INTERVAL_SECONDS | スケジューラチェック間隔 | 60 [FR-2.1] |
| TRANSFORM_TIMEOUT_SECONDS | Transform 実行タイムアウト | 300 [FR-2.1] |

## 関連コードマップ

- [backend.md](./backend.md) - バックエンド構造詳細
- [frontend.md](./frontend.md) - フロントエンド構造詳細
- [data.md](./data.md) - データモデルとスキーマ
