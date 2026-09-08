import { chromium } from "@playwright/test";
import assert from "node:assert/strict";
import { execFileSync, spawn } from "node:child_process";
import { mkdtemp, rm, mkdir } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
const temp = await mkdtemp(join(tmpdir(), "agentos-profiles-"));
const browser = await chromium.launch({ headless: true });
const python = process.env.PYTHON ?? "python3";
try {
  for (const profile of ["research", "operations", "monitoring"]) {
    const root = join(temp, profile);
    execFileSync(python, [
      "scripts/new_workspace.py",
      root,
      "--name",
      profile + " studio",
      "--profile",
      profile,
    ]);
    const server = spawn(python, ["-m", "reference.server", "--port", "0"], {
      cwd: root,
      stdio: ["ignore", "pipe", "pipe"],
    });
    try {
      const url = await new Promise((resolve, reject) => {
        let text = "";
        const timer = setTimeout(
          () => reject(Error("Startup timed out")),
          10000,
        );
        server.on("exit", (code) => {
          clearTimeout(timer);
          reject(Error("Server exited " + code));
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
      const page = await browser.newPage({
        viewport: { width: 1440, height: 1050 },
      });
      page.setDefaultTimeout(15000);
      const errors = [];
      page.on("pageerror", (e) => errors.push(e.message));
      await page.goto(url);
      await page.locator("#as-of").filter({ hasText: /\d/ }).waitFor();
      assert.equal(await page.title(), "AgentOS · " + profile + " studio");
      assert.equal(
        await page.locator("body").getAttribute("data-composition"),
        "orbital",
      );
      assert.equal(await page.locator(".center-object").isVisible(), true);
      assert.equal(await page.locator(".orbital-tool").count(), 4);
      const center = await page.locator(".center-object").boundingBox();
      assert.ok(Math.abs(center.x + center.width / 2 - 720) < 2);
      await page.getByRole("button", { name: "Open workspace views" }).click();
      await page
        .getByRole("button", { name: "Work view", exact: true })
        .click();
      assert.deepEqual(
        await page.locator(".center-object").boundingBox(),
        center,
      );
      await page.keyboard.press("Escape");
      await page.getByRole("button", { name: "New capture" }).click();
      await page
        .getByLabel("Name the work")
        .fill("Synthetic " + profile + " brief");
      await page
        .getByLabel("Source or brief")
        .fill(
          "Investigate the next useful step. Unknown evidence must stay unknown.",
        );
      await page.getByRole("button", { name: "Capture source" }).click();
      await page
        .getByRole("button", { name: "Run skill", exact: true })
        .click();
      await page.getByRole("button", { name: "Open job result" }).click();
      await page
        .getByRole("button", { name: "Accept as local project" })
        .click();
      await page.getByRole("button", { name: "Open accepted project" }).click();
      await Promise.all([
        page.waitForResponse(
          (r) => r.url().endsWith("/api/task") && r.status() === 200,
        ),
        page
          .getByLabel("Status: Confirm scope and expected deliverable.")
          .selectOption("done"),
      ]);
      await page.waitForFunction(
        () =>
          document.querySelector("#inspector-body select")?.value === "done",
      );
      await page.keyboard.press("Escape");
      if (process.env.UPDATE_SCREENSHOTS === "1") {
        await mkdir("docs/images", { recursive: true });
        await page.screenshot({
          path: "docs/images/" + profile + "-workspace.png",
          fullPage: true,
        });
      }
      await page
        .getByRole("button", { name: "All instruments", exact: true })
        .click();
      await page.getByRole("button", { name: "Memory", exact: true }).click();
      await page.getByLabel("Search memory").fill("synthetic");
      await page
        .getByRole("button", {
          name: new RegExp("Synthetic " + profile + " brief decision"),
        })
        .waitFor();
      await page.keyboard.press("Escape");
      await page
        .getByRole("button", { name: "All instruments", exact: true })
        .click();
      await page
        .locator(".widget-controls")
        .first()
        .getByRole("button", { name: "Collapse", exact: true })
        .click();
      await page
        .locator(".widget-controls")
        .first()
        .getByRole("button", { name: "Expand", exact: true })
        .waitFor();
      await page.keyboard.press("Escape");
      await page.reload();
      await page.locator("#as-of").filter({ hasText: /\d/ }).waitFor();
      assert.equal(
        await page
          .locator("#sources-panel")
          .evaluate((e) => e.classList.contains("collapsed")),
        true,
      );
      await page
        .getByRole("button", { name: "All instruments", exact: true })
        .click();
      await page
        .getByRole("button", { name: "Restore layout", exact: true })
        .click();
      await page.locator("#inspector").waitFor({ state: "hidden" });
      await page.setViewportSize({ width: 390, height: 844 });
      assert.equal(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
        true,
      );
      assert.deepEqual(errors, []);
      await page.close();
    } finally {
      server.kill("SIGTERM");
      await new Promise((r) => {
        if (server.exitCode !== null || server.signalCode !== null) r();
        else server.once("exit", r);
      });
    }
  }
  console.log(
    "Three fresh profile browser workflows passed: durable jobs, review, task progress, memory, persistent collapse and narrow layouts.",
  );
} finally {
  await browser.close();
  await rm(temp, { recursive: true, force: true });
}
