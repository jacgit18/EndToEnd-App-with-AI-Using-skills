#!/usr/bin/env node
// Checks that the properties (YAML frontmatter) of vault markdown docs are intact.
// Rule: /home/jac/.claude/rules/vault-properties.md
//
//   node fm-check.mjs <dir|file>...            report problems, exit 1 if any error
//   options: --skip=archive,images,node_modules,.git  --require=Purpose,Status,EditDate  --quiet
//
// Errors (break Obsidian's Properties panel or hide the block): no block on line 1,
// no closing ---, tab indent, duplicate key, an unquoted value that YAML cannot parse
// ("a: b" inside a value, a leading [[wikilink]], *, &, !, |, >, %, @, backtick),
// unbalanced quotes, a toc marker inside the block, a missing required key.
// No dependencies; a line-based check, not a full YAML parser.
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { join } from 'node:path'

const args = process.argv.slice(2)
const flag = (n, d) => (args.find(a => a.startsWith(`--${n}=`)) ?? `--${n}=${d}`).split('=')[1]
const quiet = args.includes('--quiet')
const skip = new Set(flag('skip', 'archive,images,node_modules,.git').split(','))
const required = flag('require', 'Purpose,Status,EditDate').split(',').filter(Boolean)
const targets = args.filter(a => !a.startsWith('--'))

function walk(p, out) {
  const s = statSync(p)
  if (s.isFile()) { if (p.endsWith('.md') && !p.endsWith('/CLAUDE.md')) out.push(p); return }
  for (const e of readdirSync(p)) if (!skip.has(e)) walk(join(p, e), out)
}

export function checkText(text, req = required) {
  const errs = []
  if (text.charCodeAt(0) === 0xfeff) errs.push('starts with a byte-order mark; the --- must be the first characters')
  const lines = text.replace(/^﻿/, '').split('\n')
  if (lines[0].trimEnd() !== '---') {
    errs.push('line 1 is not --- (no properties block, or something sits above it)')
    return errs
  }
  const end = lines.findIndex((l, i) => i > 0 && l.trimEnd() === '---')
  if (end < 0) { errs.push('properties block is never closed (no second ---)'); return errs }
  const keys = new Map()
  for (let i = 1; i < end; i++) {
    const l = lines[i]
    const n = i + 1
    if (!l.trim() || /^\s*#/.test(l)) continue
    if (/<!--\s*\/?toc/.test(l)) { errs.push(`line ${n}: toc marker inside the properties block`); continue }
    if (/^\t| \t/.test(l.match(/^\s*/)[0])) { errs.push(`line ${n}: tab indent (YAML needs spaces)`); continue }
    if (/^\s+-(\s|$)/.test(l)) {
      const item = l.replace(/^\s+-\s*/, '')
      const bad = scalarProblem(item)
      if (bad) errs.push(`line ${n}: list item ${bad}`)
      continue
    }
    if (/^\s/.test(l)) continue // continuation of a previous value
    const m = /^([^:]+?):(?:\s+(.*)|\s*)$/.exec(l)
    if (!m) { errs.push(`line ${n}: not "key: value" or "key:" (${l.trim().slice(0, 40)})`); continue }
    const key = m[1].trim()
    if (keys.has(key)) errs.push(`line ${n}: duplicate key "${key}" (first on line ${keys.get(key)})`)
    else keys.set(key, n)
    const val = (m[2] ?? '').trim()
    if (val) { const bad = scalarProblem(val); if (bad) errs.push(`line ${n}: ${key} ${bad}`) }
  }
  for (const k of req) if (!keys.has(k)) errs.push(`missing required property "${k}"`)
  return errs
}

// Returns a problem string for an unquoted-or-quoted scalar, or '' when it parses.
function scalarProblem(v) {
  v = v.trim()
  if (!v) return ''
  const q = v[0]
  if (q === '"' || q === "'") {
    const closeAt = q === '"' ? closingDouble(v) : v.indexOf("'", 1)
    if (closeAt < 0) return 'has an unbalanced quote'
    const rest = v.slice(closeAt + 1).trim()
    if (rest && !rest.startsWith('#')) return 'has text after the closing quote'
    return ''
  }
  if (v.startsWith('[[')) return 'starts with an unquoted [[wikilink]] (quote it: "[[note]]")'
  if (v.startsWith('[') || v.startsWith('{')) return /[\]}]\s*$/.test(v) ? '' : 'has an unclosed [ or {'
  if (/^[*&!|>%@`]/.test(v) && !/^[|>][+-]?\d*$/.test(v)) return `starts with "${v[0]}", which YAML reads as a tag, anchor or block (quote the value)`
  if (/: |:$/.test(v)) return 'has ": " inside an unquoted value (quote the value)'
  return ''
}

function closingDouble(v) {
  for (let i = 1; i < v.length; i++) { if (v[i] === '\\') i++; else if (v[i] === '"') return i }
  return -1
}

if (process.argv[1] && process.argv[1].endsWith('fm-check.mjs')) {
  const files = []
  for (const t of targets) walk(t, files)
  let bad = 0
  for (const f of files) {
    const errs = checkText(readFileSync(f, 'utf8'))
    if (errs.length) { bad++; if (!quiet) console.log(`${f}\n${errs.map(e => '  - ' + e).join('\n')}`) }
  }
  if (!quiet || bad) console.log(`${files.length} file(s) checked, ${bad} with broken or incomplete properties`)
  process.exit(bad ? 1 : 0)
}
