# 運用ランブック (RUNBOOK)

最終更新: 2026-02-04

---

## 1. 環境一覧

| 環境 | フロントエンド | API | 用途 |
|------|---------------|-----|------|
| local | http://localhost:3000 | http://localhost:8000 | 開発・テスト |
| staging | https://bi-staging.internal.company.com | 内部ALB | 検証環境 |
| production | https://bi.internal.company.com | 内部ALB | 本番環境 |

### ローカル環境サービス一覧

| サービス | ポート | 用途 |
|---------|--------|------|
| frontend | 3000 | React SPA (Vite) |
| api | 8000 | FastAPI |
| executor | 8080 | Python Sandbox (Card/Transform実行) |
| dynamodb-local | 8001 (外部) / 8000 (内部) | DynamoDB互換DB |
| minio | 9000 (API) / 9001 (Console) | S3互換ストレージ |

---

## 2. デプロイ

### ローカル

```bash
# 起動
docker compose up --build

# バックグラウンド起動
docker compose up -d --build

# 停止
docker compose down

# 停止 + データ削除 (DynamoDB/MinIO)
docker compose down -v
```

### AWS (ECS Fargate)

```bash
# API
docker build -t bi-api:latest -f backend/Dockerfile.dev backend/
docker tag bi-api:latest <account-id>.dkr.ecr.ap-northeast-1.amazonaws.com/bi-api:$(git rev-parse --short HEAD)
docker push <account-id>.dkr.ecr.ap-northeast-1.amazonaws.com/bi-api:$(git rev-parse --short HEAD)
aws ecs update-service --cluster bi-cluster --service bi-api-service --force-new-deployment

# Executor
docker build -t bi-executor:latest -f executor/Dockerfile executor/
docker tag bi-executor:latest <account-id>.dkr.ecr.ap-northeast-1.amazonaws.com/bi-executor:$(git rev-parse --short HEAD)
docker push <account-id>.dkr.ecr.ap-northeast-1.amazonaws.com/bi-executor:$(git rev-parse --short HEAD)
aws ecs update-service --cluster bi-cluster --service bi-executor-service --force-new-deployment

# フロントエンド
cd frontend && npm ci && npm run build
aws s3 sync dist/ s3://bi-static-<env>/ --delete
aws cloudfront create-invalidation --distribution-id <id> --paths "/*"
```

### デプロイ前チェック

| チェック | コマンド | 基準 |
|---------|---------|------|
| フロントエンド lint | `npm run lint` | エラーなし |
| フロントエンド type | `npm run typecheck` | エラーなし |
| フロントエンド test | `npm run test:coverage` | 83%+ |
| バックエンド lint | `ruff check app/` | エラーなし |
| バックエンド type | `mypy app/` | エラーなし |
| バックエンド test | `pytest --cov=app` | pass |

---

## 3. ヘルスチェック

| サービス | エンドポイント | 期待値 |
|---------|---------------|--------|
| API | `GET /api/health` | `{"status": "ok"}` |
| Executor | `GET /health` | `{"status": "ok"}` |

```bash
# ローカル環境
curl -s http://localhost:8000/api/health | jq .
curl -s http://localhost:8080/health | jq .

# Docker内部
docker compose exec api curl -s http://localhost:8000/api/health
docker compose exec executor curl -s http://localhost:8080/health
```

---

## 4. 監視

### メトリクス (CloudWatch)

| メトリクス | Warning | Critical | 対応 |
|-----------|---------|----------|------|
| API レスポンスタイム (p95) | > 5秒 | > 10秒 | スケールアップ/クエリ最適化 |
| API エラーレート (5xx) | > 5% | > 10% | ログ確認/ロールバック検討 |
| Executor タイムアウト率 | > 10% | > 20% | カードコード見直し |
| Transform 失敗率 | > 20% | > 30% | Executorログ確認、コードレビュー |
| ECS CPU使用率 | > 80% | > 90% | タスク数増加 |
| ECS メモリ使用率 | > 80% | > 90% | タスク数増加/メモリ増加 |

### ログ

| サービス | 出力先 | フォーマット |
|---------|--------|-------------|
| API | CloudWatch `/ecs/bi-<env>-api` | JSON |
| Executor | CloudWatch `/ecs/bi-<env>-executor` | JSON |
| フロントエンド | CloudFront / S3 Access Logs | CLF |

```bash
# ログ確認
aws logs tail /ecs/bi-production-api --follow

# エラーのみ抽出
aws logs filter-log-events --log-group-name /ecs/bi-production-api \
  --filter-pattern "ERROR" --start-time $(date -d '1 hour ago' +%s)000
```

