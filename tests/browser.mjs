import { chromium } from "@playwright/test";
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { mkdtemp, rm, mkdir } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
const data = await mkdtemp(join(tmpdir(), "agentos-browser-"));
const server = spawn(
  process.env.PYTHON ?? "python3",
  ["-m", "reference.server", "--port", "0", "--data-dir", data],
  { stdio: ["ignore", "pipe", "pipe"] },
);
let browser;
try {
  const url = await new Promise((resolve, reject) => {
    let text = "";
    const timer = setTimeout(
      () => reject(new Error("Server did not start")),
      10000,
    );
    server.once("exit", (code) => {
      clearTimeout(timer);
      reject(new Error("Server exit " + code));
    });
    server.stdout.on("data", (chunk) => {
      text += chunk;
      const match = text.match(/http:\/\/127\.0\.0\.1:\d+/);
      if (match) {
        clearTimeout(timer);
        resolve(match[0]);
      }
    });
  });
  browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({
    viewport: { width: 1440, height: 1050 },
  });
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto(url);
  await page.locator("#as-of").filter({ hasText: /\d/ }).waitFor();
  assert.equal(await page.locator("footer").count(), 0);
  assert.ok((await page.locator("header").boundingBox()).height <= 56);
  const anchor = await page.locator(".center-object").boundingBox();
  assert.ok(Math.abs(anchor.x + anchor.width / 2 - 720) < 2);
  assert.ok(Math.abs(anchor.y + anchor.height / 2 - 525) < 2);
  const left = await page.locator("#capture-panel").boundingBox(),
    right = await page.locator("#review-panel").boundingBox();
  assert.ok(Math.abs(left.width - right.width) < 2);
  await page.getByRole("button", { name: "New capture" }).click();
  assert.deepEqual(await page.locator(".center-object").boundingBox(), anchor);
  await page
    .getByLabel("Name the work")
    .fill("Synthetic example · Research studio");
  await page
    .getByLabel("Source or brief")
    .fill(
      "Compare two research methods using cited evidence. Identify unknowns before choosing the next experiment.",
    );
  await page.getByRole("button", { name: "Capture source" }).click();
  await page
    .getByRole("button", { name: "Create plan draft", exact: true })
    .click();
  await page.getByRole("button", { name: "Accept as local project" }).waitFor();
  assert.deepEqual(await page.locator(".center-object").boundingBox(), anchor);
  assert.equal(
    await page
      .locator("#inspector-body")
      .getByText("Deterministic reference · validation passed")
      .count(),
    1,
  );
  await page.getByRole("button", { name: "Close inspector" }).click();
  await mkdir("docs/images", { recursive: true });
  if (process.env.UPDATE_SCREENSHOTS === "1")
    await page.screenshot({
      path: "docs/images/workspace-desktop.png",
      fullPage: true,
    });
  await page
    .getByRole("button", { name: "Synthetic example · Research studio Draft" })
    .click();
  await page.getByRole("button", { name: "Accept as local project" }).click();
  await page.getByRole("button", { name: "Open accepted project" }).click();
  await page
    .getByText("No task has been executed by this reference.")
    .waitFor();
  await page.keyboard.press("Escape");
  await page.reload();
  await page.getByText("1 accepted", { exact: true }).waitFor();
  await page
    .getByRole("button", { name: "All instruments", exact: true })
    .click();
  await page
    .locator(".widget-controls")
    .first()
    .getByRole("button", { name: "Hide" })
    .click();
  await page.keyboard.press("Escape");
  await page.reload();
  assert.equal(await page.locator("#sources-panel").isVisible(), false);
  await page
    .getByRole("button", { name: "All instruments", exact: true })
    .click();
  await page.getByRole("button", { name: "Restore layout" }).click();
  assert.equal(await page.locator("#sources-panel").isVisible(), true);
  await page.getByRole("button", { name: "List view", exact: true }).click();
  await page.reload();
  assert.equal(
    await page.locator("#orbit").getAttribute("class"),
    "orbit list",
  );
  await page.getByRole("button", { name: "Map view", exact: true }).click();
  await page.getByRole("button", { name: "New capture" }).click();
  await page.getByLabel("Name the work").fill("Draft survives reload");
  await page.reload();
  await page.getByRole("button", { name: "New capture" }).click();
  assert.equal(
    await page.getByLabel("Name the work").inputValue(),
    "Draft survives reload",
  );
  await page.getByLabel("Name the work").fill("Untrusted text fixture");
  await page
    .getByLabel("Source or brief")
    .fill("<script>window.compromised=true</script>");
  await page.getByRole("button", { name: "Capture source" }).click();
  await page.locator("#inspector-body pre").waitFor();
  assert.equal(await page.evaluate(() => window.compromised), undefined);
  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: "Workspace guide" }).click();
  for (let i = 0; i < 6; i++) {
    await page.keyboard.press("Tab");
    assert.equal(
      await page.evaluate(() =>
        document.querySelector("#inspector").contains(document.activeElement),
      ),
      true,
    );
  }
  await page.keyboard.press("Escape");
  assert.equal(
    await page
      .locator("#guide-button")
      .evaluate((e) => e === document.activeElement),
    true,
  );
  await page.setViewportSize({ width: 390, height: 844 });
  assert.equal(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
    true,
  );
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.getByRole("button", { name: "Projects 1 accepted" }).click();
  await page
    .getByRole("button", {
      name: "Synthetic example · Research studio Open record",
    })
    .click();
  assert.equal(await page.locator("#inspector").isVisible(), true);
  await page.keyboard.press("Escape");
  if (process.env.UPDATE_SCREENSHOTS === "1")
    await page.screenshot({
      path: "docs/images/workspace-mobile.png",
      fullPage: true,
    });
  assert.deepEqual(errors, []);
  console.log(
    "Browser workflow passed: capture, draft, review, persistence, layout, safe text, focus, mobile and reduced motion.",
  );
} finally {
  if (browser) await browser.close();
  server.kill("SIGTERM");
  await new Promise((resolve) => {
    if (server.exitCode !== null) resolve();
    else server.once("exit", resolve);
  });
  await rm(data, { recursive: true, force: true });
}
