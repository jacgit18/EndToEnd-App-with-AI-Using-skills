// Compare two screenshot folders: node tools/visual-diff.mjs <before> <after> <out>
// For every PNG that changed, was added or was removed, writes <out>/before/, after/
// and diff/ copies (diff = changed pixels in red over a faded "after"), plus
// <out>/summary.json and a one-line-per-file report on stdout. Exit code is 0 either
// way; the workflow reads summary.json to decide whether to comment.
import { copyFile, mkdir, readdir, readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";

import pixelmatch from "pixelmatch";
import { PNG } from "pngjs";

const [beforeDir, afterDir, outDir] = process.argv.slice(2);
if (!beforeDir || !afterDir || !outDir) {
  console.error("usage: node tools/visual-diff.mjs <before-dir> <after-dir> <out-dir>");
  process.exit(2);
}

const pngs = async (dir) => (await readdir(dir).catch(() => [])).filter((f) => f.endsWith(".png"));
const load = async (path) => PNG.sync.read(await readFile(path));

// Pad to a common size so a page that grew taller still diffs instead of erroring.
function pad(img, width, height) {
  if (img.width === width && img.height === height) return img;
  const out = new PNG({ width, height, fill: true });
  out.data.fill(255);
  PNG.bitblt(img, out, 0, 0, img.width, img.height, 0, 0);
  return out;
}

async function main() {
  const before = new Set(await pngs(beforeDir));
  const after = new Set(await pngs(afterDir));
  const names = [...new Set([...before, ...after])].sort();
  for (const sub of ["before", "after", "diff"]) await mkdir(join(outDir, sub), { recursive: true });

  const results = [];
  for (const name of names) {
    if (!before.has(name) || !after.has(name)) {
      const status = before.has(name) ? "removed" : "added";
      const [dir, sub] = status === "added" ? [afterDir, "after"] : [beforeDir, "before"];
      await copyFile(join(dir, name), join(outDir, sub, name));
      results.push({ name, status });
      continue;
    }
    const [a, b] = await Promise.all([load(join(beforeDir, name)), load(join(afterDir, name))]);
    const width = Math.max(a.width, b.width);
    const height = Math.max(a.height, b.height);
    const diff = new PNG({ width, height });
    // threshold 0.1 = pixelmatch default; ignores anti-aliasing noise, catches real changes.
    const changed = pixelmatch(pad(a, width, height).data, pad(b, width, height).data, diff.data, width, height, { threshold: 0.1 });
    if (changed === 0 && a.height === b.height && a.width === b.width) {
      results.push({ name, status: "unchanged" });
      continue;
    }
    await copyFile(join(beforeDir, name), join(outDir, "before", name));
    await copyFile(join(afterDir, name), join(outDir, "after", name));
    await writeFile(join(outDir, "diff", name), PNG.sync.write(diff));
    results.push({ name, status: "changed", pixels: changed, percent: +((100 * changed) / (width * height)).toFixed(3) });
  }

  await writeFile(join(outDir, "summary.json"), JSON.stringify(results, null, 2) + "\n");
  for (const r of results) {
    console.log(`${r.status.padEnd(9)} ${r.name}${r.pixels ? `  (${r.pixels} px, ${r.percent}%)` : ""}`);
  }
  const touched = results.filter((r) => r.status !== "unchanged").length;
  console.log(`${touched} of ${results.length} screenshots differ`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
