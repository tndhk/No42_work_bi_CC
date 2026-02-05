/**
 * Card + Dashboard E2E Tests
 */
import { test, expect } from '@playwright/test';
import { loginViaUI } from './helpers/login-helper';
import {
  getAccessToken,
  createDataset,
  createCard,
  cleanupTestData,
  type TestDataCleanup,
} from './helpers/api-helper';

// テストユーザ情報
const TEST_USER_EMAIL = 'e2e@example.com';
const TEST_USER_PASSWORD = 'Test@1234';

test.describe('Card + Dashboard', () => {
  let cleanup: TestDataCleanup;
  let token: string;

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

    // トークン取得
    token = await getAccessToken(TEST_USER_EMAIL, TEST_USER_PASSWORD);

    // ログイン
    await loginViaUI(page, TEST_USER_EMAIL, TEST_USER_PASSWORD);
  });

  test.afterEach(async () => {
    // テストデータをクリーンアップ
    if (cleanup.datasetIds.length > 0 || cleanup.cardIds.length > 0 || cleanup.dashboardIds.length > 0) {
      await cleanupTestData(token, cleanup);
    }
  });

  test('Card作成', async ({ page }) => {
    // 事前にデータセットを作成
    const csvContent = 'date,product,amount,quantity\n2024-01-01,Widget A,1000,10\n';
    const datasetName = `E2E Dataset for Card ${Date.now()}`;
    const datasetId = await createDataset(token, datasetName, csvContent);
    cleanup.datasetIds.push(datasetId);

    // サイドバーの「カード」をクリック
    await page.getByRole('link', { name: 'カード' }).click();

    // カード一覧ページに移動したことを確認
    await expect(page).toHaveURL('/cards');

    // 「新規作成」ボタンをクリック
    await page.getByRole('button', { name: '新規作成' }).click();

    // カード作成ページに遷移することを確認
    await expect(page).toHaveURL('/cards/new');

    // カード名を入力
    const cardName = `E2E Test Card ${Date.now()}`;
    await page.getByLabel('カード名').fill(cardName);

    // 説明を入力
    await page.getByLabel('説明').fill('E2E test card');

    // データセットを選択
    await page.getByLabel('データセット').click();
    await page.getByRole('option', { name: datasetName }).click();

    // Pythonコードを入力 (Monaco Editorに直接設定)
    const pythonCode = 'import pandas as pd\n\ndf.head()';
    await page.evaluate((code) => {
      // Monaco Editorのモデル値を直接設定
      const editor = (window as any).monacoEditor;
      if (editor) {
        editor.setValue(code);
      }
    }, pythonCode);

    // 「保存」ボタンをクリック
    await page.getByRole('button', { name: '保存' }).click();

    // カード詳細ページに遷移することを確認
    await expect(page).toHaveURL(/\/cards\/card_[a-zA-Z0-9]+/);

    // カード名が表示されることを確認
    await expect(page.getByRole('heading', { name: cardName })).toBeVisible();

    // カードIDを取得してクリーンアップ用に保存
    const url = page.url();
    const match = url.match(/\/cards\/(card_[a-zA-Z0-9]+)/);
    if (match) {
      cleanup.cardIds.push(match[1]);
    }

    // カード一覧に戻る
    await page.getByRole('link', { name: 'カード' }).click();

    // 作成したカードが一覧に表示されることを確認
    await expect(page.getByText(cardName)).toBeVisible();
  });

  test('Dashboard作成・閲覧', async ({ page }) => {
    // 事前にデータセットとカードを作成
    const csvContent = 'date,product,amount,quantity\n2024-01-01,Widget A,1000,10\n';
    const datasetName = `E2E Dataset for Dashboard ${Date.now()}`;
    const datasetId = await createDataset(token, datasetName, csvContent);
    cleanup.datasetIds.push(datasetId);

    const cardName = `E2E Card for Dashboard ${Date.now()}`;
    const cardId = await createCard(token, cardName, datasetId, 'import pandas as pd\ndf');
    cleanup.cardIds.push(cardId);

    // サイドバーの「ダッシュボード」をクリック
    await page.getByRole('link', { name: 'ダッシュボード' }).click();

    // ダッシュボード一覧ページに移動したことを確認
    await expect(page).toHaveURL('/dashboards');

    // 「新規作成」ボタンをクリック
    await page.getByRole('button', { name: '新規作成' }).click();

    // ダッシュボード作成ダイアログが表示されることを確認
    await expect(page.getByRole('dialog')).toBeVisible();

    // ダッシュボード名を入力
    const dashboardName = `E2E Test Dashboard ${Date.now()}`;
    await page.getByLabel('ダッシュボード名').fill(dashboardName);

    // 説明を入力
    await page.getByLabel('説明').fill('E2E test dashboard');

    // 「作成」ボタンをクリック
    await page.getByRole('button', { name: '作成' }).last().click();

    // ダッシュボード編集ページに遷移することを確認
    await expect(page).toHaveURL(/\/dashboards\/dash_[a-zA-Z0-9]+\/edit/);

    // ダッシュボードIDを取得してクリーンアップ用に保存
    let dashboardId: string | undefined;
    const editUrl = page.url();
    const editMatch = editUrl.match(/\/dashboards\/(dash_[a-zA-Z0-9]+)\/edit/);
    if (editMatch) {
      dashboardId = editMatch[1];
      cleanup.dashboardIds.push(dashboardId);
    }

    // カード追加ボタンをクリック
    await page.getByRole('button', { name: 'カードを追加' }).click();

    // カード選択ダイアログが表示されることを確認
    await expect(page.getByRole('dialog')).toBeVisible();

    // 作成したカードを選択
    await page.getByText(cardName).click();

    // 「追加」ボタンをクリック
    await page.getByRole('button', { name: '追加' }).last().click();

    // カードが追加されたことを確認
    await expect(page.getByText(cardName)).toBeVisible();

    // 「保存」ボタンをクリック
    await page.getByRole('button', { name: '保存' }).click();

    // 保存成功メッセージまたは閲覧ページへの遷移を確認
    // 閲覧ページに遷移する場合
    if (dashboardId) {
      await page.goto(`/dashboards/${dashboardId}`);
    }

    // ダッシュボード名が表示されることを確認
    await expect(page.getByRole('heading', { name: dashboardName })).toBeVisible();

    // カードが表示されることを確認
    await expect(page.getByText(cardName)).toBeVisible();
  });

  test('Dashboard一覧からの閲覧', async ({ page }) => {
    // 事前にデータセット、カード、ダッシュボードを作成
    const csvContent = 'date,product,amount,quantity\n2024-01-01,Widget A,1000,10\n';
    const datasetName = `E2E Dataset ${Date.now()}`;
    const datasetId = await createDataset(token, datasetName, csvContent);
    cleanup.datasetIds.push(datasetId);

    const cardName = `E2E Card ${Date.now()}`;
    const cardId = await createCard(token, cardName, datasetId, 'import pandas as pd\ndf');
    cleanup.cardIds.push(cardId);

    const { createDashboard } = await import('./helpers/api-helper');
    const dashboardName = `E2E Dashboard ${Date.now()}`;
    const dashboardId = await createDashboard(token, dashboardName, [cardId]);
    cleanup.dashboardIds.push(dashboardId);

    // サイドバーの「ダッシュボード」をクリック
    await page.getByRole('link', { name: 'ダッシュボード' }).click();

    // ダッシュボード一覧ページに移動したことを確認
    await expect(page).toHaveURL('/dashboards');

    // 作成したダッシュボードが一覧に表示されることを確認
    await expect(page.getByText(dashboardName)).toBeVisible();

    // ダッシュボードをクリック
    await page.getByText(dashboardName).click();

    // ダッシュボード閲覧ページに遷移することを確認
    await expect(page).toHaveURL(/\/dashboards\/dash_[a-zA-Z0-9]+/);

    // ダッシュボード名が表示されることを確認
    await expect(page.getByRole('heading', { name: dashboardName })).toBeVisible();

    // カードが表示されることを確認
    await expect(page.getByText(cardName)).toBeVisible();
  });

  test('Card削除', async ({ page }) => {
    // 事前にデータセットとカードを作成
    const csvContent = 'date,product,amount,quantity\n2024-01-01,Widget A,1000,10\n';
    const datasetName = `E2E Dataset for Card Delete ${Date.now()}`;
    const datasetId = await createDataset(token, datasetName, csvContent);
    cleanup.datasetIds.push(datasetId);

    const cardName = `E2E Card for Delete ${Date.now()}`;
    const cardId = await createCard(token, cardName, datasetId);
    cleanup.cardIds.push(cardId);

    // サイドバーの「カード」をクリック
    await page.getByRole('link', { name: 'カード' }).click();

    // カード一覧に表示されることを確認
    await expect(page.getByText(cardName)).toBeVisible();

    // カードをクリックして詳細ページに移動
    await page.getByText(cardName).click();

    // 詳細ページに遷移することを確認
    await expect(page).toHaveURL(/\/cards\/card_[a-zA-Z0-9]+/);

    // 削除ボタンをクリック
    await page.getByRole('button', { name: '削除' }).click();

    // 確認ダイアログが表示されることを確認
    await expect(page.getByRole('alertdialog')).toBeVisible();

    // 確認ダイアログの「削除」ボタンをクリック
    await page.getByRole('button', { name: '削除' }).last().click();

    // カード一覧ページにリダイレクトされることを確認
    await expect(page).toHaveURL('/cards');

    // 削除したカードが一覧に表示されないことを確認
    await expect(page.getByText(cardName)).not.toBeVisible();

    // クリーンアップリストから削除 (既に削除済み)
    cleanup.cardIds = cleanup.cardIds.filter(id => id !== cardId);
  });
});
