/**
 * E2E Test API Helper
 * テストデータの作成・削除を直接HTTP経由で実行
 */

const API_BASE_URL = 'http://localhost:8000/api';

export interface TestDataCleanup {
  datasetIds: string[];
  cardIds: string[];
  dashboardIds: string[];
}

/**
 * アクセストークンを取得 (ログイン)
 */
export async function getAccessToken(email: string, password: string): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    throw new Error(`Login failed: ${response.status} ${response.statusText}`);
  }

  const data = await response.json();
  return data.data.access_token;
}

/**
 * データセットを作成
 */
export async function createDataset(
  token: string,
  name: string,
  csvContent: string
): Promise<string> {
  const blob = new Blob([csvContent], { type: 'text/csv' });
  const formData = new FormData();
  formData.append('file', blob, 'test.csv');
  formData.append('name', name);
  formData.append('description', `Test dataset: ${name}`);

  const response = await fetch(`${API_BASE_URL}/datasets`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Create dataset failed: ${response.status} ${response.statusText}`);
  }

  const data = await response.json();
  return data.data.id;
}

/**
 * データセットを削除
 */
export async function deleteDataset(token: string, datasetId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/datasets/${datasetId}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!response.ok && response.status !== 404) {
    throw new Error(`Delete dataset failed: ${response.status} ${response.statusText}`);
  }
}

/**
 * カードを作成
 */
export async function createCard(
  token: string,
  name: string,
  datasetId: string,
  code: string = 'import pandas as pd\ndf'
): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/cards`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      name,
      description: `Test card: ${name}`,
      dataset_id: datasetId,
      code,
    }),
  });

  if (!response.ok) {
    throw new Error(`Create card failed: ${response.status} ${response.statusText}`);
  }

  const data = await response.json();
  return data.data.id;
}

/**
 * カードを削除
 */
export async function deleteCard(token: string, cardId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/cards/${cardId}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!response.ok && response.status !== 404) {
    throw new Error(`Delete card failed: ${response.status} ${response.statusText}`);
  }
}

/**
 * ダッシュボードを作成
 */
export async function createDashboard(
  token: string,
  name: string,
  cardIds: string[] = []
): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/dashboards`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      name,
      description: `Test dashboard: ${name}`,
      card_ids: cardIds,
    }),
  });

  if (!response.ok) {
    throw new Error(`Create dashboard failed: ${response.status} ${response.statusText}`);
  }

  const data = await response.json();
  return data.data.id;
}

/**
 * ダッシュボードを削除
 */
export async function deleteDashboard(token: string, dashboardId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/dashboards/${dashboardId}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!response.ok && response.status !== 404) {
    throw new Error(`Delete dashboard failed: ${response.status} ${response.statusText}`);
  }
}

/**
 * テストデータを一括削除
 */
export async function cleanupTestData(token: string, cleanup: TestDataCleanup): Promise<void> {
  // 逆順で削除 (Dashboard → Card → Dataset)
  for (const dashboardId of cleanup.dashboardIds) {
    await deleteDashboard(token, dashboardId);
  }
  for (const cardId of cleanup.cardIds) {
    await deleteCard(token, cardId);
  }
  for (const datasetId of cleanup.datasetIds) {
    await deleteDataset(token, datasetId);
  }
}
