# Layout-shift diagnosis

## Contents

- [1. Record every shift and what moved](#1-record-every-shift-and-what-moved)
- [2. Lay out twice: fonts blocked vs loaded](#2-lay-out-twice-fonts-blocked-vs-loaded)
- [3. Font swap or the app's own rendering?](#3-font-swap-or-the-apps-own-rendering)
- [4. Measure fallback-font metrics (never copy them)](#4-measure-fallback-font-metrics-never-copy-them)
- [5. Preload only the one font that matters](#5-preload-only-the-one-font-that-matters)

Reference for `SKILL.md` Step 3 and Step 4. All snippets run in the page (DevTools console,
or Playwright's `page.evaluate` / `page.addInitScript`).

## 1. Record every shift and what moved

Install before the page's own scripts run (`page.addInitScript` in Playwright), then read
`window.__shifts` after load:

```js
window.__shifts = [];
new PerformanceObserver((list) => {
  for (const e of list.getEntries()) {
    window.__shifts.push({
      t: Math.round(e.startTime),
      value: +e.value.toFixed(4),
      recentInput: e.hadRecentInput,          // excluded from CLS; suspicious if nothing was tapped
      fonts: document.fonts.status,           // "loading" vs "loaded" at the moment of the shift
      moved: e.sources.map((s) => ({
        node: s.node?.nodeName + (s.node?.id ? "#" + s.node.id : "") +
              (s.node?.className ? "." + String(s.node.className).split(" ")[0] : ""),
        from: s.previousRect.height, to: s.currentRect.height,
        dy: s.currentRect.y - s.previousRect.y,
      })),
    });
  }
}).observe({ type: "layout-shift", buffered: true });
```

`fonts: "loading"` at shift time points at a font swap; `"loaded"` points at the app's own
rendering (step 3 below).

## 2. Lay out twice: fonts blocked vs loaded

Any element whose height differs between the two layouts will shift when the font swaps in.

```js
// Playwright (Node)
const SEL = "header, nav, main > *, [class*=bar], [class*=row]";   // adjust to the page
async function heights(page) {
  // Key by tag + first class + occurrence so an extra element in one run doesn't misalign the rest
  return page.$$eval(SEL, (els) => {
    const seen = {};
    return Object.fromEntries(els.map((el) => {
      const base = `${el.tagName}.${String(el.className).split(" ")[0]}`;
      seen[base] = (seen[base] || 0) + 1;
      return [`${base}#${seen[base]}`, Math.round(el.getBoundingClientRect().height)];
    }));
  });
}

for (const width of [375, 960, 1280]) {
  const blocked = await browser.newPage({ viewport: { width, height: 900 } });
  await blocked.route(/\.(woff2?|ttf|otf)(\?.*)?$/, (r) => r.abort());
  await blocked.goto(URL); await blocked.waitForLoadState("networkidle");
  const a = await heights(blocked);

  const loaded = await browser.newPage({ viewport: { width, height: 900 } });
  await loaded.goto(URL); await loaded.evaluate(() => document.fonts.ready.then(() => true));
  const b = await heights(loaded);

  for (const [key, h] of Object.entries(a)) {
    if (key in b && b[key] !== h) console.log(width, key, h, "→", b[key]);
  }
}
```

The usual result is a header, toolbar or row whose text wraps onto an extra line with the
fallback font (or stops wrapping with the web font).

## 3. Font swap or the app's own rendering?

Shifts recorded with `document.fonts.status === "loaded"` are not font swaps. Common app
causes: a "Loading…" frame rendered before synchronous local data is read; status text whose
length changes the height of a wrapping container; content inserted above the fold after
fetch. Fix those in the app — no font change will help.

## 4. Measure fallback-font metrics (never copy them)

Run in a page where the web font has loaded. Use the app's own text, per weight:

```js
async function fallbackMetrics(family, weight, fallback = "Arial", sample) {
  await document.fonts.load(`${weight} 100px "${family}"`);
  const ctx = document.createElement("canvas").getContext("2d");
  const m = (f) => { ctx.font = `${weight} 100px ${f}`; return ctx.measureText(sample); };
  const web = m(`"${family}"`), fb = m(fallback);
  const sizeAdjust = web.width / fb.width;
  return {
    "size-adjust": (sizeAdjust * 100).toFixed(1) + "%",
    // overrides are scaled by size-adjust, so divide it back out
    "ascent-override":  (web.fontBoundingBoxAscent  / 100 / sizeAdjust * 100).toFixed(1) + "%",
    "descent-override": (web.fontBoundingBoxDescent / 100 / sizeAdjust * 100).toFixed(1) + "%",
    "line-gap-override": "0%",
  };
}
// fallbackMetrics("Barlow", 600, "Arial", document.querySelector("header").innerText)
```

Then declare one fallback face per weight and put it right after the web font in the stack:

```css
@font-face {
  font-family: "Barlow Fallback";
  src: local("Arial"), local("Liberation Sans"), local("Helvetica");
  font-weight: 600;
  size-adjust: 93.4%; ascent-override: 106.9%; descent-override: 21.4%; line-gap-override: 0%;
}
body { font-family: "Barlow", "Barlow Fallback", sans-serif; }
```

(Example values only.) Liberation Sans has Arial's metrics, so the same numbers hold on Linux.
Condensed families land far from Arial (≈70% in the tested case) — still worth matching.

**Verify by effect:** re-run section 2. The heights should now match at every width; if one
still differs, that element's text uses a weight or family you did not cover.

## 5. Preload only the one font that matters

If one font is still late on the critical text, preload that single file. Build tools hash
filenames, so emit the `<link rel="preload" as="font" type="font/woff2" crossorigin>` from a
small build step that reads the manifest. Preloading every weight delayed first paint by about
250 ms in the tested case, with no CLS gain over metric-matched fallbacks.