---

## 5. トラブルシューティング

### API起動失敗

```bash
# ログ確認
docker compose logs api

# 環境変数確認
docker compose exec api env | sort

# DynamoDB接続確認
docker compose exec api python -c "from app.db.dynamodb import get_table; print(get_table('bi_users'))"
```

### カード実行タイムアウト

| 原因 | 診断 | 対策 |
|------|------|------|
| Pythonコードが重い | 実行時間ログ確認 | pandasベクトル演算を使用 |
| データセットが大きい | row_count確認 | フィルタで絞り込む |
| Executorリソース不足 | ECS メトリクス | CPU/メモリ増加 |
| 無限ループ | タイムアウトログ | コードレビュー |

### CSVインポート失敗

| 原因 | エラーメッセージ | 対策 |
|------|----------------|------|
| ファイルサイズ超過 | "File too large" | 100MB以下に分割 |
| 文字コード | "Encoding error" | utf-8/shift_jis/cp932 を明示指定 |
| 不正なCSV形式 | "CSV parse error" | 区切り文字・ヘッダ設定確認 |

### JWT認証エラー (401)

| 原因 | 確認方法 | 対策 |
|------|---------|------|
| トークン有効期限切れ | jwt decode | 再ログイン |
| SECRET_KEY不一致 | 環境変数比較 | 全サービスで同一キーを設定 |
| トークン形式不正 | Authorization header | "Bearer <token>" 形式確認 |

### DynamoDBテーブルが見つからない

```bash
# テーブル一覧確認
aws dynamodb list-tables --endpoint-url http://localhost:8001 --region ap-northeast-1

# テーブル再作成
docker compose run --rm dynamodb-init
```

現在のテーブル一覧:

init_tables.py で自動作成されるテーブル (10テーブル):
- `bi_users` - ユーザー (GSI: UsersByEmail)
- `bi_datasets` - データセット (GSI: DatasetsByOwner)
- `bi_cards` - カード (GSI: CardsByOwner)
- `bi_dashboards` - ダッシュボード (GSI: DashboardsByOwner)
- `bi_filter_views` - フィルタビュー (GSI: FilterViewsByDashboard)
- `bi_groups` - グループ (GSI: GroupsByName)
- `bi_group_members` - グループメンバー (GSI: MembersByUser)
- `bi_dashboard_shares` - ダッシュボード共有 (GSI: SharesByDashboard, SharesByTarget)
- `bi_transforms` - Transform (GSI: TransformsByOwner)
- `bi_transform_executions` - Transform実行履歴 (PK: transformId, SK: startedAt)

### FilterView可視性

| 条件 | 結果 |
|------|------|
| owner | 常に可視 |
| owner以外 + is_shared=false | 不可視 (403) |
| owner以外 + is_shared=true + Dashboard権限あり | 可視 |

### Dashboard共有エラー

| HTTPステータス | 原因 | 対策 |
|---------------|------|------|
| 403 | オーナー以外が共有管理 | オーナーでログイン |
| 404 | ダッシュボード/共有が存在しない | ID確認 |
| 409 | 同一対象への共有が既存 | PUT で権限更新 |

### Transform実行エラー

| HTTPステータス | 原因 | 対策 |
|---------------|------|------|
| 400 | 入力Datasetが見つからない/データなし | Dataset ID確認、データ再取り込み |
| 403 | オーナー以外が実行 | オーナーでログイン |
| 404 | Transformが見つからない | Transform ID確認 |
| 500 | Executor実行失敗 | Executorログ確認、コードレビュー |

| 原因 | 診断 | 対策 |
|------|------|------|
| transform関数が未定義 | エラーメッセージ確認 | コードに`def transform(inputs, params):`を定義 |
| 戻り値がDataFrameでない | エラーメッセージ確認 | DataFrameを返すように修正 |
| タイムアウト (300秒超過) | Executorログ確認 | コードの最適化、データ量削減 |
| メモリ超過 (4096MB) | リソースモニタリング | データ量削減、処理の分割 |

Transform コード規約:
```python
def transform(inputs, params):
    # inputs: dict[str, DataFrame] -- 入力Dataset (キー: dataset_id)
    # params: dict -- パラメータ (現在未使用)
    # 戻り値: DataFrame (必須)
    sales = inputs['ds_xxxx']
    result = sales.groupby('category').sum()
    return result
```

### Dataset再取り込み (スキーマ変更) エラー

