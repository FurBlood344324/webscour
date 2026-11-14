# webscour skill: one file, five loaders

Everything in this directory is a pi-format skill: `SKILL.md` with YAML frontmatter, relative
`references/` and `scripts/` beside it. The format is the same everywhere. Only the thing that
discovers it changes, so the skill is written once and installed wherever the agent runs.

| Harness | Install | Notes |
|---|---|---|
| pi | `pi install npm:webscour` (the shortest form), or `pi install git:github.com/FurBlood344324/webscour`, or copy this directory to `~/.pi/agent/skills/webscour/` | `pi install` reads `pi.skills` from the package manifest |
| Claude Code | `claude plugin marketplace add /path/to/webscour` then `claude plugin install webscour`, or copy to `~/.claude/skills/webscour/` | the repo ships `.claude-plugin/marketplace.json` pointing at this directory |
| dsh | copy or symlink to `~/.agents/skills/webscour/` (shared across harnesses) or a project's `.dsh/skills/webscour/` | symlinks are what this machine uses |
| agy | copy or symlink to `~/.gemini/config/skills/webscour/` | same frontmatter, no manifest |
| no plugin system | put the absolute path to `SKILL.md` in the prompt: "read ~/projects/webscour/skill/SKILL.md first" | works in any agent that can read a file, reference paths relative to it |

The skill itself never names a loader, a manifest or a directory outside its own tree. Its reference
links are relative (`references/choosing-a-source.md`), so a copy into any of the locations above
keeps working, and `scripts/` resolves the CLI with `command -v wsc` before falling back to
`python3 -m webscour.cli`, so it works from any working directory and from a checkout that was never
installed.

To change what the model does, change `SKILL.md` or a reference file and reinstall or re-symlink.
There is no generated copy and no build step.
