/**
 * Sharing & Group E2E Tests
 *
 * テストシナリオ:
 * 1. Dashboard共有フロー (Owner -> ShareDialog -> 追加 -> 確認)
 * 2. 共有されたダッシュボードの閲覧 (共有先ユーザー視点)
 * 3. 権限別操作制限 (viewer / editor / owner)
 * 4. Group管理 (Admin限定)
 */
import { test, expect } from '@playwright/test';
import { loginViaUI } from './helpers/login-helper';
import {
  getAccessToken,
  createDataset,
  createCard,
  createDashboard,
  createShare,
  createGroup,
  cleanupTestData,
  type TestDataCleanup,
} from './helpers/api-helper';

// --- テストユーザー情報 (scripts/seed_test_user.py で作成済み想定) ---
// Owner / Admin ユーザー
const ADMIN_EMAIL = 'admin@example.com';
const ADMIN_PASSWORD = 'Admin@1234';

// 共有先ユーザー (viewer 用)
const VIEWER_EMAIL = 'e2e-viewer@example.com';
const VIEWER_PASSWORD = 'Test@1234';

// 共有先ユーザー (editor 用)
const EDITOR_EMAIL = 'e2e-editor@example.com';
const EDITOR_PASSWORD = 'Test@1234';

// 非Admin ユーザー
const MEMBER_EMAIL = 'e2e-member@example.com';
const MEMBER_PASSWORD = 'Test@1234';

// -----------------------------------------------------------------------
// 1. Dashboard共有フロー
// -----------------------------------------------------------------------
test.describe('Dashboard共有フロー', () => {
  let cleanup: TestDataCleanup;
  let adminToken: string;

  test.beforeEach(async () => {
    cleanup = {
      datasetIds: [],
      cardIds: [],
      dashboardIds: [],
      shareIds: [],
      groupIds: [],
      transformIds: [],
      filterViewIds: [],
    };
    adminToken = await getAccessToken(ADMIN_EMAIL, ADMIN_PASSWORD);
  });

  test.afterEach(async () => {
    await cleanupTestData(adminToken, cleanup);
  });

  test('Owner がダッシュボードを共有できる', async ({ page }) => {
    // --- 事前準備: ダッシュボード作成 ---
    const csvContent = 'date,product,amount\n2024-01-01,Widget A,1000\n';
    const dsName = `E2E Share DS ${Date.now()}`;
    const dsId = await createDataset(adminToken, dsName, csvContent);
    cleanup.datasetIds.push(dsId);

    const cardName = `E2E Share Card ${Date.now()}`;
    const cardId = await createCard(adminToken, cardName, dsId);
    cleanup.cardIds.push(cardId);

    const dashName = `E2E Share Dashboard ${Date.now()}`;
    const dashId = await createDashboard(adminToken, dashName, [cardId]);
    cleanup.dashboardIds.push(dashId);

    // --- UI操作 ---
    await loginViaUI(page, ADMIN_EMAIL, ADMIN_PASSWORD);

    // ダッシュボード閲覧ページへ直接移動
    await page.goto(`/dashboards/${dashId}`);
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: dashName })).toBeVisible();

    // 共有ボタンが表示されていることを確認 (owner のみ)
    const shareButton = page.getByRole('button', { name: /共有/ });
    await expect(shareButton).toBeVisible();

    // 共有ボタンをクリック → ShareDialog が開く
    await shareButton.click();
    await expect(page.getByRole('heading', { name: '共有設定' })).toBeVisible();

    // 共有先ID入力
    await page.getByLabel('共有先ID').fill('test-user-123');

    // 権限選択 (デフォルト: viewer)
    // 権限ドロップダウンを開いて editor を選択
    await page.getByLabel('権限').click();
    await page.getByRole('option', { name: 'editor' }).click();

    // 追加ボタンをクリック
    await page.getByRole('button', { name: '追加' }).click();

    // 共有一覧テーブルに追加されたことを確認
    await page.waitForTimeout(1000); // 追加処理完了待ち
    await expect(page.getByText('test-user-123')).toBeVisible();
    // テーブル行内の editor 権限を確認
    const shareRow = page.locator('tr').filter({ hasText: 'test-user-123' });
    await expect(shareRow.getByText('editor')).toBeVisible();
  });
});