| HTTPステータス | 原因 | 対策 |
|---------------|------|------|
| 200 (pending_confirmation) | スキーマ変更を検知 | schema_changes を確認し、force=true で再リクエスト |
| 400 | ソースファイルが見つからない | S3キー/ローカルファイル確認 |

スキーマ変更の種類:
- `column_added` - 新しい列が追加された
- `column_removed` - 既存の列が削除された (破壊的変更)
- `type_changed` - 列の型が変更された (破壊的変更)

### グループ管理

| HTTPステータス | 原因 | 対策 |
|---------------|------|------|
| 403 | admin以外がアクセス | adminユーザーでログイン |
| 409 | 同名グループが既存 | 別名を使用 |

---

## 6. ロールバック

### ECS

```bash
# 前のリビジョンを確認
aws ecs list-task-definitions --family-prefix bi-api --sort DESC --max-items 5

# ロールバック
aws ecs update-service --cluster bi-cluster --service bi-api-service --task-definition bi-api:<revision>

# デプロイ状況確認
aws ecs describe-services --cluster bi-cluster --services bi-api-service \
  --query 'services[0].deployments'
```

### フロントエンド

```bash
# バックアップから復元
aws s3 sync s3://bi-static-<env>-backup/ s3://bi-static-<env>/ --delete

# CloudFrontキャッシュ無効化
aws cloudfront create-invalidation --distribution-id <id> --paths "/*"
```

### データベース (DynamoDB)

- Point-in-Time Recovery (PITR) が有効な場合:
```bash
aws dynamodb restore-table-to-point-in-time \
  --source-table-name bi_dashboards \
  --target-table-name bi_dashboards_restored \
  --restore-date-time 2026-02-03T10:00:00Z
```

---

## 7. スケーリング

### 推奨構成

| 同時ユーザ | API タスク | Executor タスク | CPU/メモリ |
|-----------|-----------|----------------|-----------|
| ~10 | 2 | 2 | 0.5vCPU / 1GB |
| 10-30 | 4 | 4 | 1vCPU / 2GB |
| 30-50 | 6 | 8 | 2vCPU / 4GB |

```bash
# API スケール
aws ecs update-service --cluster bi-cluster --service bi-api-service --desired-count 4

# Executor スケール
aws ecs update-service --cluster bi-cluster --service bi-executor-service --desired-count 4
```

### Auto Scaling設定

```bash
# Target Tracking Policy (CPU 70%)
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --scalable-dimension ecs:service:DesiredCount \
  --resource-id service/bi-cluster/bi-api-service \
  --min-capacity 2 \
  --max-capacity 10
```

### Executor リソース制限

| 実行タイプ | CPU | メモリ | タイムアウト | ディスク |
|-----------|-----|--------|------------|---------|
| Card実行 | 1 vCPU | 2048 MB | 10秒 | 1 GB |
| Transform実行 | 2 vCPU | 4096 MB | 300秒 | 10 GB |

---

## 8. 定期メンテナンス

| 頻度 | タスク | 担当 |
|------|--------|------|
| 日次 | エラーログ確認、監視アラート確認 | 運用担当 |
| 週次 | `pip audit` / `npm audit`、ストレージ使用量確認 | 開発担当 |
| 月次 | 依存パッケージ更新、セキュリティパッチ適用 | 開発担当 |
| 四半期 | コスト最適化レビュー、性能テスト | チーム |

### セキュリティ監査コマンド

```bash
# Python依存関係
cd backend && pip-audit

# Node.js依存関係
cd frontend && npm audit

# Dockerイメージスキャン
docker scan bi-api:latest
```

---

## 9. セキュリティ

### 秘匿情報管理

| 環境 | 管理方法 |
|------|---------|
| ローカル | `.env` ファイル (Gitignore) |
| ステージング/本番 | AWS Secrets Manager |

### 必須セキュリティ設定

| 項目 | 要件 |
|------|------|
| `JWT_SECRET_KEY` | 32文字以上のランダム文字列 |
| S3バケット | パブリックアクセスブロック有効 |
| DynamoDB | 暗号化有効 (AWS managed key) |
| CloudFront | HTTPS強制、TLS 1.2以上 |

### Executor サンドボックス

| 制限 | 値 |
|------|-----|
| 実行ユーザー | 非root (appuser) |
| タイムアウト | カード 10秒, Transform 300秒 |
| メモリ | カード 2048MB, Transform 4096MB |
| ネットワーク | S3 VPCエンドポイントのみ |
| ブロックモジュール | `os`, `sys`, `subprocess`, `socket`, `http`, `requests`, `pickle` 等 |

---

## 10. エスカレーション

