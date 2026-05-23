# Authoring a custom skill

A skill is a procedure your agent can call by name. Harness Kit follows the [`anthropics/skills`](https://github.com/anthropics/skills) format so any tool that reads that convention can use the same skill file.

## Format

```
SKILLS/<skill-name>/
  SKILL.md              # required
  (optional resources)  # any supporting files the skill references
```

## SKILL.md shape

```markdown
---
name: my-skill                                   # kebab-case
description: One-line, ≥10 chars, ≤1024 chars
version: 1.0.0
when_to_use: When the agent should reach for this skill.
inputs:
  - {name: input1, type: string, required: true}
outputs:
  - {name: output1, type: object, description: "What it returns."}
---

# My Skill

## Steps

1. First step
2. Second step
3. Third step

## Failure modes to avoid

- ...
```

## Validate

```python
from harness.skills_io import Skill, validate_skill

skill = Skill.parse(open("SKILLS/my-skill/SKILL.md").read())
issues = validate_skill(skill)
assert not issues, issues
```

## Add to a blueprint

Drop the directory under `src/harness/blueprints/<bp-name>/skills/<skill-name>/` and list the skill in `blueprint.yaml`:

```yaml
skills:
  - my-skill
  - existing-skill-1
```

## Use a catalog skill in a user's repo

```bash
harness skills list                       # show local + catalog skills
harness skills show my-skill              # print the SKILL.md
harness skills add my-skill .             # copy from catalog into ./SKILLS/
```

## Conventions

- **Name** is the directory name, lowercase, hyphen-separated, must start with a letter.
- **Description** is what the agent reads in tool discovery — keep it crisp, action-oriented.
- **when_to_use** is the routing hint — when should the agent reach for this vs. another skill?
- **Steps** should be testable. "Make a good answer" is not a step. "Re-fetch the cited URL and confirm 200" is.
- **Failure modes** is the most-useful section for the LLM — it learns from negatives faster than positives.
