# 運用ランブック (RUNBOOK)

**最終更新:** 2026-02-02
**プロジェクト:** 社内BI・Pythonカード MVP
**フェーズ:** Phase Q4 (E2E) + Q5 (クリーンアップ) + FilterView / S3 Import 実装中

---

## 1. 環境一覧

| 環境 | 用途 | フロントエンドURL | API URL |
|------|------|------------------|---------|
| local | 開発 | http://localhost:3000 | http://localhost:8000 |
| staging | 検証 | https://bi-staging.internal.company.com | 内部ALB |
| production | 本番 | https://bi.internal.company.com | 内部ALB |

**サービス構成:**

| サービス | テクノロジー | ポート (local) | AWS (staging/prod) |
|---------|------------|---------|------------------|
| Frontend | React 18 + Vite 5 | 3000 | S3 + CloudFront |
| API | FastAPI 0.109 + Uvicorn | 8000 | ECS Fargate |
| Executor | Python 3.11 サンドボックス | 8080 | ECS Fargate (ネットワーク隔離) |
| Database | DynamoDB | 8001 (DynamoDB Local) | DynamoDB (オンデマンド) |
| Storage | S3 | 9000/9001 (MinIO) | S3 (バージョニング有効) |

---

## 2. デプロイ手順

### 2.1 ローカル開発環境

```bash
# 起動
docker compose up --build

# 停止
docker compose down

# データをリセットして起動 (DynamoDB / MinIO のデータを削除)
docker compose down -v && docker compose up --build
```

### 2.2 AWS ステージング / 本番デプロイ

本番環境は AWS ECS Fargate 上で稼働します。デプロイは以下のコンポーネント単位で行います。

#### 2.2.1 前提条件

- AWS CLI が設定済みであること
- ECR リポジトリが作成済みであること
- ECS クラスタ、サービス、タスク定義が設定済みであること
- 必要なシークレットが Secrets Manager に登録されていること
  - `JWT_SECRET_KEY` (最低32文字のランダム文字列)
  - `VERTEX_AI_PROJECT_ID`

#### 2.2.2 バックエンド (API) デプロイ

```bash
# 1. Docker イメージをビルド
docker build -t bi-api:latest -f backend/Dockerfile.dev backend/

# 2. ECR にタグ付けしてプッシュ
aws ecr get-login-password --region ap-northeast-1 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.ap-northeast-1.amazonaws.com
docker tag bi-api:latest <account-id>.dkr.ecr.ap-northeast-1.amazonaws.com/bi-api:$(git rev-parse --short HEAD)
docker push <account-id>.dkr.ecr.ap-northeast-1.amazonaws.com/bi-api:$(git rev-parse --short HEAD)

# 3. ECS サービスを更新 (新リビジョンのタスク定義でデプロイ)
aws ecs update-service \
  --cluster bi-cluster \
  --service bi-api-service \
  --force-new-deployment

# 4. デプロイ完了を待機
aws ecs wait services-stable \
  --cluster bi-cluster \
  --services bi-api-service
```

#### 2.2.3 Executor デプロイ

```bash
# 1. Docker イメージをビルド
docker build -t bi-executor:latest -f executor/Dockerfile executor/

# 2. ECR にプッシュ
docker tag bi-executor:latest <account-id>.dkr.ecr.ap-northeast-1.amazonaws.com/bi-executor:$(git rev-parse --short HEAD)
docker push <account-id>.dkr.ecr.ap-northeast-1.amazonaws.com/bi-executor:$(git rev-parse --short HEAD)

# 3. ECS サービスを更新
aws ecs update-service \
  --cluster bi-cluster \
  --service bi-executor-service \
  --force-new-deployment

# 4. デプロイ完了を待機
aws ecs wait services-stable \
  --cluster bi-cluster \
  --services bi-executor-service
```

#### 2.2.4 フロントエンドデプロイ

```bash
# 1. プロダクションビルド
cd frontend
npm ci
npm run build

# 2. S3 にアップロード
aws s3 sync dist/ s3://bi-static-<env>/ --delete

# 3. CloudFront キャッシュを無効化
aws cloudfront create-invalidation \
  --distribution-id <distribution-id> \
  --paths "/*"
```

#### 2.2.5 DynamoDB テーブル初期化 (初回のみ)

```bash
# ローカルから直接実行する場合
cd scripts
pip install boto3
python init_tables.py

# Docker で実行する場合
docker compose run --rm dynamodb-init
```

