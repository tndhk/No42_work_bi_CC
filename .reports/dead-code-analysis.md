# Dead Code Analysis

Date: 2026-02-05
Scope: frontend

## Commands
- (cd frontend) npx --yes knip
- (cd frontend) npx --yes depcheck
- (cd frontend) npx --yes ts-prune
- (cd frontend) npm run test:coverage (pre-delete)
- (cd frontend) npm run test:coverage (post-delete)

## Assumptions and constraints
- Full test suite for this deletion is interpreted as frontend-only (`npm run test:coverage`) because the change is confined to frontend files.
- Backend test suite failure is pre-existing and blocks backend gating: `docker compose exec -T api pytest --cov=app` failed with 38 failed and 15 errors (dashboard/dataset/transform-related).

## Tool outputs

### knip
```
Unused files (3)
src/__tests__/vitest.d.ts       src/__tests__/vitest.d.ts
src/components/common/index.ts  src/components/common/index.ts
src/components/ui/form.tsx      src/components/ui/form.tsx
Unlisted dependencies (2)
react-resizable/css/styles.css  src/components/dashboard/DashboardEditor.tsx:5:9
react-resizable/css/styles.css  src/components/dashboard/DashboardViewer.tsx:4:9
Unused exports (40)
deleteDataset                 function  e2e/helpers/api-helper.ts:65:23
deleteCard                    function  e2e/helpers/api-helper.ts:110:23
deleteDashboard               function  e2e/helpers/api-helper.ts:153:23
deleteShare                   function  e2e/helpers/api-helper.ts:198:23
deleteGroup                   function  e2e/helpers/api-helper.ts:240:23
addGroupMember                function  e2e/helpers/api-helper.ts:254:23
registerUser                  function  e2e/helpers/api-helper.ts:276:23
createTestQueryClient         function  src/__tests__/helpers/test-utils.tsx:8:17
renderWithProviders           function  src/__tests__/helpers/test-utils.tsx:18:17
createMockTransformExecution  function  src/__tests__/helpers/test-utils.tsx:112:17
AlertDialogPortal                       src/components/ui/alert-dialog.tsx:129:3
AlertDialogOverlay                      src/components/ui/alert-dialog.tsx:130:3
AlertDialogTrigger                      src/components/ui/alert-dialog.tsx:131:3
badgeVariants                           src/components/ui/badge.tsx:36:17
CardFooter                              src/components/ui/card.tsx:79:28
DialogPortal                            src/components/ui/dialog.tsx:111:3
DialogOverlay                           src/components/ui/dialog.tsx:112:3
DialogClose                             src/components/ui/dialog.tsx:113:3
DialogTrigger                           src/components/ui/dialog.tsx:114:3
DropdownMenuCheckboxItem                src/components/ui/dropdown-menu.tsx:189:3
DropdownMenuRadioItem                   src/components/ui/dropdown-menu.tsx:190:3
DropdownMenuLabel                       src/components/ui/dropdown-menu.tsx:191:3
DropdownMenuShortcut                    src/components/ui/dropdown-menu.tsx:193:3
DropdownMenuGroup                       src/components/ui/dropdown-menu.tsx:194:3
DropdownMenuPortal                      src/components/ui/dropdown-menu.tsx:195:3
DropdownMenuSub                         src/components/ui/dropdown-menu.tsx:196:3
DropdownMenuSubContent                  src/components/ui/dropdown-menu.tsx:197:3
DropdownMenuSubTrigger                  src/components/ui/dropdown-menu.tsx:198:3
DropdownMenuRadioGroup                  src/components/ui/dropdown-menu.tsx:199:3
SelectGroup                             src/components/ui/select.tsx:149:3
SelectLabel                             src/components/ui/select.tsx:153:3
SelectSeparator                         src/components/ui/select.tsx:155:3
SelectScrollUpButton                    src/components/ui/select.tsx:156:3
SelectScrollDownButton                  src/components/ui/select.tsx:157:3
TableFooter                             src/components/ui/table.tsx:112:3
TableCaption                            src/components/ui/table.tsx:116:3
useCurrentUser                          src/hooks/index.ts:1:31
useUpdateDataset                        src/hooks/index.ts:7:3
useCloneDashboard                       src/hooks/index.ts:28:3
useUpdateGroup                          src/hooks/index.ts:47:3
Unused exported types (28)
BadgeProps              interface  src/components/ui/badge.tsx:26:18
ButtonProps             interface  src/components/ui/button.tsx:36:18
CalendarProps           type       src/components/ui/calendar.tsx:8:13
AuthState               interface  src/stores/auth-store.ts:4:18
DatasetCreateRequest    interface  src/types/dataset.ts:27:18
GroupRef                type       src/types/index.ts:4:3
ColumnSchema            type       src/types/index.ts:11:3
DatasetCreateRequest    type       src/types/index.ts:14:3
CardRef                 type       src/types/index.ts:23:3
OwnerRef                type       src/types/index.ts:24:3
Permission              type       src/types/index.ts:42:3
SharedToType            type       src/types/index.ts:43:3
DashboardShare          type       src/types/index.ts:44:3
ShareCreateRequest      type       src/types/index.ts:45:3
ShareUpdateRequest      type       src/types/index.ts:46:3
Group                   type       src/types/index.ts:57:3
GroupDetail             type       src/types/index.ts:58:3
GroupMember             type       src/types/index.ts:59:3
GroupCreateRequest      type       src/types/index.ts:60:3
GroupUpdateRequest      type       src/types/index.ts:61:3
AddMemberRequest        type       src/types/index.ts:62:3
ApiErrorResponse        type       src/types/index.ts:67:3
Pagination              type       src/types/index.ts:69:3
SchemaChangeType        type       src/types/index.ts:75:3
SchemaChange            type       src/types/index.ts:76:3
ReimportDryRunResponse  type       src/types/index.ts:77:3
ReimportRequest         type       src/types/index.ts:78:3
ReimportRequest         interface  src/types/reimport.ts:17:18
```

