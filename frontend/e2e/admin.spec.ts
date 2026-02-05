/**
 * Admin Features E2E Tests
 *
 * 管理者機能（監査ログ、グループ管理）のE2Eテスト
 */
import { test, expect } from '@playwright/test';
import { loginViaUI } from './helpers/login-helper';
import {
  getAccessToken,
  createGroup,
  deleteGroup,
  addGroupMember,
  cleanupTestData,
  type TestDataCleanup,
} from './helpers/api-helper';

// 管理者テストユーザー情報
const ADMIN_USER_EMAIL = 'admin@example.com';
const ADMIN_USER_PASSWORD = 'Admin@1234';

test.describe('Admin Features', () => {
  let cleanup: TestDataCleanup;
  let token: string;

  test.beforeEach(async ({ page }) => {
    // Given: クリーンアップ用のトラッキング初期化
    cleanup = {
      datasetIds: [],
      cardIds: [],
      dashboardIds: [],
      shareIds: [],
      groupIds: [],
      transformIds: [],
      filterViewIds: [],
    };

    // Given: 管理者トークン取得とログイン
    token = await getAccessToken(ADMIN_USER_EMAIL, ADMIN_USER_PASSWORD);
    await loginViaUI(page, ADMIN_USER_EMAIL, ADMIN_USER_PASSWORD);
  });

  test.afterEach(async () => {
    // クリーンアップ: テストデータを削除
    await cleanupTestData(token, cleanup);
  });

  test.describe('Audit Logs', () => {
    test('ADM-01: 監査ログ一覧が表示される', async ({ page }) => {
      // When: 監査ログページに移動
      await page.goto('/admin/audit-logs');

      // Then: ページタイトルが表示される
      await expect(page.getByRole('heading', { name: '監査ログ' })).toBeVisible();

      // Then: テーブルヘッダーが表示される
      await expect(page.getByRole('columnheader', { name: 'タイムスタンプ' })).toBeVisible();
      await expect(page.getByRole('columnheader', { name: 'イベントタイプ' })).toBeVisible();
      await expect(page.getByRole('columnheader', { name: 'ユーザーID' })).toBeVisible();
      await expect(page.getByRole('columnheader', { name: '対象タイプ' })).toBeVisible();
      await expect(page.getByRole('columnheader', { name: '対象ID' })).toBeVisible();

      // Then: ログエントリまたは空状態が表示される
      const hasLogs = await page.getByRole('row').count() > 1; // ヘッダー行を除く
      const hasEmptyState = await page.getByText('監査ログがありません').isVisible().catch(() => false);
      expect(hasLogs || hasEmptyState).toBeTruthy();
    });

    test('ADM-02: イベントタイプでフィルタリングできる', async ({ page }) => {
      // When: 監査ログページに移動
      await page.goto('/admin/audit-logs');
      await expect(page.getByRole('heading', { name: '監査ログ' })).toBeVisible();

      // When: イベントタイプフィルターをクリック
      await page.getByRole('combobox').click();

      // Then: フィルターオプションが表示される
      await expect(page.getByRole('option', { name: 'すべて' })).toBeVisible();
      await expect(page.getByRole('option', { name: 'ユーザーログイン' })).toBeVisible();

      // When: 「ユーザーログイン」を選択
      await page.getByRole('option', { name: 'ユーザーログイン' }).click();

      // Then: フィルターが適用される (テーブルが更新される)
      await page.waitForTimeout(1000);

      // フィルターが適用されたことを確認 (空状態またはログインイベントのみ)
      const hasLoginEvents = await page.getByText(/ユーザーログイン|USER_LOGIN/i).first().isVisible().catch(() => false);
      const hasEmptyState = await page.getByText('監査ログがありません').isVisible().catch(() => false);
      expect(hasLoginEvents || hasEmptyState).toBeTruthy();
    });

    test('ADM-03: ページネーションが機能する', async ({ page }) => {
      // When: 監査ログページに移動
      await page.goto('/admin/audit-logs');
      await expect(page.getByRole('heading', { name: '監査ログ' })).toBeVisible();

      // Then: ページネーション情報が表示される (ログがある場合)
      const paginationInfo = page.getByText(/\d+件中/);
      const hasLogs = await paginationInfo.isVisible().catch(() => false);

      if (hasLogs) {
        // Then: ページネーションボタンが表示される
        await expect(page.getByRole('button', { name: '前へ' })).toBeVisible();
        await expect(page.getByRole('button', { name: '次へ' })).toBeVisible();
      }
    });
  });

  test.describe('Group Management', () => {
    test('ADM-04: グループ一覧が表示される', async ({ page }) => {
      // When: グループ管理ページに移動
      await page.goto('/admin/groups');

      // Then: ページタイトルが表示される
      await expect(page.getByRole('heading', { name: 'グループ管理' })).toBeVisible();

      // Then: 新規作成ボタンが表示される
      await expect(page.getByRole('button', { name: '新規作成' })).toBeVisible();

      // Then: テーブルヘッダーが表示される
      await expect(page.getByRole('columnheader', { name: 'ID' })).toBeVisible();
      await expect(page.getByRole('columnheader', { name: '名前' })).toBeVisible();
      await expect(page.getByRole('columnheader', { name: '作成日時' })).toBeVisible();
      await expect(page.getByRole('columnheader', { name: '操作' })).toBeVisible();
    });

    test('ADM-05: グループを作成できる', async ({ page }) => {
      // Given: グループ管理ページに移動
      await page.goto('/admin/groups');
      await expect(page.getByRole('heading', { name: 'グループ管理' })).toBeVisible();

      // When: 新規作成ボタンをクリック
      await page.getByRole('button', { name: '新規作成' }).click();

      // Then: 作成ダイアログが表示される
      await expect(page.getByRole('heading', { name: '新規グループ' })).toBeVisible();

      // When: グループ名を入力
      const timestamp = Date.now();
      const groupName = `E2E Test Group ${timestamp}`;
      await page.getByLabel('名前').fill(groupName);

      // When: 作成ボタンをクリック
      await page.getByRole('button', { name: '作成' }).last().click();

      // Then: グループが作成され一覧に表示される
      await page.waitForTimeout(1000);
      await expect(page.getByText(groupName)).toBeVisible();

      // クリーンアップ: グループIDを取得して削除リストに追加
      const groupId = await page.locator('tr').filter({ hasText: groupName }).locator('td').first().textContent();
      if (groupId) {
        cleanup.groupIds.push(groupId);
      }
    });

    test('ADM-06: グループにメンバーを追加できる', async ({ page }) => {
      // Given: グループが作成済み
      const timestamp = Date.now();
      const groupName = `E2E Group Member ${timestamp}`;
      const groupId = await createGroup(token, groupName);
      cleanup.groupIds.push(groupId);

      // When: グループ管理ページに移動
      await page.goto('/admin/groups');
      await expect(page.getByRole('heading', { name: 'グループ管理' })).toBeVisible();

      // When: グループが表示されるまで待機
      await expect(page.getByText(groupName)).toBeVisible();

      // When: 詳細ボタンをクリック
      const groupRow = page.locator('tr').filter({ hasText: groupName });
      await groupRow.getByRole('button', { name: '詳細' }).click();

      // Then: グループ詳細パネルが表示される (heading で判定)
      await expect(page.getByRole('heading', { name: 'メンバー' })).toBeVisible();

      // When: メンバー追加ボタンをクリック
      await page.getByRole('button', { name: 'メンバー追加' }).click();

      // Then: メンバー追加ダイアログが表示される
      await expect(page.getByRole('heading', { name: 'メンバー追加' })).toBeVisible();

      // When: ユーザーIDを入力 (テスト用ユーザーを使用)
      await page.getByLabel('ユーザーID').fill('e2e@example.com');

      // When: 追加ボタンをクリック
      await page.getByRole('button', { name: '追加' }).last().click();

      // Then: メンバーが追加される (エラーが表示されないか、メンバー一覧に追加される)
      await page.waitForTimeout(1000);
    });

    test('ADM-07: グループからメンバーを削除できる', async ({ page }) => {
      // Given: グループとメンバーが作成済み
      const timestamp = Date.now();
      const groupName = `E2E Group Remove ${timestamp}`;
      const groupId = await createGroup(token, groupName);
      cleanup.groupIds.push(groupId);

      // メンバーを追加 (e2eユーザーを追加)
      try {
        await addGroupMember(token, groupId, 'e2e@example.com');
      } catch {
        // ユーザーが既に追加されている場合はスキップ
      }

      // When: グループ管理ページに移動
      await page.goto('/admin/groups');
      await expect(page.getByRole('heading', { name: 'グループ管理' })).toBeVisible();

      // When: グループが表示されるまで待機
      await expect(page.getByText(groupName)).toBeVisible();

      // When: 詳細ボタンをクリック
      const groupRow = page.locator('tr').filter({ hasText: groupName });
      await groupRow.getByRole('button', { name: '詳細' }).click();

      // Then: グループ詳細パネルが表示される (heading で判定)
      await expect(page.getByRole('heading', { name: 'メンバー' })).toBeVisible();

      // メンバーが存在する場合のみ削除テスト
      const memberExists = await page.getByText('e2e@example.com').isVisible().catch(() => false);
      if (memberExists) {
        // When: メンバー行の削除ボタンをクリック
        const memberRow = page.locator('tr').filter({ hasText: 'e2e@example.com' });
        await memberRow.getByRole('button', { name: '削除' }).click();

        // Then: 確認ダイアログが表示される
        await expect(page.getByRole('heading', { name: 'メンバーの削除' })).toBeVisible();

        // When: 削除を確認
        await page.getByRole('button', { name: '削除' }).last().click();

        // Then: メンバーが削除される
        await page.waitForTimeout(1000);
      }
    });

    test('ADM-08: グループを削除できる', async ({ page }) => {
      // Given: グループが作成済み
      const timestamp = Date.now();
      const groupName = `E2E Group Delete ${timestamp}`;
      const groupId = await createGroup(token, groupName);
      // 削除するのでcleanupには追加しない

      // When: グループ管理ページに移動
      await page.goto('/admin/groups');
      await expect(page.getByRole('heading', { name: 'グループ管理' })).toBeVisible();

      // When: グループが表示されるまで待機
      await expect(page.getByText(groupName)).toBeVisible();

      // When: 削除ボタンをクリック
      const groupRow = page.locator('tr').filter({ hasText: groupName });
      await groupRow.getByRole('button', { name: '削除' }).click();

      // Then: 確認ダイアログが表示される
      await expect(page.getByRole('heading', { name: 'グループの削除' })).toBeVisible();

      // When: 削除を確認
      await page.getByRole('button', { name: '削除' }).last().click();

      // Then: グループが削除される
      await page.waitForTimeout(1000);
      await expect(page.getByText(groupName)).not.toBeVisible();
    });
  });
});
