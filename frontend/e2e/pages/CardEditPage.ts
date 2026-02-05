/**
 * CardEditPage Page Object
 *
 * カード編集/作成ページのPage Object
 */
import { type Page, type Locator, expect } from '@playwright/test';

export class CardEditPage {
  readonly page: Page;
  readonly nameInput: Locator;
  readonly descriptionInput: Locator;
  readonly datasetSelect: Locator;
  readonly saveButton: Locator;
  readonly previewButton: Locator;
  readonly deleteButton: Locator;
  readonly previewIframe: Locator;
  readonly cardTitle: Locator;

  constructor(page: Page) {
    this.page = page;
    this.nameInput = page.getByLabel('カード名');
    this.descriptionInput = page.getByLabel('説明');
    this.datasetSelect = page.getByLabel('データセット');
    this.saveButton = page.getByRole('button', { name: '保存' });
    this.previewButton = page.getByRole('button', { name: 'プレビュー' });
    this.deleteButton = page.getByRole('button', { name: '削除' });
    this.previewIframe = page.locator('iframe[title="card-preview"]');
    this.cardTitle = page.getByRole('heading').first();
  }

  async goto(cardId: string) {
    await this.page.goto(`/cards/${cardId}`);
  }

  async gotoNew() {
    await this.page.goto('/cards/new');
  }

  async fillName(name: string) {
    await this.nameInput.fill(name);
  }

  async fillDescription(description: string) {
    await this.descriptionInput.fill(description);
  }

  async selectDataset(datasetName: string) {
    await this.datasetSelect.click();
    await this.page.getByRole('option', { name: datasetName }).click();
  }

  async setCode(code: string) {
    await this.page.evaluate((c) => {
      const editor = (window as unknown as { monacoEditor?: { setValue: (v: string) => void } })
        .monacoEditor;
      if (editor) {
        editor.setValue(c);
      }
    }, code);
  }

  async save() {
    await this.saveButton.click();
  }

  async preview() {
    await this.previewButton.click();
  }

  async delete() {
    await this.deleteButton.click();
  }

  async confirmDelete() {
    await this.page.getByRole('button', { name: '削除' }).last().click();
  }

  async expectPreviewVisible() {
    await expect(this.previewIframe).toBeVisible({ timeout: 30000 });
  }

  async expectPreviewContent() {
    const frame = this.page.frameLocator('iframe[title="card-preview"]');
    await expect(frame.locator('body')).not.toBeEmpty({ timeout: 30000 });
  }

  async expectToBeOnEditPage(cardId?: string) {
    if (cardId) {
      await expect(this.page).toHaveURL(`/cards/${cardId}`);
    } else {
      await expect(this.page).toHaveURL(/\/cards\/card_[a-zA-Z0-9]+/);
    }
  }

  async expectToBeOnNewPage() {
    await expect(this.page).toHaveURL('/cards/new');
  }

  getCardIdFromUrl(): string | null {
    const url = this.page.url();
    const match = url.match(/\/cards\/(card_[a-zA-Z0-9]+)/);
    return match ? match[1] : null;
  }
}
