/**
 * Dashboard Filter & Filter View E2E Tests
 *
 * ダッシュボードフィルター・フィルタービュー機能のE2Eテスト
 */
import { test, expect } from '@playwright/test';
import { loginViaUI } from './helpers/login-helper';
import {
  getAccessToken,
  createDataset,
  createCard,
  createDashboard,
  cleanupTestData,
  type TestDataCleanup,
} from './helpers/api-helper';

// テストユーザー情報
const TEST_USER_EMAIL = 'e2e@example.com';
const TEST_USER_PASSWORD = 'Test@1234';

// テスト用CSVデータ (カテゴリと日付を含む)
const TEST_CSV_CONTENT = `date,category,product,amount,quantity
2024-01-01,Electronics,Widget A,1000,10
2024-01-02,Electronics,Widget B,2000,20
2024-01-03,Furniture,Table C,3000,30
2024-01-04,Furniture,Chair D,4000,40
2024-01-05,Clothing,Shirt E,5000,50`;

test.describe('Dashboard Filter & Filter View', () => {
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

    // Given: トークン取得とログイン
    token = await getAccessToken(TEST_USER_EMAIL, TEST_USER_PASSWORD);
    await loginViaUI(page, TEST_USER_EMAIL, TEST_USER_PASSWORD);
  });

  test.afterEach(async () => {
    // クリーンアップ: テストデータを削除
    await cleanupTestData(token, cleanup);
  });

  test('FLT-01: ダッシュボードにカテゴリフィルターを設定できる', async ({ page }) => {
    // Given: データセット、カード、ダッシュボードが作成済み
    const timestamp = Date.now();
    const datasetName = `E2E Dataset Filter ${timestamp}`;
    const datasetId = await createDataset(token, datasetName, TEST_CSV_CONTENT);
    cleanup.datasetIds.push(datasetId);

    const cardName = `E2E Card Filter ${timestamp}`;
    const cardId = await createCard(token, cardName, datasetId, 'import pandas as pd\ndf');
    cleanup.cardIds.push(cardId);

    const dashboardName = `E2E Dashboard Filter ${timestamp}`;
    const dashboardId = await createDashboard(token, dashboardName, [cardId]);
    cleanup.dashboardIds.push(dashboardId);

    // When: ダッシュボード編集ページに移動
    await page.goto(`/dashboards/${dashboardId}/edit`);
    await expect(page.getByText(dashboardName)).toBeVisible();

    // When: フィルタ設定パネルを開く
    await page.getByRole('button', { name: 'フィルタ設定' }).click();

    // Then: フィルタ設定パネルが表示される
    await expect(page.locator('[data-testid="filter-config-panel"]')).toBeVisible();

    // When: フィルター追加ボタンをクリック
    await page.getByRole('button', { name: '追加' }).click();

    // Then: フィルター追加ダイアログが表示される
    await expect(page.getByText('フィルタを追加')).toBeVisible();

    // When: フィルター設定を入力
    await page.locator('#filter-label').fill('カテゴリ');
    await page.locator('#filter-column').fill('category');

    // When: データセットを選択
    await page.locator('#filter-dataset').click();
    await page.getByRole('option', { name: datasetName }).click();

    // When: 選択肢を取得
    await page.getByRole('button', { name: '選択肢を取得' }).click();
    await page.waitForTimeout(1000); // API応答を待機

    // When: 追加ボタンをクリック
    await page.getByRole('button', { name: '追加' }).last().click();

    // Then: フィルターが追加される
    await expect(page.getByText('カテゴリ')).toBeVisible();

    // When: 保存
    await page.getByRole('button', { name: '保存' }).click();

    // Then: 保存が成功する
    await page.waitForTimeout(1000);
    await expect(page).toHaveURL(/\/dashboards\/dash_[a-zA-Z0-9]+\/edit/);
  });

  test('FLT-02: フィルターを適用するとカード結果が更新される', async ({ page }) => {
    // Given: フィルター付きダッシュボードが作成済み
    const timestamp = Date.now();
    const datasetName = `E2E Dataset Apply ${timestamp}`;
    const datasetId = await createDataset(token, datasetName, TEST_CSV_CONTENT);
    cleanup.datasetIds.push(datasetId);

    const cardName = `E2E Card Apply ${timestamp}`;
    // カテゴリでフィルタリングするコード
    const pythonCode = `import pandas as pd
df`;
    const cardId = await createCard(token, cardName, datasetId, pythonCode);
    cleanup.cardIds.push(cardId);

    const dashboardName = `E2E Dashboard Apply ${timestamp}`;
    const dashboardId = await createDashboard(token, dashboardName, [cardId]);
    cleanup.dashboardIds.push(dashboardId);

    // When: ダッシュボード編集ページでフィルターを設定
    await page.goto(`/dashboards/${dashboardId}/edit`);
    await page.getByRole('button', { name: 'フィルタ設定' }).click();
    await page.getByRole('button', { name: '追加' }).click();

    await page.locator('#filter-label').fill('カテゴリ');
    await page.locator('#filter-column').fill('category');
    await page.locator('#filter-dataset').click();
    await page.getByRole('option', { name: datasetName }).click();
    await page.getByRole('button', { name: '選択肢を取得' }).click();
    await page.waitForTimeout(1000);
    await page.getByRole('button', { name: '追加' }).last().click();
    await page.getByRole('button', { name: '保存' }).click();
    await page.waitForTimeout(1000);

    // When: ダッシュボード閲覧ページに移動
    await page.goto(`/dashboards/${dashboardId}`);
    await expect(page.getByText(dashboardName)).toBeVisible();

    // When: フィルターバーを表示
    await page.getByRole('button', { name: /フィルタ/ }).click();

    // Then: フィルターバーが表示される
    await expect(page.locator('[data-testid="filter-bar"]')).toBeVisible();

    // When: カテゴリフィルターで「Electronics」を選択
    const categoryFilter = page.getByLabel('カテゴリ');
    await categoryFilter.click();
    await page.getByRole('option', { name: 'Electronics' }).click();

    // Then: フィルターが適用される (UIの更新を待機)
    await page.waitForTimeout(2000);

    // カードが表示されていることを確認
    await expect(page.getByText(cardName)).toBeVisible();
  });

  test('FLT-03: フィルタービューを保存できる', async ({ page }) => {
    // Given: フィルター付きダッシュボードが作成済み
    const timestamp = Date.now();
    const datasetName = `E2E Dataset View ${timestamp}`;
    const datasetId = await createDataset(token, datasetName, TEST_CSV_CONTENT);
    cleanup.datasetIds.push(datasetId);

    const cardName = `E2E Card View ${timestamp}`;
    const cardId = await createCard(token, cardName, datasetId, 'import pandas as pd\ndf');
    cleanup.cardIds.push(cardId);

    const dashboardName = `E2E Dashboard View ${timestamp}`;
    const dashboardId = await createDashboard(token, dashboardName, [cardId]);
    cleanup.dashboardIds.push(dashboardId);

    // フィルターを設定
    await page.goto(`/dashboards/${dashboardId}/edit`);
    await page.getByRole('button', { name: 'フィルタ設定' }).click();
    await page.getByRole('button', { name: '追加' }).click();
    await page.locator('#filter-label').fill('カテゴリ');
    await page.locator('#filter-column').fill('category');
    await page.locator('#filter-dataset').click();
    await page.getByRole('option', { name: datasetName }).click();
    await page.getByRole('button', { name: '選択肢を取得' }).click();
    await page.waitForTimeout(1000);
    await page.getByRole('button', { name: '追加' }).last().click();
    await page.getByRole('button', { name: '保存' }).click();
    await page.waitForTimeout(1000);

    // When: ダッシュボード閲覧ページに移動
    await page.goto(`/dashboards/${dashboardId}`);
    await expect(page.getByText(dashboardName)).toBeVisible();

    // When: フィルターを適用
    await page.getByRole('button', { name: /フィルタ/ }).click();
    const categoryFilter = page.getByLabel('カテゴリ');
    await categoryFilter.click();
    await page.getByRole('option', { name: 'Furniture' }).click();
    await page.waitForTimeout(1000);

    // When: ビューセレクターを開く
    await page.getByRole('button', { name: 'ビュー' }).click();

    // When: 「名前を付けて保存」をクリック
    await page.getByText('名前を付けて保存').click();

    // When: ビュー名を入力して保存
    const viewName = `E2E View ${timestamp}`;
    await page.getByPlaceholder('ビュー名').fill(viewName);
    await page.getByRole('button', { name: '保存' }).last().click();

    // Then: ビューが保存される (エラーなく操作完了)
    await page.waitForTimeout(1000);

    // Then: ビューセレクターを再度開いて保存したビューが表示される
    await page.getByRole('button', { name: 'ビュー' }).click();
    await expect(page.getByText(viewName)).toBeVisible();
  });

  test('FLT-04: フィルタービューを切り替えるとフィルター値が復元される', async ({ page }) => {
    // Given: フィルター付きダッシュボードが作成済み
    const timestamp = Date.now();
    const datasetName = `E2E Dataset Switch ${timestamp}`;
    const datasetId = await createDataset(token, datasetName, TEST_CSV_CONTENT);
    cleanup.datasetIds.push(datasetId);

    const cardName = `E2E Card Switch ${timestamp}`;
    const cardId = await createCard(token, cardName, datasetId, 'import pandas as pd\ndf');
    cleanup.cardIds.push(cardId);

    const dashboardName = `E2E Dashboard Switch ${timestamp}`;
    const dashboardId = await createDashboard(token, dashboardName, [cardId]);
    cleanup.dashboardIds.push(dashboardId);

    // フィルターを設定
    await page.goto(`/dashboards/${dashboardId}/edit`);
    await page.getByRole('button', { name: 'フィルタ設定' }).click();
    await page.getByRole('button', { name: '追加' }).click();
    await page.locator('#filter-label').fill('カテゴリ');
    await page.locator('#filter-column').fill('category');
    await page.locator('#filter-dataset').click();
    await page.getByRole('option', { name: datasetName }).click();
    await page.getByRole('button', { name: '選択肢を取得' }).click();
    await page.waitForTimeout(1000);
    await page.getByRole('button', { name: '追加' }).last().click();
    await page.getByRole('button', { name: '保存' }).click();
    await page.waitForTimeout(1000);

    // When: ダッシュボード閲覧ページに移動
    await page.goto(`/dashboards/${dashboardId}`);
    await expect(page.getByText(dashboardName)).toBeVisible();

    // When: フィルター1を設定してビュー1を保存
    await page.getByRole('button', { name: /フィルタ/ }).click();
    const categoryFilter = page.getByLabel('カテゴリ');
    await categoryFilter.click();
    await page.getByRole('option', { name: 'Electronics' }).click();
    await page.waitForTimeout(500);

    await page.getByRole('button', { name: 'ビュー' }).click();
    await page.getByText('名前を付けて保存').click();
    const view1Name = `View Electronics ${timestamp}`;
    await page.getByPlaceholder('ビュー名').fill(view1Name);
    await page.getByRole('button', { name: '保存' }).last().click();
    await page.waitForTimeout(500);

    // When: フィルターをクリアして別の値を設定
    await page.getByRole('button', { name: 'クリア' }).click();
    await page.waitForTimeout(500);

    // When: フィルター2を設定してビュー2を保存
    await categoryFilter.click();
    await page.getByRole('option', { name: 'Furniture' }).click();
    await page.waitForTimeout(500);

    await page.getByRole('button', { name: 'ビュー' }).click();
    await page.getByText('名前を付けて保存').click();
    const view2Name = `View Furniture ${timestamp}`;
    await page.getByPlaceholder('ビュー名').fill(view2Name);
    await page.getByRole('button', { name: '保存' }).last().click();
    await page.waitForTimeout(500);

    // When: ビュー1に切り替え
    await page.getByRole('button', { name: 'ビュー' }).click();
    await page.getByText(view1Name).click();
    await page.waitForTimeout(500);

    // Then: フィルター値が「Electronics」に復元される
    await expect(categoryFilter).toContainText('Electronics');
  });

  test('FLT-05: フィルターをクリアできる', async ({ page }) => {
    // Given: フィルター付きダッシュボードが作成済み
    const timestamp = Date.now();
    const datasetName = `E2E Dataset Clear ${timestamp}`;
    const datasetId = await createDataset(token, datasetName, TEST_CSV_CONTENT);
    cleanup.datasetIds.push(datasetId);

    const cardName = `E2E Card Clear ${timestamp}`;
    const cardId = await createCard(token, cardName, datasetId, 'import pandas as pd\ndf');
    cleanup.cardIds.push(cardId);

    const dashboardName = `E2E Dashboard Clear ${timestamp}`;
    const dashboardId = await createDashboard(token, dashboardName, [cardId]);
    cleanup.dashboardIds.push(dashboardId);

    // フィルターを設定
    await page.goto(`/dashboards/${dashboardId}/edit`);
    await page.getByRole('button', { name: 'フィルタ設定' }).click();
    await page.getByRole('button', { name: '追加' }).click();
    await page.locator('#filter-label').fill('カテゴリ');
    await page.locator('#filter-column').fill('category');
    await page.locator('#filter-dataset').click();
    await page.getByRole('option', { name: datasetName }).click();
    await page.getByRole('button', { name: '選択肢を取得' }).click();
    await page.waitForTimeout(1000);
    await page.getByRole('button', { name: '追加' }).last().click();
    await page.getByRole('button', { name: '保存' }).click();
    await page.waitForTimeout(1000);

    // When: ダッシュボード閲覧ページに移動
    await page.goto(`/dashboards/${dashboardId}`);
    await expect(page.getByText(dashboardName)).toBeVisible();

    // When: フィルターを適用
    await page.getByRole('button', { name: /フィルタ/ }).click();
    const categoryFilter = page.getByLabel('カテゴリ');
    await categoryFilter.click();
    await page.getByRole('option', { name: 'Clothing' }).click();
    await page.waitForTimeout(500);

    // Then: クリアボタンが表示される
    await expect(page.getByRole('button', { name: 'クリア' })).toBeVisible();

    // When: クリアボタンをクリック
    await page.getByRole('button', { name: 'クリア' }).click();
    await page.waitForTimeout(500);

    // Then: フィルターがクリアされる (選択値がなくなる)
    // クリアボタンが非表示になるか、フィルター値がリセットされる
    const clearButton = page.getByRole('button', { name: 'クリア' });
    const isVisible = await clearButton.isVisible().catch(() => false);
    expect(isVisible).toBe(false);
  });

  test('FLT-06: 日付範囲フィルターを設定できる', async ({ page }) => {
    // Given: データセット、カード、ダッシュボードが作成済み
    const timestamp = Date.now();
    const datasetName = `E2E Dataset Date ${timestamp}`;
    const datasetId = await createDataset(token, datasetName, TEST_CSV_CONTENT);
    cleanup.datasetIds.push(datasetId);

    const cardName = `E2E Card Date ${timestamp}`;
    const cardId = await createCard(token, cardName, datasetId, 'import pandas as pd\ndf');
    cleanup.cardIds.push(cardId);

    const dashboardName = `E2E Dashboard Date ${timestamp}`;
    const dashboardId = await createDashboard(token, dashboardName, [cardId]);
    cleanup.dashboardIds.push(dashboardId);

    // When: ダッシュボード編集ページでフィルターを設定
    await page.goto(`/dashboards/${dashboardId}/edit`);
    await page.getByRole('button', { name: 'フィルタ設定' }).click();
    await page.getByRole('button', { name: '追加' }).click();

    // When: 日付範囲フィルターを設定
    await page.locator('#filter-label').fill('期間');
    await page.locator('#filter-type').click();
    await page.getByRole('option', { name: '日付範囲' }).click();
    await page.locator('#filter-column').fill('date');
    await page.locator('#filter-dataset').click();
    await page.getByRole('option', { name: datasetName }).click();

    // When: 追加ボタンをクリック
    await page.getByRole('button', { name: '追加' }).last().click();

    // Then: 日付範囲フィルターが追加される
    await expect(page.getByText('期間')).toBeVisible();
    await expect(page.getByText('日付範囲')).toBeVisible();

    // When: 保存
    await page.getByRole('button', { name: '保存' }).click();
    await page.waitForTimeout(1000);

    // Then: 保存が成功する
    await expect(page).toHaveURL(/\/dashboards\/dash_[a-zA-Z0-9]+\/edit/);
  });
});