| 重大度 | 条件 | 対応時間 | 連絡先 |
|--------|------|---------|--------|
| Critical | 全面停止、データ損失 | 即時 | オンコール担当 |
| High | 5xxエラー 10%超、主要機能停止 | 1時間以内 | 開発リード |
| Medium | パフォーマンス劣化、一部機能障害 | 営業時間内 | 運用担当 |
| Low | 軽微なUI問題、非重要機能 | 次営業日 | チケット起票 |

---

## 11. バックアップ・リカバリ

### DynamoDB

| 設定 | 値 |
|------|-----|
| Point-in-Time Recovery | 有効 (35日間) |
| オンデマンドバックアップ | 週次 (日曜深夜) |

### S3

| バケット | バージョニング | ライフサイクル |
|---------|--------------|---------------|
| bi-datasets | 有効 | 90日後にGlacier移行 |
| bi-static | 無効 | - |
| bi-static-backup | 有効 | 30日後に削除 |

### リカバリ手順

1. 障害発生時刻を特定
2. PITR で復元テーブル作成
3. 復元テーブルの整合性確認
4. テーブル名をリネーム or アプリ設定変更
5. 正常性確認

---

## 12. 機能別運用メモ

### Transform (FR-2.1/2.2/2.3) -- 2026-02-04 更新

Transform は Python コードで複数の Dataset を入力として受け取り、新しい Dataset を出力する ETL 機能。

運用上の注意点:
- 手動実行は同期処理 (API レスポンスが返るまで最大300秒ブロック)
- 実行履歴は `bi_transform_executions` テーブルに自動記録される (status: running/success/failed)
- Transform の出力 Dataset は `source_type: "transform"` で記録される
- 同時実行数上限: `EXECUTOR_MAX_CONCURRENT_TRANSFORMS` (デフォルト 5)

#### スケジュール実行

環境変数でスケジューラーを有効化:
```
SCHEDULER_ENABLED=true          # スケジューラー有効化 (デフォルト: false)
SCHEDULER_INTERVAL_SECONDS=60   # チェック間隔 (デフォルト: 60秒)
```

スケジューラー動作確認:
```bash
# ログでスケジューラー開始を確認
docker compose logs api | grep "scheduler"

# Transform のスケジュール設定を確認
curl -s http://localhost:8000/api/transforms -H "Authorization: Bearer <token>" | jq '.data[] | {id, name, schedule_cron, schedule_enabled}'
```

スケジューラーの仕様:
- asyncio バックグラウンドタスクとして API プロセス内で実行
- `SCHEDULER_INTERVAL_SECONDS` 間隔で `schedule_enabled=true` の Transform を DynamoDB scan
- cron 式に基づいて実行タイミングを判定 (croniter 使用)
- 実行中の Transform (status=running) はスキップ (重複実行防止)
- 実行は `triggered_by: "schedule"` として実行履歴に記録

#### 実行履歴

実行履歴 API:
```bash
# Transform の実行履歴を取得
curl -s http://localhost:8000/api/transforms/<transform_id>/executions -H "Authorization: Bearer <token>" | jq .
```

実行履歴のフィールド:
- `execution_id` - 実行 ID
- `status` - running / success / failed
- `started_at` / `finished_at` - 開始/終了時刻
- `duration_ms` - 実行時間 (ミリ秒)
- `output_row_count` - 出力行数
- `error` - エラーメッセージ (失敗時)
- `triggered_by` - manual / schedule

Transform 実行障害時の確認手順:
```bash
# 1. 実行履歴を確認
curl -s http://localhost:8000/api/transforms/<transform_id>/executions -H "Authorization: Bearer <token>" | jq '.data[0]'

# 2. Executor ログ確認
docker compose logs executor | grep -i transform

# 3. Transform の入力 Dataset が存在するか確認
curl -s http://localhost:8000/api/datasets/<dataset_id> -H "Authorization: Bearer <token>" | jq .

# 4. Executor ヘルスチェック
curl -s http://localhost:8080/health | jq .
```

### Dataset再取り込み (FR-1.3) -- 2026-02-03 追加

再取り込み時のスキーマ変更検知フロー:
1. `POST /api/datasets/{id}/import` (force=false) で再取り込みリクエスト
2. スキーマ変更がある場合 `import_status: "pending_confirmation"` が返る
3. フロントエンド `SchemaChangeWarningDialog` で変更内容を表示
4. ユーザーが続行を選択した場合 force=true で再リクエスト
5. 破壊的変更 (列削除・型変更) がある場合は依存する Card/Transform に影響がある可能性があるため注意
