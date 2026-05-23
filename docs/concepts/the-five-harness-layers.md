# The five harness layers

Hermes (Nous Research) named these layers in April 2026 and the framing has stuck. Every reviewer in the agent infrastructure space now uses it. harnessforge maps to all five — but we *generate* the artifacts; the agent *runs* them.

## Layer 1 — Instructions

What the agent reads on startup to understand the project.

**harnessforge generates:**

- `AGENTS.md` — universal entry, OpenAI Codex CLI convention
- `SOUL.md` — personality + tone (Hermes / OpenClaw convention)
- `.claude/CLAUDE.md` — Claude Code adapter
- `.cursor/rules` — Cursor adapter
- `.continue/config.json` — Continue adapter
- `.windsurf/rules` — Windsurf adapter

## Layer 2 — Constraints

Tool permissions, sandboxed execution, forbidden paths and commands.

**harnessforge generates:**

- Profile-driven `forbidden_paths`, `forbidden_commands`, `requires_human_approval` lists rendered into every adapter file
- Validators that run inside an AST-allowlist sandbox (via the internal `aegis` module)

## Layer 3 — Feedback

The validation + repair loop the agent uses to self-correct.

**harnessforge generates:**

- `harness verify` — runs blueprint-defined validators (Pydantic schema checks, citation cross-checks, eval questions)
- Stable JSON contract that your coding agent can read programmatically:

  ```json
  {
    "schema_version": 1,
    "blueprint": "rag-agent",
    "checks": [{"name": "...", "status": "pass|fail|skipped|error", "messages": [...]}],
    "summary": {"total": N, "passed": N, "failed": N}
  }
  ```

- Same contract exposed via MCP (`harness verify` tool) so the agent can call it as a typed tool

## Layer 4 — Memory

Persistent + session knowledge structures the agent uses across turns.

**harnessforge generates:**

- `MEMORY.md` — describes the memory model
- JSON Schemas for the standard shapes — `conversation`, `rag-chunks`, `ticket-history`
- `SKILLS/` directory with anthropics/skills-compatible procedural memory — every coding agent that follows that convention reads the same files

## Layer 5 — Orchestration

Multi-step plan + sub-agent delegation + scheduling.

**harnessforge generates (v0.1):**

- Patterns documented in `AGENTS.md`
- Workflow blueprint's `decompose-task` skill that captures the plan structure

v0.1 leaves the runtime loop to the coding agent — your IDE is the brain. v0.2 will ship sub-agent blueprints.

---

## Who owns what at runtime

| Layer | Owner |
|---|---|
| 1. Instructions | Coding agent reads them; we generate them |
| 2. Constraints | Coding agent honors them; we generate them |
| 3. Feedback | Coding agent calls `harness verify`; we generate the validators |
| 4. Memory | Coding agent writes during runtime; we generate the schemas + starter skills |
| 5. Orchestration | Coding agent runs the loop; we document the pattern |

The coding agent owns runtime. We own the bootstrap.
