# `/eod-log` – hand-off

End-of-day skill. Works out what I did today, proposes calendar time blocks linked to Jira, flags anything it can't link, then writes the approved blocks to Google Calendar. Toggl picks them up through its calendar integration.

**Goal:** a clear view of the day, and a calendar that maps 1:1 to Toggl entries with little effort.

Decided in a grill-me session, 2026-11-06.

## Location

- `~/dev/my-skills/skills/eod-log/SKILL.md` (my-skills plugin, alongside `little-loop`)
- Invoke: `/eod-log [date]`. Date defaults to today; also takes `yesterday` or `YYYY-MM-DD`

## Sources

| Source | How | Gives |
|---|---|---|
| Jira | Atlassian MCP: JQL for issues I updated/commented on/transitioned on the date | ticket key, activity time |
| Git | `git log --author=mandy.hale@madecurious.com --all` across repos in `~/projects` and `~/dev` (include `*__worktrees`) | commit time, msg, branch |
| Claude sessions | `~/.claude/projects/*/*.jsonl`: fields `cwd`, `gitBranch`, `timestamp` (UTC) | session start/end per repo/branch |
| Slack | Slack MCP search `from:me on:<date>` (public + private + DMs) | message time, text (for matching only) |
| Calendar (read only) | Google Calendar MCP, primary `mandy.hale@madecurious.com` | existing meetings + existing 🕒 blocks |

Existing meetings are **not** turned into blocks (they already sync to Toggl). They're only used to stop overlaps.

All times shown and written in `Pacific/Auckland`. Convert UTC timestamps.

## Ticket matching

Find a Jira key (`[A-Z][A-Z0-9]+-\d+`) in this order:
1. branch name (git / Claude `gitBranch`)
2. commit message
3. Slack message text
4. Jira activity (the key is the ticket itself)

No key → flagged **no Jira**. No repo → default ticket map yet (could be added later).

## Building blocks

- Group nearby activity on the same ticket into one block
- Merge gaps under 30 min between same-ticket activity (if no meeting in between)
- Round to 15 min; minimum block 15 min
- Never overlap existing meetings or existing 🕒 blocks
- Working window **08:30–15:00**
  - activity outside the window → shown, flagged **outside hours** (I choose log/skip)
- Gaps inside the window with no activity/meeting:
  - under 60 min → flagged **unknown**
  - 60 min or more → treated as a break, left empty, not flagged

## Re-runs

Existing 🕒 blocks on that day = done. Leave them untouched (keeps manual edits); only propose blocks for time they don't cover. Never delete.

## Review flow (nothing is written before approval)

1. Show a table: `# | time | title | sources | flag`, flagged rows first
2. I reply per row:
   - `3: DIAMP-1902` → check the ticket exists in Jira, use its summary in the title
   - `5: standup prep` → plain-text title, no Jira link
   - `7: skip` → not logged
   - `3: the husky ticket` → search my recent Jira tickets, suggest a match, confirm
3. On approval, create all blocks in one go and report what was created

## Calendar event format

- **Calendar:** primary (`mandy.hale@madecurious.com`)
- **Title:** `🕒 DIAMP-1841 · Agency eligibility request emails`, or `🕒 <my description>` if no Jira
  - Toggl uses the event title as the entry description, so keep it clean
- **Colour:** pink, Google "Flamingo" (`colorId` 4: check against the colours API)
- **Show as:** free (transparency `transparent`)
- **No** guests, **no** reminders
- **Description:** Jira link + general summary only, e.g. `3 commits, 1 PR review, 2 Slack threads`. **Never** include Slack message text, DM content or commit messages (main calendar can be seen by coworkers)

## Toggl

No Toggl API or token. I turn events into entries myself in Toggl's calendar view. Prerequisite: Toggl's Google Calendar integration is connected to the primary calendar.

## Out of scope (for now)

- Writing directly to Toggl (API)
- Repo → default ticket map
- Jira worklogs (`addWorklogToJiraIssue`)
- Scheduling it to run automatically

## Open items for the builder

- ~~Flamingo `colorId`~~ → `"4"`, confirmed (see [`CONNECTORS.md`](CONNECTORS.md))
- ~~Calendar MCP transparency / colour~~ → `availability: AVAILABILITY_FREE`, `colorId`, `useDefaultReminders: false`, confirmed
- ~~JQL for my activity~~ → `updatedBy(<account id>, date, date)` + per-ticket changelog/comments by me
- ~~Atlassian cloud id~~ → fixed id in `CONNECTORS.md`
- Repo discovery: skip `node_modules`/vendor; cap search depth so it stays quick (Phase 3)
