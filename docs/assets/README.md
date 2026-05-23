# docs/assets/

Static assets referenced from the docs site + README.

## demo.gif (the README hero)

Regenerate with:

```bash
brew install vhs   # or: go install github.com/charmbracelet/vhs@latest
vhs docs/assets/demo.tape
```

This writes `docs/assets/demo.gif` (~800KB, 30s, 1100×700). Commit it.

The tape:
- creates a bare Python repo at `/tmp/portfoliowatch/`
- runs `uvx harness-kit init --no-llm`
- shows the generated tree (AGENTS.md, SOUL.md, TOOLS.md, MEMORY.md, SKILLS/)
- prints the first 20 lines of `AGENTS.md` to show real, project-specific content
- runs `harness verify --json` to show 3/3 validators passing

To preview without writing the GIF:

```bash
vhs docs/assets/demo.tape --quiet
```

To bump the recording cadence (slower/faster), edit `Set TypingSpeed` and
the `Sleep` values in `demo.tape`.

## aegis-hero.svg (legacy)

Holdover from the v0.1 project name. Kept until docs/internal/aegis is removed.
