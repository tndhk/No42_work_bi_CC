/**
 * DashboardEditPage Page Object
 *
 * ダッシュボード編集ページのPage Object
 */
import { type Page, type Locator, expect } from '@playwright/test';

export class DashboardEditPage {
  readonly page: Page;
  readonly saveButton: Locator;
  readonly addCardButton: Locator;
  readonly shareButton: Locator;
  readonly deleteButton: Locator;
  readonly cardSelectDialog: Locator;
  readonly cardAddButton: Locator;
  readonly dashboardTitle: Locator;
  readonly filterButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.saveButton = page.getByRole('button', { name: '保存' });
    this.addCardButton = page.getByRole('button', { name: 'カードを追加' });
    this.shareButton = page.getByRole('button', { name: '共有' });
    this.deleteButton = page.getByRole('button', { name: '削除' });
    this.cardSelectDialog = page.getByRole('dialog');
    this.cardAddButton = page.getByRole('button', { name: '追加' }).last();
    this.dashboardTitle = page.getByRole('heading').first();
    this.filterButton = page.getByRole('button', { name: 'フィルター' });
  }

  async goto(dashboardId: string) {
    await this.page.goto(`/dashboards/${dashboardId}/edit`);
  }

  async save() {
    await this.saveButton.click();
  }

  async clickAddCard() {
    await this.addCardButton.click();
    await expect(this.cardSelectDialog).toBeVisible();
  }

  async selectCard(cardName: string) {
    await this.page.getByText(cardName).click();
    await this.cardAddButton.click();
  }

  async addCard(cardName: string) {
    await this.clickAddCard();
    await this.selectCard(cardName);
  }

  async clickShare() {
    await this.shareButton.click();
  }

  async delete() {
    await this.deleteButton.click();
  }

  async confirmDelete() {
    await this.page.getByRole('button', { name: '削除' }).last().click();
  }

  async expectCardVisible(cardName: string) {
    await expect(this.page.getByText(cardName)).toBeVisible();
  }

  async expectToBeOnEditPage(dashboardId?: string) {
    if (dashboardId) {
      await expect(this.page).toHaveURL(`/dashboards/${dashboardId}/edit`);
    } else {
      await expect(this.page).toHaveURL(/\/dashboards\/dash_[a-zA-Z0-9]+\/edit/);
    }
  }

  getDashboardIdFromUrl(): string | null {
    const url = this.page.url();
    const match = url.match(/\/dashboards\/(dash_[a-zA-Z0-9]+)/);
    return match ? match[1] : null;
  }
}
