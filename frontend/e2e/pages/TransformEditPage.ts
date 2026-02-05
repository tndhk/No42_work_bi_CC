/**
 * TransformEditPage Page Object
 *
 * トランスフォーム編集/作成ページのPage Object
 */
import { type Page, type Locator, expect } from '@playwright/test';

export class TransformEditPage {
  readonly page: Page;
  readonly nameInput: Locator;
  readonly saveButton: Locator;
  readonly executeButton: Locator;
  readonly deleteButton: Locator;
  readonly scheduleCheckbox: Locator;
  readonly cronInput: Locator;
  readonly executionResultCard: Locator;
  readonly executionHistoryCard: Locator;
  readonly outputDatasetLink: Locator;

  constructor(page: Page) {
    this.page = page;
    this.nameInput = page.getByLabel('Transform名');
    this.saveButton = page.getByRole('button', { name: '保存' });
    this.executeButton = page.getByRole('button', { name: '実行' });
    this.deleteButton = page.getByRole('button', { name: '削除' });
    this.scheduleCheckbox = page.locator('#schedule-enabled');
    this.cronInput = page.getByPlaceholder('0 0 * * *');
    this.executionResultCard = page.getByText('実行結果').locator('..');
    this.executionHistoryCard = page.getByText('実行履歴').locator('..');
    this.outputDatasetLink = page.getByRole('link', { name: '出力データセットを表示' });
  }

  async goto(transformId: string) {
    await this.page.goto(`/transforms/${transformId}`);
  }

  async gotoNew() {
    await this.page.goto('/transforms/new');
  }

  async fillName(name: string) {
    await this.nameInput.fill(name);
  }

  async selectDataset(datasetName: string) {
    // DatasetMultiSelectのチェックボックスを選択
    await this.page.getByLabel(datasetName).check();
  }

  async unselectDataset(datasetName: string) {
    await this.page.getByLabel(datasetName).uncheck();
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

  async enableSchedule() {
    await this.scheduleCheckbox.check();
  }

  async disableSchedule() {
    await this.scheduleCheckbox.uncheck();
  }

  async setCronExpression(cron: string) {
    await this.cronInput.fill(cron);
  }

  async clickSchedulePreset(preset: '毎時' | '毎日 0:00' | '毎週月曜' | '毎月1日') {
    await this.page.getByRole('button', { name: preset }).click();
  }

  async save() {
    await this.saveButton.click();
  }

  async execute() {
    await this.executeButton.click();
  }

  async delete() {
    await this.deleteButton.click();
  }

  async confirmDelete() {
    await this.page.getByRole('button', { name: '削除' }).last().click();
  }

  async expectExecutionResultVisible() {
    await expect(this.page.getByText('行数')).toBeVisible({ timeout: 60000 });
    await expect(this.page.getByText('実行時間')).toBeVisible();
  }

  async expectExecutionHistoryVisible() {
    await expect(this.executionHistoryCard).toBeVisible();
  }

  async expectExecutionSuccess() {
    await expect(this.page.getByText('success').first()).toBeVisible({ timeout: 60000 });
  }

  async expectExecutionFailed() {
    await expect(this.page.getByText('failed').first()).toBeVisible({ timeout: 60000 });
  }

  async expectOutputDatasetLinkVisible() {
    await expect(this.outputDatasetLink).toBeVisible({ timeout: 60000 });
  }

  async clickOutputDatasetLink() {
    await this.outputDatasetLink.click();
  }

  async expectToBeOnEditPage(transformId?: string) {
    if (transformId) {
      await expect(this.page).toHaveURL(`/transforms/${transformId}`);
    } else {
      await expect(this.page).toHaveURL(/\/transforms\/transform_[a-zA-Z0-9]+/);
    }
  }

  async expectToBeOnNewPage() {
    await expect(this.page).toHaveURL('/transforms/new');
  }

  getTransformIdFromUrl(): string | null {
    const url = this.page.url();
    const match = url.match(/\/transforms\/(transform_[a-zA-Z0-9]+)/);
    return match ? match[1] : null;
  }
}
