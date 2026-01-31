/**
 * Authentication E2E Tests
 */
import { test, expect } from '@playwright/test';

// テストユーザ情報 (scripts/seed_test_user.py で作成)
const TEST_USER_EMAIL = 'e2e@example.com';
const TEST_USER_PASSWORD = 'Test@1234';

test.describe('Authentication', () => {
  test('未認証の場合、ログインページにリダイレクトされる', async ({ page }) => {
    // ダッシュボードページに直接アクセス
    await page.goto('/dashboards');

    // ログインページにリダイレクトされることを確認
    await expect(page).toHaveURL('/login');
  });

  test('バリデーション: 空のフォームを送信するとエラーが表示される', async ({ page }) => {
    // ログインページに移動
    await page.goto('/login');

    // 何も入力せずにログインボタンをクリック
    await page.getByRole('button', { name: 'ログイン' }).click();

    // バリデーションエラーが表示されることを確認
    // HTML5のrequired属性によるブラウザのバリデーションメッセージ、
    // またはカスタムバリデーションメッセージが表示される
    const emailInput = page.getByLabel('メールアドレス');

    // HTML5バリデーションが働いているか、またはページに留まっていることを確認
    await expect(page).toHaveURL('/login');

    // メールアドレス入力欄がフォーカスされている、またはinvalid状態であることを確認
    await expect(emailInput).toBeFocused();
  });

  test('認証失敗: 不正な資格情報でログインするとエラーが表示される', async ({ page }) => {
    // ログインページに移動
    await page.goto('/login');

    // 不正な資格情報を入力
    await page.getByLabel('メールアドレス').fill('wrong@example.com');
    await page.getByLabel('パスワード').fill('wrongpassword');

    // ログインボタンをクリック
    await page.getByRole('button', { name: 'ログイン' }).click();

    // エラーメッセージが表示されることを確認
    await expect(page.getByText(/メールアドレスまたはパスワードが正しくありません/)).toBeVisible();

    // ログインページに留まっていることを確認
    await expect(page).toHaveURL('/login');
  });

  test('正しい資格情報でログイン→ログアウトができる', async ({ page }) => {
    // ログインページに移動
    await page.goto('/login');

    // 正しい資格情報を入力
    await page.getByLabel('メールアドレス').fill(TEST_USER_EMAIL);
    await page.getByLabel('パスワード').fill(TEST_USER_PASSWORD);

    // ログインボタンをクリック
    await page.getByRole('button', { name: 'ログイン' }).click();

    // ダッシュボードページにリダイレクトされることを確認
    await expect(page).toHaveURL('/dashboards');

    // ヘッダーにユーザーのメールアドレスが表示されていることを確認
    await expect(page.getByText(TEST_USER_EMAIL)).toBeVisible();

    // ユーザーメニューを開く (メールアドレスが表示されているボタンをクリック)
    await page.getByRole('button', { name: TEST_USER_EMAIL }).click();

    // ログアウトメニュー項目をクリック
    await page.getByRole('menuitem', { name: 'ログアウト' }).click();

    // ログインページにリダイレクトされることを確認
    await expect(page).toHaveURL('/login');

    // 再度ダッシュボードにアクセスしようとすると、ログインページにリダイレクトされる
    await page.goto('/dashboards');
    await expect(page).toHaveURL('/login');
  });

  test('ログイン状態でログインページにアクセスするとダッシュボードにリダイレクトされる', async ({ page }) => {
    // ログインページに移動
    await page.goto('/login');

    // 正しい資格情報を入力してログイン
    await page.getByLabel('メールアドレス').fill(TEST_USER_EMAIL);
    await page.getByLabel('パスワード').fill(TEST_USER_PASSWORD);
    await page.getByRole('button', { name: 'ログイン' }).click();

    // ダッシュボードページに到達することを確認
    await expect(page).toHaveURL('/dashboards');

    // ログイン済みの状態でログインページにアクセス
    await page.goto('/login');

    // ダッシュボードにリダイレクトされることを確認
    await expect(page).toHaveURL('/dashboards');
  });
});
