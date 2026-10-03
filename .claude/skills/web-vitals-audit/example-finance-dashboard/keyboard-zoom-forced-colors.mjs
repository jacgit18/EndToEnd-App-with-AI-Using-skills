import { chromium } from "playwright-core"; import AxeBuilder from "@axe-core/playwright";
const B="http://127.0.0.1:4180"; const ROUTES=["/","/dashboard","/accounts","/categories","/budgets","/import","/login"];
const b = await chromium.launch({ executablePath: process.env.CHROME_PATH, args:["--no-sandbox"] });
const json=(s,x)=>({status:s,contentType:"application/json",body:JSON.stringify(x)});
console.log("== third-party requests (origins other than the app)");
for (const r of ROUTES) { const ctx=await b.newContext(); const p=await ctx.newPage(); const o=new Set(); p.on("request",q=>o.add(new URL(q.url()).origin)); await p.goto(B+r,{waitUntil:"networkidle"}); console.log(r, [...o].join(", ")); await ctx.close(); }
console.log("\n== keyboard: Tab order, focus indicator, traps (1280px)");
for (const r of ROUTES) {
  const ctx=await b.newContext({viewport:{width:1280,height:900}}); const p=await ctx.newPage(); await p.goto(B+r,{waitUntil:"networkidle"});
  const total = await p.evaluate(()=>[...document.querySelectorAll("a[href],button:not([disabled]),input:not([type=hidden]):not([disabled]),select:not([disabled]),textarea,[tabindex='0']")].filter(e=>e.getBoundingClientRect().width>0).length);
  const seen=[]; let noRing=[];
  for (let i=0;i<total+3;i++){ await p.keyboard.press("Tab"); const info=await p.evaluate(()=>{const e=document.activeElement;if(!e||e===document.body)return null;const cs=getComputedStyle(e);return {id:e.tagName+":"+(e.getAttribute("aria-label")||e.textContent||e.name||"").trim().slice(0,18),ring:cs.outlineStyle!=="none"&&parseFloat(cs.outlineWidth)>0,w:cs.outlineWidth,st:cs.outlineStyle,col:cs.outlineColor}}); if(info){ if(seen.includes(info.id)&&seen.length>=total)break; seen.push(info.id); if(!info.ring) noRing.push(info.id);} }
  const unique=new Set(seen).size;
  console.log(`${r}: ${total} focusable, ${unique} reached by Tab, no visible outline on: ${noRing.length?noRing.join(" | "):"none"}`);
  if (r==="/dashboard"){ const i=await p.evaluate(()=>{const e=document.querySelector("a");e.focus();const cs=getComputedStyle(e);return [cs.outlineStyle,cs.outlineWidth,cs.outlineColor].join(" ")}); console.log("   sample focus outline (link):",i); }
  await ctx.close();
}
console.log("\n== 200% text (html font-size 200%) + axe, and sideways scroll");
for (const r of ROUTES) for (const w of [1280,640]) {
  const ctx=await b.newContext({viewport:{width:w,height:900}}); const p=await ctx.newPage(); await p.goto(B+r,{waitUntil:"networkidle"});
  await p.addStyleTag({content:"html{font-size:200% !important}"}); await p.waitForTimeout(200);
  const sw=await p.evaluate(()=>document.documentElement.scrollWidth); const clipped=await p.evaluate(()=>[...document.querySelectorAll("body *")].filter(e=>{const cs=getComputedStyle(e);return (cs.overflow==="hidden"||cs.overflowY==="hidden")&&e.scrollHeight>e.clientHeight+2&&!(e.style.position==="absolute")}).length);
  const v=(await new AxeBuilder({page:p}).withTags(["wcag2a","wcag2aa","wcag21aa","wcag22aa","wcag2aaa"]).analyze()).violations.map(x=>x.id);
  console.log(`${sw<=w&&!clipped&&!v.length?"ok  ":"FAIL"} ${r} @${w}: scrollWidth ${sw}, clipped boxes ${clipped}, axe ${v.length?v.join(","):"clean"}`);
  if (r==="/accounts"&&w===640) await p.screenshot({path:"shot-200-accounts.png",fullPage:true});
  await ctx.close();
}
console.log("\n== forced colors");
{ const ctx=await b.newContext({viewport:{width:1000,height:1100},forcedColors:"active",colorScheme:"dark"}); const p=await ctx.newPage(); await p.goto(B+"/dashboard",{waitUntil:"networkidle"}); await p.screenshot({path:"shot-forced-dashboard.png",fullPage:true});
  const f=await p.evaluate(()=>({media:matchMedia("(forced-colors: active)").matches,fills:[...document.querySelectorAll("svg rect")].map(r=>getComputedStyle(r).fill)}));
  console.log("forced-colors active:",f.media,"| distinct bar fills in forced mode:",[...new Set(f.fills)].join(" ; ")); await ctx.close(); }
