---
name: eod-log
description: Use at the end of the day to log time — gathers the day's Jira, git, Claude session and Slack activity, proposes pink 🕒 calendar blocks linked to Jira tickets (which Toggl picks up), flags time with no ticket for the user to fill in, and writes the blocks only after review. Triggers on "/eod-log", "eod log", "log my day", "end of day time log".
---

# EOD log

Turn the day's activity into 🕒 calendar blocks the user turns into Toggl entries. **Nothing is written to the calendar until the user approves the table.** Never edit or delete existing events.

References: [`CONNECTORS.md`](CONNECTORS.md) (exact connector calls and ids), [`eod-handoff.md`](eod-handoff.md) (the agreed rules). Scripts live in this skill's `scripts/` folder; run them with `python3`.

Keep intermediate files (Slack text included) in the session scratchpad, never in the repo.

## Step 1 — Day

The argument: none or `today` → today; `yesterday`; or `YYYY-MM-DD`. All times are `Pacific/Auckland`. Tell the user which date you're logging.

## Step 2 — Gather (run these in parallel)

1. **Local:** `python3 <skill dir>/scripts/collect_local.py <date>` → activity list (git + Claude).
2. **Calendar:** `list_events` for the day (see `CONNECTORS.md`).
   - `summary` starts with `🕒` → `logged`
   - other timed events I haven't declined, that aren't `transparency: transparent` → `meetings`
   - skip all-day events
3. **Jira:** `updatedBy` JQL → keys + summaries. Then, **in one subagent** (per-ticket changelogs are huge: full description diffs and years of history, often 80k+ characters each), `getJiraIssue` (changelog + comments) for each key. The subagent returns **only** a JSON list `[{"key", "time"}]`: one per changelog history / comment **by me, on the date**, ignoring worklog-only histories. Turn each into `{"time", "source": "jira", "key"}`.
4. **Slack:** `from:<@me> on:<date>`, following the cursor to the end → `{"time", "source": "slack", "text", "where": "<channel or DM>"}`.

A connector failing isn't fatal: carry on without it and say which source is missing in the table header.

## Step 3 — Build

Write the builder input (format in the `build_blocks.py` docstring): `date`, `activity` (all four sources), `meetings`, `logged`, `summaries` (from Jira), and `now` (current local time) when logging today, so time that hasn't happened yet isn't flagged. Run:

```
python3 <skill dir>/scripts/build_blocks.py < input.json > blocks.json
```

If `missing_summaries` isn't empty (keys only seen in branches/commits), `getJiraIssue` each one with `fields: ["summary"]`, add the result to `summaries`, and run it again. A key that 404s → treat its blocks as `no-jira`.

## Step 4 — Review table

Number the rows. **Flagged rows first** (in time order), then the rest in time order:

```
Logging Thu 5 Nov · 08:30–15:00 · sources: Jira, git, Claude, Slack

 #  time         min  what                                          flag
 1  10:00–10:30   30  ? (Slack: #gdda-marketplace, DM)              no Jira
 2  14:15–15:00   45  ?                                             unknown
 3  15:00–15:30   30  🕒 DIAMP-1841 · AGN3: Update agency emails    outside hours
 4  09:45–10:00   15  🕒 DIAMP-1841 · AGN3: Update agency emails
```

- `what`: the title, or `?` plus `where` hints (repos, channels) for untitled rows. Hints are for the user only; they never go in the calendar
- no-Jira row with a `suggestion` (something tangible from the branch or repo, e.g. `eod-log`): pre-fill the title as `🕒 <suggestion>` and flag it `no Jira (suggested)`. It's created on `go` unless the user changes or skips it
- Show the total logged and total flagged time under the table

Then explain the replies, briefly:

| Reply | Effect |
|---|---|
| `3: DIAMP-1902` | check the key with `getJiraIssue`; title `🕒 DIAMP-1902 · <summary>`, description gets the Jira link |
| `5: standup prep` | title `🕒 standup prep`, no Jira link |
| `3: the husky ticket` | loose Jira search (`CONNECTORS.md`); offer the top 3, confirm before using |
| `7: skip` | not logged |
| `3: log` | keep an outside-hours row as it is |
| `2: 09:00–10:15` | change the times (must not overlap meetings or other rows) |
| `go` | create everything that has a title |

Several replies can go in one message. Show the updated table after each round. Before `go`:
- outside-hours rows are **skipped** unless the user says `log`
- rows still untitled are skipped. List them when confirming

## Step 5 — Create

On `go`, first merge rows that touch and have the same title into one row (e.g. 10:30–11:45 and 11:45–12:45 CANZ-2287 → 10:30–12:45). Then create every titled, not-skipped row with `create_event`, using the exact fields in `CONNECTORS.md` (`colorId "4"`, `AVAILABILITY_FREE`, `useDefaultReminders: false`, `notificationLevel: NONE`, no attendees). Description:
- Jira row: the builder description (Jira link + counts)
- text row: just the counts line (or empty)
- **never** Slack text, DM content, channel names or commit messages

Then report: rows created (time + title), rows skipped, and anything that failed. Remind the user to turn the blocks into entries in Toggl's calendar view.

## Re-runs

Running again for the same date is safe: existing 🕒 blocks go in as `logged`, so the builder only proposes time they don't cover.