作成されるテーブル (9テーブル):
- `bi_users`, `bi_groups`, `bi_datasets`, `bi_transforms`, `bi_cards`
- `bi_dashboards`, `bi_dashboard_shares`, `bi_filter_views`, `bi_audit_logs`

#### 2.2.6 デプロイ前チェックリスト

| チェック項目 | コマンド | 基準 |
|-------------|---------|------|
| フロントエンド lint | `cd frontend && npm run lint` | エラー 0 |
| フロントエンド typecheck | `cd frontend && npm run typecheck` | エラー 0 |
| フロントエンド ユニットテスト | `cd frontend && npm run test:coverage` | 83%+ coverage, 290+ tests pass |
| フロントエンド E2Eテスト | `cd frontend && npm run e2e` | 全テスト pass (Auth: 5, Dataset: 3, Card/Dashboard: 5) |
| バックエンド lint | `cd backend && ruff check app/` | エラー 0 |
| バックエンド typecheck | `cd backend && mypy app/` | エラー 0 |
| バックエンド テスト | `cd backend && pytest --cov=app` | pass |
| Executor テスト | `cd executor && pytest --cov=app` | pass |
| ビルド | `cd frontend && npm run build` | 成功 |

---

## 3. ヘルスチェック

### 3.1 エンドポイント

| サービス | エンドポイント | 期待レスポンス |
|---------|---------------|---------------|
| API | `GET /api/health` | `{"status": "ok"}` |
| Executor | `GET /health` | `{"status": "ok"}` |

### 3.2 ヘルスチェック実行

```bash
# API サーバ
curl -s http://localhost:8000/api/health | jq .

# Executor
curl -s http://localhost:8080/health | jq .

# 全サービスの簡易チェック
for port in 8000 8080; do
  echo "Port $port: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:$port/health 2>/dev/null || echo 'FAILED')"
done
```

### 3.3 依存サービス確認

```bash
# DynamoDB Local テーブル確認
aws dynamodb list-tables --endpoint-url http://localhost:8001 --region ap-northeast-1

# MinIO バケット確認
curl -s http://localhost:9000/minio/health/live

# MinIO Console: http://localhost:9001 (minioadmin / minioadmin)
```

---

## 4. 監視項目

### 4.1 メトリクス (CloudWatch)

| メトリクス | 閾値 | アラート | 対応 |
|-----------|------|---------|------|
| API レスポンスタイム (p95) | > 5秒 | Warning | APIログでスロークエリを確認 |
| API レスポンスタイム (p99) | > 10秒 | Critical | スケールアウトを検討 |
| API エラーレート (5xx) | > 5% | Critical | エラーログを確認、ロールバック検討 |
| Executor タイムアウト率 | > 10% | Warning | カードコードの最適化を促進 |
| Executor タイムアウト率 | > 20% | Critical | Executorリソース増強を検討 |
| ECS CPU使用率 | > 80% | Warning | タスク数増加を検討 |
| ECS メモリ使用率 | > 80% | Warning | メモリリーク調査 |
| DynamoDB スロットリング | > 0 | Warning | キャパシティ設定確認 |
| S3 エラーレート | > 1% | Warning | VPCエンドポイント / IAMロール確認 |

### 4.2 ログ

| サービス | ログ出力先 | フォーマット |
|---------|-----------|-------------|
| API | CloudWatch Logs (`/ecs/bi-<env>-api`) | JSON (structlog) |
| Executor | CloudWatch Logs (`/ecs/bi-<env>-executor`) | 標準出力 |
| フロントエンド | ブラウザコンソール | - |

ログには以下の情報が含まれます:
- リクエストID (`request_id`)
- ユーザID (`user_id`、認証済みリクエスト)
- エンドポイント
- レスポンスステータス
- 処理時間 (`duration_ms`)

**ログ検索コマンド:**

```bash
# CloudWatch Logs (本番)
aws logs tail /ecs/bi-production-api --follow

# エラーのみフィルタ
aws logs filter-log-events \
  --log-group-name /ecs/bi-production-api \
  --start-time $(date -d '1 hour ago' +%s)000 \
  --filter-pattern "ERROR"
```

### 4.3 重要な監査ログ

| イベント | ログフィールド | DynamoDBテーブル |
|---------|--------------|-----------------|
| ログイン成功/失敗 | `login_success` / `login_failed` + email, user_id, ip | `bi_audit_logs` |
| データセット作成 | dataset_id, owner_id | `bi_audit_logs` |
| カード実行 | card_id, execution_time_ms, cached | `bi_audit_logs` |
| ダッシュボード共有変更 | dashboard_id, shared_with, permission | `bi_audit_logs` |
| Transform実行成功/失敗 | transform_id, duration_ms, status | `bi_audit_logs` |

