/**
 * CardListPage Page Object
 *
 * カード一覧ページのPage Object
 */
import { type Page, type Locator, expect } from '@playwright/test';

export class CardListPage {
  readonly page: Page;
  readonly createButton: Locator;
  readonly cardItems: Locator;
  readonly searchInput: Locator;
  readonly pageTitle: Locator;

  constructor(page: Page) {
    this.page = page;
    this.createButton = page.getByRole('button', { name: '新規作成' });
    this.cardItems = page.locator('[data-testid="card-item"]').or(page.locator('.card-item'));
    this.searchInput = page.getByPlaceholder('検索');
    this.pageTitle = page.getByRole('heading', { name: 'カード' });
  }

  async goto() {
    await this.page.goto('/cards');
  }

  async clickCreate() {
    await this.createButton.click();
    await expect(this.page).toHaveURL('/cards/new');
  }

  async clickCard(cardName: string) {
    await this.page.getByText(cardName).click();
  }

  async expectCardVisible(cardName: string) {
    await expect(this.page.getByText(cardName)).toBeVisible();
  }

  async expectCardNotVisible(cardName: string) {
    await expect(this.page.getByText(cardName)).not.toBeVisible();
  }

  async search(query: string) {
    await this.searchInput.fill(query);
    await this.page.keyboard.press('Enter');
  }

  async expectToBeOnCardListPage() {
    await expect(this.page).toHaveURL('/cards');
    await expect(this.pageTitle).toBeVisible();
  }
}
