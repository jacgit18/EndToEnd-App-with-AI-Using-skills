import { chromium } from "playwright-core";
const b = await chromium.launch({ executablePath: process.env.CHROME_PATH, args:["--no-sandbox"] });
for (const route of ["/","/dashboard","/accounts","/categories","/budgets","/import","/login"]) {
  const p = await (await b.newContext({ viewport:{width:1280,height:900} })).newPage();
  await p.goto("http://127.0.0.1:4180"+route,{waitUntil:"networkidle"});
  const small = await p.evaluate(()=>[...document.querySelectorAll("a,button,select,input:not([type=checkbox]):not([type=radio]),label:has(>input[type=checkbox]),[tabindex=\"0\"]")].map(e=>{const r=e.getBoundingClientRect();const t=e.tagName+(e.type?":"+e.type:"")+" "+(e.textContent||e.getAttribute("aria-label")||"").trim().slice(0,20);return {t,w:Math.round(r.width),h:Math.round(r.height)}}).filter(x=>x.w>0&&(x.w<44||x.h<44)));
  console.log(route, small.length? JSON.stringify(small.slice(0,6)):"all >=44");
}
for (const [r,n] of [["/accounts","acc"],["/","tx"]]) for (const w of [1280,320]) {
  const p = await (await b.newContext({ viewport:{width:w,height:800} })).newPage();
  await p.goto("http://127.0.0.1:4180"+r,{waitUntil:"networkidle"}); await p.screenshot({path:`shot-${n}-${w}.png`,fullPage:true});
}
await b.close();
