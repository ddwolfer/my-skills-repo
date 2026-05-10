---
name: dual-plan
description: Use when the user asks to plan, design, architect, or scope a multi-step task — features, refactors, new systems, complex bug investigations. Generates `plan.md` (canonical source for AI execution) AND `plan.html` (visually rich rendering for human discussion). Triggers on `/dual-plan`, on phrases like "幫我規劃 / plan / 設計 / 架構 X", or in plan mode when the task is non-trivial. SKIP for single-line bug fixes, variable renames, simple refactors, or when an existing plan just needs execution.
---

# dual-plan — Dual-Format Planning

Produce a plan as two artifacts in one shot:

- **`plan.md`** — single source of truth, what AI reads when executing
- **`plan.html`** — rendered view of the same content, what the human reads when reviewing

The MD is canonical. HTML is regenerated from MD on every change. There is no reverse sync.

Inspired by Thariq's "Using Claude Code: The Unreasonable Effectiveness of HTML" — humans read HTML far more readily than markdown, but AI executes faster on plain MD.

## When to fire this skill

**FIRE when:**
- User explicitly invokes `/dual-plan <topic>`
- User asks to plan / design / architect / scope something with ≥ 3 steps or ≥ 30 min of work
- Entering plan mode for a feature, refactor, system design, or non-trivial investigation
- User says things like「幫我規劃」「來想想怎麼做」「設計一下 X」for non-trivial work

**SKIP when:**
- Single-line bug fix, variable rename, typo, formatting
- Pure exploration or Q&A with no implementation intent
- An existing approved plan just needs execution
- Auto mode + routine tasks

When uncertain, ask the user once: "這需要寫成 dual-plan 嗎?" Don't ask twice.

## The workflow

```
                  ┌─ user request ─┐
                  │                │
                  ▼                │
       ┌─ needs brainstorm? ──────┐│
       │                          ││
      yes                        no││
       │                          ││
       ▼                          ▼│
  superpowers:               write plan.md
  brainstorming              (use writing-plans
       │                      skill if helpful)
       └──────────┬───────────────┘
                  ▼
           render plan.html
                  │
                  ▼
           user reviews HTML
                  │
         ┌────────┼────────┐
         │                 │
     feedback           approve
         │                 │
         ▼                 ▼
   rewrite plan.md    AI executes
   re-render HTML     (reads plan.md)
         │
         └─→ loop
```

Step-by-step:

