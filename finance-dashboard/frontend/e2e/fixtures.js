// Every spec imports { test, expect } from here, never from @playwright/test, so each
// test starts from the same state: seeded mock API, frozen clock, page loaded.
//
//   test.use({ startPath: "/budgets" })  open a different route first (null = don't navigate)
//   test.use({ signedIn: false })        start with no session (every /api call but login 401s)
//   api.override("GET", /^\/dashboard$/, 500, { detail: "boom" })   force an error state
//   api.db                               the mock's live data, for assertions on what was saved
import { test as base, expect } from "@playwright/test";

import { createMockApi } from "./mock-api.js";
import { FROZEN_NOW } from "./seed.js";

export const test = base.extend({
  startPath: ["/", { option: true }],
  signedIn: [true, { option: true }],

  api: async ({ signedIn }, use) => {
    await use(createMockApi({ signedIn }));
  },

  page: async ({ page, api, startPath }, use) => {
    await api.install(page);
    // Fixed start time, then the clock runs normally (timers fire, React Query polls).
    // Date.now() reads the same everywhere, so "this month" and the default form date are stable.
    await page.clock.install({ time: FROZEN_NOW });
    if (startPath) {
      await page.goto(startPath);
      await page.waitForLoadState("networkidle").catch(() => {});
    }
    await use(page);
  },
});

export { expect };
export { CREDENTIALS, FROZEN_NOW, MONTH } from "./seed.js";
