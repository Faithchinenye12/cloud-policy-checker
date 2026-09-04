import { expect, test, type Page } from "@playwright/test";

async function mockDemoApi(page: Page) {
  await page.route("**/api/**", async route => {
    const path = new URL(route.request().url()).pathname;
    let body: unknown = {};

    if (path === "/api/auth/demo") body = { access_token: "recruiter-demo-token" };
    else if (path === "/api/auth/me") body = { id: 1, email: "recruiter@cloudconform.demo", username: "Recruiter Demo", is_active: true };
    else if (path.startsWith("/api/resources")) body = [];
    else if (path.startsWith("/api/policies")) body = [];
    else if (path === "/api/intelligence/graph") body = { summary: { resources: 0, policies: 0, scans: 0, open_findings: 0, risk_score: 0 }, nodes: [], edges: [], priority_actions: [] };
    else if (path === "/api/compliance/readiness") body = { disclaimer: "Evidence-based readiness, not certification.", frameworks: [] };

    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(body) });
  });
}

test("a recruiter can complete the guided evidence journey", async ({ page }) => {
  await mockDemoApi(page);
  await page.goto("/");

  await page.getByRole("button", { name: "Explore live demo" }).click();
  await expect(page.getByText("Read-only recruiter demo")).toBeVisible();

  await expect(page.getByRole("heading", { name: "Start with the asset" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Resources" })).toBeVisible();

  await page.getByRole("button", { name: "Next" }).click();
  await expect(page.getByRole("heading", { name: "Understand the rule" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Policies" })).toBeVisible();

  await page.getByRole("button", { name: "Next" }).click();
  await expect(page.getByRole("heading", { name: "Prioritise what matters" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Risk intelligence" })).toBeVisible();

  await page.getByRole("button", { name: "Next" }).click();
  await expect(page.getByRole("heading", { name: "Measure readiness honestly" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Compliance readiness" })).toBeVisible();

  await page.getByRole("button", { name: "Finish tour" }).click();
  await expect(page.getByRole("dialog")).toBeHidden();

  await page.getByRole("button", { name: "Why CloudConform", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Cloud security evidence people can actually act on." })).toBeVisible();
});

test("the public journey exposes no mutation controls", async ({ page }) => {
  await mockDemoApi(page);
  await page.goto("/");
  await page.getByRole("button", { name: "Explore live demo" }).click();
  await page.getByRole("button", { name: "Close guided tour" }).click();

  await expect(page.getByRole("button", { name: /add resource/i })).toHaveCount(0);
  await page.getByRole("button", { name: "2. Controls" }).click();
  await expect(page.getByRole("button", { name: /add policy/i })).toHaveCount(0);
  await expect(page.getByRole("button", { name: /test configuration/i })).toHaveCount(0);
  await page.getByRole("button", { name: "Scans", exact: true }).click();
  await expect(page.getByRole("button", { name: /new scan/i })).toHaveCount(0);
});
