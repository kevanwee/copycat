import {test, expect} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import fs from 'node:fs/promises';
const original = 'The lantern maker kept a notebook of impossible colours. Each evening she sketched the city as it might appear beneath a second moon. Her final drawing showed the harbour filled with paper boats and little green lights.';

test('full text comparison, evidence, revision, exports, private access and deletion', async ({page, browser}) => {
  await page.setViewportSize({width: 1440, height: 1100});
  await page.goto('/');
  await expect(page.getByRole('heading', {name: 'What are you comparing?'})).toBeVisible();
  await page.screenshot({path: '../screenshots/triage-desktop.png', fullPage: true});
  expect((await new AxeBuilder({page}).analyze()).violations).toEqual([]);
  await page.getByLabel('Original file', {exact: true}).setInputFiles({name: 'original.txt', mimeType: 'text/plain', buffer: Buffer.from(original)});
  await page.getByLabel('Comparison file', {exact: true}).setInputFiles({name: 'comparison.txt', mimeType: 'text/plain', buffer: Buffer.from(original)});
  await page.getByLabel('Comparison name').fill('The lantern maker / publication review');
  await page.getByLabel('Protected work category').selectOption('literary');
  await page.getByLabel('Alleged conduct date').fill('2026-09-01');
  await page.getByRole('button', {name: 'Continue'}).click();
  await expect(page.getByRole('heading', {name: 'What does the evidence establish?'})).toBeVisible();
  await page.getByRole('button', {name: 'Continue'}).click();
  await page.getByRole('button', {name: 'Run comparison'}).click();
  await expect(page.getByRole('heading', {name: 'More evidence needed'})).toBeVisible();
  await page.screenshot({path: '../screenshots/report-desktop.png', fullPage: true});
  expect((await new AxeBuilder({page}).analyze()).violations).toEqual([]);
  await page.getByRole('button', {name: 'Evidence', exact: true}).click();
  await expect(page.getByRole('heading', {name: 'Matching text blocks'})).toBeVisible();
  await expect(page.locator('.passage')).toContainText('lantern maker');
  await page.getByRole('button', {name: 'Legal analysis', exact: true}).click();
  await expect(page.locator('.legal-node')).toHaveCount(13);
  await page.getByRole('button', {name: 'Revise context'}).click();
  const question = page.getByRole('group', {name: 'Are the category-specific conditions for protection satisfied?', exact: true});
  await question.getByLabel('Yes', {exact: true}).check();
  await question.getByRole('textbox').fill('Exhibit 1: dated handwritten drafts identify the human author and the expression created.');
  await page.getByRole('button', {name: 'Save & rerun'}).click();
  await expect(page.getByRole('heading', {name: 'The basis for the assessment.'})).toBeVisible();
  await expect(page.locator('.legal-node').first()).toContainText('Exhibit 1');
  const dl = page.waitForEvent('download'); await page.getByRole('button', {name: 'Download PDF'}).click();
  const file = await dl; const bytes = await fs.readFile((await file.path())!); expect(bytes.subarray(0,5).toString()).toBe('%PDF-');
  const jsonDownload = page.waitForEvent('download'); await page.getByRole('button', {name: 'Export JSON'}).click();
  const jsonFile = await jsonDownload; const report = JSON.parse(await fs.readFile((await jsonFile.path())!, 'utf8'));
  expect(report.assessment.status).toBe('incomplete'); expect(report.legal_flow[0].answer).toBe('yes');
  const url = page.url(); await page.reload(); await expect(page.getByRole('heading', {name: 'More evidence needed'})).toBeVisible();
  const stranger = await browser.newContext(); const strangerPage = await stranger.newPage(); await strangerPage.goto(url);
  await expect(strangerPage.getByRole('heading', {name: 'Open your comparison.'})).toBeVisible(); await stranger.close();
  await page.getByText('Case access & deletion', {exact:true}).click();
  await page.getByRole('button', {name:'Delete case…'}).click();
  await page.getByRole('button', {name:'Delete permanently'}).click();
  await expect(page).toHaveURL('http://127.0.0.1:3000/');
});

test('mobile layout, keyboard access and required file validation', async ({page}) => {
  await page.setViewportSize({width:390, height:844}); await page.goto('/');
  await expect(page.getByRole('heading', {name:'What are you comparing?'})).toBeVisible();
  await page.keyboard.press('Tab'); await expect(page.getByRole('link', {name:'Skip to content'})).toBeFocused();
  await page.getByRole('button', {name:'Continue'}).click(); await expect(page.locator('.error[role="alert"]')).toContainText('Add both');
  await page.screenshot({path:'../screenshots/triage-mobile.png', fullPage:true});
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
  expect((await new AxeBuilder({page}).analyze()).violations).toEqual([]);
});

test('recoverable server error', async ({page}) => {
  await page.route('**/api/v1/cases/questionnaire', route => route.abort()); await page.goto('/');
  await expect(page.locator('.error[role="alert"]')).toContainText('Could not reach');
  await page.unroute('**/api/v1/cases/questionnaire'); await page.getByRole('button', {name:'Retry connection'}).click();
  await expect(page.getByRole('heading', {name:'What are you comparing?'})).toBeVisible();
});
