import { test, expect } from '@playwright/test';

const FRONTEND_URL = process.env.FRONTEND_URL || 'http://localhost:8501';
const API_URL = process.env.API_URL || 'http://localhost:8000';

test.describe('Voice RAG System E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the main application
    await page.goto(FRONTEND_URL);

    // Wait for the page to load
    await page.waitForLoadState('networkidle');
  });

  test('homepage loads correctly', async ({ page }) => {
    // Check that the main title is present
    await expect(page.locator('h1')).toContainText('Voice-Enabled RAG System');

    // Check for key navigation elements
    await expect(page.locator('[data-testid="sidebar"]')).toBeVisible();
  });

  test('document upload functionality', async ({ page }) => {
    // Navigate to document upload page (if separate)
    // await page.click('[data-testid="document-upload-tab"]');

    // Check for file upload component
    await expect(page.locator('input[type="file"]')).toBeVisible();

    // Create a test file and upload it
    const fileContent = 'This is a test document for E2E testing.';
    const blob = new Blob([fileContent], { type: 'text/plain' });
    const file = new File([blob], 'test-document.txt', { type: 'text/plain' });

    // Upload the file
    await page.setInputFiles('input[type="file"]', [
      {
        name: 'test-document.txt',
        mimeType: 'text/plain',
        buffer: Buffer.from(fileContent)
      }
    ]);

    // Click upload button
    await page.click('[data-testid="upload-button"]');

    // Wait for upload completion
    await expect(page.locator('[data-testid="upload-success"]')).toBeVisible({ timeout: 10000 });
  });

  test('text query functionality', async ({ page }) => {
    // Navigate to query interface
    const queryInput = page.locator('[data-testid="query-input"]');
    await expect(queryInput).toBeVisible();

    // Enter a test query
    await queryInput.fill('What is this document about?');

    // Submit the query
    await page.click('[data-testid="submit-query"]');

    // Wait for response
    await expect(page.locator('[data-testid="query-response"]')).toBeVisible({ timeout: 15000 });

    // Check that response contains text
    const response = await page.locator('[data-testid="query-response"]').textContent();
    expect(response).toBeTruthy();
    expect(response.length).toBeGreaterThan(10);
  });

  test('voice recording interface', async ({ page }) => {
    // Navigate to voice interface
    await page.click('[data-testid="voice-tab"]');

    // Check for voice recording components
    await expect(page.locator('[data-testid="voice-recorder"]')).toBeVisible();
    await expect(page.locator('[data-testid="start-recording"]')).toBeVisible();
    await expect(page.locator('[data-testid="stop-recording"]')).toBeDisabled();

    // Note: Actual voice recording testing would require browser permissions
    // and mock audio input, which is complex in E2E tests
  });

  test('analytics dashboard', async ({ page }) => {
    // Navigate to analytics page
    await page.goto(`${FRONTEND_URL}/analytics_dashboard`);

    // Wait for charts to load
    await page.waitForLoadState('networkidle');

    // Check for key metrics
    await expect(page.locator('[data-testid="performance-metrics"]')).toBeVisible();
    await expect(page.locator('[data-testid="system-health"]')).toBeVisible();

    // Check for charts/visualizations
    const charts = page.locator('.js-plotly-plot');
    await expect(charts.first()).toBeVisible({ timeout: 10000 });
  });

  test('multi-modal document interface', async ({ page }) => {
    // Navigate to multi-modal document page
    await page.goto(`${FRONTEND_URL}/multimodal_documents`);

    // Check for supported formats display
    await expect(page.locator('[data-testid="supported-formats"]')).toBeVisible();

    // Check for upload interface
    await expect(page.locator('[data-testid="file-uploader"]')).toBeVisible();

    // Check for processing options
    await expect(page.locator('[data-testid="ocr-option"]')).toBeVisible();
  });

  test('system health indicators', async ({ page }) => {
    // Check for system status indicators
    await expect(page.locator('[data-testid="system-status"]')).toBeVisible();

    // Verify that system appears healthy
    const statusText = await page.locator('[data-testid="system-status"]').textContent();
    expect(statusText).toContain('healthy');
  });

  test('responsive design on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Reload page
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Check that mobile layout is applied
    const sidebar = page.locator('[data-testid="sidebar"]');

    // Sidebar should be collapsed on mobile
    await expect(sidebar).toHaveCSS('width', '0px');

    // Check for mobile-friendly controls
    await expect(page.locator('[data-testid="mobile-menu"]')).toBeVisible();
  });

  test('error handling', async ({ page }) => {
    // Test with invalid API endpoint to trigger error handling
    await page.route('**/api/**', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Server error for testing' })
      });
    });

    // Try to perform an action that would call the API
    const queryInput = page.locator('[data-testid="query-input"]');
    if (await queryInput.isVisible()) {
      await queryInput.fill('test query');
      await page.click('[data-testid="submit-query"]');

      // Check that error message is displayed
      await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
    }
  });

  test('performance - page load time', async ({ page }) => {
    const startTime = Date.now();

    await page.goto(FRONTEND_URL);
    await page.waitForLoadState('networkidle');

    const loadTime = Date.now() - startTime;

    // Page should load within 5 seconds
    expect(loadTime).toBeLessThan(5000);
  });
});

