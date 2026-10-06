---
name: little-implement
description: Second step of little-loop — builds one phase of a little-loop plan doc, or re-works it after little-verify blocked it. Dispatched by little-loop.
disable-model-invocation: true
---

# Little implement

Build **one phase** from the plan doc. The doc is your contract: its acceptance criteria say what to build, the phase entry says what this commit delivers and how it will be proven.

Review belongs to `little-verify`, which reads your diff cold. An implementer grading their own work is the one reviewer guaranteed to be sympathetic.

## First: which mode?

- **Fresh phase** — no findings in your prompt. Work steps 1–4.
- **Re-work round** — your prompt starts "re-work round" and carries the verifier's findings. Go to [Re-work rounds](#re-work-rounds).

**Completion criterion:** you've named your mode.

## Step 1 — Load

Read the plan doc. Take the named phase's **What**, **Commit**, **Verify** and **Size**, the acceptance criteria it covers, and the **Assumed** list. No plan doc → stop and say so; a plan invented at build time has had no scrutiny.

If an assumption turns out false in the code, **stop and report it** — don't code around it. A broken assumption is a planning failure, and a diff hides it. Log it per [`RUN-LOG.md`](../little-loop/RUN-LOG.md): `assumption-broken: <which>, actually <what>`.

**Completion criterion:** you can state what this phase delivers, which ACs it covers, and how it will be verified.

## Step 2 — Build the phase

Write the change with its tests alongside, test-first where there's a test surface (per the `test-driven-development` skill). Tests assert **behaviour, not implementation**.

- **Stay inside the phase.** Everything in the diff traces to this phase's **What**. Work belonging to a later phase waits for it; a tidy-up belongs in its own ticket; a structural change the phase implies is a decision to report, not a detour to take.
- **Write to the repo's documented limits first pass** — lint rules, complexity limits, Sonar rules the repo's docs name. The quality gate only runs after push, at the end of the loop.
- **No loop vocabulary in committed code.** "Phase 2", "round 1", the plan doc's section names mean nothing to the next reader. Cite the ticket key or AC instead. Comments say what the code can't.
- **Watch the size.** Measure this phase's diff per [`SIZE.md`](../little-loop/SIZE.md) as you go. Well over the phase's **Size** estimate → stop and report rather than commit: the plan cut this phase wrong, and that's the user's call to make.
- **Record trade-offs.** A shortcut taken on purpose goes in the plan doc's **Risks**, so the reviewer weighs a decision rather than finding a surprise.

**Completion criterion:** the phase's change is written, its tests cover what **Verify** names, and every trade-off is recorded.

## Step 3 — Get the gates green

Run, and get passing:

1. Every command the phase's **Verify** line names.
2. The repo's own pre-PR checks for what you touched — whatever `CLAUDE.md` / `AGENTS.md` / `CONTRIBUTING.md` names, else the `lint` / `typecheck` / `test` scripts in `package.json` (or the equivalent `Makefile` / `composer.json` targets), scoped to the files you touched where the tool allows.
3. The loop-vocabulary check — any hit is a line to fix:
   ```bash
   git diff <base>...HEAD -- . ':(exclude)<plan doc path>' | grep -inE '^\+.*\b(phase|round) [0-9]'
   ```
4. The Sonar secrets sweep, where the loop said Sonar is available: `sonar analyze --base <base>` ([`SONAR-CLI.md`](../little-loop/SONAR-CLI.md)). A hit is blocking. It is a leak check, not the quality gate.

Keep each command's output — your report quotes it. Pipe through `tee` only with `set -o pipefail`, or a red run reads as green:

```bash
set -o pipefail
<command> 2>&1 | tee "$TMPDIR/little-<name>.log"
```

The result comes from the exit status, never from output that looks clean.

**Completion criterion:** every command above has run and passed, and you can quote its output.

## Step 4 — Commit and tick

Tick the phase's checkbox in the plan doc (`- [ ]` → `- [x]`), then commit the phase **and** the tick together as one commit, using the phase's **Commit** line: `feat|fix|chore: <TICKET> <description>`.

A pre-commit hook that auto-fixes and aborts is the hook working — re-stage and commit again.

**Stay on the branch you were handed.** No pushing, no branch switching, no rebasing — those belong to `little-loop`.

**Completion criterion:** one commit on the branch holds the phase and its tick; your report names what you built, what you ran (with output), its size against the estimate, and anything you stopped on.

## Re-work rounds

You're on a branch that already has this phase's commit. Your prompt carries the plan doc path, the phase, the phase commit sha and the findings **verbatim**.

Fix **exactly the findings** — a re-work that also tidies unrelated code sends the reviewer back to the start. Rejoin at [Step 3](#step-3--get-the-gates-green), then commit the fix as a fixup of the phase commit, which the loop squashes in once the phase passes:

```bash
git commit --fixup=<phase commit sha>
```

**A finding you think is wrong gets an argument, not a fix.** Verifiers misread plans; silently "fixing" a non-problem makes the next round worse.

**This is the last attempt.** If it isn't clean the loop stops and nothing gets pushed, so an honest "I can't fix this properly, here's why" is the most useful thing you can produce. The job is to make the code right, not the check pass. Before touching code, re-read each finding against the acceptance criteria — a mismatch there is usually the real cause.

**Completion criterion:** every finding is fixed or argued against, the checks pass again, the fixup is committed, and your report says which findings you addressed and how.
