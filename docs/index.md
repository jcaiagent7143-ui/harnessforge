# harnessforge

> _The universal harness layer for AI coding agents._
> _One command turns any repo into a project where Claude Code, Cursor, Codex, Gemini CLI, Aider, OpenHarness, and any other coding agent can work productively._

```bash
uvx harnessforge init
```

## What you get

After `harness init`, your repo has a complete harness:

| File / dir | Read by |
|---|---|
| `AGENTS.md` | every coding agent that follows the OpenAI Codex CLI convention |
| `SOUL.md` | Hermes, OpenClaw, and any agent that wants personality grounding |
| `TOOLS.md` | the universal tool/MCP catalog reference |
| `MEMORY.md` | OpenHarness, and agents that follow that convention |
| `SKILLS/` | every tool that reads the [`anthropics/skills`](https://github.com/anthropics/skills) format |
| `.claude/CLAUDE.md` | Claude Code |
| `.cursor/rules` | Cursor |
| `.continue/config.json` | Continue |
| `.windsurf/rules` | Windsurf |
| `harness.config.json` | the binding to the blueprint (used by `harness sync` + `harness verify`) |
| `.harness/profile.yaml` | the canonical machine-readable description |
| `.harness/manifest.json` | hash of every file we wrote, for drift detection |

## Why this exists

→ [Why a harness layer](concepts/why-a-harness-layer.md)

## The five layers we generate

→ [The five harness layers](concepts/the-five-harness-layers.md)

## How we fit alongside Hermes, OpenClaw, OpenHarness

→ [vs. Hermes / OpenClaw / OpenHarness](concepts/vs-hermes-openclaw-openharness.md)

## Get started

→ [Quickstart](guides/quickstart.md)