### depcheck
```
Unused devDependencies
* @vitest/coverage-v8
* autoprefixer
* knip
* postcss
* tailwindcss
Missing dependencies
* react-resizable: ./src/components/dashboard/DashboardEditor.tsx
```

### ts-prune
```
src/hooks/index.ts:1 - useLogin
src/hooks/index.ts:1 - useLogout
src/hooks/index.ts:1 - useCurrentUser
src/hooks/index.ts:3 - useDatasets
src/hooks/index.ts:4 - useDataset
src/hooks/index.ts:5 - useDatasetPreview
src/hooks/index.ts:6 - useCreateDataset
src/hooks/index.ts:7 - useUpdateDataset
src/hooks/index.ts:8 - useDeleteDataset
src/hooks/index.ts:9 - useS3ImportDataset
src/hooks/index.ts:10 - useReimportDryRun
src/hooks/index.ts:11 - useReimportDataset
src/hooks/index.ts:14 - useCards
src/hooks/index.ts:15 - useCard
src/hooks/index.ts:16 - useCreateCard
src/hooks/index.ts:17 - useUpdateCard
src/hooks/index.ts:18 - useDeleteCard
src/hooks/index.ts:19 - useExecuteCard
src/hooks/index.ts:20 - usePreviewCard
src/hooks/index.ts:23 - useDashboards
src/hooks/index.ts:24 - useDashboard
src/hooks/index.ts:25 - useCreateDashboard
src/hooks/index.ts:26 - useUpdateDashboard
src/hooks/index.ts:27 - useDeleteDashboard
src/hooks/index.ts:28 - useCloneDashboard
src/hooks/index.ts:31 - useShares
src/hooks/index.ts:32 - useCreateShare
src/hooks/index.ts:33 - useUpdateShare
src/hooks/index.ts:34 - useDeleteShare
src/hooks/index.ts:37 - useFilterViews
src/hooks/index.ts:38 - useCreateFilterView
src/hooks/index.ts:39 - useUpdateFilterView
src/hooks/index.ts:40 - useDeleteFilterView
src/hooks/index.ts:41 - getDefaultFilterView
src/hooks/index.ts:44 - useGroups
src/hooks/index.ts:45 - useGroup
src/hooks/index.ts:46 - useCreateGroup
src/hooks/index.ts:47 - useUpdateGroup
src/hooks/index.ts:48 - useDeleteGroup
src/hooks/index.ts:49 - useAddMember
src/hooks/index.ts:50 - useRemoveMember
src/hooks/index.ts:53 - useTransforms
src/hooks/index.ts:54 - useTransform
src/hooks/index.ts:55 - useCreateTransform
src/hooks/index.ts:56 - useUpdateTransform
src/hooks/index.ts:57 - useDeleteTransform
src/hooks/index.ts:58 - useExecuteTransform
src/hooks/index.ts:59 - useTransformExecutions
src/hooks/index.ts:61 - useAuditLogs
src/stores/auth-store.ts:4 - AuthState (used in module)
src/types/index.ts:2 - User
src/types/index.ts:3 - UserWithGroups
src/types/index.ts:4 - GroupRef
src/types/index.ts:5 - LoginRequest
src/types/index.ts:6 - LoginResponse
src/types/index.ts:8 - isUser
src/types/index.ts:8 - isLoginResponse
src/types/index.ts:11 - ColumnSchema
src/types/index.ts:12 - Dataset
src/types/index.ts:13 - DatasetDetail
src/types/index.ts:14 - DatasetCreateRequest
src/types/index.ts:15 - DatasetUpdateRequest
src/types/index.ts:16 - S3ImportRequest
src/types/index.ts:17 - DatasetPreview
src/types/index.ts:19 - isDataset
src/types/index.ts:19 - isColumnSchema
src/types/index.ts:22 - Card
src/types/index.ts:23 - CardRef
src/types/index.ts:24 - OwnerRef
src/types/index.ts:25 - CardDetail
src/types/index.ts:26 - CardCreateRequest
src/types/index.ts:27 - CardUpdateRequest
src/types/index.ts:28 - CardExecuteRequest
src/types/index.ts:29 - CardExecuteResponse
src/types/index.ts:30 - CardPreviewResponse
src/types/index.ts:32 - isCard
src/types/index.ts:35 - LayoutItem
src/types/index.ts:36 - FilterDefinition
src/types/index.ts:37 - DashboardLayout
src/types/index.ts:38 - Dashboard
src/types/index.ts:39 - DashboardDetail
src/types/index.ts:40 - DashboardCreateRequest
src/types/index.ts:41 - DashboardUpdateRequest
src/types/index.ts:42 - Permission
src/types/index.ts:43 - SharedToType
src/types/index.ts:44 - DashboardShare
src/types/index.ts:45 - ShareCreateRequest
src/types/index.ts:46 - ShareUpdateRequest
src/types/index.ts:48 - isDashboard
src/types/index.ts:48 - isLayoutItem
src/types/index.ts:51 - FilterView
src/types/index.ts:52 - FilterViewCreateRequest
src/types/index.ts:53 - FilterViewUpdateRequest
src/types/index.ts:57 - Group
src/types/index.ts:58 - GroupDetail
src/types/index.ts:59 - GroupMember
src/types/index.ts:60 - GroupCreateRequest
src/types/index.ts:61 - GroupUpdateRequest
src/types/index.ts:62 - AddMemberRequest
src/types/index.ts:66 - ApiResponse
src/types/index.ts:67 - ApiErrorResponse
src/types/index.ts:68 - PaginatedResponse
src/types/index.ts:69 - Pagination
src/types/index.ts:70 - PaginationParams
src/types/index.ts:72 - isApiErrorResponse
src/types/index.ts:72 - isPagination
src/types/index.ts:75 - SchemaChangeType
src/types/index.ts:76 - SchemaChange
src/types/index.ts:77 - ReimportDryRunResponse
src/types/index.ts:78 - ReimportRequest
src/types/index.ts:82 - Transform
src/types/index.ts:83 - TransformCreateRequest
src/types/index.ts:84 - TransformUpdateRequest
src/types/index.ts:85 - TransformExecuteResponse
src/types/index.ts:86 - TransformExecution
src/types/index.ts:88 - isTransform
src/types/index.ts:90 - EventType
src/types/index.ts:90 - AuditLog
src/types/index.ts:90 - AuditLogListParams
src/components/common/index.ts:1 - Layout
src/components/common/index.ts:2 - Header
src/components/common/index.ts:3 - Sidebar
src/components/common/index.ts:4 - LoadingSpinner
src/components/common/index.ts:5 - ErrorBoundary
src/components/common/index.ts:6 - ConfirmDialog
src/components/common/index.ts:7 - Pagination
src/components/common/index.ts:8 - AuthGuard
src/components/ui/alert-dialog.tsx:129 - AlertDialogPortal (used in module)
src/components/ui/alert-dialog.tsx:130 - AlertDialogOverlay (used in module)
src/components/ui/alert-dialog.tsx:131 - AlertDialogTrigger (used in module)
src/components/ui/badge.tsx:26 - BadgeProps (used in module)
src/components/ui/badge.tsx:36 - badgeVariants (used in module)
src/components/ui/button.tsx:36 - ButtonProps (used in module)
src/components/ui/calendar.tsx:8 - CalendarProps (used in module)
src/components/ui/card.tsx:79 - CardFooter (used in module)
src/components/ui/dialog.tsx:111 - DialogPortal (used in module)
src/components/ui/dialog.tsx:112 - DialogOverlay (used in module)
src/components/ui/dialog.tsx:113 - DialogClose (used in module)
src/components/ui/dialog.tsx:114 - DialogTrigger (used in module)
src/components/ui/dropdown-menu.tsx:189 - DropdownMenuCheckboxItem (used in module)
src/components/ui/dropdown-menu.tsx:190 - DropdownMenuRadioItem (used in module)
src/components/ui/dropdown-menu.tsx:191 - DropdownMenuLabel (used in module)
src/components/ui/dropdown-menu.tsx:193 - DropdownMenuShortcut (used in module)
src/components/ui/dropdown-menu.tsx:194 - DropdownMenuGroup (used in module)
src/components/ui/dropdown-menu.tsx:195 - DropdownMenuPortal (used in module)
src/components/ui/dropdown-menu.tsx:196 - DropdownMenuSub (used in module)
src/components/ui/dropdown-menu.tsx:197 - DropdownMenuSubContent (used in module)
src/components/ui/dropdown-menu.tsx:198 - DropdownMenuSubTrigger (used in module)
src/components/ui/dropdown-menu.tsx:199 - DropdownMenuRadioGroup (used in module)
src/components/ui/form.tsx:170 - useFormField (used in module)
src/components/ui/form.tsx:171 - Form (used in module)
src/components/ui/form.tsx:172 - FormItem (used in module)
src/components/ui/form.tsx:173 - FormLabel (used in module)
src/components/ui/form.tsx:174 - FormControl (used in module)
src/components/ui/form.tsx:175 - FormDescription (used in module)
src/components/ui/form.tsx:176 - FormMessage (used in module)
src/components/ui/form.tsx:177 - FormField (used in module)
src/components/ui/select.tsx:149 - SelectGroup (used in module)
src/components/ui/select.tsx:153 - SelectLabel (used in module)
src/components/ui/select.tsx:155 - SelectSeparator (used in module)
src/components/ui/select.tsx:156 - SelectScrollUpButton (used in module)
src/components/ui/select.tsx:157 - SelectScrollDownButton (used in module)
src/components/ui/table.tsx:112 - TableFooter (used in module)
src/components/ui/table.tsx:116 - TableCaption (used in module)
src/lib/api/index.ts:1 - authApi
src/lib/api/index.ts:2 - datasetsApi
src/lib/api/index.ts:3 - cardsApi
src/lib/api/index.ts:4 - dashboardsApi
src/lib/api/index.ts:5 - dashboardSharesApi
src/lib/api/index.ts:6 - filterViewsApi
src/lib/api/index.ts:7 - groupsApi
src/lib/api/index.ts:8 - transformsApi
src/lib/api/index.ts:9 - auditLogsApi
```

