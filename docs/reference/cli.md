# CLI reference

```
harness init [PATH]                       # inspect → profile → blueprint → render
  --blueprint <name>                      # rag-agent | support-agent | workflow-agent
  --no-llm                                # deterministic; no API key required
  --provider {anthropic,openai,gemini,ollama,litellm}
  --force                                 # overwrite drifted/user files
  --dry-run                               # show the plan, write nothing
  --adapter <name>[,<name>…]              # restrict adapters
  --no-skills                             # skip SKILLS/ generation

harness sync [PATH]                       # re-render from existing profile.yaml
  --adapter <name>[,<name>…]
  --check                                 # exit 1 on drift; nothing written
  --force                                 # overwrite drifted files

harness inspect [PATH]
  --format {table,json,yaml}

harness verify [TARGET]                   # exit 0 pass / 1 fail / 2 cfg / 3 no-cfg
  --check <name>                          # run only this validator
  --json                                  # stable JSON contract
  --fail-fast

harness blueprint list
harness blueprint show <name>
harness blueprint apply <name> [PATH] [--force] [--no-skills]

harness skills list [PATH]
harness skills show <name> [PATH]
harness skills add <name> [PATH]          # copy from blueprint catalog into local SKILLS/

harness doctor [PATH]                     # diagnose env: provider keys, extras, repo
harness mcp                               # stdio MCP server
harness version
```
