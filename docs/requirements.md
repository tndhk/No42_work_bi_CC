# 社内BI・Pythonカード 要件定義書 v0.3

Last Updated: 2026-02-05

## このドキュメントについて

- 役割: ビジネス要件・機能要件の正式仕様
- 関連: 設計は [design.md](design.md)、API仕様は [api-spec.md](api-spec.md) を参照

## 1. 目的・背景・スコープ

### 1.1 プロダクトの目的

ローカルCSVおよびS3上のCSVを取り込み、PythonでHTMLカードを定義してダッシュボードに配置できる社内BIツールを提供する。ダッシュボード上でページフィルタを操作し、カード群へ一括反映できる。フィルタ状態を「フィルタビュー」として保存・再利用できる。ダッシュボード単位で共有/権限管理ができる。

### 1.2 対象ユーザと利用シーン

対象ユーザ:
- データ分析担当者（Dataset取り込み、Transform作成、Card作成）
- ダッシュボード作成者（Dashboard作成、フィルタ設定、共有）
- ダッシュボード閲覧者（Dashboard閲覧、フィルタ操作、Chatbot利用）

利用シーン:
- 社内データの可視化と分析
- 定期的なレポート作成（スケジュール実行）
- データドリブンな意思決定支援
- チーム間でのダッシュボード共有

### 1.3 MVP範囲

含まれる機能:
- Dataset取り込み（Local CSV / S3 CSV）
- Transform（PythonベースETL、手動＋スケジュール実行）
- Card（PythonベースHTMLカード）
- Dashboard（作成/編集/閲覧、グリッドレイアウト）
- ページフィルタ（カテゴリ/日付）
- FilterView（フィルタ状態の保存・共有）
- 共有/権限（Dashboard単位、ユーザ/グループ）
- Chatbot（データ質問、Vertex AI）

含まれない機能（V1以降）:
- IdP連携（Entra ID等）
- Transform依存チェーンの自動実行
- クロスフィルタ（カードクリックでフィルタ反映）
- 相対日付フィルタ（過去7日など）

### 1.4 前提条件

| 項目 | 内容 |
|------|------|
| カード出力形式 | HTML |
| インタラクション | フィルタ必須 |
| Pythonカード実行 | 外部ネットワークアクセス禁止 |
| 利用範囲 | 社内 |
| データ更新 | 手動 |
| 同時閲覧 | 10人程度 |
| データ規模 | 最大50列・100万行程度 |

---

## 2. 用語定義・オブジェクトモデル

### 2.1 用語定義

Dataset
- 取り込んだCSVから生成されるデータ資産
- Local CSVまたはS3 CSVから取り込み
- Transformの出力としても生成される
- Parquet形式でS3に保存

Transform
- Pythonで定義されるETL処理
- 1つ以上のDatasetを入力として受け取り、新しいDatasetを出力
- 手動実行またはスケジュール実行可能

Card
- Pythonで定義され、Datasetとフィルタ入力からHTMLを生成する表示単位
- Dashboard上に配置される
- フィルタ適用済みデータを受け取る

Dashboard
- 複数Cardを配置し、ページフィルタ・FilterView・共有を管理する画面
- 権限管理の単位（Dashboardのみ権限概念を持つ）

FilterView
- ページフィルタの状態を名前付きで保存したもの
- 個人用または共有可能

User
- システム利用者
- MVPではローカル管理、V1以降でIdP連携

Group
- Userを束ねる単位
- Dashboard共有先として指定可能

### 2.2 オブジェクトモデル

```
User
  ├─ owns: Dataset[]
  ├─ owns: Transform[]
  ├─ owns: Card[]
  ├─ owns: Dashboard[]
  ├─ owns: FilterView[]
  └─ memberOf: Group[]

Group
  └─ members: User[]

Dataset
  ├─ owner: User
  └─ source: Local CSV | S3 CSV | Transform

Transform
  ├─ owner: User
  ├─ inputs: Dataset[]
  └─ output: Dataset

Card
  ├─ owner: User
  └─ dataset: Dataset

Dashboard
  ├─ owner: User
  ├─ cards: Card[]
  ├─ filters: Filter[]
  ├─ filterViews: FilterView[]
  └─ shares: Share[] (User | Group)

FilterView
  ├─ owner: User
  ├─ dashboard: Dashboard
  └─ filterState: FilterState
```

### 2.3 権限モデル

権限概念はDashboardのみ

