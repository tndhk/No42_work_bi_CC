# 運用ランブック (RUNBOOK)

**最終更新:** 2026-01-31
**プロジェクト:** 社内BI・Pythonカード MVP

---

## 1. 環境一覧

| 環境 | 用途 | フロントエンドURL | API URL |
|------|------|------------------|---------|
| local | 開発 | http://localhost:3000 | http://localhost:8000 |
| staging | 検証 | https://bi-staging.internal.company.com | 内部ALB |
| production | 本番 | https://bi.internal.company.com | 内部ALB |

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

#### 2.2.2 バックエンド (API) デプロイ

```bash
# 1. Docker イメージをビルド
docker build -t bi-api:latest -f backend/Dockerfile.dev backend/

# 2. ECR にタグ付けしてプッシュ
aws ecr get-login-password --region ap-northeast-1 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.ap-northeast-1.amazonaws.com
docker tag bi-api:latest <account-id>.dkr.ecr.ap-northeast-1.amazonaws.com/bi-api:latest
docker push <account-id>.dkr.ecr.ap-northeast-1.amazonaws.com/bi-api:latest

# 3. ECS サービスを更新 (新リビジョンのタスク定義でデプロイ)
aws ecs update-service \
  --cluster bi-cluster \
  --service bi-api-service \
  --force-new-deployment
```

#### 2.2.3 Executor デプロイ

```bash
# 1. Docker イメージをビルド
docker build -t bi-executor:latest -f executor/Dockerfile executor/

# 2. ECR にプッシュ
docker tag bi-executor:latest <account-id>.dkr.ecr.ap-northeast-1.amazonaws.com/bi-executor:latest
docker push <account-id>.dkr.ecr.ap-northeast-1.amazonaws.com/bi-executor:latest

# 3. ECS サービスを更新
aws ecs update-service \
  --cluster bi-cluster \
  --service bi-executor-service \
  --force-new-deployment
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

---

## 4. 監視項目

### 4.1 メトリクス (CloudWatch)

| メトリクス | 閾値 | アラート |
|-----------|------|---------|
| API レスポンスタイム (p95) | > 5秒 | Warning |
| API レスポンスタイム (p99) | > 10秒 | Critical |
| API エラーレート (5xx) | > 5% | Critical |
| Executor タイムアウト率 | > 10% | Warning |
| ECS CPU使用率 | > 80% | Warning |
| ECS メモリ使用率 | > 80% | Warning |
| DynamoDB スロットリング | > 0 | Warning |
| S3 エラーレート | > 1% | Warning |

### 4.2 ログ

| サービス | ログ出力先 | フォーマット |
|---------|-----------|-------------|
| API | CloudWatch Logs | JSON (structlog) |
| Executor | CloudWatch Logs | 標準出力 |
| フロントエンド | ブラウザコンソール | - |

ログには以下の情報が含まれます:
- リクエストID
- ユーザID (認証済みリクエスト)
- エンドポイント
- レスポンスステータス
- 処理時間

### 4.3 重要な監査ログ

| イベント | ログフィールド |
|---------|--------------|
| ログイン成功/失敗 | `login_success` / `login_failed` + email, user_id, ip |
| データセット作成 | dataset_id, owner_id |
| カード実行 | card_id, execution_time_ms, cached |
| ダッシュボード共有変更 | dashboard_id, shared_with, permission |

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

### 5.3 CSVインポートが失敗する

**症状:** データセット作成APIが422エラーを返す

**確認手順:**

1. ファイルサイズ制限 (最大100MB) を超えていないか確認
2. 文字コードが正しいか確認 (自動推定が失敗する場合は `encoding` パラメータを明示指定)
3. 区切り文字が正しいか確認 (デフォルトはカンマ)

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
aws dynamodb list-tables --endpoint-url http://localhost:8001

# テーブルを再作成
docker compose run --rm dynamodb-init
```

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

### 5.7 JWT認証エラー

**症状:** 401 Unauthorized エラー

**確認手順:**

1. トークンの有効期限が切れていないか確認
2. `JWT_SECRET_KEY` が全サービスで同じ値か確認
3. フロントエンドのトークンストレージを確認 (ブラウザの開発者ツール)

---

## 6. ロールバック手順

### 6.1 ECS サービスのロールバック

```bash
# 1. 前のタスク定義リビジョンを確認
aws ecs describe-services \
  --cluster bi-cluster \
  --services bi-api-service \
  --query 'services[0].taskDefinition'

# 2. 前のリビジョンを指定してサービスを更新
aws ecs update-service \
  --cluster bi-cluster \
  --service bi-api-service \
  --task-definition bi-api:<previous-revision>
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
aws dynamodb restore-table-to-point-in-time \
  --source-table-name bi_users \
  --target-table-name bi_users_restored \
  --restore-date-time <timestamp>
```

---

## 7. 定期メンテナンス

### 7.1 日次

| タスク | 方法 |
|--------|------|
| ログ確認 | CloudWatch Logs でエラーログを確認 |
| ヘルスチェック | 監視アラートの確認 |

### 7.2 週次

| タスク | 方法 |
|--------|------|
| 依存パッケージの脆弱性確認 | `pip audit` / `npm audit` |
| ディスク使用量確認 | S3 / DynamoDB のストレージ使用量 |
| パフォーマンス確認 | CloudWatch メトリクスダッシュボード |

### 7.3 月次

| タスク | 方法 |
|--------|------|
| 依存パッケージの更新検討 | Dependabot / 手動確認 |
| セキュリティパッチの適用 | Docker ベースイメージの更新 |
| コスト確認 | AWS Cost Explorer |

---

## 8. 連絡先・エスカレーション

| 状況 | 対応 |
|------|------|
| サービス障害 | 開発チームに連絡 |
| セキュリティインシデント | セキュリティチームにエスカレーション |
| データ損失 | DBA / インフラチームに連絡 |

---

## 9. セキュリティに関する注意事項

### 9.1 秘匿情報の管理

- `.env` ファイルは Git にコミットしない (`.gitignore` に含まれている)
- 本番環境の秘匿情報は AWS Secrets Manager で管理
- `JWT_SECRET_KEY` は最低32文字のランダム文字列を使用
- MinIO のデフォルト認証情報 (`minioadmin`) は本番環境では使用しない

### 9.2 Executor のセキュリティ

- Executor コンテナは非rootユーザ (`executor`) で実行
- ファイルシステムは読み取り専用 (`/tmp/workdir` のみ書き込み可能)
- ブロックされたモジュール: `os`, `sys`, `subprocess`, `socket`, `http`, `urllib` 等
- ブロックされた組み込み関数: `open`, `exec`, `eval`, `compile`, `__import__` (カスタムフック経由)
- カード実行タイムアウト: 10秒
- メモリ制限: 2048MB (Linux環境)
