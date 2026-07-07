# Agent Guidance (Cursor / Codex)

This repo's primary content — agents, skills, MCP connectors — is authored for
Claude (Cowork plugins + Managed Agents). See [`CLAUDE.md`](./CLAUDE.md) for
the canonical repository layout and the `vertical-plugins/` → `agent-plugins/`
sync workflow; that stays the single source of truth for skill content.

This file documents an **additive, opt-in compatibility layer** that lets
Cursor and Codex use the same skills and system prompts. Nothing under
`plugins/`, `.claude-plugin/`, or `managed-agent-cookbooks/` is modified by
this layer — it only adds `.cursor/`, `.codex/`, and `.agents/`.

## What's ported so far

All 10 named agents under `plugins/agent-plugins/` have Cursor and Codex
subagent files. `claude-for-msft-365-install/` and `managed-agent-cookbooks/`
are out of scope (Claude Managed Agents API is a hosted runtime with no
Cursor/Codex equivalent).

| Agent | Cursor | Codex | Access |
|---|---|---|---|
| pitch-agent | `.cursor/agents/pitch-agent.md` | `.codex/agents/pitch-agent.toml` | read/write/edit |
| market-researcher | `.cursor/agents/market-researcher.md` | `.codex/agents/market-researcher.toml` | read/write/edit |
| earnings-reviewer | `.cursor/agents/earnings-reviewer.md` | `.codex/agents/earnings-reviewer.toml` | read/write/edit |
| meeting-prep-agent | `.cursor/agents/meeting-prep-agent.md` | `.codex/agents/meeting-prep-agent.toml` | read/write (no edit) |
| model-builder | `.cursor/agents/model-builder.md` | `.codex/agents/model-builder.toml` | read/write/edit |
| valuation-reviewer | `.cursor/agents/valuation-reviewer.md` | `.codex/agents/valuation-reviewer.toml` | **read-only** |
| gl-reconciler | `.cursor/agents/gl-reconciler.md` | `.codex/agents/gl-reconciler.toml` | **read-only** |
| month-end-closer | `.cursor/agents/month-end-closer.md` | `.codex/agents/month-end-closer.toml` | **read-only** |
| statement-auditor | `.cursor/agents/statement-auditor.md` | `.codex/agents/statement-auditor.toml` | **read-only** |
| kyc-screener | `.cursor/agents/kyc-screener.md` | `.codex/agents/kyc-screener.toml` | **read-only** |

The read-only ones aren't a downgrade — their Claude `tools:` list is already
`Read, Grep, Glob` with no `Write`, because in the Claude source only a
nested subagent (the "publisher"/"escalator"/"resolver") holds write access.
This port only carries over the top-level orchestrator prompt, so
`readonly: true` / `sandbox_mode = "read-only"` faithfully matches that scope
rather than tightening or loosening it.

Skills: `plugins/agent-plugins/*/skills/*` (31 unique skills across all 10
agents, de-duplicated) → `.cursor/skills/*` and `.agents/skills/*`.

MCP: `plugins/vertical-plugins/financial-analysis/.mcp.json` →
`.cursor/mcp.json` and `.codex/config.toml`. `mcp__capiq__*` in the Claude
agent prose maps to the `sp-global` server here (CapIQ is an S&P Capital IQ
product; the vertical's `.mcp.json` names the server `sp-global`, not
`capiq`). Several agents also reference internal firm systems with no server
definition anywhere in this repo on the Claude side either — `crm`
(meeting-prep-agent), `portfolio` (valuation-reviewer), `internal-gl` /
`subledger` (gl-reconciler, month-end-closer), `nav` (statement-auditor),
`screening` (kyc-screener). Each agent's `.cursor/agents/*.md` and
`.codex/agents/*.toml` says so explicitly — bring your own MCP server for
those before the agent can actually pull that data.

## Why the file formats differ

Claude, Cursor, and Codex don't share a subagent file format, so each agent is
translated by hand rather than shared verbatim:

- **Skills** (`SKILL.md` with `name` + `description` frontmatter) are the one
  format all three already agree on — these are copied byte-for-byte, no
  translation needed.
- **Subagents** are NOT shared: Claude uses `name`/`description`/`tools` in
  `agents/<slug>.md`; Cursor uses `name`/`description`/`model`/`readonly`/
  `is_background` in `.cursor/agents/<slug>.md` (no `tools:` field — Cursor
  has no tool allow-list at the subagent level); Codex uses
  `name`/`description`/`developer_instructions` in `.codex/agents/<slug>.toml`.
  Each `.cursor/agents/*.md` and `.codex/agents/*.toml` in this repo is a
  hand-adapted copy of the matching Claude `agents/<slug>.md` — if you edit
  the agent's behavior, update all three.
- **MCP** connectors use the same `mcpServers` shape in Claude's `.mcp.json`
  and Cursor's `.cursor/mcp.json`, but Codex uses a different file
  (`.codex/config.toml`, `[mcp_servers.<name>]` tables). None of the servers
  here are bundled/functional out of the box — each is a third-party
  financial-data vendor (Daloopa, Factset, Moody's, LSEG, S&P Global, etc.)
  that requires the user's own paid entitlement and credentials.

## Extending this to another agent

1. Read the Claude source: `plugins/agent-plugins/<slug>/agents/<slug>.md`.
2. Write `.cursor/agents/<slug>.md` (frontmatter: `name`, `description`,
   `model: inherit`, `readonly`, `is_background`; fold any `tools:`
   restriction into prose under an "Access" heading).
3. Write `.codex/agents/<slug>.toml` (`name`, `description`,
   `developer_instructions` — the same prose as the Cursor version).
4. Run `python3 scripts/sync-crosstool-skills.py` to copy that agent's
   bundled skills into `.cursor/skills/` and `.agents/skills/`.
5. If the agent needs MCP servers not already in `.cursor/mcp.json` /
   `.codex/config.toml`, add them from the relevant
   `plugins/vertical-plugins/*/.mcp.json`.
6. Run `python3 scripts/check.py` — it validates both the Claude-native tree
   and this compatibility layer (frontmatter, TOML/JSON syntax, skill drift).

## Known upstream issue found while building this

`plugins/vertical-plugins/financial-analysis/.mcp.json` has a JSON syntax
error (missing comma/brace after the `egnyte` entry). `scripts/check.py` does
not currently lint `.mcp.json` files, so it wasn't caught. `.cursor/mcp.json`
and `.codex/config.toml` were written with the corrected server list rather
than propagating the bug — the Claude-native file itself was left untouched.
