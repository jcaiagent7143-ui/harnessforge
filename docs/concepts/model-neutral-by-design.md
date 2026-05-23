# Model-neutral by design

Harness Kit doesn't care which LLM is the brain.

## At provisioning time

`harness init` builds a profile. By default it uses whatever LLM provider you have credentials for:

- Anthropic (`ANTHROPIC_API_KEY` + `pip install 'harness-kit[anthropic]'`)
- OpenAI (`OPENAI_API_KEY` + `pip install 'harness-kit[openai]'`)
- Google Gemini (`GOOGLE_API_KEY` + `pip install 'harness-kit[gemini]'`)
- Ollama (local; `pip install 'harness-kit[ollama]'`)
- LiteLLM (100+ providers via `pip install 'harness-kit[litellm]'`)

If none is available, `harness init` falls back to the deterministic template profiler — no API key required. The output is still production-grade; the LLM only refines descriptions and conventions.

`--no-llm` forces the template path explicitly. Recommended for CI.

## At runtime

We don't run your agent. Your coding agent — Claude Code, Cursor, Codex, Gemini CLI, Aider, OpenHarness — runs whichever model it's configured for. We just generate the files it reads.

## At verification time

`harness verify` runs blueprint validators. Validators are plain Python (no LLM). They check structural invariants (schema, citations, lineage, tool log, idempotency). No model required.

## File-format neutrality

The generated files follow the de facto conventions used by every major agent project in May 2026:

- `AGENTS.md` — OpenAI Codex CLI standard
- `SOUL.md` — Hermes + OpenClaw convention
- `TOOLS.md` — OpenClaw convention
- `MEMORY.md` — OpenHarness convention
- `SKILLS/<name>/SKILL.md` — [`anthropics/skills`](https://github.com/anthropics/skills) format
- Plus per-IDE files (`.claude/CLAUDE.md`, `.cursor/rules`, `.continue/config.json`, `.windsurf/rules`)

A single bootstrapped repo is usable by any coding agent that follows any of these conventions. No tool gets second-class treatment.
