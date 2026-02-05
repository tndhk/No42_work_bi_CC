/**
 * E2E Test API Helper
 * テストデータの作成・削除を直接HTTP経由で実行
 */

const API_BASE_URL = 'http://localhost:8000/api';

export interface TestDataCleanup {
  datasetIds: string[];
  cardIds: string[];
  dashboardIds: string[];
  shareIds: { dashboardId: string; shareId: string }[];
  groupIds: string[];
  transformIds: string[];
  filterViewIds: string[];
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
 * ダッシュボード共有を作成
 */
export async function createShare(
  token: string,
  dashboardId: string,
  sharedToType: 'user' | 'group',
  sharedToId: string,
  permission: 'viewer' | 'editor'
): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/dashboards/${dashboardId}/shares`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      shared_to_type: sharedToType,
      shared_to_id: sharedToId,
      permission,
    }),
  });

  if (!response.ok) {
    throw new Error(`Create share failed: ${response.status} ${response.statusText}`);
  }

  const data = await response.json();
  return data.data.id;
}

/**
 * ダッシュボード共有を削除
 */
export async function deleteShare(
  token: string,
  dashboardId: string,
  shareId: string
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/dashboards/${dashboardId}/shares/${shareId}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!response.ok && response.status !== 404) {
    throw new Error(`Delete share failed: ${response.status} ${response.statusText}`);
  }
}

/**
 * グループを作成
 */
export async function createGroup(
  token: string,
  name: string
): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/groups`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ name }),
  });

  if (!response.ok) {
    throw new Error(`Create group failed: ${response.status} ${response.statusText}`);
  }

  const data = await response.json();
  return data.data.id;
}

/**
 * グループを削除
 */
export async function deleteGroup(token: string, groupId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/groups/${groupId}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!response.ok && response.status !== 404) {
    throw new Error(`Delete group failed: ${response.status} ${response.statusText}`);
  }
}

/**
 * グループにメンバーを追加
 */
export async function addGroupMember(
  token: string,
  groupId: string,
  userId: string
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/groups/${groupId}/members`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ user_id: userId }),
  });

  if (!response.ok) {
    throw new Error(`Add group member failed: ${response.status} ${response.statusText}`);
  }
}

/**
 * ユーザー登録 (テスト用)
 */
export async function registerUser(
  email: string,
  password: string,
  name: string,
  role: string = 'member'
): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, name, role }),
  });

  if (!response.ok && response.status !== 409) {
    throw new Error(`Register user failed: ${response.status} ${response.statusText}`);
  }

  const data = await response.json();
  return data.data?.user_id || data.data?.id || '';
}

/**
 * トランスフォームを作成
 */
export async function createTransform(
  token: string,
  name: string,
  datasetIds: string[],
  code: string = 'import pandas as pd\n\n# Transform code\ndf_0'
): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/transforms`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      name,
      description: `Test transform: ${name}`,
      dataset_ids: datasetIds,
      code,
    }),
  });

  if (!response.ok) {
    throw new Error(`Create transform failed: ${response.status} ${response.statusText}`);
  }

  const data = await response.json();
  return data.data.id;
}

/**
 * トランスフォームを削除
 */
export async function deleteTransform(token: string, transformId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/transforms/${transformId}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!response.ok && response.status !== 404) {
    throw new Error(`Delete transform failed: ${response.status} ${response.statusText}`);
  }
}

/**
 * トランスフォームを実行
 */
export async function executeTransform(token: string, transformId: string): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/transforms/${transformId}/execute`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!response.ok) {
    throw new Error(`Execute transform failed: ${response.status} ${response.statusText}`);
  }

  const data = await response.json();
  return data.data.output_dataset_id;
}

/**
 * フィルタービューを作成
 */
export async function createFilterView(
  token: string,
  dashboardId: string,
  name: string,
  filters: Record<string, unknown>,
  isShared: boolean = false
): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/dashboards/${dashboardId}/filter-views`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      name,
      filters,
      is_shared: isShared,
    }),
  });

  if (!response.ok) {
    throw new Error(`Create filter view failed: ${response.status} ${response.statusText}`);
  }

  const data = await response.json();
  return data.data.id;
}

/**
 * フィルタービューを削除
 */
export async function deleteFilterView(token: string, filterViewId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/filter-views/${filterViewId}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!response.ok && response.status !== 404) {
    throw new Error(`Delete filter view failed: ${response.status} ${response.statusText}`);
  }
}

/**
 * テストデータを一括削除
 */
export async function cleanupTestData(token: string, cleanup: TestDataCleanup): Promise<void> {
  // 逆順で削除 (FilterView → Share → Dashboard → Card → Transform → Dataset → Group)
  for (const filterViewId of cleanup.filterViewIds) {
    await deleteFilterView(token, filterViewId);
  }
  for (const share of cleanup.shareIds) {
    await deleteShare(token, share.dashboardId, share.shareId);
  }
  for (const dashboardId of cleanup.dashboardIds) {
    await deleteDashboard(token, dashboardId);
  }
  for (const cardId of cleanup.cardIds) {
    await deleteCard(token, cardId);
  }
  for (const transformId of cleanup.transformIds) {
    await deleteTransform(token, transformId);
  }
  for (const datasetId of cleanup.datasetIds) {
    await deleteDataset(token, datasetId);
  }
  for (const groupId of cleanup.groupIds) {
    await deleteGroup(token, groupId);
  }
}
