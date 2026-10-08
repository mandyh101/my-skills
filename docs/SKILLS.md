# Skills reference

## little-loop

Entry point. Trigger: `little-loop <ticket>`, "run the little loop on <ticket>".

Grills the ticket, gets a phased plan signed off, then dispatches `little-implement` and `little-verify` one phase (one commit) at a time. Reads [`SIZE.md`](../skills/little-loop/SIZE.md) for the PR size limit, [`SONAR-CLI.md`](../skills/little-loop/SONAR-CLI.md) for the Sonar CLI fallback path, and [`RUN-LOG.md`](../skills/little-loop/RUN-LOG.md) for what to log and when.

## little-plan

First step, dispatched by `little-loop` (or run by hand to plan without building). Turns a ticket into a phased plan doc an unattended agent can build from — see [`PLAN-TEMPLATE.md`](../skills/little-plan/PLAN-TEMPLATE.md).

## little-implement

Second step, dispatched by `little-loop`. Builds one phase of a plan doc, or re-works it after `little-verify` blocked it.

## little-verify

Third step, dispatched by `little-loop` as a fresh agent every time. Checks one built phase against the plan doc and returns a verdict.

## little-address

Manual-only (`disable-model-invocation: true`). Works through review comments, failed checks and Sonar on a PR `little-loop` raised, using its plan doc as context.

## little-retro

Manual-only. Retro on a finished `little-loop` run — what worked, what didn't, across all its sessions. Raises a GitHub issue on this repo with the skill improvements you agree, then removes the plan doc before merge.

## Shared conventions

- **PR size limit** — [`little-loop/SIZE.md`](../skills/little-loop/SIZE.md): 300 changed lines or 10 files, overridable per-repo in `CLAUDE.md`/`AGENTS.md`.
- **Sonar CLI** — [`little-loop/SONAR-CLI.md`](../skills/little-loop/SONAR-CLI.md): what it catches, what it doesn't, how to fall back when it's not installed.
- **Run log** — [`little-loop/RUN-LOG.md`](../skills/little-loop/RUN-LOG.md): one plain-text file per ticket outside the repo, append-only, who writes what.
