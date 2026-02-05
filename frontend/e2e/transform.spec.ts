/**
 * Transform Management E2E Tests
 *
 * トランスフォーム管理機能のE2Eテスト
 */
import { test, expect } from '@playwright/test';
import { loginViaUI } from './helpers/login-helper';
import {
  getAccessToken,
  createDataset,
  createTransform,
  deleteTransform,
  cleanupTestData,
  type TestDataCleanup,
} from './helpers/api-helper';

// テストユーザー情報
const TEST_USER_EMAIL = 'e2e@example.com';
const TEST_USER_PASSWORD = 'Test@1234';

// テスト用CSVデータ
const TEST_CSV_CONTENT = `date,product,amount,quantity
2024-01-01,Widget A,1000,10
2024-01-02,Widget B,2000,20
2024-01-03,Widget C,3000,30`;

test.describe('Transform Management', () => {
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
    if (
      cleanup.datasetIds.length > 0 ||
      cleanup.transformIds.length > 0
    ) {
      await cleanupTestData(token, cleanup);
    }
  });

  test('TRF-01: Transform作成が成功し一覧に表示される', async ({ page }) => {
    // Given: データセットが作成済み
    const timestamp = Date.now();
    const datasetName = `E2E Dataset Transform ${timestamp}`;
    const datasetId = await createDataset(token, datasetName, TEST_CSV_CONTENT);
    cleanup.datasetIds.push(datasetId);

    // When: トランスフォーム一覧ページに移動
    await page.getByRole('link', { name: 'トランスフォーム' }).click();
    await expect(page).toHaveURL('/transforms');

    // When: 新規作成ボタンをクリック
    await page.getByRole('button', { name: '新規作成' }).click();
    await expect(page).toHaveURL('/transforms/new');

    // When: Transform情報を入力
    const transformName = `E2E Transform ${timestamp}`;
    await page.getByLabel('Transform名').fill(transformName);

    // When: データセットを選択 (チェックボックス)
    await page.getByText(datasetName).click();

    // When: Pythonコードを入力
    const pythonCode = `import pandas as pd

# df_0 is the first selected dataset
result = df_0.copy()
result`;
    await page.evaluate((code) => {
      const editor = (window as unknown as { monacoEditor?: { setValue: (v: string) => void } })
        .monacoEditor;
      if (editor) {
        editor.setValue(code);
      }
    }, pythonCode);

    // When: 保存
    await page.getByRole('button', { name: '保存' }).click();

    // Then: Transform編集ページに遷移
    await expect(page).toHaveURL(/\/transforms\/transform_[a-zA-Z0-9]+/, { timeout: 10000 });

    // TransformIDを取得してクリーンアップ用に保存
    const url = page.url();
    const match = url.match(/\/transforms\/(transform_[a-zA-Z0-9]+)/);
    if (match) {
      cleanup.transformIds.push(match[1]);
    }

    // When: トランスフォーム一覧に戻る
    await page.getByRole('link', { name: 'トランスフォーム' }).click();
    await expect(page).toHaveURL('/transforms');

    // Then: 作成したTransformが一覧に表示される
    await expect(page.getByText(transformName)).toBeVisible();
  });

  test('TRF-02: Transform実行で出力データセットが作成される', async ({ page }) => {
    // Given: データセットとTransformが作成済み
    const timestamp = Date.now();
    const datasetName = `E2E Dataset Execute ${timestamp}`;
    const datasetId = await createDataset(token, datasetName, TEST_CSV_CONTENT);
    cleanup.datasetIds.push(datasetId);

    const transformName = `E2E Transform Execute ${timestamp}`;
    const pythonCode = `import pandas as pd
result = df_0.copy()
result['new_column'] = result['amount'] * 2
result`;
    const transformId = await createTransform(token, transformName, [datasetId], pythonCode);
    cleanup.transformIds.push(transformId);

    // When: Transform編集ページに移動
    await page.goto(`/transforms/${transformId}`);
    await expect(page.getByText(transformName)).toBeVisible();

    // When: 実行ボタンをクリック
    await page.getByRole('button', { name: '実行' }).click();

    // Then: 実行結果が表示される (行数、実行時間)
    await expect(page.getByText('行数')).toBeVisible({ timeout: 60000 });
    await expect(page.getByText('実行時間')).toBeVisible();

    // Then: 出力データセットへのリンクが表示される
    await expect(page.getByRole('link', { name: '出力データセットを表示' })).toBeVisible({
      timeout: 60000,
    });

    // Then: 実行履歴にsuccess状態が表示される
    await expect(page.getByText('success').first()).toBeVisible();
  });

  test('TRF-03: Transform実行履歴が表示される', async ({ page }) => {
    // Given: データセットとTransformが作成済み
    const timestamp = Date.now();
    const datasetName = `E2E Dataset History ${timestamp}`;
    const datasetId = await createDataset(token, datasetName, TEST_CSV_CONTENT);
    cleanup.datasetIds.push(datasetId);

    const transformName = `E2E Transform History ${timestamp}`;
    const pythonCode = `import pandas as pd
result = df_0.copy()
result`;
    const transformId = await createTransform(token, transformName, [datasetId], pythonCode);
    cleanup.transformIds.push(transformId);

    // When: Transform編集ページに移動
    await page.goto(`/transforms/${transformId}`);
    await expect(page.getByText(transformName)).toBeVisible();

    // When: 実行ボタンをクリック (1回目)
    await page.getByRole('button', { name: '実行' }).click();
    await expect(page.getByText('success').first()).toBeVisible({ timeout: 60000 });

    // When: もう一度実行 (2回目)
    await page.getByRole('button', { name: '実行' }).click();
    await page.waitForTimeout(2000); // 実行完了を待機

    // Then: 実行履歴に複数の実行が表示される
    const successBadges = page.getByText('success');
    await expect(successBadges.first()).toBeVisible({ timeout: 60000 });

    // Then: 実行履歴カードが表示される
    await expect(page.getByText('実行履歴')).toBeVisible();

    // Then: 手動実行のラベルが表示される
    await expect(page.getByText('手動実行').first()).toBeVisible();
  });

  test('TRF-04: Transformスケジュール設定が保存される', async ({ page }) => {
    // Given: データセットとTransformが作成済み
    const timestamp = Date.now();
    const datasetName = `E2E Dataset Schedule ${timestamp}`;
    const datasetId = await createDataset(token, datasetName, TEST_CSV_CONTENT);
    cleanup.datasetIds.push(datasetId);

    const transformName = `E2E Transform Schedule ${timestamp}`;
    const pythonCode = `import pandas as pd
result = df_0.copy()
result`;
    const transformId = await createTransform(token, transformName, [datasetId], pythonCode);
    cleanup.transformIds.push(transformId);

    // When: Transform編集ページに移動
    await page.goto(`/transforms/${transformId}`);
    await expect(page.getByText(transformName)).toBeVisible();

    // When: スケジュールを有効化
    await page.locator('#schedule-enabled').check();

    // When: プリセットボタン「毎日 0:00」をクリック
    await page.getByRole('button', { name: '毎日 0:00' }).click();

    // When: 保存
    await page.getByRole('button', { name: '保存' }).click();

    // Then: 保存が成功する (ページがリロードまたは遷移しない)
    await expect(page).toHaveURL(`/transforms/${transformId}`);

    // When: ページをリロードして設定が保持されていることを確認
    await page.reload();

    // Then: スケジュールチェックボックスがチェックされている
    await expect(page.locator('#schedule-enabled')).toBeChecked();

    // Then: Cron式が設定されている
    const cronInput = page.getByPlaceholder('0 0 * * *');
    await expect(cronInput).toHaveValue('0 0 * * *');
  });

  test('TRF-05: Transform削除が成功し一覧から削除される', async ({ page }) => {
    // Given: データセットとTransformが作成済み
    const timestamp = Date.now();
    const datasetName = `E2E Dataset Delete ${timestamp}`;
    const datasetId = await createDataset(token, datasetName, TEST_CSV_CONTENT);
    cleanup.datasetIds.push(datasetId);

    const transformName = `E2E Transform Delete ${timestamp}`;
    const pythonCode = `import pandas as pd
result = df_0.copy()
result`;
    const transformId = await createTransform(token, transformName, [datasetId], pythonCode);
    // 削除するのでcleanupには追加しない

    // When: Transform編集ページに移動
    await page.goto(`/transforms/${transformId}`);
    await expect(page.getByText(transformName)).toBeVisible();

    // When: 削除ボタンをクリック
    await page.getByRole('button', { name: '削除' }).click();

    // When: 確認ダイアログで削除を確認
    await expect(page.getByRole('alertdialog')).toBeVisible();
    await page.getByRole('button', { name: '削除' }).last().click();

    // Then: トランスフォーム一覧ページにリダイレクトされる
    await expect(page).toHaveURL('/transforms');

    // Then: 削除したTransformが一覧に表示されない
    await expect(page.getByText(transformName)).not.toBeVisible();
  });

  test('TRF-06: 不正なPythonコードでTransform実行がエラーになる', async ({ page }) => {
    // Given: データセットとTransformが作成済み (不正なコード)
    const timestamp = Date.now();
    const datasetName = `E2E Dataset Error ${timestamp}`;
    const datasetId = await createDataset(token, datasetName, TEST_CSV_CONTENT);
    cleanup.datasetIds.push(datasetId);

    const transformName = `E2E Transform Error ${timestamp}`;
    const invalidCode = `import pandas as pd
# Intentional error
undefined_variable`;
    const transformId = await createTransform(token, transformName, [datasetId], invalidCode);
    cleanup.transformIds.push(transformId);

    // When: Transform編集ページに移動
    await page.goto(`/transforms/${transformId}`);
    await expect(page.getByText(transformName)).toBeVisible();

    // When: 実行ボタンをクリック
    await page.getByRole('button', { name: '実行' }).click();

    // Then: エラー状態が表示される
    await expect(page.getByText('failed').first()).toBeVisible({ timeout: 60000 });
  });

  test('TRF-07: Transform新規作成から実行までの完全フロー', async ({ page }) => {
    // Given: データセットが作成済み
    const timestamp = Date.now();
    const datasetName = `E2E Dataset Flow ${timestamp}`;
    const datasetId = await createDataset(token, datasetName, TEST_CSV_CONTENT);
    cleanup.datasetIds.push(datasetId);

    // When: トランスフォーム一覧ページから新規作成
    await page.getByRole('link', { name: 'トランスフォーム' }).click();
    await expect(page).toHaveURL('/transforms');
    await page.getByRole('button', { name: '新規作成' }).click();
    await expect(page).toHaveURL('/transforms/new');

    // When: Transform情報を入力
    const transformName = `E2E Transform Flow ${timestamp}`;
    await page.getByLabel('Transform名').fill(transformName);

    // When: データセットを選択
    await page.getByText(datasetName).click();

    // When: Pythonコードを入力
    const pythonCode = `import pandas as pd

# Calculate sum of amount
result = df_0.groupby('product')['amount'].sum().reset_index()
result`;
    await page.evaluate((code) => {
      const editor = (window as unknown as { monacoEditor?: { setValue: (v: string) => void } })
        .monacoEditor;
      if (editor) {
        editor.setValue(code);
      }
    }, pythonCode);

    // When: 保存
    await page.getByRole('button', { name: '保存' }).click();

    // Then: Transform編集ページに遷移
    await expect(page).toHaveURL(/\/transforms\/transform_[a-zA-Z0-9]+/, { timeout: 10000 });

    // TransformIDを取得
    const url = page.url();
    const match = url.match(/\/transforms\/(transform_[a-zA-Z0-9]+)/);
    if (match) {
      cleanup.transformIds.push(match[1]);
    }

    // When: 実行ボタンをクリック
    await page.getByRole('button', { name: '実行' }).click();

    // Then: 実行結果が表示される
    await expect(page.getByText('行数')).toBeVisible({ timeout: 60000 });
    await expect(page.getByText('success').first()).toBeVisible();

    // Then: 出力データセットへのリンクが表示される
    await expect(page.getByRole('link', { name: '出力データセットを表示' })).toBeVisible();
  });
});
