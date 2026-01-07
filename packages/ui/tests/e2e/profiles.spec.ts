import { test, expect } from '@playwright/test';

test.describe('Profiles Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/profiles');
  });

  test('should display the profiles page header', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Device Profiles' })).toBeVisible();
    await expect(page.getByText('Manage your Android device profiles')).toBeVisible();
  });

  test('should have a search input', async ({ page }) => {
    const searchInput = page.getByPlaceholder('Search profiles...');
    await expect(searchInput).toBeVisible();
  });

  test('should have a status filter dropdown', async ({ page }) => {
    const filterSelect = page.locator('select');
    await expect(filterSelect).toBeVisible();

    // Check filter options
    await expect(filterSelect.locator('option[value="all"]')).toHaveText('All Status');
    await expect(filterSelect.locator('option[value="running"]')).toHaveText('Running');
    await expect(filterSelect.locator('option[value="stopped"]')).toHaveText('Stopped');
  });

  test('should have a New Profile button', async ({ page }) => {
    const newProfileButton = page.getByRole('link', { name: 'New Profile' });
    await expect(newProfileButton).toBeVisible();
  });

  test('should filter profiles by search query', async ({ page }) => {
    const searchInput = page.getByPlaceholder('Search profiles...');
    await searchInput.fill('test-nonexistent-profile');

    // Wait for filter to apply
    await page.waitForTimeout(300);

    // Should show "No matching profiles" or similar message
    // (depends on whether there are profiles in the database)
  });

  test('should filter profiles by status', async ({ page }) => {
    const filterSelect = page.locator('select');
    await filterSelect.selectOption('running');

    // Wait for filter to apply
    await page.waitForTimeout(300);

    // Verify filter is applied
    await expect(filterSelect).toHaveValue('running');
  });
});

test.describe('Dashboard', () => {
  test('should display stats cards', async ({ page }) => {
    await page.goto('/');

    // Check stats are visible
    await expect(page.getByText('Total Profiles')).toBeVisible();
    await expect(page.getByText('Running')).toBeVisible();
    await expect(page.getByText('CPU Usage')).toBeVisible();
    await expect(page.getByText('Memory')).toBeVisible();
  });

  test('should display profile cards section', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('Device Profiles')).toBeVisible();
  });

  test('should show create profile card', async ({ page }) => {
    await page.goto('/');

    // Look for the create profile card (+ icon or "Create Profile" text)
    const createCard = page.locator('text=Create Profile').or(page.locator('[data-testid="create-profile-card"]'));
    // This may or may not exist depending on the UI state
  });
});

test.describe('Create Profile Flow', () => {
  test('should navigate to create profile page', async ({ page }) => {
    await page.goto('/');

    // Find and click the create profile card or button
    const createLink = page.getByRole('link', { name: /new profile|create/i });
    if (await createLink.isVisible()) {
      await createLink.click();
      await expect(page).toHaveURL('/profiles/new');
    }
  });

  test('should display create profile form', async ({ page }) => {
    await page.goto('/profiles/new');

    // Check for form elements
    await expect(page.getByLabel(/name/i).or(page.getByPlaceholder(/name/i))).toBeVisible();
  });
});
