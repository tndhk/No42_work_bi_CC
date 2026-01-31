/**
 * Playwright Global Setup
 * API ヘルスチェックでバックエンドの起動を待機
 */

const HEALTH_CHECK_URL = 'http://localhost:8000/api/health';
const MAX_RETRIES = 30;
const RETRY_INTERVAL = 2000; // 2秒

async function globalSetup() {
  console.log('Waiting for backend to be ready...');

  for (let i = 0; i < MAX_RETRIES; i++) {
    try {
      const response = await fetch(HEALTH_CHECK_URL);
      if (response.ok) {
        console.log('✅ Backend is ready!');
        return;
      }
    } catch (error) {
      // Connection error - backend not ready yet
    }

    if (i === MAX_RETRIES - 1) {
      throw new Error(
        `Backend health check failed after ${MAX_RETRIES} attempts. ` +
        `Make sure docker-compose is running.`
      );
    }

    console.log(`Waiting for backend... (${i + 1}/${MAX_RETRIES})`);
    await new Promise(resolve => setTimeout(resolve, RETRY_INTERVAL));
  }
}

export default globalSetup;