監査ログのGSI:
- `LogsByTimestamp` -- 時系列検索
- `LogsByTarget` -- 対象リソース別検索

---

## 5. トラブルシューティング

### 5.1 APIサーバが起動しない

**症状:** `docker compose logs api` でエラーが表示される

**確認手順:**

1. 環境変数を確認
   ```bash
   docker compose exec api env | sort
   ```

2. DynamoDB への接続を確認
   ```bash
   docker compose logs dynamodb-local
   docker compose logs dynamodb-init
   ```

3. 依存パッケージの問題
   ```bash
   docker compose build --no-cache api
   ```

### 5.2 カード実行がタイムアウトする

**症状:** カードプレビュー/実行時に408エラーが返る

**原因と対策:**

| 原因 | 対策 |
|------|------|
| Pythonコードが重い (大量ループ等) | コードを最適化。pandas のベクトル演算を使用 |
| データセットが大きすぎる | フィルタで絞り込む。必要な列のみ使用 |
| 無限ループ | タイムアウト (10秒) で自動停止される |
| Executor のリソース不足 | ECS タスクの CPU/メモリを増やす |

**Executor ログの確認:**
```bash
docker compose logs -f executor
```

**Executor リソース設定 (環境変数):**
- `EXECUTOR_TIMEOUT_CARD=10` (秒)
- `EXECUTOR_TIMEOUT_TRANSFORM=300` (秒)
- `EXECUTOR_MAX_CONCURRENT_CARDS=10`
- `EXECUTOR_MAX_CONCURRENT_TRANSFORMS=5`

### 5.3 CSVインポートが失敗する

**症状:** データセット作成APIが422エラーを返す

**確認手順:**

1. ファイルサイズ制限 (最大100MB) を超えていないか確認
2. 文字コードが正しいか確認 (自動推定が失敗する場合は `encoding` パラメータを明示指定)
3. 区切り文字が正しいか確認 (デフォルトはカンマ)

**サポートされる文字コード:**
- `utf-8` (デフォルト)
- `shift_jis` / `cp932` (日本語Windows)
- 自動推定は chardet ライブラリを使用

### 5.4 フロントエンドが API に接続できない

**症状:** ブラウザコンソールに CORS エラー / Network Error が表示される

**確認手順:**

1. APIサーバが起動しているか確認
   ```bash
   curl http://localhost:8000/api/health
   ```

2. CORS設定を確認 (backend/app/core/config.py)
   - `cors_origins` にフロントエンドのURLが含まれているか

3. Vite のプロキシ設定を確認 (docker-compose.yml)
   - `VITE_API_URL` が正しいか

### 5.5 DynamoDB テーブルが見つからない

**症状:** APIレスポンスで "Table not found" エラー

**対策:**
```bash
# テーブルの存在確認
aws dynamodb list-tables --endpoint-url http://localhost:8001 --region ap-northeast-1

# テーブルを再作成
docker compose run --rm dynamodb-init
```

**作成されるべきテーブル (9テーブル):**
`bi_users`, `bi_groups`, `bi_datasets`, `bi_transforms`, `bi_cards`, `bi_dashboards`, `bi_dashboard_shares`, `bi_filter_views`, `bi_audit_logs`

### 5.6 MinIO / S3 のファイルアクセスエラー

**症状:** データセットのプレビューやカード実行でS3関連エラー

**確認手順:**

1. MinIOが起動しているか確認
   ```bash
   curl http://localhost:9000/minio/health/live
   ```