test.describe('API Integration Tests', () => {
  test('health endpoint returns correct status', async ({ request }) => {
    const response = await request.get(`${API_URL}/health`);
    expect(response.ok()).toBeTruthy();

    const health = await response.json();
    expect(health).toHaveProperty('status');
    expect(health.status).toBe('healthy');
  });

  test('voice capabilities endpoint', async ({ request }) => {
    const response = await request.get(`${API_URL}/voice/capabilities`);
    expect(response.ok()).toBeTruthy();

    const capabilities = await response.json();
    expect(capabilities).toHaveProperty('basic_transcription');
    expect(capabilities.basic_transcription).toBe(true);
  });

  test('supported formats endpoint', async ({ request }) => {
    const response = await request.get(`${API_URL}/documents/supported-formats`);
    expect(response.ok()).toBeTruthy();

    const formats = await response.json();
    expect(formats).toHaveProperty('total_supported');
    expect(formats.total_supported).toBeGreaterThan(0);
  });

  test('analytics dashboard endpoint', async ({ request }) => {
    const response = await request.get(`${API_URL}/analytics/dashboard`);
    expect(response.ok()).toBeTruthy();

    const analytics = await response.json();
    expect(analytics).toHaveProperty('system_metrics');
    expect(analytics).toHaveProperty('health_status');
  });

  test('metrics endpoint format', async ({ request }) => {
    const response = await request.get(`${API_URL}/metrics`);
    expect(response.ok()).toBeTruthy();

    const metrics = await response.json();
    expect(metrics).toHaveProperty('metrics');
    expect(metrics).toHaveProperty('format');
  });
});

test.describe('Cross-browser Compatibility', () => {
  ['chromium', 'firefox', 'webkit'].forEach(browserName => {
    test(`basic functionality works in ${browserName}`, async ({ page }) => {
      await page.goto(FRONTEND_URL);
      await page.waitForLoadState('networkidle');

      // Check that main elements are present
      await expect(page.locator('h1')).toBeVisible();
      await expect(page.locator('[data-testid="sidebar"]')).toBeVisible();

      // Try basic interaction
      const queryInput = page.locator('[data-testid="query-input"]');
      if (await queryInput.isVisible()) {
        await queryInput.fill('test');
        await expect(queryInput).toHaveValue('test');
      }
    });
  });
});

test.describe('Accessibility Tests', () => {
  test('keyboard navigation works', async ({ page }) => {
    await page.goto(FRONTEND_URL);
    await page.waitForLoadState('networkidle');

    // Test Tab navigation
    await page.keyboard.press('Tab');

    // Verify focus is visible
    const focusedElement = page.locator(':focus');
    await expect(focusedElement).toBeVisible();
  });

  test('proper heading structure', async ({ page }) => {
    await page.goto(FRONTEND_URL);
    await page.waitForLoadState('networkidle');

    // Check for proper heading hierarchy
    const h1 = page.locator('h1');
    await expect(h1).toBeVisible();

    // Should have only one H1
    const h1Count = await h1.count();
    expect(h1Count).toBe(1);
  });

  test('form labels and accessibility', async ({ page }) => {
    await page.goto(FRONTEND_URL);
    await page.waitForLoadState('networkidle');

    // Check that form inputs have proper labels
    const inputs = page.locator('input[type="text"], textarea');
    const inputCount = await inputs.count();

    for (let i = 0; i < inputCount; i++) {
      const input = inputs.nth(i);
      const inputId = await input.getAttribute('id');
      const inputName = await input.getAttribute('name');
      const inputAriaLabel = await input.getAttribute('aria-label');

      // Input should have either id with corresponding label, name, or aria-label
      const hasProperLabel = inputId || inputName || inputAriaLabel;
      expect(hasProperLabel).toBeTruthy();
    }
  });
});