- Dataset/Transform/Cardには権限概念を持たせない（ownerのみ編集可能）
- Dashboardには3種類の権限がある:
  - Owner: 編集可＋共有管理可
  - Editor: 編集可（レイアウト変更、フィルタ設定、ビュー作成）
  - Viewer: 閲覧のみ

データアクセス境界

- Dashboardを閲覧できるユーザは、そのDashboard上の全Card表示に必要なDatasetへ暗黙アクセスする
- Dashboard共有が事実上のデータアクセス境界となる
- 共有ダイアログに「このDashboardが参照しているDataset一覧」を表示し、共有前に可視化する（事故防止）

注意事項

Dataset/Cardに権限を持たせない設計は運用が軽い一方、共有境界がDashboardに固定されるため、Dashboardに1枚でも過剰なカードが入るとデータ露出の影響範囲が大きくなる。これを補うには「DashboardごとのDataset利用一覧の可視化」「共有時の警告」「監査ログ」が実質必須。

---

## 3. 機能要件

### FR-1: Dataset取り込み

#### FR-1.1 Local CSV Import

機能:
- UIでファイル選択またはドラッグ&ドロップ
- プレビュー表示
- 取り込み設定:
  - ヘッダ有無
  - 区切り文字（, など）
  - 文字コード（自動推定＋手動選択）
- 取り込み後にDatasetとして保存

受け入れ基準:
- 50列・100万行のCSVを取り込み、Datasetとして参照可能になる
- プレビューでデータ構造が確認できる

#### FR-1.2 S3 CSV Import

機能:
- 接続設定（認証情報の登録方式は別途決める：IAMロール/キー等）
- バケット/プレフィックス/ファイル選択
- 手動実行で取り込み

受け入れ基準:
- S3上のCSVを選択して取り込み可能
- 認証情報が安全に管理される

#### FR-1.3 Dataset再取り込み

機能:
- Dataset詳細画面に「再取り込み」ボタン
- 取り込み結果:
  - 成功/失敗
  - 行数、列数、更新時刻、実行者
  - スキーマ変化（列追加/削除/型変更）の検知と警告

受け入れ基準:
- 再取り込み時にスキーマが変わった場合、警告が表示される（中止/続行の選択は要件化する）

### FR-2: Transform（PythonベースETL）

#### FR-2.1 Transform定義

機能:
- Transform作成/編集画面
- 入力Dataset選択（複数可）
- Pythonコード編集
- 規約エントリポイント:
  ```python
  def transform(inputs: dict[str, "DataFrameLike"], params: dict) -> "DataFrameLike":
      # inputs["sales"], inputs["products"] のように複数Dataset参照可能
      return result_df
  ```

受け入れ基準:
- 複数Datasetを入力として受け取り、新しいDatasetを出力できる

#### FR-2.2 Transform実行

機能:
- 手動実行（UI上の「実行」ボタン）
- スケジュール実行（cron形式で設定）
- 実行履歴表示

受け入れ基準:
- 手動実行でTransformが正常に実行され、出力Datasetが生成される
- スケジュール設定で自動実行される

#### FR-2.3 Transform実行制約

機能:
- 外部ネットワーク遮断
- CPU/メモリ/タイムアウト上限（5分）
- ホワイトリストライブラリのみ許可

受け入れ基準:
- 外部HTTP通信が発生しない
- タイムアウト上限が守られる

### FR-3: Card（PythonベースHTMLカード）

#### FR-3.1 カード定義形式

機能:
- Card作成/編集画面
- Pythonコード編集
- 規約エントリポイント:
  ```python
  def render(dataset: "DataFrameLike", filters: dict, params: dict) -> "HTMLResult":
      # フィルタ適用済みデータを受け取る
      return HTMLResult(
          html="<div>...</div>",
          used_columns=["col1", "col2"],
          filter_applicable=["category", "date"]
      )
  ```

受け入れ基準:
- フィルタ適用済みデータを受け取り、HTMLを生成できる

#### FR-3.2 フィルタ適用

機能:
- プラットフォーム側でフィルタ適用
- フィルタ適用済みデータをカードへ渡す

受け入れ基準:
- ページフィルタ変更でカードが再描画される（フィルタ反映が確認できる）

#### FR-3.3 HTMLの安全な表示

機能:
- iframe分離を原則
- CSP（Content-Security-Policy）を適用
- Plotly等の社内ホスト済み静的ライブラリのみ許可

受け入れ基準:
- XSSや任意スクリプト混入が防止される
- Plotly等の許可ライブラリが動作する

#### FR-3.4 カード実行制約