// -----------------------------------------------------------------------
// 2. 共有されたダッシュボードの閲覧
// -----------------------------------------------------------------------
test.describe('共有されたダッシュボードの閲覧', () => {
  let cleanup: TestDataCleanup;
  let adminToken: string;
  let dashId: string;
  let dashName: string;

  test.beforeAll(async () => {
    cleanup = {
      datasetIds: [],
      cardIds: [],
      dashboardIds: [],
      shareIds: [],
      groupIds: [],
      transformIds: [],
      filterViewIds: [],
    };

    adminToken = await getAccessToken(ADMIN_EMAIL, ADMIN_PASSWORD);

    // ダッシュボード作成
    const csvContent = 'date,product,amount\n2024-01-01,Widget A,1000\n';
    const dsId = await createDataset(adminToken, `E2E Shared DS ${Date.now()}`, csvContent);
    cleanup.datasetIds.push(dsId);

    const cardId = await createCard(adminToken, `E2E Shared Card ${Date.now()}`, dsId);
    cleanup.cardIds.push(cardId);

    dashName = `E2E Shared Dashboard ${Date.now()}`;
    dashId = await createDashboard(adminToken, dashName, [cardId]);
    cleanup.dashboardIds.push(dashId);

    // viewer 権限で共有
    // viewerToken のユーザーIDを取得するため、login API のレスポンスを使う
    const loginRes = await fetch('http://localhost:8000/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: VIEWER_EMAIL, password: VIEWER_PASSWORD }),
    });
    const loginData = await loginRes.json();
    const viewerUserId = loginData.data.user.user_id;

    const shareId = await createShare(adminToken, dashId, 'user', viewerUserId, 'viewer');
    cleanup.shareIds.push({ dashboardId: dashId, shareId });
  });

  test.afterAll(async () => {
    await cleanupTestData(adminToken, cleanup);
  });

  test('共有先ユーザーのダッシュボード一覧に共有ダッシュボードが表示される', async ({ page }) => {
    await loginViaUI(page, VIEWER_EMAIL, VIEWER_PASSWORD);

    // ダッシュボード一覧ページで共有されたダッシュボードが表示される
    await expect(page.getByText(dashName)).toBeVisible();
  });

  test('viewer 権限では編集ボタンが非表示', async ({ page }) => {
    await loginViaUI(page, VIEWER_EMAIL, VIEWER_PASSWORD);

    // ダッシュボード閲覧ページへ
    await page.goto(`/dashboards/${dashId}`);
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: dashName })).toBeVisible();

    // 編集ボタンが非表示
    await expect(page.getByRole('button', { name: /編集/ })).not.toBeVisible();

    // 共有ボタンも非表示 (owner のみ)
    await expect(page.getByRole('button', { name: /共有/ })).not.toBeVisible();
  });

  test('viewer 権限でもダッシュボードの内容を閲覧できる', async ({ page }) => {
    await loginViaUI(page, VIEWER_EMAIL, VIEWER_PASSWORD);

    await page.goto(`/dashboards/${dashId}`);
    await expect(page.getByRole('heading', { name: dashName })).toBeVisible();

    // ダッシュボード内にカードが表示されること (ローディング完了待ち)
    await page.waitForLoadState('networkidle');
  });
});

