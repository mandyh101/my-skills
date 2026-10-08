# Run log

One plain-text file per ticket, outside the repo, so a loop that spans several sessions still leaves one record behind for [`little-retro`](../little-retro/SKILL.md):

```
~/.claude/loop-runs/<repo>/<TICKET>.md
```

`<repo>` is `basename "$(git rev-parse --show-toplevel)"`. Create the directory if missing. It never lives in the repo, so it never lands in a PR and survives the plan doc being deleted.

## Line format

Append only. One dated line per event, written the moment it happens — never reconstructed later from memory:

```
YYYY-MM-DD <skill> <event>: <short note>
```

```bash
mkdir -p ~/.claude/loop-runs/<repo>
echo "$(date +%F) little-loop escalation: phase 3 — verifier and implementer disagree on null handling" >> ~/.claude/loop-runs/<repo>/<TICKET>.md
```

The first line of a new file is a header: `# <TICKET> — <title> · plan: <plan doc path> · PR: <url once known>`.

## Who writes what

One event, one writer — a line written twice inflates the count retro reads.

| Event | Writer | Note carries |
|---|---|---|
| `start` | little-loop | base branch, Sonar available yes/no |
| `grill` | little-plan | questions asked, decided count, assumed count |
| `signoff` | little-loop | go / changed (what) / stopped; size opt-out if taken |
| `phase-done` | little-loop | phase N, rounds taken, `size: est X, actual Y` |
| `rework` | little-loop | phase N, round, one-line reason per blocker |
| `assumption-broken` | little-implement | which assumption, what was actually true |
| `size-pause` | little-loop | actual vs limit, what the user chose |
| `escalation` | little-loop | phase, why it stopped |
| `intervention` | little-loop | any time the user steps in mid-run, even if the run recovers |
| `ci` | little-loop | which check / Sonar condition failed, and outcome |
| `address` | little-address | PR round N; counts per triage bucket; wrong assumptions named |
| `retro` | little-retro | findings: fix (issue URL) / watching / dropped |

## What stays out

Event types, counts and short notes only. No ticket prose, customer data, secrets, or reviewer names — the note says what class of thing happened, not who.
