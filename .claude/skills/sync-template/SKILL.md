---
name: sync-template
description: Sync this project's structure and conventions with the canonical template repo (example-project). Use when the user asks to sync or update the project structure, pull the latest template conventions, or after the template repo has changed. Also handles upstreaming a local convention improvement back to the template.
---

# Sync with the canonical template

The canonical template is `Aleksandr-Mikhailov-Corporate/example-project`. Repos created
from a template share no git history with it, so there is no `git merge` from the
template — syncing is a file-level comparison, which is what this skill does.

## This project is a deliberately lean subset

`meeting_transcribator` is a small single-purpose CLI. It intentionally adopts only the
template's config hygiene and tooling, NOT its big-project folders. **Do not re-add these
on a sync** unless the user asks — their absence is a choice, not drift:

- `data/`, `data/db`, `data/migrations` — no database.
- `notebooks/` — no research/exploration.
- `project-management/` (log.md, stakeholders.md, meeting-notes, communications, library)
  — solo tool, no stakeholder process.
- `docs/architecture`, `docs/data-model`, `docs/technical-documentation`, `docs/plans`
  and per-folder `CLAUDE.md` for every folder — the root `CLAUDE.md` covers it.
- tests split into `unit/integration/llm` — the flat `tests/` suite is enough here.
- `.vscode/` editor task buttons — manual runs go through Claude or the terminal
  (`uv run transcribe ...`), not editor buttons.

What this project DOES track with the template: `.gitattributes`, `.editorconfig`,
`.gitignore` hygiene, `.claude/` (settings + skills), `.env.example`, the root
`CLAUDE.md` section structure, and the `README.md` skeleton.

## Locate the template

1. Check `CLAUDE.local.md` → "Related projects & repositories" for a local path to
   example-project. Prefer the local clone and `git pull` it first so you compare against
   the latest state.
2. If there is no local path, clone fresh into the scratchpad directory:
   `gh repo clone Aleksandr-Mikhailov-Corporate/example-project <scratchpad>/template-sync`.

## What to compare (within this project's lean scope)

Only structure and conventions — never project content (`src/`, `recordings/`,
`outputs/`, transcripts stay untouched):

- Root `CLAUDE.md`: section structure and convention rules — NOT the project-specific
  filled-in values (project identity, commands, the provider rule).
- `.gitignore`, `.gitattributes`, `.editorconfig`, `.env.example` — merge new entries,
  keep project-specific ones (the recordings/outputs/audio privacy rules are ours).
- `.claude/`: settings.json, skills/, hooks/, agents/ — add new items from the template,
  never delete project-local ones.
- `README.md` skeleton sections.

## Rules for applying

- Additive by default within scope: new convention sections and skills → add them.
- Placeholders never overwrite filled values. If the template says `Build: <command>` and
  this project says `Build: uv run ...`, the project's value wins.
- If the template removed or renamed something this project still has, list it and ask the
  user before deleting or renaming anything.
- After applying: update `README.md` to mirror any `CLAUDE.md` changes, run `uv run pytest`,
  and commit with a message that records which template commit hash was synced.

## Upstreaming (reverse direction)

If the user says a convention from this project should become standard: apply the change in
the template clone, commit, and push to the template repo. Only conventions and structure —
never project-specific content or secrets.

## Report

End with a short summary: what was added, what was kept as-is, and what needs a user decision.
