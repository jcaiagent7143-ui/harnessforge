# Zulip + Support

`zulip/zulip` × `support-agent` blueprint.

```bash
./run.sh
HERO_ZULIP_SHA=abc1234 ./run.sh
```

What you get:

- `AGENTS.md` — support loop (intent → KB → ticket → escalate)
- `SOUL.md` — "warm but brief" voice for an OSS community
- `TOOLS.md` — GitHub (Zulip's tracker), postgres, slack, SLA matrix
- `MEMORY.md` — conversation + ticket-history schemas
- `SKILLS/{classify-intent, retrieve-kb-answer, file-ticket, escalate-if-unresolved}/`
- Five IDE adapters

See [Cookbook: Zulip + Support demo](../../../docs/cookbook/zulip-support-demo.md).
