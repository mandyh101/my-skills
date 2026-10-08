---
name: little-retro
description: Retro on a finished little-loop run — finds what worked and what didn't across all its sessions, raises a GitHub issue with the skill improvements you agree, then removes the plan doc before merge.
disable-model-invocation: true
---

# Little retro

Turn one little-loop run — however many sessions it took — into a few concrete improvements to the `little-*` skills, captured as a GitHub issue on the `my-skills` repo. The run log records what happened; deciding what it **means** is this skill's job; deciding what to change is the user's, **one finding at a time**.

Run it once the PR is approved and before it's merged: its last act removes the plan doc from the branch.

This is not the session `retro` skill — that reviews one conversation. This reviews a **run**, from what the run left behind.

## Step 0 — Find the run

From the current branch or the user's message, get the ticket and PR, then load:

- the run log, `~/.claude/loop-runs/<repo>/<TICKET>.md`
- the plan doc on the branch
- the PR: `gh pr view <pr> --json url,reviewDecision,state,commits,additions,deletions,changedFiles`

Not approved yet → say so and ask whether to go ahead anyway. No run log → retro is working from the PR and git alone; say so, because the rework rounds and escalations are invisible without it.

**Completion criterion:** the run log, plan doc and PR are loaded, or their absence is stated.

## Step 1 — Gather the evidence

- **This run's log** — every line.
- **The PR's human comments** — inline, review bodies and issue comments, excluding any reply starting `(from Claude)`. These are what the loop shipped that a person objected to — the blind spots `little-verify` structurally can't see about itself.
- **The plan doc** — Assumed items vs what address and implement found broken; each phase's **Size** estimate vs actual (from `phase-done` lines).
- **Past runs** — `~/.claude/loop-runs/*/*.md`. Look for the same kind of event recurring, and for `retro` lines listing findings being **watched**: a watched item that happened again is now a repeat.

**Completion criterion:** you can state how many sessions and days the run spanned, and count each event type in its log.

## Step 2 — Find what it means

Look for these, each grounded in a count or a quoted log line — "2 of 4 phases needed a re-work, both for missing error states" is a finding; "verify was sometimes strict" is a feeling:

- **What the grill missed** — wrong assumptions caught in review or by the implementer. The planner should have asked; which kind of gap was it?
- **Why phases needed a re-work** — same reason twice points at the implementer's guidance or the plan's Verify lines, not bad luck.
- **Escalations and interventions** — what was happening just before each one?
- **Size estimates** — consistently under? The planner's estimating needs a nudge.
- **CI and Sonar failures** the per-phase checks didn't catch — a gap between local checks and the gate.
- **Address triage** — many smell/CI items = implementer guidance; many wrong-assumption items = planner guidance.
- **What went well** — a phase that verified first time on a hard change, a grill question that headed off a real mistake. Worth naming so it isn't "improved" away.

One run is a thin sample. Say so, and treat a one-off as **watch**, not fix, unless it was costly or the user felt it.

**Completion criterion:** each finding has its evidence and the skill it points at; went-well items are listed separately.

## Step 3 — Ask what the log couldn't see

Show the findings as a short list, one line each with its evidence, plus what went well. Then ask the user, once: **anything about this run that felt like friction, whether or not it's on that list?** A run can succeed on paper and still be a slog. Add what they say as findings flagged "you mentioned" — no invented counts.

**Completion criterion:** the user has seen the list and been asked for their own; both sets are on one list.

## Step 4 — Triage one at a time

Take the list most-evidenced first. **Stop on each item** — never batch into one approve-all. For each, give:

- **What** happened, and the evidence.
- **Where** it belongs — the file and section: `little-plan`, `little-implement`, `little-verify`, `little-loop` (incl. `SIZE.md`, `SONAR-CLI.md`, `RUN-LOG.md`), `little-address`, the plan template, or the repo's own `CLAUDE.md`.
- **Check or gate** — prefer a **check** (a rule, a command, a verify step that catches it mechanically) over a **gate** (another place the loop stops to ask). Gates added by reflex dismantle the autonomous loop one reasonable-sounding pause at a time.
- **Your recommendation**: **fix now**, **watch**, or **drop**.

Then the user picks.

**Fix now** → draft the exact edit (file, section, old text → new text) and confirm it with the user. **Don't apply it** — this run's skills are the installed plugin copy, which the next update overwrites. Agreed edits go into the issue in Step 5, and the fix lands as a PR from there.

A fix for the project repo's own `CLAUDE.md` isn't a skill change: list it in the close-out for the user to action, and leave it out of the issue.

Edits stay small and specific, follow `writing-great-skills`, and replace rather than pile on — a skill that only ever grows rots.

**Completion criterion:** every item has an outcome — fix (edit drafted and agreed), watching, or dropped.

## Step 5 — Raise the improvements issue

Skip this step if nothing was marked **fix**.

Otherwise, draft one issue on `mandyh101/my-skills` and show it to the user before creating it:

- **Title:** `Retro: <TICKET> — <n> skill improvements`
- **Body:**
  - one line on the run (ticket, PR link, sessions, days, phases, attempts)
  - **Fixes** — one section per item: what happened and the evidence; where it goes (`file § section`); check or gate; the drafted edit as old → new
  - **Watching** — short names with one line of evidence, so a later retro can count repeats
  - **Went well** — so a later fix doesn't undo it

On the user's go-ahead:

```bash
gh issue create --repo mandyh101/my-skills --title '<title>' --body-file <body file>
```

**Completion criterion:** the issue is created and its URL noted, or there was nothing to fix.

## Step 6 — Log it

Append to the run log per [`RUN-LOG.md`](../little-loop/RUN-LOG.md):

```
YYYY-MM-DD little-retro retro: fix — <short names> (<issue URL>); watching — <short names>; dropped — <short names>
```

Watching items are named so the next retro can count repeats.

## Step 7 — Remove the plan doc

Anything in the plan worth keeping in the repo — a decision a future reader needs — is the user's call; offer it once, and only move it if they say so.

Then, **with the user's go-ahead**:

```bash
git rm <plan path>
git commit -m 'chore: <TICKET> remove plan doc'
git push
```

Tell the user that CI reruns on this commit and some repos need a re-approve; after that, merging is theirs.

**Completion criterion:** the plan doc is removed and pushed, or the user said to keep it.

## Step 8 — Close out

Short, in the terminal, no file: the run (sessions, days, phases, attempts), what went well, the improvements issue link, any `CLAUDE.md` fixes for the user to action, what's being watched. Say plainly when the sample was too thin to conclude much — a retro that invents findings costs a real afternoon later.
