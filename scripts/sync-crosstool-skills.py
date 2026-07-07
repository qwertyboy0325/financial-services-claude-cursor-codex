#!/usr/bin/env python3
"""
Re-sync Cursor/Codex skill copies for every ported agent.

An agent is "ported" once it has a .cursor/agents/<slug>.md file. For each
ported agent, this copies plugins/agent-plugins/<slug>/skills/<name>/ (itself
a vendored copy of plugins/vertical-plugins/*/skills/<name>/, see
sync-agent-skills.py) into:

  .cursor/skills/<name>/   — Cursor project skills
  .agents/skills/<name>/   — Codex repo skills

Run scripts/sync-agent-skills.py first if you edited a skill in
vertical-plugins/, then run this to propagate into the cross-tool copies.

Usage: python3 scripts/sync-crosstool-skills.py
"""
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "plugins" / "agent-plugins"
CURSOR_AGENTS = ROOT / ".cursor" / "agents"
CURSOR_SKILLS = ROOT / ".cursor" / "skills"
CODEX_SKILLS = ROOT / ".agents" / "skills"

ported_slugs = sorted(p.stem for p in CURSOR_AGENTS.glob("*.md")) if CURSOR_AGENTS.is_dir() else []

synced = 0
missing: list[str] = []
for slug in ported_slugs:
    bundle = AGENTS / slug / "skills"
    if not bundle.is_dir():
        missing.append(f"plugins/agent-plugins/{slug}/skills/ (referenced by .cursor/agents/{slug}.md)")
        continue
    for src in sorted(bundle.iterdir()):
        if not src.is_dir():
            continue
        for dest_root in (CURSOR_SKILLS, CODEX_SKILLS):
            dest = dest_root / src.name
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(src, dest)
            synced += 1

print(f"synced {synced} cross-tool skill dir(s) for {len(ported_slugs)} ported agent(s)")
if missing:
    print("WARN: no bundled skills/ found for:", file=sys.stderr)
    for m in missing:
        print(f"  - {m}", file=sys.stderr)
    sys.exit(1)
