# Plan doc template

Copy into the plan path (`docs/plans/<TICKET>-<short-slug>.md` unless the repo's `CLAUDE.md` names another) and fill every section. **The headings are a contract** — little-loop, little-implement, little-verify, little-address and little-retro read them by name. Keep them exactly.

---

# <TICKET> — <one-line title>

**Source:** <ticket URL or "pasted"> · **Branch:** `<TICKET>-<slug>` · **Base:** `<default branch>`

## Problem statement

<Two or three sentences: what we're solving and why.>

## Scope

**In scope**

- <…>

**Non-goals**

- <what this deliberately does not do>

## Acceptance criteria

1. <Concrete, checkable condition.>

## Decided vs assumed

Mark each decided item with where it came from — `(ticket)`, `(code)`, or `(grill)` for one the user settled. A plan with no `(grill)` items is one where nobody was asked.

**Decided**

- <…> (ticket | code | grill)

**Assumed** (unconfirmed — verify checks each one held; the PR lists them for the reviewer)

- <…>

## Open questions

What the grill left open, what it blocks, and who can answer. Empty is valid.

- <…>

## Code map

- `<path>` — <why it's relevant>

## Approach

<How it's solved within the existing architecture. Name any structural change so it arrives as a decision, not a surprise in the diff.>

## Phases

One phase = one commit. Ordered by dependency, riskiest first. Each phase stands on its own: the repo builds and its tests pass after it lands.

- [ ] **1 — <name>** · covers AC 1, 2
  - **What:** <the change this phase makes>
  - **Commit:** `feat: <TICKET> <description>` — <what's in it, and what's left for the next phase>
  - **Verify:** <exact commands, test names, observable behaviour. "Manual: <reason automation doesn't fit>" only as a last resort>
  - **Size:** <estimate, e.g. "~3 files, ~80 lines">
- [ ] **2 — <name>** · covers AC 3
  - **What:** <…>
  - **Commit:** <…>
  - **Verify:** <…>
  - **Size:** <…>

**Total size:** <sum of estimates> against <limit> — <within limit | over>

<!-- Only when over the limit and the user chose to go anyway: -->
**Opt-out:** <why this PR can't be cut smaller>

## Risks

- <Risk or unknown, and what we do if it happens. Implementers add deliberate trade-offs here.>
