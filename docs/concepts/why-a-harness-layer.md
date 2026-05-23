# Why a harness layer

> *"The next big open-source opportunity is not another coding agent.*
> *It is the harness layer that every coding agent can use."*

Every time a developer builds an AI agent — sales agent, RAG agent, browser agent, finance agent, support agent — they rebuild the same foundation from scratch:

- tool wiring
- repo instructions
- memory files
- test commands
- validation scripts
- MCP configs
- retry/loop logic

**Different agents, same repeated foundation.** That's the real harness problem.

A sales agent needs lead qualification, CRM tools, product Q&A, handover logic, follow-up workflow, conversation memory. A RAG agent needs ingestion, chunking, embedding, retrieval, reranking, citation checking, fallback logic, eval. A browser agent needs page observation, click/type actions, screenshot validation, error recovery. A support agent needs intent classification, FAQ retrieval, ticket creation, escalation rules, SLA logic.

In 2026, developers still hand-author all of this per project per IDE.

By 2027, the coding LLM should generate it. Claude Code, Codex, Gemini CLI, Cursor — they should ask "what type of agent am I building? what modules do I need? what tools should I connect? what files should I create? what memory structure? what validation tests?" — and a shared layer should answer.

**harnessforge is that bridge.** One command, run today, gives any coding agent the harness it would otherwise spend hours building. Then it gets out of the way.

The coding LLM still writes the code. The coding LLM still makes the decisions. The coding LLM still drives the loop. But it no longer starts from zero.

## What we're explicitly NOT building

- **Not another coding agent.** Claude Code, Cursor, Codex, Gemini CLI, Aider, OpenHarness — keep using whichever you already use. harnessforge is what they read on startup.
- **Not a guardrails-only library.** Guardrails are part of it but not the point.
- **Not a runtime.** We don't run your agent. We generate files and exit. Your IDE keeps the loop.
- **Not opinionated about the model.** Model-neutral by design. Any LLM works.

## What we ARE building

A **provisioning layer**: `harness init` walks your repo, infers what kind of project it is, picks an appropriate agent blueprint, and renders the right files — `AGENTS.md`, `SOUL.md`, `TOOLS.md`, `MEMORY.md`, `SKILLS/`, plus per-IDE adapter files, plus blueprint validators.

The artifacts are committed to your repo. The next person who clones it — human or AI — sees a fully-set-up project.