// -----------------------------------------------------------------------
// 3. 権限別操作制限
// -----------------------------------------------------------------------
test.describe('権限別操作制限', () => {
  let cleanup: TestDataCleanup;
  let adminToken: string;
  let dashId: string;
  let dashName: string;

  test.beforeAll(async () => {
    cleanup = {
      datasetIds: [],
      cardIds: [],
      dashboardIds: [],
      shareIds: [],
      groupIds: [],
      transformIds: [],
      filterViewIds: [],
    };

    adminToken = await getAccessToken(ADMIN_EMAIL, ADMIN_PASSWORD);

    // ダッシュボード作成
    const csvContent = 'date,product,amount\n2024-01-01,Widget A,1000\n';
    const dsId = await createDataset(adminToken, `E2E Perm DS ${Date.now()}`, csvContent);
    cleanup.datasetIds.push(dsId);

    const cardId = await createCard(adminToken, `E2E Perm Card ${Date.now()}`, dsId);
    cleanup.cardIds.push(cardId);

    dashName = `E2E Permission Dashboard ${Date.now()}`;
    dashId = await createDashboard(adminToken, dashName, [cardId]);
    cleanup.dashboardIds.push(dashId);

    // viewer, editor のユーザーIDを取得して共有
    for (const { email, password, perm } of [
      { email: VIEWER_EMAIL, password: VIEWER_PASSWORD, perm: 'viewer' as const },
      { email: EDITOR_EMAIL, password: EDITOR_PASSWORD, perm: 'editor' as const },
    ]) {
      const loginRes = await fetch('http://localhost:8000/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      const loginData = await loginRes.json();
      const userId = loginData.data.user.user_id;
      const shareId = await createShare(adminToken, dashId, 'user', userId, perm);
      cleanup.shareIds.push({ dashboardId: dashId, shareId });
    }
  });

  test.afterAll(async () => {
    await cleanupTestData(adminToken, cleanup);
  });

  test('Viewer: 編集ボタンなし、共有ボタンなし', async ({ page }) => {
    await loginViaUI(page, VIEWER_EMAIL, VIEWER_PASSWORD);
    await page.goto(`/dashboards/${dashId}`);
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: dashName })).toBeVisible();

    // 編集ボタン非表示
    await expect(page.getByRole('button', { name: /編集/ })).not.toBeVisible();
    // 共有ボタン非表示
    await expect(page.getByRole('button', { name: /共有/ })).not.toBeVisible();
  });

  test('Editor: 編集ボタンあり、共有ボタンなし', async ({ page }) => {
    await loginViaUI(page, EDITOR_EMAIL, EDITOR_PASSWORD);
    await page.goto(`/dashboards/${dashId}`);
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: dashName })).toBeVisible();

    // 編集ボタンあり
    await expect(page.getByRole('button', { name: /編集/ })).toBeVisible();
    // 共有ボタン非表示 (owner のみ)
    await expect(page.getByRole('button', { name: /共有/ })).not.toBeVisible();
  });

  test('Editor: ダッシュボード一覧で削除ボタンなし', async ({ page }) => {
    await loginViaUI(page, EDITOR_EMAIL, EDITOR_PASSWORD);
    await page.goto('/dashboards');

    // ダッシュボード名の行を特定
    const row = page.getByRole('row').filter({ hasText: dashName });
    await expect(row).toBeVisible();

    // その行の中に編集アイコンボタン(Pencil)があること
    // (icon button は aria-label がないので、行内の button 数で判断)
    const editBtn = row.locator('button').nth(1); // 0=Eye, 1=Pencil
    await expect(editBtn).toBeVisible();

    // 削除ボタン(Trash2)がないこと (owner のみ)
    const buttons = row.locator('button');
    const buttonCount = await buttons.count();
    // viewer: Eye のみ(1), editor: Eye + Pencil(2), owner: Eye + Pencil + Trash(3)
    expect(buttonCount).toBe(2);
  });

  test('Owner: 全ボタンあり (編集・共有・削除)', async ({ page }) => {
    await loginViaUI(page, ADMIN_EMAIL, ADMIN_PASSWORD);
    await page.goto(`/dashboards/${dashId}`);
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: dashName })).toBeVisible();

    // 編集ボタンあり
    await expect(page.getByRole('button', { name: /編集/ })).toBeVisible();
    // 共有ボタンあり
    await expect(page.getByRole('button', { name: /共有/ })).toBeVisible();
  });

  test('Owner: ダッシュボード一覧で全操作ボタン表示', async ({ page }) => {
    await loginViaUI(page, ADMIN_EMAIL, ADMIN_PASSWORD);
    await page.goto('/dashboards');

    const row = page.getByRole('row').filter({ hasText: dashName });
    await expect(row).toBeVisible();

    // owner: Eye + Pencil + Trash(3)
    const buttons = row.locator('button');
    const buttonCount = await buttons.count();
    expect(buttonCount).toBe(3);
  });
});

