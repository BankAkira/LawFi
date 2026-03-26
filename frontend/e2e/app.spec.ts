import { test, expect } from "@playwright/test";

test.describe("Homepage", () => {
  test("renders search box and LawFi branding", async ({ page }) => {
    await page.goto("/");

    await expect(page.locator("h1")).toContainText("LawFi");
    await expect(
      page.getByPlaceholder("ค้นหาฎีกา")
    ).toBeVisible();
    await expect(page.getByRole("button", { name: "ค้นหา" })).toBeVisible();
  });

  test("advanced filters toggle works", async ({ page }) => {
    await page.goto("/");

    // Filter select hidden by default
    await expect(page.locator("select")).not.toBeVisible();

    // Click toggle
    await page.getByText("ตัวกรองขั้นสูง").click();

    // Filter select now visible
    await expect(page.locator("select")).toBeVisible();
  });

  test("search navigates to results page", async ({ page }) => {
    await page.goto("/");

    await page.getByPlaceholder("ค้นหาฎีกา").fill("สัญญาซื้อขาย");
    await page.getByRole("button", { name: "ค้นหา" }).click();

    await expect(page).toHaveURL(/\/search\?q=/);
    await expect(page.locator("h1")).toContainText("สัญญาซื้อขาย");
  });
});

test.describe("Auth pages", () => {
  test("login page renders form", async ({ page }) => {
    await page.goto("/login");

    await expect(
      page.getByRole("heading", { name: /เข้าสู่ระบบ/ })
    ).toBeVisible();
    await expect(page.getByPlaceholder("you@example.com")).toBeVisible();
    await expect(page.getByPlaceholder("รหัสผ่าน")).toBeVisible();
  });

  test("register page renders form", async ({ page }) => {
    await page.goto("/register");

    await expect(
      page.getByRole("heading", { name: /สมัครสมาชิก/ })
    ).toBeVisible();
    await expect(page.getByPlaceholder("ชื่อของคุณ")).toBeVisible();
  });

  test("login link navigates from register", async ({ page }) => {
    await page.goto("/register");

    // Use the link inside the form (not the navbar)
    await page.locator("form").getByRole("link", { name: "เข้าสู่ระบบ" }).click();
    await expect(page).toHaveURL("/login");
  });
});

test.describe("Responsive", () => {
  test("homepage renders correctly on mobile", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto("/");

    await expect(page.locator("h1")).toContainText("LawFi");
    await expect(
      page.getByPlaceholder("ค้นหาฎีกา")
    ).toBeVisible();
  });
});
