/**
 * E2E Test Login Helper
 * UI経由でログインを実行
 */
import { Page } from '@playwright/test';

/**
 * UI経由でログイン
 * @param page Playwright Page オブジェクト
 * @param email メールアドレス
 * @param password パスワード
 */
export async function loginViaUI(
  page: Page,
  email: string,
  password: string
): Promise<void> {
  // ログインページに移動
  await page.goto('/login');

  // フォームに入力
  await page.getByLabel('メールアドレス').fill(email);
  await page.getByLabel('パスワード').fill(password);

  // ログインボタンをクリック
  await page.getByRole('button', { name: 'ログイン' }).click();

  // /dashboards にリダイレクトされるまで待機
  await page.waitForURL('/dashboards', { timeout: 10000 });
}