1. **Detect ambiguity.** If the request is vague ("我想做個 X 但還沒想清楚"), invoke `superpowers:brainstorming` first to clarify.
2. **Decide slug & directory.** Compute `<YYYY-MM-DD>-<short-slug>` from current date and the request topic. The directory is `<cwd>/plans/<slug>/`. Create it if needed.
3. **First-time setup (if applicable).** If `<cwd>/plans/` is being created in this repo for the first time AND a `.gitignore` exists at `<cwd>`, append `plans/**/plan.html` to it. Tell the user you did this.
4. **Write `plan.md`.** Use `superpowers:writing-plans` conventions if available. The MD is the canonical artifact — it should be self-sufficient for AI execution.
5. **Render `plan.html`.** Run `python ~/.claude/skills/dual-plan/render.py <plan.md path>`. The script reads frontmatter, injects body, writes `plan.html` next to it, auto-snapshots prior versions to `history/`. Don't hand-write the HTML — the script handles substitutions and avoids 19 KB of CSS/JS context bloat.
6. **Tell user where to look.** "Plan at `plans/<slug>/plan.md`. Open `plan.html` in browser to review."
7. **Iterate.** When user gives feedback, edit `plan.md` in batch (apply ALL their feedback in one round of edits, don't re-render between each edit). When you bump `version` in frontmatter, also update `updated`. Then re-run `render.py`. Never edit `plan.html` by hand — it is generated.
8. **Approve & execute.** When the user says "好" / "go" / "approve" / "開始做" / similar, stop iterating. Update frontmatter `status: approved`, render once more, then from this point AI executes by reading `plan.md`. Do not modify the plan during execution; if the user wants changes, stop and re-iterate.

## File layout

```
<cwd>/
  plans/
    2026-05-10-feature-x/
      plan.md           ← canonical, AI reads this
      plan.html         ← rendered view, human reads this (gitignored)
      history/          ← prior versions, auto-snapshotted by render.py
        v0.1.md
        v0.2.md
      attachments/      ← optional: screenshots, references
    2026-05-12-other/
      ...
  .gitignore            ← contains: plans/**/plan.html
```

Slug rules:
- Date prefix `YYYY-MM-DD` (use current date — convert relative dates like "today" to absolute)
- Short kebab-case description (3–5 words max)
- Lowercase ASCII; if topic is Chinese, transliterate or summarize in English

## plan.md frontmatter (REQUIRED)

Every `plan.md` starts with YAML frontmatter. The render script reads it for the title, version, slug, etc. Skeleton at `~/.claude/skills/dual-plan/templates/plan.md.skel`.

```yaml
---
title: <Plan title — short, < 60 chars>
version: 0.1                       # bump on every meaningful iteration
status: draft                      # draft | approved | archived
created: 2026-05-10                # YYYY-MM-DD, set once at creation
updated: 2026-05-10                # YYYY-MM-DD, bump on every edit
slug: 2026-05-10-feature-x         # matches the directory name
# Render via dual-plan template only — uses custom marked tokenizer.
---
```

**Why frontmatter**:
- `version` drives auto-snapshot to `history/` on each render
- `title` becomes `<title>` and masthead in HTML
- `slug` is used in masthead path display
- `status` tells downstream consumers (e.g. multi-agent) where in the lifecycle this plan is

When you bump `version` (e.g. 0.2 → 0.3), also update `updated`. Don't touch `created`.

## Writing good plan.md

Treat `plan.md` as a real plan, not a sketch. Include:

- **Goal** — one-paragraph statement of what we're building and why
- **Approach** — how we'll do it, key decisions, alternatives considered
- **Steps** — numbered, concrete, each step actionable on its own
- **Out of scope** — what we're explicitly NOT doing
- **Open questions** — anything needing user input before execution
- Use `mermaid` code fences for flowcharts/diagrams (renders to SVG in HTML)
- Use tables for structured comparisons
- Use task-list checkboxes (`- [ ]`) for verification items

The MD must stand alone — if a different AI session reads only `plan.md` (no HTML, no chat), it should have everything needed to execute.

## When to add rich HTML features

The render template handles the basics (typography, mermaid, theme toggle, code blocks). Per-plan, you may **embed raw HTML inside `plan.md`** for:

| Feature | Add when... |
|---------|------------|
| **SVG illustration** | A concept benefits from a hand-drawn diagram that mermaid can't express well — architecture overviews, "before/after" comparisons, spatial relationships |
| **Interactive sliders** | The plan has tunable parameters and the user benefits from previewing combinations (e.g., "rollout %", "timeout values", "feature flag mix") |
| **"Copy as Prompt" button** | The slider/control output should feed back into a prompt — let the user copy a structured request to paste back into Claude Code |
| **Custom interactive demo** | A concept in the plan is best understood by interaction (e.g., a state machine the user can step through) |

**Don't add these by default.** Mermaid + tables + code blocks cover 90% of plans. Reserve the rich features for plans where they earn their keep.

When you do add raw HTML inside `plan.md`, see the next section.

## Critical: raw HTML blocks must not contain blank lines

Marked.js (and CommonMark) terminate raw HTML blocks at the first blank line, after which content is parsed as markdown again. This breaks SVG and complex HTML.

**Two safeguards are in place:**

1. **The render template includes a custom marked tokenizer** that consumes raw HTML blocks (`<div>`, `<svg>`, `<figure>`, `<section>`, `<aside>`, `<nav>`, `<article>`, `<table>`, `<form>`) greedily until the matching closing tag, regardless of internal blank lines. This is automatic.

2. **Still, you should write raw HTML compactly** — avoid blank lines inside `<svg>...</svg>`, `<div class="tuner">...</div>`, etc. Use HTML comments (`<!-- ... -->`) as visual separators if you want spacing. This keeps things working even if a future template version drops the tokenizer fix.

## Re-render policy

- **At the end of each MD edit batch**, re-render `plan.html` by invoking `render.py`. Don't re-render between every single line edit during a batch — wait for the batch to settle.
- Never edit `plan.html` by hand. The script regenerates it from template + MD on every run.
- `render.py` auto-handles: title, masthead path, timestamp, MD injection, and version snapshot.
- The masthead `<span class="stamp">` updates with each render (current system time, no manual timestamps needed).

### Version & history

- Every meaningful iteration bumps `version` in plan.md frontmatter (0.1 → 0.2 → 0.3 ...).
- Always update `updated:` field when bumping version.
- `render.py` auto-snapshots: if the prior `plan.html` had a different `version` than the new one, the prior MD source is extracted from that HTML and saved to `history/v<old>.md` before overwriting.
- This means **history is automatic** — no manual snapshot step needed. Don't pre-copy plan.md to history yourself.
- The `history/` folder belongs in git (unlike `plan.html` which is gitignored).

## .gitignore handling

- On first plan creation in a project, check if `<cwd>/.gitignore` exists.
- If yes: append `plans/**/plan.html` (only if not already present). Tell the user.
- If no: don't create one — the user might not be using git.
- Don't gitignore `plan.md` (canonical, must be reviewable).
- Don't gitignore `attachments/` (user assets).

## Approve & execute

The user transitions from "discussing the plan" to "executing the plan" via natural language. Look for:

- "好" / "可以" / "go" / "ok" / "approve" / "開始做" / "start" / "let's go"
- Or implicit: user starts asking questions about implementation details rather than the plan itself

When you detect approval, acknowledge briefly and switch modes. From here, `plan.md` is frozen — execute against it. If the user wants changes mid-execution, stop, ask them to give feedback on the plan, then re-iterate (re-render after MD edit).

## Render mechanics (reference)

Rendering is automated via `~/.claude/skills/dual-plan/render.py`. Invoke as:

```bash
python ~/.claude/skills/dual-plan/render.py path/to/plans/<slug>/plan.md
```

The script:

1. Reads `plan.md`, parses YAML frontmatter, separates body
2. Reads template at `~/.claude/skills/dual-plan/templates/plan-render.html`
3. Substitutes `<title>`, masthead path, current timestamp, and the embedded `<script type="text/markdown">` block
4. Writes the result to `plans/<slug>/plan.html` (overwrites)
5. Auto-snapshots: if prior `plan.html` had a different `version`, extracts its MD and writes to `history/v<old>.md`

Stdlib only (no pip install). Tested on Python 3.13+.

If python is unavailable for some reason, manual fallback: read template, do the four substitutions yourself, write the file. But always prefer the script.

## Don'ts

- Don't try to keep two-way sync between MD and HTML
- Don't re-render between individual edits within a batch — wait until the batch is done
- Don't hand-write plan.html — always use `render.py`
- Don't manually snapshot to `history/` — `render.py` does it from the prior HTML
- Don't pollute the user's chat with the entire MD content — point them at the file
- Don't ask the user to install anything; the template uses CDN-hosted JS, render.py uses stdlib only
- Don't generate a fancy SVG/tuner unless the plan genuinely benefits — restraint is the default
- Don't omit frontmatter from plan.md — every plan needs it

## See also

- Render script: `~/.claude/skills/dual-plan/render.py`
- Render template: `~/.claude/skills/dual-plan/templates/plan-render.html`
- plan.md skeleton: `~/.claude/skills/dual-plan/templates/plan.md.skel`
- Skill intro for humans: `~/.claude/skills/dual-plan/README.html` (open in browser)
- Inspiration: Thariq, "Using Claude Code: The Unreasonable Effectiveness of HTML"
- Companion skills: `superpowers:brainstorming`, `superpowers:writing-plans`
