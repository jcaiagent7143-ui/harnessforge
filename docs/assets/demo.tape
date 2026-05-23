# vhs tape — renders the README demo GIF
#
# Usage:
#   brew install vhs   # or: go install github.com/charmbracelet/vhs@latest
#   vhs docs/assets/demo.tape
#
# Produces docs/assets/demo.gif (~30s, ~800x500). Commit alongside the README.
#
# Scenario: take a bare Python repo, run `harness init`, show what was
# generated, run `harness verify`. Total runtime ~22-28s on most machines.

Output docs/assets/demo.gif

Set FontSize 14
Set Width 1100
Set Height 700
Set Theme "GitHub Dark"
Set TypingSpeed 40ms
Set Margin 12
Set Padding 18

# ─── setup (off-screen) ─────────────────────────────────────────────
Hide
Type "rm -rf /tmp/portfoliowatch && mkdir /tmp/portfoliowatch && cd /tmp/portfoliowatch"
Enter
Type "printf '# PortfolioWatch\n\nAI stock-analysis agent.\n' > README.md && printf '[project]\nname = \"portfoliowatch\"\nversion = \"0.0.1\"\ndependencies = []\n' > pyproject.toml"
Enter
Type "clear"
Enter
Sleep 200ms
Show

# ─── scene 1: empty repo ────────────────────────────────────────────
Type "ls -A"
Enter
Sleep 1200ms

# ─── scene 2: one command bootstraps everything ─────────────────────
Type "uvx harness-kit init --no-llm"
Sleep 600ms
Enter
Sleep 6000ms

# ─── scene 3: what got written ──────────────────────────────────────
Type "clear && ls -A && echo '---' && ls SKILLS/"
Enter
Sleep 2500ms

# ─── scene 4: AGENTS.md is real, project-specific content ───────────
Type "clear && head -20 AGENTS.md"
Enter
Sleep 3500ms

# ─── scene 5: validators run ────────────────────────────────────────
Type "clear && harness verify --json"
Enter
Sleep 4000ms

# ─── tail ──────────────────────────────────────────────────────────
Type "# Your Claude Code / Cursor / Codex / Aider just got a project-aware brain."
Enter
Sleep 2500ms