2. バケットが存在するか確認
   - MinIO Console (http://localhost:9001) にログイン
   - ユーザ: `minioadmin` / パスワード: `minioadmin`

3. バケットを再作成
   ```bash
   docker compose run --rm minio-init
   ```

**必要なバケット:**
- `bi-datasets` -- Parquetデータ格納
- `bi-static` -- 静的アセット (Plotly等)

### 5.7 JWT認証エラー

**症状:** 401 Unauthorized エラー

**確認手順:**

1. トークンの有効期限が切れていないか確認 (デフォルト24時間)
2. `JWT_SECRET_KEY` が全サービスで同じ値か確認
3. フロントエンドのトークンストレージを確認 (ブラウザの開発者ツール)

### 5.8 フロントエンドテストの失敗

**症状:** CI/CDパイプラインでテストが失敗する

**確認手順:**

```bash
cd frontend

# 全テスト実行 (詳細出力)
npx vitest --reporter=verbose

# 特定のテストファイルをデバッグ
npx vitest src/__tests__/pages/LoginPage.test.tsx --reporter=verbose

# UIモードで視覚的にデバッグ
npx vitest --ui
```

**現在のテスト基準:**
- 46テストファイル、290+テストケースが全て合格すること
- Statement coverage 83%+ を維持すること

---

## 6. ロールバック手順

### 6.1 ECS サービスのロールバック

```bash
# 1. 現在のタスク定義リビジョンを確認
aws ecs describe-services \
  --cluster bi-cluster \
  --services bi-api-service \
  --query 'services[0].taskDefinition'

# 2. タスク定義のリビジョン一覧を確認
aws ecs list-task-definitions \
  --family-prefix bi-api \
  --sort DESC \
  --max-items 5

# 3. 前のリビジョンを指定してサービスを更新
aws ecs update-service \
  --cluster bi-cluster \
  --service bi-api-service \
  --task-definition bi-api:<previous-revision>

# 4. ロールバック完了を待機
aws ecs wait services-stable \
  --cluster bi-cluster \
  --services bi-api-service
```

Executorのロールバックも同様の手順で実行:
```bash
aws ecs update-service \
  --cluster bi-cluster \
  --service bi-executor-service \
  --task-definition bi-executor:<previous-revision>
```

### 6.2 フロントエンドのロールバック

```bash
# S3 のバージョニングから前のバージョンを復元
# または、前のビルド成果物を再アップロード
aws s3 sync s3://bi-static-<env>-backup/ s3://bi-static-<env>/ --delete
aws cloudfront create-invalidation --distribution-id <id> --paths "/*"
```

### 6.3 DynamoDB データのリストア

DynamoDB はポイントインタイムリカバリ (PITR) が有効な場合:

```bash
# 特定時点のデータに復元
aws dynamodb restore-table-to-point-in-time \
  --source-table-name bi_dashboards \
  --target-table-name bi_dashboards_restored \
  --restore-date-time <timestamp>

# 復元されたテーブルのデータを確認後、テーブル名を変更して本番適用
```

### 6.4 S3データのリストア

S3バージョニングが有効な場合:

```bash
# 特定バージョンのオブジェクトを復元
aws s3api get-object \
  --bucket bi-datasets-production \
  --key datasets/<dataset-id>/data/part-0000.parquet \
  --version-id "<version-id>" \
  restored-file.parquet
```

---

## 7. スケーリング

### 7.1 ECS サービスのスケーリング

```bash
# APIサービスのタスク数を変更
aws ecs update-service \
  --cluster bi-cluster \
  --service bi-api-service \
  --desired-count 4

# Executorサービスのタスク数を変更
aws ecs update-service \
  --cluster bi-cluster \
  --service bi-executor-service \
  --desired-count 4
```

### 7.2 リソースサイジング目安

| 同時ユーザ数 | API タスク数 | Executor タスク数 |
|-------------|-------------|-----------------|
| ~10 | 2 | 2 |
| 10-30 | 4 | 4 |
| 30-50 | 6 | 8 |

### 7.3 ECS タスクリソース設定

| サービス | CPU | メモリ |
|---------|-----|-------|
| API | 0.5 vCPU | 1 GB |
| Executor (Card) | 1 vCPU | 2 GB |
| Executor (Transform) | 2 vCPU | 4 GB |

---

## 8. 定期メンテナンス

### 8.1 日次

| タスク | 方法 |
|--------|------|
| ログ確認 | CloudWatch Logs でエラーログを確認 |
| ヘルスチェック | 監視アラートの確認 |

### 8.2 週次

| タスク | 方法 |
|--------|------|
| 依存パッケージの脆弱性確認 | `pip audit` / `npm audit` |
| ディスク使用量確認 | S3 / DynamoDB のストレージ使用量 |
| パフォーマンス確認 | CloudWatch メトリクスダッシュボード |
| テストカバレッジ確認 | フロントエンド 83%+ / バックエンド pass を維持 |

### 8.3 月次

| タスク | 方法 |
|--------|------|
| 依存パッケージの更新検討 | Dependabot / 手動確認 |
| セキュリティパッチの適用 | Docker ベースイメージの更新 |
| コスト確認 | AWS Cost Explorer |
| 監査ログレビュー | `bi_audit_logs` テーブルの確認 |
| Executor ホワイトリストライブラリの更新確認 | pandas, plotly 等のバージョン |

---

## 9. 連絡先・エスカレーション

| 状況 | 対応 |
|------|------|
| サービス障害 | 開発チームに連絡 |
| セキュリティインシデント | セキュリティチームにエスカレーション |
| データ損失 | DBA / インフラチームに連絡 |

**エスカレーション判断基準:**

| 重大度 | 条件 | 対応時間 |
|--------|------|---------|
| Critical | API/Executor 全面停止、データ損失 | 即時 |
| High | 5xx エラーレート 10%超、主要機能障害 | 1時間以内 |
| Medium | パフォーマンス劣化、一部機能障害 | 営業時間内 |
| Low | 軽微なUI問題、非重要機能の障害 | 次営業日 |

---

## 10. セキュリティに関する注意事項

### 10.1 秘匿情報の管理

- `.env` ファイルは Git にコミットしない (`.gitignore` に含まれている)
- 本番環境の秘匿情報は AWS Secrets Manager で管理
- `JWT_SECRET_KEY` は最低32文字のランダム文字列を使用
- MinIO のデフォルト認証情報 (`minioadmin`) は本番環境では使用しない
- GCPサービスアカウントキー (`GOOGLE_APPLICATION_CREDENTIALS`) は Secrets Manager で管理

### 10.2 Executor のセキュリティ

- Executor コンテナは非rootユーザ (`executor`) で実行
- ファイルシステムは読み取り専用 (`/tmp/workdir` のみ書き込み可能)
- ブロックされたモジュール: `os`, `sys`, `subprocess`, `socket`, `http`, `urllib`, `requests`, `httpx`, `ftplib`, `smtplib`, `telnetlib`, `pickle`, `shelve`, `marshal`, `ctypes`, `multiprocessing`
- ブロックされた組み込み関数: `open`, `exec`, `eval`, `compile`, `__import__` (カスタムフック経由)
- カード実行タイムアウト: 10秒 (SIGALRM)
- Transform実行タイムアウト: 300秒
- メモリ制限: 2048MB (Linux環境)
- ネットワーク: S3 VPCエンドポイント経由のみ許可、外部通信完全遮断

### 10.3 セキュリティチェックリスト (デプロイ前)

- [ ] JWT_SECRET_KEY が32文字以上で十分にランダム
- [ ] パスワードハッシュのワークファクターが12以上 (bcrypt)
- [ ] CSP設定が適用されている
- [ ] iframe sandbox属性が設定されている
- [ ] Executorのセキュリティグループが外部通信を遮断している
- [ ] Executorが非rootユーザで実行されている
- [ ] 読み取り専用ファイルシステムが有効
- [ ] 監査ログが有効
- [ ] シークレットがSecrets Managerで管理されている

---

## 11. テスト品質ダッシュボード

### 11.1 現在のカバレッジ (Phase Q4 + Q5 完了時点)

**フロントエンド ユニットテスト (frontend/):**

| メトリクス | 値 |
|-----------|-----|
| テストファイル | 46 |
| テストケース | 290+ |
| Statements | 83.07% |
| フレームワーク | Vitest 1.x + @testing-library/react 14.x |

**フロントエンド E2Eテスト (frontend/e2e/):**

| メトリクス | 値 |
|-----------|-----|
| テストスイート | 3 (auth.spec.ts, dataset.spec.ts, card-dashboard.spec.ts) |
| テストケース | 13 (Auth: 5, Dataset: 3, Card/Dashboard: 5) |
| フレームワーク | Playwright 1.58+ (Chromium) |
| テストユーザ | e2e@example.com (scripts/seed_test_user.py でSeed) |

**テスト対象カバレッジ内訳:**

| レイヤー | ファイル数 | テスト対象 |
|---------|-----------|-----------|
| Pages | 9 | 全9ページ (Login, Dashboard x3, Dataset x3, Card x2) |
| Components | 21 | Common (8), Dashboard (8), Dashboard/filters (2), Dataset (1), Card (2) |
| Hooks | 5 | use-auth, use-cards, use-dashboards, use-datasets, use-filter-views |
| API Layer | 5 | auth, cards, dashboards, datasets, filter-views |
| Lib/Utils | 3 | api-client, utils, layout-utils |
| Stores | 1 | auth-store |
| Types | 1 | type-guards |

**バックエンド (backend/):**
- テストフレームワーク: pytest 7.x + moto 5.0
- テスト対象: API routes, core, db, models, repositories, services
