import { chromium } from "playwright-core"; import AxeBuilder from "@axe-core/playwright";
const B = "http://127.0.0.1:4180";
const TAGS = ["wcag2a","wcag2aa","wcag21a","wcag21aa","wcag22aa","wcag2aaa","best-practice"];
const b = await chromium.launch({ executablePath: process.env.CHROME_PATH, args:["--no-sandbox"] });
const json = (status, body) => ({ status, contentType: "application/json", body: JSON.stringify(body) });
async function audit(page, label) {
  const r = await new AxeBuilder({page}).withTags(TAGS).analyze();
  const sw = await page.evaluate(()=>document.documentElement.scrollWidth), vw = page.viewportSize().width;
  console.log(`${r.violations.length===0&&sw<=vw?"ok  ":"FAIL"} ${label} @${vw}: ${r.violations.length} violations, scrollWidth ${sw}`);
  for (const v of r.violations) console.log("      ", v.id, v.impact, v.nodes.length, "|", v.nodes[0].target.join(" "), "|", v.help);
}
const scenarios = {
  "accounts: edit row": async p => { await p.goto(B+"/accounts",{waitUntil:"networkidle"}); await p.getByRole("button",{name:"Edit"}).first().click(); },
  "accounts: create error": async p => { await p.route("**/api/accounts",r=>r.request().method()==="POST"?r.fulfill(json(422,{detail:"Name already in use"})):r.fallback()); await p.goto(B+"/accounts",{waitUntil:"networkidle"}); await p.getByLabel("Name").first().fill("Checking"); await p.getByRole("button",{name:"Add account"}).click(); await p.getByRole("alert").first().waitFor(); },
  "accounts: bad starting balance": async p => { await p.goto(B+"/accounts",{waitUntil:"networkidle"}); await p.getByLabel("Name").first().fill("X"); await p.getByLabel(/starting balance/i).first().fill("abc"); await p.getByRole("alert").first().waitFor(); },
  "accounts: show archived": async p => { await p.goto(B+"/accounts",{waitUntil:"networkidle"}); await p.getByLabel(/show archived/i).check(); },
  "categories: edit row": async p => { await p.goto(B+"/categories",{waitUntil:"networkidle"}); await p.getByRole("button",{name:"Rename"}).first().click(); },
  "categories: create error": async p => { await p.route("**/api/categories",r=>r.request().method()==="POST"?r.fulfill(json(409,{detail:"Category exists"})):r.fallback()); await p.goto(B+"/categories",{waitUntil:"networkidle"}); await p.getByLabel("Name").first().fill("Dining"); await p.getByRole("button",{name:/add/i}).first().click(); await p.getByRole("alert").first().waitFor(); },
  "budgets: copy-forward error": async p => { await p.route("**/api/budgets/*/copy-forward",r=>r.fulfill(json(409,{detail:"Nothing to copy"}))); await p.goto(B+"/budgets",{waitUntil:"networkidle"}); await p.getByRole("button",{name:/copy/i}).click(); await p.getByRole("alert").first().waitFor(); },
  "budgets: month cleared": async p => { await p.goto(B+"/budgets",{waitUntil:"networkidle"}); await p.getByLabel("Month").fill(""); },
  "home: create error": async p => { await p.route("**/api/transactions",r=>r.request().method()==="POST"?r.fulfill(json(422,{detail:"Amount is not a number"})):r.fallback()); await p.goto(B+"/",{waitUntil:"networkidle"}); await p.getByLabel("Account",{exact:true}).selectOption({index:1}); await p.getByLabel("Amount (- for expense)").fill("1"); await p.getByLabel("Description",{exact:true}).fill("x"); await p.getByRole("button",{name:"Add"}).click(); await p.getByText("Amount is not a number").waitFor(); },
  "home: backend unreachable": async p => { await p.route("**/health",r=>r.abort()); await p.goto(B+"/",{waitUntil:"networkidle"}); await p.getByText("unreachable").waitFor(); },
  "dashboard: API error": async p => { await p.route("**/api/dashboard?*",r=>r.fulfill(json(500,{detail:"Server error"}))); await p.goto(B+"/dashboard",{waitUntil:"networkidle"}); await p.getByRole("alert").first().waitFor(); },
  "dashboard: month cleared": async p => { await p.goto(B+"/dashboard",{waitUntil:"networkidle"}); await p.getByLabel("Month").fill(""); await p.getByText("Pick a month.").waitFor(); },
  "dashboard: empty month": async p => { await p.route("**/api/dashboard?*",r=>r.fulfill(json(200,{month:"2026-10",income:"0.00",expense:"0.00",net:"0.00",categories:[],recent:[]}))); await p.goto(B+"/dashboard",{waitUntil:"networkidle"}); await p.getByText("No transactions this month.").waitFor(); },
  "login: wrong password": async p => { await p.route("**/api/auth/login",r=>r.fulfill(json(401,{detail:"Invalid email or password"}))); await p.goto(B+"/login",{waitUntil:"networkidle"}); await p.getByLabel(/email/i).fill("a@b.c"); await p.getByLabel(/password/i).fill("x"); await p.getByRole("button",{name:/sign in|log in/i}).click(); await p.getByRole("alert").waitFor(); },
};
const preview = {headers:["Date","Amount","Memo","Account"],rows:[["2026-10-01","-4.50","Coffee","Checking"],["2026-10-02","-82.10","Groceries","Savings"]],row_count:2,delimiter:",",distinct_values:{Account:["Checking","Savings"]}};
async function importFlow(p, w) {
  await p.route("**/api/imports/preview",r=>r.fulfill(json(200,preview)));
  await p.goto(B+"/import",{waitUntil:"networkidle"});
  await p.locator("input[type=file]").setInputFiles({name:"bank.csv",mimeType:"text/csv",buffer:Buffer.from("Date,Amount,Memo,Account\n2026-10-01,-4.50,Coffee,Checking\n")});
  await p.getByText("Coffee").first().waitFor(); await audit(p,"import: preview shown");
  const sel = async (re,val)=>{ await p.getByLabel(re).selectOption(val); };
  await sel(/date column/i,"Date"); await sel(/amount column/i,"Amount"); await sel(/description column/i,"Memo"); await sel(/date format/i,{index:1});
  await audit(p,"import: columns chosen");
  await p.getByLabel(/file has several accounts|several accounts|multi/i).check().catch(()=>{});
  await audit(p,"import: multi-account mode");
  await p.getByLabel(/one account|single/i).check().catch(()=>{});
}
for (const w of [1280,320]) {
  for (const [name,fn] of Object.entries(scenarios)) {
    const ctx = await b.newContext({viewport:{width:w,height:900}}); const p = await ctx.newPage();
    try { await fn(p); await audit(p,name); } catch(e) { console.log("SKIP ",name,"@"+w,"-",e.message.split("\n")[0].slice(0,110)); }
    await ctx.close();
  }
  const ctx = await b.newContext({viewport:{width:w,height:900}}); const p = await ctx.newPage();
  try { await importFlow(p,w); } catch(e) { console.log("SKIP import flow @"+w,"-",e.message.split("\n")[0].slice(0,140)); }
  await ctx.close();
}
await b.close();
