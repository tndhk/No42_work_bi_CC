# プロジェクト開発メモ

## TDDアプローチでの実装

### 例外変換のレイヤー設計 (2026-02-05)

NoSuchKey エラーのグレースフルハンドリング実装時の学び:

1. テスト設計と実装アーキテクチャの整合性が重要
   - TDDでテストを先に書く際、実装のレイヤー境界を明確にする
   - 例: `test_get_dataset_rows_propagates_dataset_file_not_found_error` では、当初 mock で生の `FileNotFoundError` を raise させていたが、実際には `parquet_storage.py` が `DatasetFileNotFoundError` に変換する設計だった
   - 結果: `_get_dataset_rows` に防御的ハンドリングを追加し、`dataset_id` を補完する層として機能させた
   - 教訓: 例外変換はどの層で行うか、テスト時点で明確にしておく。mock を使う場合、実装後の動作を正確に模倣すること

2. 例外の構造化データ補完
   - 下位レイヤー (`parquet_storage.py`) で基本情報 (s3_path) をセット
   - 上位レイヤー (`card_execution_service.py`) でコンテキスト情報 (dataset_id) を補完
   - これにより、API層で適切なエラーレスポンスを返せる

3. pytest 実行環境
   - backend ディレクトリでは `python3 -m pytest` が確実
   - `source .venv/bin/activate` や `.venv/bin/pytest` は環境により失敗する可能性あり

## アーキテクチャパターン

### 例外ハンドリングの層化
- 低レイヤー: プロトコル固有エラー (NoSuchKey) → ドメイン例外 (DatasetFileNotFoundError)
- 中間レイヤー: コンテキスト情報の補完 (dataset_id の追加)
- API層: HTTPステータスコードへの変換 (404)
- 各層で監査ログ記録

このパターンは他の例外処理にも適用可能。
