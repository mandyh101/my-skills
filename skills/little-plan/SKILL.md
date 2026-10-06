---
name: little-plan
description: First step of little-loop — turns a ticket into a phased plan doc an unattended agent can build from. Dispatched by little-loop; run by hand to plan without building.
disable-model-invocation: true
---

# Little plan

Turn a ticket into a plan doc that `little-implement` and `little-verify` can execute **with nobody watching**. A plan that says _what_ to build but not _how the agent will know it worked_ is unfinished.

## Relay mode

Under [`little-loop`](../little-loop/SKILL.md) you're a subagent: you can't talk to the user directly. Each time you need an answer, **end your turn with exactly one question** and your recommendation. The orchestrator relays it verbatim and sends the answer back to you with `SendMessage`, context intact. Run by hand, ask the user directly — same rules.

## Step 1 — Read the ticket and the code

Jira key given → pull it via the Atlassian MCP: description, acceptance criteria, comments, linked tickets that bear on scope. No key or no access → ask for the ticket text.

Ground it in the code: read the repo's `CLAUDE.md` / `AGENTS.md`, then spawn Explore subagents to find the files, components and boundaries the change touches. A plan written from the ticket alone describes a codebase that may not exist.

**Completion criterion:** you can state the acceptance criteria in your own words and name the files the change will touch.

## Step 2 — Survey what the ticket didn't settle

List every gap before deciding anything. Sweep at least:

- **Unhappy paths** — failure, timeout, 403; recoverable vs terminal; silent, inline or whole-page.
- **Empty and boundary states** — none, one, a thousand; max length; null vs missing.
- **In-flight and stale states** — loading, double submit.
- **Permissions** — who sees it, who acts on it, what others get.
- **Edges of the ticket** — implied but unstated behaviour; what a reader would assume is included that you intend to leave out.
- **Data and lifecycle** — existing records, backfill, reversibility.
- **Contradictions with the code** — the ticket describes something the code already does differently.

**Facts are looked up, never asked.** Anything the filesystem, tests, Jira or `git log` can answer is yours to resolve. What survives is the list of genuine **decisions** — where two reasonable people would choose differently. Give each one your **recommended answer** and why.

**Completion criterion:** a list of open decisions, each with a recommendation; every lookup-able question struck off.

## Step 3 — Grill

**Always grill.** Silence is not a wave-through. Only the user explicitly saying "skip the questions" / "just go" ends it early — then file your recommendations as **Assumed**.

- **One question at a time**, waiting for the answer before the next.
- **Every question carries your recommendation**, so agreeing is one word.
- **Walk the decision tree** — answers open new branches; follow them, don't work from a fixed script.
- **Push back** once where "whatever you think" lands on something expensive to get wrong.
- **Stop when the next question would be manufactured**, and say so.

Then confirm shared understanding back in a few lines, and only then write.

What the user settles is **Decided `(grill)`**. What they wave through on your recommendation without engaging is **Assumed**.

**Completion criterion:** every open decision answered or consciously deferred, shared understanding confirmed, each answer filed as decided or assumed.

## Step 4 — Assume, don't stall

For anything still open, take the most reasonable reading and record it under **Assumed**. Two exceptions where you stop and ask even if told to skip: ambiguity touching **auth, permissions, money, or data migration**; and a ticket so wide it wants re-drawing rather than phasing.

**Test-harness behaviour is never an assumption** — how a helper resolves, which suite runs a test, what a fixture seeds. Look it up and write the answer into the phase's **Verify** line. A wrong harness guess gives a green run that proved nothing.

**Completion criterion:** every gap written down as decided or assumed; nothing unresolved left in your head.

## Step 5 — Cut phases

One phase = one commit. Size it to be verifiable on its own but not so small it's commit noise — "wire up the new endpoint" is a phase; a one-line change isn't.

- **Riskiest first.** A spike, an unfamiliar library, a tricky integration goes early, so surprises land while the plan is cheap to change.
- **Each phase leaves the repo green** — builds, tests pass, nothing half-wired that breaks the app.
- **Tests ride with the code they prove**, in the same phase — never a "write the tests" phase at the end.
- **Estimate each phase's size**, and the total, against [`SIZE.md`](../little-loop/SIZE.md). Over the limit → **cut scope or split the ticket first**; if it genuinely can't shrink, say so plainly in your report — the orchestrator puts it to the user at sign-off. Don't write an **Opt-out:** yourself; that's the user's call.

**Completion criterion:** every phase has What / Commit / Size, each leaves the repo green, and the total is stated against the limit.

## Step 6 — Give every phase its evidence

This is what lets the loop run unattended. Each phase's **Verify** line names:

- **Which tests, in which files** — down to the test name, so the run can be scoped.
- **The exact commands** to run them, copy-pasteable.
- **Observable behaviour** for anything user-facing, as the automated test that asserts it.
- **Which acceptance criteria** it covers, by number.

Automated first. "Manual: <reason>" only where nothing automatable fits, with the reason stated. A phase you can't write a Verify line for is cut wrong — re-cut it.

**Completion criterion:** every phase names tests, runnable commands and ACs; none says only "test it".

## Step 7 — Write the doc

Write to `docs/plans/<TICKET>-<short-slug>.md` (or the path the repo's `CLAUDE.md` names) using [`PLAN-TEMPLATE.md`](PLAN-TEMPLATE.md). Keep its headings exactly.

**Leave it uncommitted** — branches and commits belong to `little-loop`. Run by hand, that leaves the user's git state as you found it.

Append to the run log per [`RUN-LOG.md`](../little-loop/RUN-LOG.md): `grill: <n> questions, <d> decided, <a> assumed`.

**Completion criterion:** the file exists with every section filled, decided items carry provenance, open items are under **Open questions**, the run log line is written, and git state is unchanged.

Report the doc path, the total size against the limit, and anything under **Open questions**.

## Revisions

The orchestrator may send back a change the user asked for at sign-off. Edit the doc in place, keep the decided/assumed split honest (a user-requested change is **Decided `(grill)`**), and report what changed.