// -----------------------------------------------------------------------
// 4. Group管理 (Admin限定)
// -----------------------------------------------------------------------
test.describe('Group管理', () => {
  let cleanup: TestDataCleanup;
  let adminToken: string;

  test.beforeEach(async () => {
    cleanup = {
      datasetIds: [],
      cardIds: [],
      dashboardIds: [],
      shareIds: [],
      groupIds: [],
      transformIds: [],
      filterViewIds: [],
    };
    adminToken = await getAccessToken(ADMIN_EMAIL, ADMIN_PASSWORD);
  });

  test.afterEach(async () => {
    await cleanupTestData(adminToken, cleanup);
  });

  test('Admin: サイドバーに「グループ管理」リンクが表示される', async ({ page }) => {
    await loginViaUI(page, ADMIN_EMAIL, ADMIN_PASSWORD);

    // サイドバーに「グループ管理」リンクがある (NavLink として表示)
    await expect(page.getByRole('link', { name: 'グループ管理' })).toBeVisible();
  });

  test('非Admin: サイドバーに「グループ管理」リンクが表示されない', async ({ page }) => {
    await loginViaUI(page, MEMBER_EMAIL, MEMBER_PASSWORD);

    // サイドバーに「グループ管理」リンクがない
    await expect(page.getByRole('link', { name: 'グループ管理' })).not.toBeVisible();
  });

  test('Admin: グループ作成ができる', async ({ page }) => {
    await loginViaUI(page, ADMIN_EMAIL, ADMIN_PASSWORD);

    // グループ管理ページへ
    await page.getByRole('link', { name: 'グループ管理' }).click();
    await expect(page).toHaveURL('/admin/groups');

    // ページ見出し
    await expect(page.getByRole('heading', { name: 'グループ管理' })).toBeVisible();

    // 新規作成ボタンをクリック
    await page.getByRole('button', { name: '新規作成' }).click();

    // ダイアログが開く (DialogTitle として表示)
    await expect(page.getByRole('heading', { name: '新規グループ' })).toBeVisible();

    // グループ名を入力
    const groupName = `E2E Test Group ${Date.now()}`;
    await page.getByLabel('名前').fill(groupName);

    // 作成ボタンをクリック (ダイアログ内の2つ目の作成ボタン)
    await page.getByRole('button', { name: '作成' }).last().click();

    // ダイアログが閉じて一覧にグループが表示される
    await page.waitForTimeout(1000);
    await expect(page.getByText(groupName)).toBeVisible();

    // クリーンアップ: 作成されたグループIDを取得
    const groupRow = page.locator('tr').filter({ hasText: groupName });
    const groupIdCell = groupRow.locator('td').first();
    const groupId = await groupIdCell.textContent();
    if (groupId) {
      cleanup.groupIds.push(groupId.trim());
    }
  });

  test('Admin: グループにメンバーを追加できる', async ({ page }) => {
    // --- 事前準備: グループ作成 (API経由) ---
    const groupName = `E2E Member Group ${Date.now()}`;
    const groupId = await createGroup(adminToken, groupName);
    cleanup.groupIds.push(groupId);

    await loginViaUI(page, ADMIN_EMAIL, ADMIN_PASSWORD);

    // グループ管理ページへ
    await page.goto('/admin/groups');
    await expect(page.getByRole('heading', { name: 'グループ管理' })).toBeVisible();
    await expect(page.getByText(groupName)).toBeVisible();

    // グループの詳細ボタンをクリック
    const groupRow = page.locator('tr').filter({ hasText: groupName });
    await groupRow.getByRole('button', { name: '詳細' }).click();

    // GroupDetailPanel が表示される
    await expect(page.getByRole('heading', { name: 'メンバー' })).toBeVisible();

    // 「メンバー追加」ボタンをクリック
    await page.getByRole('button', { name: 'メンバー追加' }).click();

    // MemberAddDialog が開く
    await expect(page.getByRole('heading', { name: 'メンバー追加' })).toBeVisible();

    // ユーザーID入力 (実在する e2e@example.com を使用)
    await page.getByLabel('ユーザーID').fill('e2e@example.com');

    // 追加ボタンをクリック
    await page.getByRole('button', { name: '追加' }).last().click();

    // メンバーテーブルにユーザーIDが表示される
    await page.waitForTimeout(1000);
  });

  test('Admin: グループを削除できる', async ({ page }) => {
    // --- 事前準備: グループ作成 (API経由) ---
    const groupName = `E2E Delete Group ${Date.now()}`;
    const groupId = await createGroup(adminToken, groupName);
    cleanup.groupIds.push(groupId);

    await loginViaUI(page, ADMIN_EMAIL, ADMIN_PASSWORD);

    // グループ管理ページへ
    await page.goto('/admin/groups');
    await expect(page.getByRole('heading', { name: 'グループ管理' })).toBeVisible();
    await expect(page.getByText(groupName)).toBeVisible();

    // 削除ボタンをクリック
    const groupRow = page.locator('tr').filter({ hasText: groupName });
    await groupRow.getByRole('button', { name: '削除' }).click();

    // 確認ダイアログ
    await expect(page.getByRole('heading', { name: 'グループの削除' })).toBeVisible();

    // 確認ダイアログの「削除」ボタンをクリック
    await page.getByRole('button', { name: '削除' }).last().click();

    // 一覧からグループが消える
    await page.waitForTimeout(1000);
    await expect(page.getByText(groupName)).not.toBeVisible();

    // 既に削除済みなのでクリーンアップから除外
    cleanup.groupIds = cleanup.groupIds.filter((id) => id !== groupId);
  });
});