機能:
- 外部ネットワーク遮断
- CPU/メモリ/タイムアウト上限（10秒）
- ホワイトリストライブラリのみ許可
- 実行ログ（カード単位）: 実行時間、失敗理由、入力フィルタ、生成サイズ

受け入れ基準:
- 外部HTTP通信が発生しない（実行環境・ブラウザ両面で）
- タイムアウト上限が守られる

### FR-4: Dashboard（作成・配置・閲覧）

#### FR-4.1 Dashboard作成/編集

機能:
- Dashboard作成、複製、削除
- レイアウト編集:
  - カードの追加/削除
  - 移動/リサイズ（グリッド）
- 1 Dashboardあたりカード数上限: 20（暫定、性能検証で見直し）

受け入れ基準:
- 保存後にレイアウトが保持される

#### FR-4.2 Dashboard閲覧モード

機能:
- カードのロード状態/エラー状態が視認できる
- 複数カード配置

受け入れ基準:
- カードの状態が明確に表示される

### FR-5: ページフィルタ（カテゴリ、日付）

#### FR-5.1 フィルタ種別

機能:
- カテゴリフィルタ（1選択/複数選択）
- 日付フィルタ（期間）:
  - カレンダーUI
  - 相対期間（過去7日など）はV1でもよい（要優先度）

受け入れ基準:
- カテゴリ・日付の変更が、複数カードに反映される

#### FR-5.2 フィルタ適用ルール

機能:
- Dashboardに設定されたページフィルタは、対象カードへ一括適用される
- カード側は「対応するフィルタ項目」を宣言できる（宣言がないフィルタは無視）

受け入れ基準:
- フィルタが適用されているカードが識別できる

#### FR-5.3 フィルタUI

機能:
- フィルタバー表示/非表示
- フィルタ適用中の表示（カード上のアイコン等）

受け入れ基準:
- フィルタ状態が視覚的に分かる

### FR-6: FilterView（フィルタ状態の保存）

#### FR-6.1 FilterView操作

機能:
- 現在のフィルタ状態を「名前付きビュー」として保存
- 保存済みビューの適用
- ビューの更新/削除

受け入れ基準:
- ビュー適用で複数フィルタが一括復元される

#### FR-6.2 FilterView共有

機能:
- 個人用ビュー
- Dashboard共有範囲内での共有ビュー
- デフォルトビュー設定（任意、ただし利便性が高い）

受け入れ基準:
- 共有ビューが共有メンバーに表示される

### FR-7: 共有/権限（Dashboardのみ） -- 実装済み (2026-02-03)

#### FR-7.1 Dashboard共有

ステータス: 実装済み

実装内容:
- Dashboard を個別ユーザまたはグループへ共有（`SharedToType`: `user` / `group`）
- 権限レベル 3 段階: `VIEWER` / `EDITOR` / `OWNER`
- 共有 CRUD API: `POST/GET/PUT/DELETE /api/dashboards/{dashboard_id}/shares`
- 共有管理は Dashboard の Owner のみ操作可能（403 で拒否）
- 重複共有は 409 Conflict で拒否

受け入れ基準:
- Ownerがグループへ共有でき、グループメンバーが閲覧できる
- Editorが編集でき、Viewerは編集できない

#### FR-7.2 権限チェック

ステータス: 実装済み

実装内容:
- `PermissionService` による権限判定ロジック (`backend/app/services/permission_service.py`)
- 判定優先順位: (1) Dashboard owner チェック -> (2) 直接ユーザ共有 -> (3) グループ経由共有
- 複数経路で権限がある場合は最高レベルを適用
- `assert_permission()` で必要権限に満たない場合 403 を返す

受け入れ基準:
- 権限のない操作が拒否される

#### FR-7.3 グループ管理

ステータス: 実装済み

実装内容:
- グループ CRUD API: `POST/GET/PUT/DELETE /api/groups` (admin 専用)
- グループメンバー管理: `POST/DELETE /api/groups/{group_id}/members`
- グループ名の一意性制約（409 Conflict で拒否）
- `GroupMemberRepository` で複合キー (`groupId` + `userId`) を使用
- `MembersByUser` GSI でユーザの所属グループを逆引き

受け入れ基準:
- admin ユーザがグループの作成・編集・削除・メンバー管理を行える
- admin 以外のユーザはグループ操作が拒否される

#### FR-7.4 ユーザ検索

ステータス: 実装済み

実装内容:
- ユーザ検索 API: `GET /api/users?q={email}&limit={n}`
- メール部分一致検索（共有ダイアログでの宛先選択用）
- パスワードハッシュ等の機密フィールドを除外してレスポンス

