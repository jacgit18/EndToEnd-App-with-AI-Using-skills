#!/usr/bin/env python3
"""Toggle which catalog skills Claude sees in full, via `skillOverrides` in .claude/settings.local.json.

  profile.py core     skills listed in .claude/skills/CORE.txt stay "on"; every other catalog skill -> "name-only"
  profile.py all      remove every override for catalog skills (all skills "on")
  profile.py toggle   read the current state and flip it: any catalog skill overridden -> all; none overridden -> core
  profile.py status   show the current counts

Only keys that are catalog skill names are touched; any other settings keys and any overrides for
skills outside this catalog (plugin skills, commands) are preserved. "name-only" keeps the skill
in the `/` menu and lists only its name to Claude (no description), which frees listing budget.
"""
import glob, json, os, sys

ROOT = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
SKILLS = os.path.join(ROOT, ".claude", "skills")
SETTINGS = os.path.join(ROOT, ".claude", "settings.local.json")


def catalog():
    return sorted(os.path.basename(os.path.dirname(p)) for p in glob.glob(os.path.join(SKILLS, "*", "SKILL.md")))


def core():
    path = os.path.join(SKILLS, "CORE.txt")
    if not os.path.exists(path):
        sys.exit("profile.py: .claude/skills/CORE.txt not found")
    return [l.strip() for l in open(path) if l.strip() and not l.lstrip().startswith("#")]


def load():
    if os.path.exists(SETTINGS):
        with open(SETTINGS) as f:
            return json.load(f)
    return {}


def save(cfg):
    with open(SETTINGS, "w") as f:
        json.dump(cfg, f, indent=2)
        f.write("\n")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "status"
    names = set(catalog())
    cfg = load()
    ov = cfg.get("skillOverrides", {})
    if mode == "toggle":
        # Flip based on what is actually in settings, not on a remembered mode.
        mode = "all" if any(n in ov for n in names) else "core"
        print(f"toggle: {'some skills overridden' if mode == 'all' else 'all skills fully listed'} -> switching to {mode}")
    if mode == "core":
        keep = core()
        unknown = [k for k in keep if k not in names]
        if unknown:
            print("warning: CORE.txt names no such skill:", ", ".join(unknown), file=sys.stderr)
        for n in names:
            if n in keep:
                ov.pop(n, None)
            else:
                ov[n] = "name-only"
    elif mode == "all":
        for n in names:
            ov.pop(n, None)
    elif mode != "status":
        sys.exit(__doc__)
    if mode in ("core", "all"):
        if ov:
            cfg["skillOverrides"] = ov
        else:
            cfg.pop("skillOverrides", None)
        save(cfg)
    mine = {n: ov[n] for n in names if n in ov}
    on = len(names) - len(mine)
    print(f"catalog skills: {len(names)} | fully listed: {on} | overridden: {len(mine)} "
          f"({', '.join(sorted(set(mine.values()))) or 'none'})")
    if mode != "all":
        print("fully listed:", ", ".join(sorted(n for n in names if n not in mine)))


if __name__ == "__main__":
    main()
