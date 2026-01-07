import { test, expect } from '@playwright/test';

test.describe('Navigation', () => {
  test('should display the header with navigation links', async ({ page }) => {
    await page.goto('/');

    // Check header is visible
    const header = page.locator('header');
    await expect(header).toBeVisible();

    // Check logo/brand name
    await expect(page.getByText('MobileDroid')).toBeVisible();

    // Check navigation links
    await expect(page.getByRole('link', { name: 'Dashboard' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Profiles' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Settings' })).toBeVisible();
  });

  test('should navigate to Dashboard', async ({ page }) => {
    await page.goto('/profiles');
    await page.getByRole('link', { name: 'Dashboard' }).click();
    await expect(page).toHaveURL('/');
    await expect(page.getByText('Device Profiles')).toBeVisible();
  });

  test('should navigate to Profiles page', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('link', { name: 'Profiles' }).click();
    await expect(page).toHaveURL('/profiles');
    await expect(page.getByRole('heading', { name: 'Device Profiles' })).toBeVisible();
  });

  test('should navigate to Settings page', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('link', { name: 'Settings' }).click();
    await expect(page).toHaveURL('/settings');
    await expect(page.getByRole('heading', { name: 'Settings' })).toBeVisible();
  });

  test('should navigate to New Profile page', async ({ page }) => {
    await page.goto('/profiles');
    await page.getByRole('link', { name: 'New Profile' }).click();
    await expect(page).toHaveURL('/profiles/new');
  });
});
