---
name: add-cli-command
description: Add a new subcommand or flag to the project's CLI without breaking existing UX.
version: 1.0.0
when_to_use: User asks for "add a --foo flag" or "make it take a NAME positional".
inputs:
  - {name: command_name, type: string, required: true}
  - {name: behavior, type: string, required: true, description: "One-line description of what the command does."}
outputs:
  - {name: files_changed, type: array}
---

# Add CLI command

## Steps

1. **Find the CLI entry point.** Look for `if __name__ == "__main__":`, or a `main()` function, or a Typer/Click/argparse setup. Don't grep blindly — `[project.scripts]` in `pyproject.toml` names it.
2. **Match the existing CLI library.** If the project uses argparse, stay with argparse — don't introduce Typer mid-project.
3. **Add the command** with a docstring matching surrounding style.
4. **Wire `--help`** — every command needs a one-line help string.
5. **Write a test** in the project's test file. Use the same test framework already in use.
6. **Run tests + lint** before declaring done.

## Failure modes to avoid

- Adding a new CLI library (Typer/Click) when the project already uses argparse.
- Adding a `--verbose` flag when the project already has one called `--log-level`.
- Breaking `--help` for existing commands by changing shared argparse defaults.
- Shipping without a test.
