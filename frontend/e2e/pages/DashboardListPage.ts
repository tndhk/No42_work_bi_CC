/**
 * DashboardListPage Page Object
 *
 * ダッシュボード一覧ページのPage Object
 */
import { type Page, type Locator, expect } from '@playwright/test';

export class DashboardListPage {
  readonly page: Page;
  readonly createButton: Locator;
  readonly dashboardItems: Locator;
  readonly searchInput: Locator;
  readonly pageTitle: Locator;
  readonly createDialog: Locator;
  readonly dialogNameInput: Locator;
  readonly dialogDescriptionInput: Locator;
  readonly dialogCreateButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.createButton = page.getByRole('button', { name: '新規作成' });
    this.dashboardItems = page
      .locator('[data-testid="dashboard-item"]')
      .or(page.locator('.dashboard-item'));
    this.searchInput = page.getByPlaceholder('検索');
    this.pageTitle = page.getByRole('heading', { name: 'ダッシュボード' });
    this.createDialog = page.getByRole('dialog');
    this.dialogNameInput = page.getByLabel('ダッシュボード名');
    this.dialogDescriptionInput = page.getByLabel('説明');
    this.dialogCreateButton = page.getByRole('button', { name: '作成' }).last();
  }

  async goto() {
    await this.page.goto('/dashboards');
  }

  async clickCreate() {
    await this.createButton.click();
    await expect(this.createDialog).toBeVisible();
  }

  async createDashboard(name: string, description?: string) {
    await this.clickCreate();
    await this.dialogNameInput.fill(name);
    if (description) {
      await this.dialogDescriptionInput.fill(description);
    }
    await this.dialogCreateButton.click();
  }

  async clickDashboard(dashboardName: string) {
    await this.page.getByText(dashboardName).click();
  }

  async expectDashboardVisible(dashboardName: string) {
    await expect(this.page.getByText(dashboardName)).toBeVisible();
  }

  async expectDashboardNotVisible(dashboardName: string) {
    await expect(this.page.getByText(dashboardName)).not.toBeVisible();
  }

  async search(query: string) {
    await this.searchInput.fill(query);
    await this.page.keyboard.press('Enter');
  }

  async expectToBeOnDashboardListPage() {
    await expect(this.page).toHaveURL('/dashboards');
    await expect(this.pageTitle).toBeVisible();
  }
}
