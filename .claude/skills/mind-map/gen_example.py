import json, math
D="iron-log/docs/"
def adr(n,slug,label): return f"[[{D}architecture/decisions/{n}-{slug}|{label}]]"
fm=f"[[{D}feature-map|feature map]]"
dr=f"[[{D}backend-data-rules|data rules]]"
R=[ # (title,color,leaves)
("Product & features","4",[
 "**Five tabs**: Board · Daily · Progress · Program · Settings",
 "**Weekly board**: 7 columns. Card day = program day → moved → swapped order → rest-day shift",
 "**Logging**: a check-off writes an `auto` entry; a hand-logged session replaces it; undo restores both",
 "**Training logic**: 5 phases, targets, progression, stall, back-off, repeat-day suggestions (`planFix`)",
 "**Also**: stretches, supplements & water, medical, body weight, timers, muscle map",
 f"{fm} · 21 documented conflicts (C1–C21)",
 "New accounts start clean: "+adr("016","new-account-starting-state","ADR 016"),
]),
("Client (PWA)","5",[
 "React 19 + Vite PWA, installed on the phone",
 "TypeScript `strict` ("+adr("005","language-typescript-node","ADR 005")+")",
 "Works offline ~2 days: persisted save queue, replay on reconnect",
 "`src/shared/` holds framework-free code used by client and `server/` ("+adr("015","shared-code-layout","ADR 015")+")",
 "Release flag **API sync** (`VITE_API_SYNC`); admin-only feature registry (`src/features.ts`)",
]),
("Sync","6",[
 "Server-versioned rows, per-user `seq` cursor ("+adr("003","sync-versioned-rows","ADR 003")+")",
 "Tombstones (`deleted_at`) so a merge tells *removed* from *never seen*",
 "Stale edit refused; server returns the current row",
 "One **command** per user action, one transaction, cross-row rules enforced there",
 "Refused write is quarantined on device, visible and exportable, **never dropped**",
 "`import-legacy`: one-time upload, empty account only, dedupe by client id",
]),
("Backend API","1",[
 "Own API in Docker, not Firebase/Supabase ("+adr("001","backend-shape","ADR 001")+")",
 "Express 5, thin routes ("+adr("007","web-framework-express","ADR 007")+")",
 "Command endpoints over JSON HTTP + one pull endpoint ("+adr("008","api-style-commands-json-http","ADR 008")+")",

 "Kysely, raw `sql` escape hatch, generated types ("+adr("009","data-access-kysely","ADR 009")+")",
 "Server is authoritative: re-validates every rule in "+dr,
]),
]
L=[
("Data (Neon Postgres)","3",[
 "Neon Postgres, database-first ("+adr("002","datastore-neon-postgres","ADR 002")+")",
 f"13 tables: users, config, programs, library_items, log_entries, body_entries, weeks, stretch_weeks, list_items, supplement_days, row_history, refused_writes, share_grants · [[{D}data-model/iron-log|data model]]",
 "`jsonb` for config, programs, week maps, per-set detail; each has `schema_version`",
 "dbmate plain-SQL migrations ("+adr("012","migrations-dbmate","ADR 012")+")",
 "Weights stored in pounds, `numeric` 4 dp ("+adr("006","weight-unit-canonical-lb","ADR 006")+")",
 "Local calendar dates, Sunday-start week ("+adr("011","date-and-week-policy","ADR 011")+")",
 "`row_history` filled by one trigger; ≥90 days kept",
]),
("Auth & security","2",[
 "Better Auth in our API, Google login first ("+adr("004","auth-better-auth","ADR 004")+")",
 "Flat ownership; Postgres **row-level security** on `user_id`",
 "API connects as non-owner `ironlog_app`; refuses to run as owner in production",
 "CSRF guard + `Secure` `HttpOnly` `SameSite` cookies; same origin so no CORS",
 f"[[{D}security-audit/run-1/REPORT|Security audit run-1]]: no critical/high/medium; 2 low, 5 open leads",
]),
("Hosting & ops","2",[
 "Google Cloud Run serves API + PWA on one origin ("+adr("010","hosting-cloud-run","ADR 010")+")",
 "`max-instances=1` + budget alert as the spend guard; Render free as fallback",
 f"[[{D}deploy-runbook|Deploy runbook]] + `scripts/deploy-cloud-run.sh`",
 "Cloud Logging + own client-error endpoint ("+adr("013","error-reporting-cloud-logging","ADR 013")+")",
 "Backups: scheduled `pg_dump`, rehearsed restore; jobs for history pruning & tombstone purge",
]),
("Quality & process","6",[
 "Vitest + real Postgres in a throwaway container ("+adr("014","backend-test-tooling","ADR 014")+")",
 "Playwright e2e + axe accessibility checks",
 f"[[{D}architecture/failure-modes/sync|Failure-mode register]]: FM-01…24, hub is FM-02 (queue drops a write)",
 "Reconciliation invariant: after flush + pull, phone rows == server rows; ≤1 check-off per card & week",
 f"Docs: [[{D}architecture/stack-walkthrough|stack walkthrough]] · [[{D}build-spec|build spec]] · [[{D}backlog|backlog]]",
]),
]
nodes=[];edges=[]
def h(t,w=330):
    lines=sum(max(1,math.ceil(len(seg)/ (w/8.2))) for seg in t.split("\n"))
    return max(70, 36+lines*26)
LW=360; HW=250; GAP=30; BGAP=90
cid="center"
nodes.append(dict(id=cid,type="text",text="# Iron Log\nGym-training PWA going multi-user.\n**Top priority:** no lost workout.",x=-190,y=-90,width=380,height=180,color="5"))
def side(branches,sign):
    sizes=[]
    for t,c,lv in branches:
        hs=[h(x,LW-30) for x in lv]; sizes.append((hs,sum(hs)+GAP*(len(hs)-1)))
    total=sum(s for _,s in sizes)+BGAP*(len(sizes)-1)
    y=-total/2
    for bi,((t,c,lv),(hs,tot)) in enumerate(zip(branches,sizes)):
        hid=f"{'r' if sign>0 else 'l'}{bi}"
        hx=sign*330 if sign>0 else -330-HW
        nodes.append(dict(id=hid,type="text",text=f"## {t}",x=int(hx),y=int(y+tot/2-35),width=HW,height=70,color=c))
        edges.append(dict(id=f"e-{hid}",fromNode=cid,fromSide="right" if sign>0 else "left",toNode=hid,toSide="left" if sign>0 else "right",color=c))
        lx=int(hx+HW+90) if sign>0 else int(hx-90-LW)
        yy=y
        for i,(x,hh) in enumerate(zip(lv,hs)):
            lid=f"{hid}n{i}"
            nodes.append(dict(id=lid,type="text",text=x,x=lx,y=int(yy),width=LW,height=hh,color=c))
            edges.append(dict(id=f"e-{lid}",fromNode=hid,fromSide="right" if sign>0 else "left",toNode=lid,toSide="left" if sign>0 else "right",color=c))
            yy+=hh+GAP
        y+=tot+BGAP
side(R,1);side(L,-1)
out="/home/jac/Videos/DevHiveMind/iron-log/docs/architecture/Iron Log Design Mind Map.canvas"
json.dump(dict(nodes=nodes,edges=edges),open(out,"w"),indent=1)
print(len(nodes),len(edges))
