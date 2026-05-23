---
name: decompose-task
description: Turn a user task into an ordered, executable plan of named steps.
version: 1.0.0
when_to_use: Step 1 of every workflow run. Always.
inputs:
  - { name: task, type: string, required: true }
outputs:
  - { name: plan, type: array, description: "[{step, name, tool, args_template, expected_effect}]" }
---

# Decompose Task

## Steps

1. Read the task description.
2. List the concrete observable effects it requires (file written? API
   called? row inserted?).
3. Group effects into ordered steps. Prefer fewer, bigger steps over many
   small ones — atomicity, not granularity.
4. For each step, name the tool and sketch `args_template`. Mark steps
   as idempotent or non-idempotent; the last step should be idempotent.
5. Return the plan. If you can't decompose unambiguously, ask the user.

## Output shape

```jsonc
{
  "plan": [
    {
      "step": 1, "name": "fetch-input",
      "tool": "fetch", "args_template": {"url": "<from user>"},
      "expected_effect": "200 + JSON body cached", "idempotent": true
    },
    {
      "step": 2, "name": "transform",
      "tool": "shell", "args_template": {"cmd": "jq ... > out.json"},
      "expected_effect": "out.json written", "idempotent": true
    }
  ]
}
```

## Failure modes

- 17 steps because each line is its own step → users can't reason about it.
- A non-idempotent final step (validator catches this).
- Hidden side effects ("step 4 also clears the cache") that aren't in `expected_effect`.
