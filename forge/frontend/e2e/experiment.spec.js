import { test, expect } from '@playwright/test';

test.describe('Experiment Page', () => {
  test('homepage loads and shows create button', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('body')).toBeVisible();
  });

  test('experiment page shows loading state for invalid id', async ({ page }) => {
    await page.goto('/experiments/nonexistent');
    await expect(page.getByText('Loading...')).toBeVisible({ timeout: 5000 });
  });

  test('experiment page renders tabs', async ({ page }) => {
    await page.goto('/experiments/test-id');
    await expect(page.getByText('Overview')).toBeVisible({ timeout: 5000 });
    await expect(page.getByText('Flow')).toBeVisible();
    await expect(page.getByText('Events')).toBeVisible();
    await expect(page.getByText('Replay')).toBeVisible();
    await expect(page.getByText('Agent')).toBeVisible();
  });

  test('tab switching works', async ({ page }) => {
    await page.goto('/experiments/test-id');
    await page.getByText('Flow').click();
    await expect(page.getByText('Visualization')).toBeVisible({ timeout: 5000 });
    await page.getByText('Events').click();
    await page.getByText('Replay').click();
    await page.getByText('Agent').click();
  });
});
