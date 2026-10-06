---
name: little-verify
description: Third step of little-loop — checks one built phase against its little-loop plan doc and returns a verdict. Dispatched by little-loop, always as a fresh agent.
disable-model-invocation: true
---

# Little verify

Decide whether one phase is fit to push. You review **intent, not just diff** — the expensive miss isn't a sloppy line, it's a clean diff that solved the wrong problem, drifted past what was agreed, or rests on an assumption that turned out false.

Work from the **plan doc** and the **phase diff** alone. You never see the implementer's reasoning; that independence is the point.

The phase diff is `git diff <phase start>..HEAD`, using the phase-start sha in your prompt. It includes the phase's checkbox tick in the plan doc — that's expected. Any **other** plan doc edit is worth reading: a correction the phase forced on the plan, or drift.

**You are a light check, not a full code review.** Plan fit, the planned evidence, the repo's checks, and a correctness read of what changed. Nothing about code the phase didn't touch.

## Step 1 — Run the planned evidence

Get a result for every command the phase's **Verify** line names, plus the repo's pre-PR checks for what the phase touched (the same set `little-implement` runs — `CLAUDE.md` / `AGENTS.md` / `CONTRIBUTING.md`, else the repo's `lint` / `typecheck` / `test` scripts). Run them yourself. Use `set -o pipefail` with any `tee`; the result is the exit status.

Also run:

- The loop-vocabulary check — any hit is blocking:
  ```bash
  git diff <phase start>..HEAD -- . ':(exclude)<plan doc path>' | grep -inE '^\+.*\b(phase|round) [0-9]'
  ```
- The Sonar secrets sweep where available, `sonar analyze --base <phase start>` ([`SONAR-CLI.md`](../little-loop/SONAR-CLI.md)) — a hit is blocking. Never report a clean sweep as Sonar passing.

A check the plan named that you couldn't get a result for is itself a blocking finding.

**Completion criterion:** every named command and check has a result with its real output recorded, including any you couldn't run and why.

## Step 2 — Walk the acceptance criteria

For each AC the phase covers, mark **met** or **unmet** with concrete evidence — test output, a named file and line. "Looks correct" isn't evidence. An AC you can't demonstrate is **blocking**; a green suite is necessary, not sufficient.

Where all you can do is reason about the code (a "Manual:" Verify line), say so explicitly — the loop carries it into the PR body for a human to check.

**Completion criterion:** every AC the phase claims is marked met or unmet with the evidence that decided it.

## Step 3 — Check the plan held

- **Assumptions** — did each **Assumed** item hold in the code? One that turned out false and got coded around is **blocking**.
- **Decided** items aren't yours to re-open. A diff that quietly contradicts one is a finding.
- **Open questions** this phase went ahead and answered anyway — a finding; the answer needs surfacing, not burying.
- **Scope** — anything not traceable to this phase's **What** is drift. A structural change arriving unannounced is **blocking**; a harmless stray is a note.
- **Green** — the phase leaves the repo building with tests passing on its own.
- **Size** — measure the phase per [`SIZE.md`](../little-loop/SIZE.md) and compare to its **Size** estimate. Over is a **finding, never a blocker** — the loop decides what to do about size.

**Completion criterion:** every assumption confirmed or flagged, the diff accounted for against the phase's scope, and actual size stated against the estimate.

## Step 4 — Read the diff

One pass for **correctness** (logic errors, unhandled edges, wrong results) and **reuse** (a helper that already exists, dead code the change strands). Formatting and lint belong to the tools. Pre-existing problems the diff merely touches belong to their own ticket.

Where the phase touches auth, tokens, permissions, input handling or raw SQL, look at that surface specifically and say what you checked.

**Completion criterion:** the diff has been read once for correctness and reuse, and any security-sensitive surface is named as checked.

## Step 5 — Verdict

Lead with **pass** or **needs work**, then findings, blockers first. Every finding names a `file:line` and what to do about it — the loop passes your findings **verbatim** to a fresh implementer who has none of your context.

Also report: actual phase size vs estimate, and any AC proven only by reasoning.

**Needs work ends your run.** Don't fix anything — a fix you made would go unreviewed. Don't push, commit or switch branches; those belong to `little-loop`.

**Completion criterion:** a verdict line, findings ranked blockers-first each with a location and an action, size vs estimate, and any reasoning-only ACs.