console.log("\n== import result + account-column mapping really shown");
{ const ctx=await b.newContext({viewport:{width:1280,height:900}}); const p=await ctx.newPage();
  await p.route("**/api/imports/preview",r=>r.fulfill(json(200,{headers:["Date","Amount","Memo","Account"],rows:[["2026-10-01","-4.50","Coffee","Checking"]],row_count:1,delimiter:",",distinct_values:{Account:["Checking","Savings"]}})));
  await p.route("**/api/imports",r=>r.request().method()==="POST"?r.fulfill(json(201,{batch_id:2,imported_count:2,skipped_count:0,rejected_count:1,excluded_count:0,rejected:[{line:3,reason:"Bad date"}],batches:[{batch_id:2,account_id:1,imported_count:2,skipped_count:0,rejected_count:1}]})):r.fallback());
  await p.goto(B+"/import",{waitUntil:"networkidle"}); await p.locator("input[type=file]").setInputFiles({name:"b.csv",mimeType:"text/csv",buffer:Buffer.from("x")}); await p.getByText("Coffee").first().waitFor();
  await p.getByLabel(/date column/i).selectOption("Date"); await p.getByLabel(/amount column/i).selectOption("Amount"); await p.getByLabel(/description column/i).selectOption("Memo"); await p.getByLabel(/date format/i).selectOption({index:1});
  await p.locator("label:has(input[type=radio])").nth(1).click(); const before=await p.locator("select").count();
  await p.locator("select").filter({has:p.locator("option",{hasText:"Account"})}).last().selectOption("Account").catch(()=>{}); const after=await p.locator("select").count();
  const v=(await new AxeBuilder({page:p}).withTags(["wcag2a","wcag2aa","wcag21aa","wcag22aa","wcag2aaa","best-practice"]).analyze()).violations.map(x=>x.id);
  console.log(`selects before/after choosing account column: ${before}/${after}; axe: ${v.length?v.join(","):"clean"}`);
  await p.locator("label:has(input[type=radio])").nth(0).click(); await p.locator("select").nth(4).selectOption({index:1}).catch(()=>{});
  await p.getByRole("button",{name:/^import/i}).click().catch(()=>{}); const fin=await p.getByText(/Import finished/i).count(); console.log("'Import finished' shown:",fin>0, "| rejected line listed:", await p.getByText(/Bad date/).count()>0);
  await ctx.close(); }
console.log("\n== visible text (for the reading-level check)");
for (const r of ROUTES){ const ctx=await b.newContext(); const p=await ctx.newPage(); await p.goto(B+r,{waitUntil:"networkidle"}); const t=await p.evaluate(()=>[...new Set([...document.querySelectorAll("h1,h2,label,button,th,p,a,legend,option")].map(e=>e.textContent.trim()).filter(x=>x&&x.length<90))]); console.log(r+":",t.join(" | ")); await ctx.close(); }
await b.close();
