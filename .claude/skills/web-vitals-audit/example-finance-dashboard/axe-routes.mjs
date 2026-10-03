import { chromium } from "playwright-core"; import AxeBuilder from "@axe-core/playwright";
const b = await chromium.launch({ executablePath: process.env.CHROME_PATH, args:["--no-sandbox"] });
for (const route of ["/","/dashboard","/accounts","/categories","/budgets","/import","/login"]) for (const w of [1280,320]) {
  const p = await (await b.newContext({ viewport:{width:w,height:900} })).newPage();
  await p.goto("http://127.0.0.1:4180"+route, {waitUntil:"networkidle"}); await p.waitForTimeout(500);
  const r = await new AxeBuilder({page:p}).withTags(["wcag2a","wcag2aa","wcag21a","wcag21aa","wcag22aa","wcag2aaa","best-practice"]).analyze();
  const sw = await p.evaluate(()=>document.documentElement.scrollWidth);
  console.log(route,w+"px","violations:",r.violations.length,"scrollWidth",sw, "h1:",await p.locator("h1").count(),"main:",await p.locator("main").count());
  for (const v of r.violations) console.log("   ",v.id,v.impact,v.nodes.length+" nodes |",v.help);
}
await b.close();
