/**
 * Dataset E2E Tests
 */
import { test, expect } from '@playwright/test';
import { loginViaUI } from './helpers/login-helper';
import { getAccessToken, cleanupTestData, type TestDataCleanup } from './helpers/api-helper';
import path from 'path';

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

    // オプション: 説明を入力
    await page.getByLabel('説明').fill('E2E test dataset for CSV import');

    // 「インポート」ボタンをクリックして送信
    await page.getByRole('button', { name: 'インポート' }).click();

    // インポート成功後、データセット詳細ページに遷移することを確認
    await expect(page).toHaveURL(/\/datasets\/ds_[a-zA-Z0-9]+/);

    // データセット名が表示されることを確認
    await expect(page.getByRole('heading', { name: datasetName })).toBeVisible();

    // スキーマ情報が表示されることを確認
    await expect(page.getByText('date')).toBeVisible();
    await expect(page.getByText('product')).toBeVisible();
    await expect(page.getByText('amount')).toBeVisible();
    await expect(page.getByText('quantity')).toBeVisible();

    // 行数が表示されることを確認 (5行)
    await expect(page.getByText('5')).toBeVisible();

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
    const { createDataset } = await import('./helpers/api-helper');
    const datasetName = `E2E Test Dataset for Delete ${Date.now()}`;
    const datasetId = await createDataset(token, datasetName, csvContent);
    cleanup.datasetIds.push(datasetId);

    // サイドバーの「データセット」をクリック
    await page.getByRole('link', { name: 'データセット' }).click();

    // データセット一覧ページに移動したことを確認
    await expect(page).toHaveURL('/datasets');

    // 作成したデータセットが一覧に表示されることを確認
    await expect(page.getByText(datasetName)).toBeVisible();

    // データセット行をクリックして詳細ページに移動
    await page.getByText(datasetName).click();

    // 詳細ページに遷移することを確認
    await expect(page).toHaveURL(/\/datasets\/ds_[a-zA-Z0-9]+/);

    // 削除ボタンをクリック
    await page.getByRole('button', { name: '削除' }).click();

    // 確認ダイアログが表示されることを確認
    await expect(page.getByRole('alertdialog')).toBeVisible();
    await expect(page.getByText(/本当に削除しますか/)).toBeVisible();

    // 確認ダイアログの「削除」ボタンをクリック
    await page.getByRole('button', { name: '削除' }).last().click();

    // データセット一覧ページにリダイレクトされることを確認
    await expect(page).toHaveURL('/datasets');

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
    const { createDataset } = await import('./helpers/api-helper');
    const datasetName = `E2E Test Dataset Preview ${Date.now()}`;
    const datasetId = await createDataset(token, datasetName, csvContent);
    cleanup.datasetIds.push(datasetId);

    // データセット詳細ページに直接移動
    await page.goto(`/datasets/${datasetId}`);

    // データセット名が表示されることを確認
    await expect(page.getByRole('heading', { name: datasetName })).toBeVisible();

    // プレビューセクションが表示されることを確認
    await expect(page.getByText(/プレビュー|Preview/)).toBeVisible();

    // データのプレビューが表示されることを確認
    await expect(page.getByText('Widget A')).toBeVisible();
    await expect(page.getByText('Widget B')).toBeVisible();
    await expect(page.getByText('1000')).toBeVisible();
    await expect(page.getByText('1500')).toBeVisible();
  });
});
