// Run: DIST=/abs/path/to/dist node fixture-server.mjs   (listens on 0.0.0.0:4173, fixture data only)
// Serves the production dist like Caddyfile.prod (SPA fallback + its headers) with FIXTURE /api data.
import http from "node:http"; import fs from "node:fs"; import path from "node:path";
const dist = process.env.DIST; // absolute path to the production build, e.g. /path/to/app/frontend/dist
if (!dist) throw new Error("set DIST to the production build folder");
const types = { ".js": "text/javascript", ".html": "text/html; charset=utf-8", ".css": "text/css", ".svg": "image/svg+xml" };
const m = new Date(); const cur = `${m.getFullYear()}-${String(m.getMonth()+1).padStart(2,"0")}`;
const recent = [
 {id:5,date:`${cur}-12`,description:"Coffee",amount:"-4.50",account_id:1,category_id:1},
 {id:4,date:`${cur}-10`,description:"Groceries",amount:"-82.10",account_id:1,category_id:2},
 {id:3,date:`${cur}-05`,description:"Paycheck",amount:"2500.00",account_id:1,category_id:3}];
const dash = {month:cur,income:"2500.00",expense:"86.60",net:"2413.40",categories:[
 {category_id:1,name:"Dining",actual:"4.50",budget:"50.00"},{category_id:2,name:"Groceries",actual:"82.10",budget:"60.00"},{category_id:null,name:"Uncategorized",actual:"0.00",budget:null}],recent};
const trend = {month:cur,points:[-120,300,50,900,-40,2413.4].map((n,i)=>({month:`m${i}`,net:n.toFixed(2)}))};
http.createServer((req,res)=>{
 const u = new URL(req.url,"http://x"); const h = {"X-Content-Type-Options":"nosniff","X-Frame-Options":"DENY","Referrer-Policy":"same-origin"};
 if (u.pathname==="/api/dashboard") { res.writeHead(200,{...h,"content-type":"application/json"}); return res.end(JSON.stringify(dash)); }
 if (u.pathname==="/api/dashboard/trend") { res.writeHead(200,{...h,"content-type":"application/json"}); return res.end(JSON.stringify(trend)); }
 const acc=[{id:1,name:"Checking",type:"checking",starting_balance:"1000.00",balance:"3413.40",is_archived:false,created_at:"2026-01-01T00:00:00Z"}];
 const cat=[{id:1,name:"Dining",kind:"expense",is_archived:false,created_at:"2026-01-01T00:00:00Z"},{id:2,name:"Groceries",kind:"expense",is_archived:false,created_at:"2026-01-01T00:00:00Z"},{id:3,name:"Salary",kind:"income",is_archived:false,created_at:"2026-01-01T00:00:00Z"}];
 const bud=[{id:1,category_id:1,month:cur,amount:"50.00"},{id:2,category_id:2,month:cur,amount:"60.00"}];
 const txs=recent.map(t=>({...t,type:"manual",reverses_transaction_id:null,created_at:"2026-10-01T00:00:00Z"}));
 const imps=[{id:1,filename:"bank.csv",account_id:1,imported_count:3,skipped_count:0,rejected_count:0,created_at:"2026-10-01T00:00:00Z"}];
 const data={"/api/accounts":acc,"/api/categories":cat,"/api/budgets":bud,"/api/transactions":txs,"/api/imports":imps,"/health":{status:"ok",db:"connected"}};
 if (data[u.pathname]) { res.writeHead(200,{...h,"content-type":"application/json"}); return res.end(JSON.stringify(data[u.pathname])); }
 if (u.pathname.startsWith("/api")||u.pathname==="/health") { res.writeHead(200,{...h,"content-type":"application/json"}); return res.end("[]"); }
 let f = path.join(dist,u.pathname); if (!f.startsWith(dist)||!fs.existsSync(f)||fs.statSync(f).isDirectory()) f = path.join(dist,"index.html");
 res.writeHead(200,{...h,"content-type":types[path.extname(f)]??"application/octet-stream"}); fs.createReadStream(f).pipe(res);
}).listen(4173,"0.0.0.0");
