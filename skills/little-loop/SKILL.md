---
name: little-loop
description: Use when taking a ticket to one small reviewable PR — grills the ticket and gets a phased plan signed off, then implements and verifies one phase (one commit) at a time. Triggers on "little-loop <ticket>", "run the little loop on <ticket>".
---

# Little loop

Take one ticket to one draft-then-ready PR. You **orchestrate**; every step runs as a **subagent**, so its context stays out of yours and the verifier stays independent of the implementer. You never write product code yourself.

**Two things ask something of the user, both before any code exists: the grill, and the plan sign-off.** Neither is optional — the run waits for each, and only the user explicitly saying so skips either. After sign-off the phases run without asking, unless the loop has to **escalate**. Invoking this skill is the user's authorisation to commit and push on their behalf for this ticket — say so once at the start.

Shared reference: [`SIZE.md`](SIZE.md) (PR size limit), [`SONAR-CLI.md`](SONAR-CLI.md), [`RUN-LOG.md`](RUN-LOG.md) (what to log, when).

## Step 0 — Preflight

1. **Ticket** — the key from the user's message or the current branch name.
2. **Resuming?** A plan doc for this ticket already on the current branch means an earlier session started this run — go to [Resuming](#resuming).
3. **Clean tree** — `git status --porcelain` empty. Not clean → stop; uncommitted work is the user's to deal with.
4. **Base** — `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`, then `git fetch origin <base>`. Every branch in the run roots on `origin/<base>`.
5. **GitHub** — `gh auth status` passes. Failing → stop.
6. **Sonar** — work [`SONAR-CLI.md § Is it here?`](SONAR-CLI.md#is-it-here) and [`§ Which project?`](SONAR-CLI.md#which-project), and **carry the answer** (available + key, or not) into every subagent prompt. Never stops the run.
7. **Size limit** — the default in [`SIZE.md`](SIZE.md), or the repo's override.
8. **Plan path** — `docs/plans/<TICKET>-<slug>.md` unless the repo's `CLAUDE.md` names another.
9. **Run log** — create `~/.claude/loop-runs/<repo>/<TICKET>.md` with its header if missing; log `start`.

Then tell the user: the ticket; that a **round of questions and a plan sign-off come first**, then the loop goes autonomous; that you'll commit and push on their behalf; and that merging stays theirs. An unannounced grill reads as the loop being stuck.

**Completion criterion:** ticket, base, Sonar availability, size limit and plan path are known; tree is clean; run log started; the user has been told what's coming.

## Step 1 — Plan

### Dispatch the planner

Dispatch one `general-purpose` subagent and **keep its ID** so you can talk to it:

> Read `~/.claude/skills/little-plan/SKILL.md` and follow it in relay mode. Ticket: `<key or pasted text>`. Plan path: `<path>`. Size limit: `<limit>`.

### Relay the grill

The planner has the ticket and the code in its context; you deliberately don't. It drives, **you relay**. Each time it hands back a question, put it to the user **verbatim** — recommendation included — and send the answer straight back:

```
SendMessage({to: "<planner ID>", message: "<the user's answer, verbatim>"})
```

- **One question at a time, unedited.** No batching, no summarising its reasoning away.
- **Never answer for the user.** You have less context than either party.
- **The planner decides when it's done**, not you.

**Wait for each answer.** Silence is not a wave-through. Only "skip the questions" / "just go" ends it early — then tell the planner to take its recommendations as Assumed.

### Commit the plan

Branches are yours. Commit, but **don't push yet**:

```bash
git switch -c <TICKET>-<slug> origin/<base>          # the uncommitted doc follows
git add <plan path> && git commit -m 'docs: <TICKET> plan'
```

### Get the plan signed off

**Stop and put the plan in front of the user.** A mis-cut phase costs a paragraph now and a whole run later. Summarise in a few lines and link the doc:

- **Size first, if over the limit** — total estimate vs limit, then three choices: **(a)** shrink scope / split the ticket and plan only the first part; **(b)** hand off to a bigger workflow (e.g. `slice-loop` where the repo has it) and stop here; **(c)** go anyway — the user's reason becomes the plan's **Opt-out:** line.
- **The phases**, in order, one line each with its size.
- **What was assumed** rather than decided — the Assumed list, short.
- **Open questions**, if any.

Ask for one of: **go**, **change something**, or **stop**. A change goes back to the same planner via `SendMessage`, verbatim; then amend while still unpushed:

```bash
git add <plan path> && git commit --amend --no-edit
```

**Wait for the answer.** No reply isn't a go. Log `signoff`.

### Push it as a draft PR

```bash
git push -u origin <TICKET>-<slug>
gh pr create --draft --assignee @me --base <base> --title '<type>: <TICKET> <title>' --body '<body>'
```

Body: first check the repo for a PR template (`.github/pull_request_template.md`, `.github/PULL_REQUEST_TEMPLATE.md`, `.github/PULL_REQUEST_TEMPLATE/`, `docs/`, or repo root; case-insensitive). If one exists, use it as the body: fill its sections, and fit the items below into the matching sections (or add them at the end if none match). Otherwise, use: a link to the ticket, one line on what the PR will deliver, a link to the plan doc for plan review, and the Assumed list. The PR is a draft until the loop finishes. Add the PR URL to the run log header.

**Completion criterion:** grill run and plan signed off (or explicitly waived), plan committed alone as the branch's first commit, draft PR raised, and you can list the phases in order.

## Step 2 — Loop, one phase at a time

For each unticked phase, in order. **Never start a phase until the one before it is verified and pushed.**

1. **Mark the start.** `PHASE_START=$(git rev-parse HEAD)`.

2. **Implement.** Dispatch a fresh `general-purpose` subagent:

   > Read `~/.claude/skills/little-implement/SKILL.md` and follow it. Plan doc: `<path>`. Phase: `<N — name>`. Branch: `<branch>`. Base: `origin/<base>`. Ticket: `<key>`. Sonar: `<available, key | not available>`. Run log: `<path>`. Commit the phase and its checkbox tick together as one commit.

   Wait for it to **finish** before touching the checkout. If it stopped on a broken assumption or a size overrun, **escalate**.

3. **Verify.** Dispatch a **fresh** `general-purpose` subagent — never the implementer:

   > Read `~/.claude/skills/little-verify/SKILL.md` and follow it. Plan doc: `<path>`. Phase: `<N — name>`. Phase start: `<PHASE_START>`. Sonar: `<…>`.

4. **On needs work** — a phase gets **three attempts** in total: the first build, and up to **two re-work rounds**. Dispatch a new implementer whose prompt opens with **"re-work round <1|2>"**, then the plan doc, phase, branch, phase-start sha, the phase commit sha, and the latest verifier's findings **verbatim** — on round 2, also say it's the **last attempt**. A fresh agent has no memory; a paraphrased finding sends it off rebuilding from scratch. Then re-verify with a fresh verifier. Log `rework` with the round and a one-line reason per blocker.

   Still needs work after re-work round 2 → **escalate**. So is an implementer arguing a finding is wrong — the user settles it, not another round.

5. **On pass — squash and push.** Fold any fixups into the one phase commit, then push:

   ```bash
   PHASE_COMMIT=$(git rev-list --reverse "$PHASE_START"..HEAD | head -1)
   git reset --soft "$PHASE_START" && git commit -C "$PHASE_COMMIT"
   git push
   ```

   Skip the reset when there's only one commit. Don't wait for CI here — that happens once, at Step 3.

6. **Size check.** Measure the running total per [`SIZE.md`](SIZE.md). Over the limit — or the next phase's estimate would take it over — and no **Opt-out:** in the plan → **pause** before the next phase: show actual vs limit and the remaining phases, and offer **continue** (the user's reason becomes the Opt-out, committed with the next phase), **stop here** (remaining phases go to a follow-up ticket; jump to Step 3), or **re-plan**. Log `size-pause`.

7. **Log** `phase-done` with attempts taken and `size: est X, actual Y`.

### Escalate

A phase that won't verify, a broken assumption, a disputed finding, a plan that turns out wrong — **stop the loop and report**. Leave the failing phase's commits local and unpushed. Tell the user: which phase, the findings that survived (verbatim), what the implementer said about them, and the options — **retry with their guidance**, **re-plan** (send the planner back in), or **stop**. Log `escalation`. Pushing through confusion produces PRs nobody can trust.

**Completion criterion:** every phase is ticked and pushed, or the loop has stopped on an escalation or size pause the user has been told about.

## Step 3 — Gate

Once every phase is pushed:

1. **CI** — `gh pr checks <pr> --watch --fail-fast`, bounded at about ten minutes. Still running at the bound is reported as still running, never as passing.
2. **Sonar gate**, where available — the gate endpoint in [`SONAR-CLI.md`](SONAR-CLI.md#what-replaces-the-dashboard) is the authority.

**Red** → add a `ci-fix` phase to the plan doc (What = the failing check or each Sonar issue's rule + `file:line`, verbatim) and run it through Step 2 — same three attempts (build + two re-work rounds), same escalation. Then gate again. Log `ci`.

**Green** → update the PR body (below), then `gh pr ready <pr>`.

PR body — written for a reviewer, linking the plan rather than retelling it:

- **Summary** — what and why, one or two sentences, ticket linked.
- **Changes** — one line per phase commit.
- **Testing** — each AC and the evidence that proves it; any AC proven only by reasoning gets its own **Needs eyes** heading with where to look.
- **Assumptions** — every Assumed item, since checking them is the reviewer's main job.
- **Size** — actual vs limit, and the Opt-out reason if one was taken.

**Completion criterion:** checks and gate green and PR marked ready — or a red check escalated, or a pending one reported as pending.

## Step 4 — Report

- The PR URL and its state.
- Every **assumption** and **open question**. If the user waived the grill or sign-off, say so — the list carries decisions a person would otherwise have made.
- Any **Needs eyes** items.
- Any escalation, size pause or pending check, and where the run stopped.
- Size: actual vs limit.
- Whether Sonar was available — without it, `little-address` will need the issue list pasted.
- **Next**: when review lands, run `little-address`; once approved, run `little-retro` before merging (it removes the plan doc). Merging is the user's.

**Completion criterion:** every PR detail, assumption, escalation and next step is in the report.

## Resuming

A plan doc on the current branch means a run is already under way. Read the doc and the run log, then pick up at the first thing not done: plan not signed off → Step 1's sign-off; unticked phases → Step 2 at the first one; all ticked → Step 3. A ticked phase with unpushed commits gets verified before it's pushed. Log `intervention: resumed at <where>`.

## Guardrails

- **One phase, one commit.** Bundling phases costs the review benefit of phasing.
- **Merging is the user's.** The loop raises the PR and marks it ready; that's all.
- **Pushed history is read history.** Never amend, rebase or force-push anything already pushed. Squashing only ever touches the current phase's unpushed commits.
- **Escalate rather than improvise.**
- **Subagents share this checkout.** Never switch branches, edit or commit while one may still be running.
- **Log as it happens**, per [`RUN-LOG.md`](RUN-LOG.md) — a retro across sessions only sees what got written down.
