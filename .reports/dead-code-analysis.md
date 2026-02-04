# Dead Code Analysis Report

日付: 2026-02-04

## 分析ツール

- Frontend: knip, depcheck, tsc --noEmit, ESLint
- Backend/Executor: ruff (F401/F811/F841), vulture

## 実行結果サマリ

### Phase 1: Backend テストコード未使用import/変数修正
- 修正件数: 46件（自動修正42件 + 手動修正4件）
- 対象: 27ファイル
- 内訳: 未使用import 43件、未使用変数 3件
- テスト結果: 681 passed

### Phase 2: Backend 本番コード未使用import修正
- 修正件数: 1件
- 対象: `backend/app/services/dataset_service.py` -- ColumnSchema import削除
- テスト結果: 681 passed

### Phase 3: Executor テストコード未使用import修正
- 修正件数: 3件
- 対象: conftest.py, test_execute_api.py, test_health.py -- `import pytest` 削除
- テスト結果: 62 passed

### Phase 4: Frontend 未使用UIコンポーネントファイル削除
- 削除ファイル:
  - `frontend/src/components/ui/separator.tsx`
  - `frontend/src/components/ui/sheet.tsx`

### Phase 5: Frontend 未使用依存パッケージ削除
- 削除パッケージ: `@radix-ui/react-separator`

### Phase 6: Frontend 未使用コードの修正
- 6-A: 型ガード関数削除（4関数 + re-export行）
  - isFilterView, isGroup, isSchemaChange, isReimportDryRunResponse
- 6-B: 未使用変数修正（3件）
  - e2e/sharing.spec.ts: viewerToken削除
  - SchemaChangeWarningDialog.test.tsx: table変数を直接呼び出しに変更
  - use-filter-views.test.ts: mockGet削除
- 6-C: api-client.ts default export重複解消 + 未使用型export削除

### Frontend 検証結果
- テスト: 57ファイル / 434テスト passed
- 型チェック: エラーなし
- ビルド: 成功
- Lint: 今回の修正に起因するエラー 0件

## 修正統計

| 領域 | 修正件数 | テスト結果 |
|------|---------|-----------|
| Backend テスト | 46件 | 681 passed |
| Backend 本番 | 1件 | 681 passed |
| Executor テスト | 3件 | 62 passed |
| Frontend ファイル削除 | 2ファイル | 434 passed |
| Frontend パッケージ削除 | 1パッケージ | ビルド成功 |
| Frontend コード修正 | 型ガード4関数 + 変数3件 + export2件 | lint正常 |

## CAUTION項目（今回変更しない）

| 項目 | 件数 | 保留理由 |
|------|------|---------|
| shadcn/ui 未使用re-export | 25件 | UIライブラリの慣習。全exportが標準パターン |
| 未使用型エクスポート (types/index.ts) | 29件 | 将来の機能実装で利用される可能性 |
| 未使用hooks (useCurrentUser等) | 4件 | テスト済み。将来のUI統合で使用予定 |
| E2Eヘルパー未使用関数 | 7件 | テスト拡充時に利用予定 |
| テストユーティリティ未使用 | 2件 | テスト追加時に利用予定 |
| DashboardViewPage.tsx:56 の `_` | 1件 | destructuring `{ [key]: _, ...rest }` の慣習パターン |

## 今後の推奨事項

1. CI/CDでruff (F401/F841) とESLint no-unused-varsを常時チェックし、未使用コードの蓄積を防止する
2. 四半期ごとにknip/depcheckを実行し、未使用ファイル・パッケージを定期的に棚卸しする
3. CAUTION項目は次回の機能実装時に再評価し、不要であれば削除する
4. shadcn/uiコンポーネントは使用時にのみ追加する運用を徹底する
