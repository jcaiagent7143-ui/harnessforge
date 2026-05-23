# Skills format

We follow the [`anthropics/skills`](https://github.com/anthropics/skills) convention exactly. Any tool that reads that format can use harness-generated skills, and vice versa.

## Directory shape

```
SKILLS/
  <skill-name>/
    SKILL.md                  # required
    (optional resources)
```

`<skill-name>` is the canonical identifier — kebab-case, must start with a letter.

## SKILL.md shape

```markdown
---
name: skill-name              # must match directory
description: 10–1024 chars
version: 1.0.0
when_to_use: routing hint
inputs:
  - {name: ..., type: ..., required: true/false, description: ...}
outputs:
  - {name: ..., type: ..., description: ...}
---

# Human-readable title

## Steps

1. ...
2. ...

## Failure modes to avoid

- ...
```

Frontmatter is YAML; body is markdown. Both are required.

## Validators

`harness.skills_io.validate_skill` enforces:

- `name` matches `^[a-z][a-z0-9-]*$`
- `description` between 10 and 1024 chars
- `body` is non-empty

The validator is intentionally lenient — we don't want to break anthropics/skills compatibility by over-specifying.

## CLI

```bash
harness skills list           # local + catalog
harness skills show <name>    # print SKILL.md
harness skills add <name>     # copy from blueprint catalog
```