## Categorized findings

### SAFE
- `frontend/src/components/common/index.ts` (unused barrel file; no imports of `@/components/common` found)

### CAUTION (review before any deletion)
- `frontend/src/components/ui/form.tsx` (unused file but UI component; possible indirect use)
- `frontend/src/__tests__/vitest.d.ts` (test types file; avoid deleting without test review)
- Unused exports in `e2e/helpers/api-helper.ts` and `src/__tests__/helpers/test-utils.tsx` (test code)
- Unused exports/types across `src/components/ui/*`, `src/hooks/index.ts`, `src/types/index.ts`, `src/stores/auth-store.ts` (likely false positives via path aliases or runtime usage)
- depcheck unused devDependencies: `@vitest/coverage-v8`, `autoprefixer`, `knip`, `postcss`, `tailwindcss` (likely build/test tooling)
- knip unlisted dependency `react-resizable/css/styles.css` in dashboard components (dependency/config issue, not deletion)

### DANGER (do not delete; address separately)
- depcheck missing dependency `react-resizable` referenced by `DashboardEditor.tsx`

## Proposed safe deletions
- (none; safe item deleted after frontend test gate)

## Deletions applied
- `frontend/src/components/common/index.ts`

## Test gate results
- Pre-delete: `npm run test:coverage` passed.
- Post-delete: `npm run test:coverage` passed.

