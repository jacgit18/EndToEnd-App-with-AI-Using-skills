#!/usr/bin/env bash
# PostToolUse (Write|Edit|MultiEdit): refresh the generated table of contents of a project doc just edited.
# Rule: ~/.claude/rules/document-toc.md. Only .md files under DevHiveMind/Projects; never fails the tool call.
f=$(node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{console.log(JSON.parse(s).tool_input.file_path||"")}catch{console.log("")}})')
case "$f" in
  /home/jac/Videos/DevHiveMind/Projects/*.md)
    case "$f" in */archive/*|*/images/*) exit 0;; esac
    node "$HOME/.claude/scripts/doc-toc.mjs" "$f" >/dev/null 2>&1 ;;
esac
exit 0