受け入れ基準:
- 共有ダイアログからユーザをメールアドレスで検索して選択できる

### FR-8: Chatbot（データ質問）

#### FR-8.1 Chatbot機能

機能:
- Dashboard画面にチャットパネルを追加
- そのDashboardが参照するDatasetについてAIに質問できる
- LLM: Vertex AI（Gemini）
- 質問＋Datasetサマリ（スキーマ、サンプル行、統計情報）をプロンプトに含めてLLMへ送信

受け入れ基準:
- Dashboardのデータについて自然言語で質問でき、適切な回答が得られる

#### FR-8.2 Datasetサマリ生成

機能:
- 大規模Datasetは全行送信不可
- サマリ化またはサンプリングで対応

受け入れ基準:
- 100万行のDatasetでもサマリが生成され、質問に回答できる

---

## 4. 非機能要件

### NFR-1: 性能（暫定SLO）

前提条件:
- 同時閲覧10人
- カード20枚
- Dataset最大100万行

SLO:
- Dashboard初回表示: p95 5秒以内（同一条件でキャッシュが効く場合）
- フィルタ変更後の再描画: p95 2.5秒以内（カード並列実行＋キャッシュ前提）
- カード単体実行タイムアウト: 10秒
- Transform実行タイムアウト: 5分

性能担保設計:
- Dataset: Parquet形式、日付パーティション
- フィルタ適用: パーティションプルーニング
- カード実行: 並列化
- キャッシュ: フィルタ値をキーにHTML出力キャッシュ

注意事項:

100万行を毎回Pythonでフルスキャンすると、フィルタ変更のたびに遅くなる可能性が高い。取り込み時に列指向フォーマット（例：Parquet）へ変換し、日付カラムでパーティションするなど、クエリコストを下げる前提を置かないとSLOが守れない。

### NFR-2: 可用性

要件:
- Python実行基盤のワーカーは水平スケール可能
- 実行キュー（同時実行数制限、バックプレッシャ）

受け入れ基準:
- 10人同時閲覧で破綻しない

### NFR-3: セキュリティ

Python実行:
- ネットワーク遮断
- 権限分離
- リソース制限

HTML表示:
- iframe分離＋CSP＋サニタイズ

監査ログ（最低限）:
- Dashboard共有変更（誰が誰/どのグループに付与したか）
- Dataset取り込み履歴
- Transform実行履歴
- カード実行失敗ログ

受け入れ基準:
- 外部ネットワークアクセスが発生しない
- XSSが防止される
- 監査ログが記録される

### NFR-4: 監査ログ

記録対象:
- Dashboard共有変更
- Dataset取り込み/Transform実行
- カード実行失敗

受け入れ基準:
- 監査ログが検索可能な形式で記録される

---

## 5. 制約事項・前提条件

### 5.1 技術的制約

Pythonカード実行:
- 外部ネットワークアクセス禁止
- CPU/メモリ/タイムアウト上限あり
- ホワイトリストライブラリのみ許可

HTMLカード表示:
- iframe分離必須
- CSP適用必須
- 任意スクリプト禁止

データ規模:
- 最大50列・100万行程度

同時閲覧:
- 10人程度

### 5.2 運用制約

データ更新:
- 手動（自動更新はV1以降）

利用範囲:
- 社内のみ

### 5.3 前提条件

インフラ:
- AWS（ECS/Fargate、DynamoDB、S3）
- ローカル開発環境（docker-compose）

認証:
- MVP: ローカル管理
- V1以降: IdP連携

---

## 6. 未確定事項

実装前に決定が必要な事項:

1. 日付フィルタの詳細仕様
   - タイムゾーン（JST固定か、ユーザ依存か）
   - 境界（開始日/終了日を含むか）
   - データ型（date/datetime、文字列の日付を許容するか）

2. 許可ライブラリのホワイトリスト
   - 確定: pandas, pyarrow, plotly
   - 検討: numpy, scipy, matplotlib, seaborn 等

3. S3認証方式
   - IAMロール（ECSタスクロール経由） or ユーザ別アクセスキー登録

4. HTMLカードで許可するJSライブラリ
   - Plotly等のバージョン固定、CDN配信方式

5. 相対日付フィルタ（過去7日等）
   - MVP対象 or V1対象

---

## 7. MVP対象外（V1以降）

- IdP連携（Entra ID等）
- Transform依存チェーンの自動実行
- クロスフィルタ（カードクリックでフィルタ反映）
- 相対日付フィルタ（優先度次第でMVPに含める）
