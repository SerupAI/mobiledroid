import { test, expect } from '@playwright/test';

test.describe('Settings Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/settings');
  });

  test('should display the settings page header', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Settings' })).toBeVisible();
    await expect(page.getByText('Configure MobileDroid to your preferences')).toBeVisible();
  });

  test('should display all setting tabs', async ({ page }) => {
    await expect(page.getByRole('button', { name: 'General' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'API Keys' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Docker' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Proxy' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Notifications' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Appearance' })).toBeVisible();
  });

  test('should display system info section', async ({ page }) => {
    await expect(page.getByText('System Info')).toBeVisible();
    await expect(page.getByText('Version')).toBeVisible();
    await expect(page.getByText('Status')).toBeVisible();
  });

  test('should switch to API Keys tab', async ({ page }) => {
    await page.getByRole('button', { name: 'API Keys' }).click();
    await expect(page.getByText('Anthropic API Key')).toBeVisible();
    await expect(page.getByText('OpenAI API Key')).toBeVisible();
  });

  test('should switch to Docker tab', async ({ page }) => {
    await page.getByRole('button', { name: 'Docker' }).click();
    await expect(page.getByText('Docker Settings')).toBeVisible();
    await expect(page.getByText('Docker Host')).toBeVisible();
    await expect(page.getByText('Redroid Image')).toBeVisible();
  });

  test('should switch to Proxy tab', async ({ page }) => {
    await page.getByRole('button', { name: 'Proxy' }).click();
    await expect(page.getByText('Default Proxy Settings')).toBeVisible();
    await expect(page.getByText('Proxy Type')).toBeVisible();
  });

  test('should switch to Notifications tab', async ({ page }) => {
    await page.getByRole('button', { name: 'Notifications' }).click();
    await expect(page.getByText('Task Completion')).toBeVisible();
    await expect(page.getByText('Profile Errors')).toBeVisible();
  });

  test('should switch to Appearance tab', async ({ page }) => {
    await page.getByRole('button', { name: 'Appearance' }).click();
    await expect(page.getByText('Theme')).toBeVisible();
    await expect(page.getByText('Dark')).toBeVisible();
    await expect(page.getByText('Light')).toBeVisible();
  });

  test('should have Save and Reset buttons', async ({ page }) => {
    await expect(page.getByRole('button', { name: 'Save Changes' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Reset' })).toBeVisible();
  });

  test('should display General settings by default', async ({ page }) => {
    await expect(page.getByText('General Settings')).toBeVisible();
    await expect(page.getByText('Default Android Version')).toBeVisible();
    await expect(page.getByText('Default Screen Resolution')).toBeVisible();
  });
});
