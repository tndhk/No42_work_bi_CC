/**
 * DatasetListPage Page Object
 *
 * データセット一覧ページのPage Object
 */
import { type Page, type Locator, expect } from '@playwright/test';
import * as path from 'path';

export class DatasetListPage {
  readonly page: Page;
  readonly importButton: Locator;
  readonly datasetItems: Locator;
  readonly searchInput: Locator;
  readonly pageTitle: Locator;

  constructor(page: Page) {
    this.page = page;
    this.importButton = page.getByRole('button', { name: 'インポート' });
    this.datasetItems = page
      .locator('[data-testid="dataset-item"]')
      .or(page.locator('.dataset-item'));
    this.searchInput = page.getByPlaceholder('検索');
    this.pageTitle = page.getByRole('heading', { name: 'データセット' });
  }

  async goto() {
    await this.page.goto('/datasets');
  }

  async gotoImport() {
    await this.page.goto('/datasets/import');
  }

  async clickImport() {
    await this.importButton.click();
    await expect(this.page).toHaveURL('/datasets/import');
  }

  async clickDataset(datasetName: string) {
    await this.page.getByText(datasetName).click();
  }

  async expectDatasetVisible(datasetName: string) {
    await expect(this.page.getByText(datasetName)).toBeVisible();
  }

  async expectDatasetNotVisible(datasetName: string) {
    await expect(this.page.getByText(datasetName)).not.toBeVisible();
  }

  async uploadCsv(filePath: string) {
    // ファイルインプットを取得してアップロード
    const fileInput = this.page.locator('input[type="file"]');
    await fileInput.setInputFiles(filePath);
  }

  async fillDatasetName(name: string) {
    await this.page.getByLabel('データセット名').fill(name);
  }

  async fillDescription(description: string) {
    await this.page.getByLabel('説明').fill(description);
  }

  async submitImport() {
    await this.page.getByRole('button', { name: 'インポート' }).click();
  }

  async search(query: string) {
    await this.searchInput.fill(query);
    await this.page.keyboard.press('Enter');
  }

  async expectToBeOnDatasetListPage() {
    await expect(this.page).toHaveURL('/datasets');
    await expect(this.pageTitle).toBeVisible();
  }

  async expectToBeOnImportPage() {
    await expect(this.page).toHaveURL('/datasets/import');
  }
}
