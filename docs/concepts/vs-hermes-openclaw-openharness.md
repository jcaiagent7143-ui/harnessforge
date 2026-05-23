# harnessforge vs. Hermes / OpenClaw / OpenHarness

The agent-infrastructure space settled into three patterns by May 2026. harnessforge picks a fourth lane that none of them occupies.

## The landscape

### [Hermes (Nous Research)](https://github.com/NousResearch/hermes-agent)

Standalone agent runtime with the harness *built in*. "First personal AI agent that ships with the harness already built in." Replaces Claude Code / Cursor for the autonomous-agent use case. Goes from 0 → 57k stars in six weeks (April 2026).

**Use Hermes if:** you want a personal AI agent that owns its own runtime + memory + skills, and you're not committed to a specific coding IDE.

### [OpenClaw](https://github.com/openclaw/openclaw)

Standalone Gateway daemon. Multi-channel personal assistant — WhatsApp, Telegram, Slack, Discord, iMessage. Single-user local-first. Ships its own skills under `~/.openclaw/workspace/skills/`.

**Use OpenClaw if:** you want a single-user personal assistant that talks across messaging platforms.

### [OpenHarness (HKUDS)](https://github.com/HKUDS/OpenHarness)

Runtime harness for existing agents. "The model is the agent. The code is the harness." The `oh` CLI runs your agent through a tool-call loop with permissions, skills, MCP, memory. Compatible with `anthropics/skills`.

**Use OpenHarness if:** you want a Python runtime that wraps your agent loop with permissions and skill loading.

### [OpenAI Agents SDK](https://github.com/openai/openai-agents-python) / [Mastra](https://github.com/mastra-ai/mastra)

Library / framework. Primitives for building agents in code.

**Use these if:** you're writing custom agent code from scratch and want a SDK with batteries.

### harnessforge

**Provisioning harness.** One command — `uvx harnessforge init` — inspects your repo, picks a blueprint, generates `AGENTS.md` + `SOUL.md` + `TOOLS.md` + `MEMORY.md` + `SKILLS/` + validators + MCP config, then steps away. Your existing coding agent (Claude Code, Cursor, Codex, Gemini CLI, Aider, OpenHarness) reads the output.

**Use harnessforge if:** you use Claude Code / Cursor / Codex / Gemini CLI / Aider / OpenHarness and want them to start a project with the right ground truth, blueprint, validators, and tools without hand-authoring any of it.

## The key distinction vs. OpenHarness

OpenHarness is a **runtime** harness — you pipe your agent through `oh` and it provides the loop. harnessforge is a **provisioner** — we generate files into your repo and exit. Your agent never knows we exist; it just sees the right ground truth on startup.

Different lifecycle, different abstraction:

| | OpenHarness | harnessforge |
|---|---|---|
| Owns the loop | Yes (`oh` CLI runs your agent) | No (your IDE keeps the loop) |
| Lives in your shell | Yes (always-on `oh` process) | No (one-shot `harness init`) |
| Files in your repo | Discovers `~/.openharness/skills/`, `CLAUDE.md`, `MEMORY.md` | Generates `AGENTS.md`, `SOUL.md`, `TOOLS.md`, `MEMORY.md`, `SKILLS/`, plus per-IDE files |
| Visible to your coding agent | Yes (the agent runs inside it) | No (the agent reads the generated files; we're invisible) |
| Compatible with your existing setup | Replaces your loop | Augments your existing tool |

Both are good tools for different jobs. harnessforge doesn't compete with OpenHarness's runtime; it bootstraps a repo that *either* tool (or any other coding agent) can then use.

## The positioning sentence

If you use Hermes or OpenClaw, you don't need harnessforge — those agents ship with their own harness.

If you use Claude Code, Cursor, Codex, Gemini CLI, Aider, OpenHarness, or anything else, you do.
