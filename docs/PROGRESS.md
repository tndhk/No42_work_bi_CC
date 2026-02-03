# 社内BI・Pythonカード 実装進捗

Last Updated: 2026-02-03

要件定義書 (docs/requirements.md) および設計書 (docs/design.md) に基づく全機能の実装ステータス。

---

## 実装ステータス一覧

### FR-1: Dataset取り込み

- [x] FR-1.1 Local CSV Import (ファイルアップロード、プレビュー、スキーマ推定、Parquet変換)
- [x] FR-1.2 S3 CSV Import (バケット/キー指定、S3ImportForm UI、Parquet変換)
- [x] FR-1.3 Dataset再取り込み (スキーマ変化検知・警告、中止/続行選択)

### FR-2: Transform (PythonベースETL)

- [ ] FR-2.1 Transform定義 (モデル・リポジトリ・API・フロントエンド画面)
- [ ] FR-2.2 Transform実行 (手動実行・スケジュール実行・実行履歴)
- [ ] FR-2.3 Transform実行制約 (Executor連携、5分タイムアウト)

### FR-3: Card (PythonベースHTMLカード)

- [x] FR-3.1 カード定義形式 (Monaco Editor、Pythonコード編集)
- [x] FR-3.2 フィルタ適用 (バックエンド filters パラメータ対応済み)
- [x] FR-3.3 HTMLの安全な表示 (iframe + CSP)
- [x] FR-3.4 カード実行制約 (Executor sandbox、10秒タイムアウト、リソース制限)

### FR-4: Dashboard (作成・配置・閲覧)

- [x] FR-4.1 Dashboard作成/編集 (react-grid-layout、ドラッグ&ドロップ)
- [x] FR-4.2 Dashboard閲覧モード (カード表示、ロード/エラー状態)
- [x] Dashboard複製 (Clone API)

### FR-5: ページフィルタ

- [x] FR-5.1 フィルタ種別 (FilterDefinition モデル: type, column, label, multi_select)
- [x] FR-5.2 フィルタ適用ルール (Dashboard→Card一括適用のフロントエンド実装: DashboardViewer filterValues対応)
- [x] FR-5.3 フィルタUI (FilterBar, FilterConfigPanel, FilterDefinitionForm, CategoryFilter, DateRangeFilter)

### FR-6: FilterView (フィルタ状態の保存)

- [x] FR-6.1 FilterView操作 (CRUD API、FilterViewRepository、FilterViewSelector UI)
- [x] FR-6.2 FilterView共有 (個人用/共有ビュー、デフォルトビュー)

### FR-7: 共有/権限 (Dashboardのみ)

- [x] FR-7.1 Dashboard共有 (DashboardShareモデル・共有CRUD API・ShareDialog UI・ユーザー/グループ宛共有)
- [x] FR-7.2 権限チェック (Owner/Editor/Viewer、PermissionService、グループ経由の権限解決、APIレベル認可)

### FR-8: Chatbot (データ質問)

- [ ] FR-8.1 Chatbot機能 (Vertex AI Gemini連携、ChatbotPanel UI)
- [ ] FR-8.2 Datasetサマリ生成 (スキーマ・サンプル行・統計情報)

---

## 非機能要件

### NFR-1: 性能

- [x] Parquet形式によるデータ保存
- [x] カード実行キャッシュ (TTL管理)
- [ ] パーティションプルーニング
- [ ] カード並列実行

### NFR-2: 可用性

- [x] Docker Compose ヘルスチェック
- [ ] 実行キュー (同時実行数制限、バックプレッシャ)
- [ ] 水平スケール対応

### NFR-3/4: セキュリティ・監査ログ

- [x] Executor sandbox (ネットワーク遮断、モジュール制限、リソース制限)
- [x] 認証 (JWT、レート制限)
- [ ] AuditLog モデル・リポジトリ
- [ ] ログ記録 (共有変更、取り込み履歴、実行失敗)
- [ ] ログ検索API

---

## インフラ・管理機能

- [x] Group CRUD (Groupモデル・GroupRepository・Groups API・GroupListPage UI)
- [x] Group メンバー管理 (GroupMember・GroupMemberRepository・メンバー追加/削除API・GroupDetailPanel UI)
- [x] User一覧/検索API (UserRepository.scan_by_email_prefix・Users API)
- [ ] S3認証方式 (IAMロール/アクセスキー)
- [ ] EventBridge Scheduler 連携

---

## 品質・テスト (完了済み)

- [x] フロントエンドテスト 83%+ カバレッジ (53テストファイル)
- [x] バックエンドテスト充実 (45モジュール、11,515行)
- [x] Playwright E2Eテスト基盤 (auth, dataset, card-dashboard, sharing)
- [x] Docker Compose ヘルスチェック
- [x] ドキュメント整備 (codemaps, CONTRIB.md, RUNBOOK.md)

---

## 完了済みフェーズ

| Phase | 内容 | コミット | 日付 |
|-------|------|---------|------|
| Phase 0-5 | MVP初期実装 (Backend, Frontend, Executor) | ff7f80f | 2026-01-30 |
| Phase Q3 | フロントエンドテスト充実 83.07% | 9ec0228 | 2026-01-30 |
| Phase Q4 | Playwright E2E + API標準化 | 701aa1e | 2026-01-31 |
| Phase Q5 | クリーンアップ・依存整理 | 701aa1e | 2026-01-31 |
| Docs | コードマップ・開発ガイド更新 | 5c728e8 | 2026-01-31 |
| FR-5/6 + FR-1.2 | フィルタUI + FilterView CRUD + S3 Import | (WIP) | 2026-02-02 |
| FR-7 | Dashboard共有/権限 + グループ管理 + User検索API | -- | 2026-02-03 |
| FR-1.3 | Dataset再取り込み (スキーマ変化検知・警告) | -- | 2026-02-03 |

## 次期フェーズ候補

| 優先度 | 機能群 | 依存関係 | 複雑度 |
|--------|--------|----------|--------|
| 高 | Transform (ETL) | Executor基盤あり | 大 |
| 中 | Chatbot (Vertex AI) | Vertex AI設定が必要 | 大 |
| 中 | 監査ログ | 他機能に依存しない | 中 |
| 低 | パーティションプルーニング | NFR-1 | 中 |
