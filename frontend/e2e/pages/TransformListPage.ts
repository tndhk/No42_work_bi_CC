/**
 * TransformListPage Page Object
 *
 * トランスフォーム一覧ページのPage Object
 */
import { type Page, type Locator, expect } from '@playwright/test';

export class TransformListPage {
  readonly page: Page;
  readonly createButton: Locator;
  readonly transformItems: Locator;
  readonly searchInput: Locator;
  readonly pageTitle: Locator;

  constructor(page: Page) {
    this.page = page;
    this.createButton = page.getByRole('button', { name: '新規作成' });
    this.transformItems = page
      .locator('[data-testid="transform-item"]')
      .or(page.locator('.transform-item'));
    this.searchInput = page.getByPlaceholder('検索');
    this.pageTitle = page.getByRole('heading', { name: 'トランスフォーム' });
  }

  async goto() {
    await this.page.goto('/transforms');
  }

  async clickCreate() {
    await this.createButton.click();
    await expect(this.page).toHaveURL('/transforms/new');
  }

  async clickTransform(transformName: string) {
    await this.page.getByText(transformName).click();
  }

  async expectTransformVisible(transformName: string) {
    await expect(this.page.getByText(transformName)).toBeVisible();
  }

  async expectTransformNotVisible(transformName: string) {
    await expect(this.page.getByText(transformName)).not.toBeVisible();
  }

  async search(query: string) {
    await this.searchInput.fill(query);
    await this.page.keyboard.press('Enter');
  }

  async expectToBeOnTransformListPage() {
    await expect(this.page).toHaveURL('/transforms');
    await expect(this.pageTitle).toBeVisible();
  }
}
