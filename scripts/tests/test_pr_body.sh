#!/usr/bin/env bash
# PR description script: .github/pr-kit.json and the PR template agree, and the audience is inferred as documented.
. "$(dirname "$0")/lib.sh"

PB="$SCRIPTS/pr-body.mjs"
command -v node >/dev/null 2>&1 || { echo "SKIP  node not installed"; exit 0; }
js() { run node --input-type=module -e "import * as m from '$PB'; $1"; }

t_labels_have_boxes() {
  js "const c = m.loadConfig('$REPO/.github/pr-kit.json'); const t = (await import('node:fs')).readFileSync('$REPO/.github/pull_request_template.md','utf8');
      const sec = t.match(/## Audience[\s\S]*?(?=\n## |\$)/)[0].split('\n').filter(l => /^- \[ \]/.test(l));
      for (const l of Object.values(m.labelsOf(c))) { const n = sec.filter(x => x.includes(l)).length; if (n !== 1) { console.log('label ' + l + ' has ' + n + ' boxes'); process.exit(1); } }
      console.log('ok')"
  assert_status "$RC" 0 "every audience label has exactly one box"; assert_contains "$OUT" ok
}
case_ "pr-kit.json: every audience label has exactly one box in the template" t_labels_have_boxes

t_infer() {
  js "const c = m.loadConfig('$REPO/.github/pr-kit.json');
      console.log(m.inferAudience(['README.md', 'scripts/x.sh'], {}, c).audience, m.inferAudience(['server/admin.ts', 'src/App.tsx'], {}, c).audience, m.inferAudience(['src/App.tsx'], {}, c).audience, m.inferAudience(['src/features.ts','src/App.tsx'], {'src/features.ts': \"+  x: 'admin',\"}, c).audience)"
  assert_contains "$OUT" "na admin everyone admin"
}
case_ "inferAudience: docs only is n/a, admin guard or entry is admin, other source is everyone" t_infer

t_body() {
  js "const c = m.loadConfig('$REPO/.github/pr-kit.json'); const t = (await import('node:fs')).readFileSync('$REPO/.github/pull_request_template.md','utf8');
      const b = m.buildBody(t, 'admin', 'Does it.', false, '', c); console.log(b.split('\n').filter(l => /^- \[x\]/i.test(l)).length)"
  assert_contains "$OUT" "2" "one Audience box plus the auto-ticked Lighthouse line"
}
case_ "buildBody: ticks one Audience box and the Lighthouse n/a line for a non-UI change" t_body

finish