---

# Backend Dead Code Analysis

Date: 2026-02-05
Scope: backend (行数上位ファイル)

## Target Files Analyzed
1. `backend/app/services/dataset_service.py` (633行)
2. `backend/app/api/routes/datasets.py` (535行)
3. `backend/app/api/routes/cards.py` (482行)
4. `backend/app/services/parquet_storage.py` (378行)
5. `backend/app/api/routes/dashboards.py` (376行)
6. `backend/app/services/card_execution_service.py` (376行)
7. `backend/app/api/routes/transforms.py` (364行)
8. `backend/app/services/audit_service.py` (313行)
9. `backend/app/services/transform_execution_service.py` (301行)
10. `backend/app/repositories/base.py` (298行)

## Commands
- `python3 -m vulture <target_files> --min-confidence 60`
- `python3 -m ruff check --select F401,F841 <target_files>`
- `docker compose exec -T api pytest tests/api/routes/test_datasets.py --cov=app.api.routes.datasets` (pre/post-delete)

## Tool outputs

### vulture
```
app/api/routes/cards.py:41: unused class 'ExecutionResponse' (60% confidence)
app/api/routes/cards.py:78: unused function 'list_cards' (60% confidence)
app/api/routes/cards.py:130: unused function 'create_card' (60% confidence)
app/api/routes/cards.py:174: unused function 'get_card' (60% confidence)
app/api/routes/cards.py:218: unused function 'update_card' (60% confidence)
app/api/routes/cards.py:268: unused function 'delete_card' (60% confidence)
app/api/routes/cards.py:303: unused function 'preview_card' (60% confidence)
app/api/routes/cards.py:396: unused function 'execute_card' (60% confidence)
app/api/routes/dashboards.py:47: unused function 'list_dashboards' (60% confidence)
app/api/routes/dashboards.py:121: unused function 'create_dashboard' (60% confidence)
app/api/routes/dashboards.py:164: unused function 'get_dashboard' (60% confidence)
app/api/routes/dashboards.py:200: unused function 'update_dashboard' (60% confidence)
app/api/routes/dashboards.py:250: unused function 'delete_dashboard' (60% confidence)
app/api/routes/dashboards.py:285: unused function 'clone_dashboard' (60% confidence)
app/api/routes/datasets.py:7: unused import 'ReimportDryRunResponse' (90% confidence)
app/api/routes/datasets.py:16: unused function 'list_datasets' (60% confidence)
app/api/routes/datasets.py:49: unused function 'create_dataset' (60% confidence)
app/api/routes/datasets.py:126: unused function 's3_import_dataset' (60% confidence)
app/api/routes/datasets.py:180: unused function 'get_dataset' (60% confidence)
app/api/routes/datasets.py:211: unused function 'update_dataset' (60% confidence)
app/api/routes/datasets.py:262: unused function 'delete_dataset' (60% confidence)
app/api/routes/datasets.py:354: unused function 'get_dataset_preview' (60% confidence)
app/api/routes/transforms.py:45: unused function 'list_transforms' (60% confidence)
app/api/routes/transforms.py:83: unused function 'create_transform' (60% confidence)
app/api/routes/transforms.py:113: unused function 'get_transform' (60% confidence)
app/api/routes/transforms.py:149: unused function 'update_transform' (60% confidence)
app/api/routes/transforms.py:199: unused function 'delete_transform' (60% confidence)
app/api/routes/transforms.py:234: unused function 'execute_transform' (60% confidence)
app/api/routes/transforms.py:318: unused function 'list_transform_executions' (60% confidence)
app/repositories/base.py:10: unused class 'BaseRepository' (60% confidence)
app/services/audit_service.py:60: unused method 'log_user_login' (60% confidence)
app/services/audit_service.py:76: unused method 'log_user_logout' (60% confidence)
app/services/audit_service.py:92: unused method 'log_user_login_failed' (60% confidence)
app/services/audit_service.py:117: unused method 'log_dashboard_share_added' (60% confidence)
app/services/audit_service.py:142: unused method 'log_dashboard_share_removed' (60% confidence)
app/services/audit_service.py:165: unused method 'log_dashboard_share_updated' (60% confidence)
app/services/card_execution_service.py:157: unused method 'invalidate_by_dataset' (60% confidence)
app/services/parquet_storage.py:31: unused variable 'partitioned' (60% confidence)
app/services/parquet_storage.py:33: unused variable 'partitions' (60% confidence)
```

