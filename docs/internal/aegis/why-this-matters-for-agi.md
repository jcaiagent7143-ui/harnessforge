# Why this matters for AGI (internal note)

The thesis that drove the original Aegis project:

> *"In 2027, developers will stop setting up agent harnesses. The LLM will design its own harness for each unique task."*

Aegis was an early reference implementation — for one task, the LLM emitted real Python (Pydantic schemas, tool guards, verifiers), executed inside a sandbox, and returned a verified result.

harnessforge is the *project-scoped* version of the same idea. Instead of generating a harness per task, it generates a harness per project, then hands runtime control to the user's coding agent. The per-task synthesis layer (Aegis) is now an implementation detail of the validator runtime.

The end-state — agents that need zero hand-authored ground truth before doing useful work — is unchanged. harnessforge is the bridge: useful in 2026 with today's coding agents, while the per-task self-generation path matures.
