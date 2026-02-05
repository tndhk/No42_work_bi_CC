/**
 * Dataset E2E Tests
 */
import { test, expect } from '@playwright/test';
import { loginViaUI } from './helpers/login-helper';
import { getAccessToken, cleanupTestData, createDataset, type TestDataCleanup } from './helpers/api-helper';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// テストユーザ情報
const TEST_USER_EMAIL = 'e2e@example.com';
const TEST_USER_PASSWORD = 'Test@1234';

test.describe('Dataset', () => {
  let cleanup: TestDataCleanup;

  test.beforeEach(async ({ page }) => {
    // クリーンアップ用のトラッキング初期化
    cleanup = {
      datasetIds: [],
      cardIds: [],
      dashboardIds: [],
      shareIds: [],
      groupIds: [],
      transformIds: [],
      filterViewIds: [],
    };

    // ログイン
    await loginViaUI(page, TEST_USER_EMAIL, TEST_USER_PASSWORD);
  });

  test.afterEach(async () => {
    // テストデータをクリーンアップ
    if (cleanup.datasetIds.length > 0 || cleanup.cardIds.length > 0 || cleanup.dashboardIds.length > 0) {
      const token = await getAccessToken(TEST_USER_EMAIL, TEST_USER_PASSWORD);
      await cleanupTestData(token, cleanup);
    }
  });

  test('CSVインポート→詳細確認', async ({ page }) => {
    // サイドバーの「データセット」をクリック
    await page.getByRole('link', { name: 'データセット' }).click();

    // データセットページに移動したことを確認
    await expect(page).toHaveURL('/datasets');

    // 「インポート」ボタンをクリック
    await page.getByRole('button', { name: 'インポート' }).click();

    // ファイル選択ダイアログが開くので、CSVファイルを選択
    const csvPath = path.join(__dirname, 'sample-data', 'test-sales.csv');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(csvPath);

    // データセット名を入力
    const datasetName = `E2E Test Dataset ${Date.now()}`;
    await page.getByLabel('データセット名').fill(datasetName);

    // 「インポート」ボタンをクリックして送信（フォーム内のsubmitボタン）
    await page.getByRole('button', { name: 'インポート', exact: true }).click();

    // インポート成功後、データセット詳細ページに遷移することを確認
    await expect(page).toHaveURL(/\/datasets\/ds_[a-zA-Z0-9]+/);

    // データセット名が表示されることを確認
    await expect(page.getByRole('heading', { name: datasetName })).toBeVisible();

    // スキーマ情報が表示されることを確認（columnheaderロールで特定）
    await expect(page.getByRole('columnheader', { name: 'date' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'product' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'amount' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'quantity' })).toBeVisible();

    // 行数が表示されることを確認 (5行)
    await expect(page.getByText('5行 / 4列')).toBeVisible();

    // データセットIDを取得してクリーンアップ用に保存
    const url = page.url();
    const match = url.match(/\/datasets\/(ds_[a-zA-Z0-9]+)/);
    if (match) {
      cleanup.datasetIds.push(match[1]);
    }
  });

  test('一覧表示・削除', async ({ page }) => {
    // 事前にデータセットを作成 (API経由)
    const token = await getAccessToken(TEST_USER_EMAIL, TEST_USER_PASSWORD);
    const csvContent = 'date,product,amount,quantity\n2024-01-01,Widget A,1000,10\n';

    const datasetName = `E2E Test Dataset for Delete ${Date.now()}`;
    const datasetId = await createDataset(token, datasetName, csvContent);
    cleanup.datasetIds.push(datasetId);

    // サイドバーの「データセット」をクリック
    await page.getByRole('link', { name: 'データセット' }).click();

    // データセット一覧ページに移動したことを確認
    await expect(page).toHaveURL('/datasets');

    // 作成したデータセットが一覧に表示されることを確認
    await expect(page.getByText(datasetName)).toBeVisible();

    // データセット名を含む行からゴミ箱アイコン（削除ボタン）をクリック
    const datasetRow = page.locator('tr').filter({ hasText: datasetName });
    await datasetRow.locator('button').last().click();

    // 確認ダイアログが表示されることを確認
    await expect(page.getByText('データセットの削除')).toBeVisible();
    await expect(page.getByText(/このデータセットを削除しますか/)).toBeVisible();

    // 確認ダイアログの「削除」ボタンをクリック
    await page.getByRole('button', { name: '削除', exact: true }).click();

    // 削除したデータセットが一覧に表示されないことを確認
    await expect(page.getByText(datasetName)).not.toBeVisible();

    // クリーンアップリストから削除 (既に削除済み)
    cleanup.datasetIds = cleanup.datasetIds.filter(id => id !== datasetId);
  });

  test('データセット詳細でプレビューが表示される', async ({ page }) => {
    // 事前にデータセットを作成 (API経由)
    const token = await getAccessToken(TEST_USER_EMAIL, TEST_USER_PASSWORD);
    const csvContent = `date,product,amount,quantity
2024-01-01,Widget A,1000,10
2024-01-02,Widget B,1500,15
2024-01-03,Widget A,2000,20`;

    const datasetName = `E2E Test Dataset Preview ${Date.now()}`;
    const datasetId = await createDataset(token, datasetName, csvContent);
    cleanup.datasetIds.push(datasetId);

    // サイドバーの「データセット」をクリック
    await page.getByRole('link', { name: 'データセット' }).click();

    // データセット一覧ページに移動したことを確認
    await expect(page).toHaveURL('/datasets');

    // 作成したデータセットが一覧に表示されることを確認
    await expect(page.getByText(datasetName)).toBeVisible();

    // 目アイコン（詳細表示ボタン）をクリックして詳細ページに移動
    const datasetRow = page.locator('tr').filter({ hasText: datasetName });
    await datasetRow.locator('button').first().click();

    // 詳細ページに遷移することを確認
    await expect(page).toHaveURL(/\/datasets\/ds_[a-zA-Z0-9]+/);

    // データセット名が表示されることを確認（h1タグ）
    await expect(page.locator('h1').filter({ hasText: datasetName })).toBeVisible();

    // プレビューセクションが表示されることを確認（CardTitleのプレビュー）
    await expect(page.getByText('プレビュー').first()).toBeVisible();

    // データのプレビューが表示されることを確認
    await expect(page.getByRole('cell', { name: 'Widget A' }).first()).toBeVisible();
    await expect(page.getByRole('cell', { name: 'Widget B' })).toBeVisible();
    await expect(page.getByRole('cell', { name: '1000' })).toBeVisible();
    await expect(page.getByRole('cell', { name: '1500' })).toBeVisible();
  });
});