### ruff
```
F401 `app.models.dataset.Dataset` imported but unused (app/api/routes/datasets.py:7:32)
F401 `app.models.dataset.ReimportDryRunResponse` imported but unused (app/api/routes/datasets.py:7:56)
```

## Categorized findings

### SAFE (削除済み)
- `app/api/routes/datasets.py:7` - 未使用インポート `Dataset` と `ReimportDryRunResponse`

### CAUTION (削除しない)
- `app/services/card_execution_service.py:157` - `invalidate_by_dataset` メソッド（将来使用の可能性）
- `app/services/parquet_storage.py:31,33` - `StorageResult` のフィールド `partitioned`, `partitions`（実際には使用されている）

### DANGER (削除不可・誤検知)
- FastAPI ルートハンドラー関数（`@router.get`, `@router.post` などでデコレータ経由で使用されている）
- `app/repositories/base.py:10` - `BaseRepository` クラス（多くのリポジトリクラスで継承されている）
- `app/services/audit_service.py` の各種ログメソッド（`auth.py`, `dashboard_shares.py` で使用されている）

## Deletions applied
- `app/api/routes/datasets.py`: 未使用インポート `Dataset` と `ReimportDryRunResponse` を削除

## Test gate results
- Pre-delete: `pytest tests/api/routes/test_datasets.py` 37 passed
- Post-delete: `pytest tests/api/routes/test_datasets.py` 37 passed
- ruff check: All checks passed

## Summary
- 削除したコード: 2件の未使用インポート
- テスト結果: 削除前後でテストは全て成功
- 注意: vulture は FastAPI のデコレータ経由の使用を検出できないため、多くの誤検知が発生。実際の削除は ruff の静的解析結果に基づいて実施。
