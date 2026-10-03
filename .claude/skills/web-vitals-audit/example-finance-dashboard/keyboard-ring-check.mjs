import { chromium } from "playwright-core"; import AxeBuilder from "@axe-core/playwright";
const B="http://127.0.0.1:4180"; const ROUTES=["/","/dashboard","/accounts","/categories","/budgets","/import","/login"];
const b = await chromium.launch({ executablePath: process.env.CHROME_PATH, args:["--no-sandbox"] });
const json=(s,x)=>({status:s,contentType:"application/json",body:JSON.stringify(x)});
console.log("== keyboard: every focusable element reached by Tab, with a visible ring");
for (const r of ROUTES) {
  const ctx=await b.newContext({viewport:{width:1280,height:900}}); const p=await ctx.newPage(); await p.goto(B+r,{waitUntil:"networkidle"});
  const total = await p.evaluate(()=>{const els=[...document.querySelectorAll("a[href],button:not([disabled]),input:not([type=hidden]):not([disabled]),select:not([disabled]),textarea,[tabindex='0']")].filter(e=>e.getBoundingClientRect().width>0); els.forEach((e,i)=>e.setAttribute("data-k",i)); return els.length});
  const reached=new Set(); const bad=[];
  for (let i=0;i<total*4;i++){ await p.keyboard.press("Tab"); const k=await p.evaluate(()=>{const e=document.activeElement;if(!e||!e.dataset.k)return null;const cs=getComputedStyle(e);return {k:e.dataset.k,n:e.tagName+":"+(e.getAttribute("aria-label")||e.textContent||"").trim().slice(0,14),ok:cs.outlineStyle!=="none"&&parseFloat(cs.outlineWidth)>=2}}); if(k){reached.add(k.k); if(!k.ok)bad.push(k.n);} }
  console.log(`${reached.size===total&&!bad.length?"ok  ":"FAIL"} ${r}: ${reached.size}/${total} reached, focus ring missing/thin on: ${bad.length?bad.join(" | "):"none"}`);
  await ctx.close();
}
console.log("\n== forced colors + dark scheme screenshots");
for (const [name,opts] of [["forced",{forcedColors:"active",colorScheme:"dark"}],["dark",{colorScheme:"dark"}]]) { const ctx=await b.newContext({viewport:{width:1000,height:900},...opts}); const p=await ctx.newPage(); await p.goto(B+"/dashboard",{waitUntil:"networkidle"}); await p.screenshot({path:`shot-${name}2.png`,clip:{x:0,y:280,width:1000,height:600}}); await ctx.close(); }
console.log("done");
console.log("\n== import: single-account run to the result panel");
{ const ctx=await b.newContext({viewport:{width:1280,height:900}}); const p=await ctx.newPage();
  await p.route("**/api/imports/preview",r=>r.fulfill(json(200,{headers:["Date","Amount","Memo"],rows:[["2026-10-01","-4.50","Coffee"]],row_count:1,delimiter:",",distinct_values:{}})));
  await p.route("**/api/imports",r=>r.request().method()==="POST"?r.fulfill(json(201,{batch_id:2,imported_count:1,skipped_count:0,rejected_count:1,excluded_count:0,rejected:[{line:3,reason:"Bad date"}],batches:[{batch_id:2,account_id:1,imported_count:1,skipped_count:0,rejected_count:1}]})):r.fallback());
  await p.goto(B+"/import",{waitUntil:"networkidle"}); await p.locator("input[type=file]").setInputFiles({name:"b.csv",mimeType:"text/csv",buffer:Buffer.from("x")}); await p.getByText("Coffee").first().waitFor();
  await p.getByLabel(/date column/i).selectOption("Date"); await p.getByLabel(/amount column/i).selectOption("Amount"); await p.getByLabel(/description column/i).selectOption("Memo"); await p.getByLabel(/date format/i).selectOption({index:1});
  await p.locator("label:has-text('Account') select").selectOption({index:1});
  const btn=p.getByRole("button",{name:/^import$/i}); console.log("Import button enabled:",await btn.isEnabled()); await btn.click(); await p.getByText("Import finished").waitFor({timeout:4000}).catch(()=>console.log("result panel did not appear"));
  console.log("result panel shown:",await p.getByText("Import finished").count()>0,"| rejected row listed:",await p.getByText(/Bad date/).count()>0);
  for (const w of [1280,320]) { await p.setViewportSize({width:w,height:900}); const r=await new AxeBuilder({page:p}).withTags(["wcag2a","wcag2aa","wcag21aa","wcag22aa","wcag2aaa","best-practice"]).analyze(); const sw=await p.evaluate(()=>document.documentElement.scrollWidth); console.log(`result panel @${w}: axe ${r.violations.length?r.violations.map(v=>v.id).join(","):"clean"}, scrollWidth ${sw}`); }
  await ctx.close(); }
await b.close();
