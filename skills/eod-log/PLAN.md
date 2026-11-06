# Plan: eod-log — end-of-day calendar time log

## Understanding
`/eod-log [date]` collects Jira, git, Claude sessions and Slack (own posts) activity, builds 15-min blocks linked to Jira inside 08:30–15:00, flags no-Jira/unknown/outside-hours, reviews in chat, then writes pink 🕒 events to the primary calendar. Full spec: [`eod-handoff.md`](eod-handoff.md).

## Phases

### Phase 0: Branch
- [x] What: new branch `eod-log` off `main` (not `skill-improvements`)
- [x] Commit: none (housekeeping)
- [x] Verification: `git branch --show-current` = `eod-log`

### Phase 1: Spike – connector capabilities
- [x] What: confirm Calendar `create_event` can set `colorId` (Flamingo), transparency = free, no reminders; Slack `from:me on:<date>` returns own posts with times; find JQL for "my Jira activity on date"; get Atlassian cloud id
- [x] Commit: `skills/eod-log/CONNECTORS.md` with exact call shapes + findings; update open items in `eod-handoff.md`
- [x] Verification: Manual – external tools, nothing to unit test. Proof = one test event created + deleted, findings recorded

### Phase 2: Block builder (core logic)
- [ ] What: `scripts/build_blocks.py` – normalised activity + meetings + existing 🕒 blocks + date (JSON in) → proposed blocks (JSON out):
  - Jira key extraction (branch → commit → Slack → Jira)
  - same-ticket grouping, merge gaps < 30 min, 15-min rounding/minimum
  - no overlap with meetings or existing 🕒 blocks
  - window 08:30–15:00; outside-hours flag; gap < 60 min = unknown, ≥ 60 min = break
  - title/description/colour formatting (no Slack/DM text or commit messages in description)
- [ ] Commit: script + `tests/test_build_blocks.py`
- [ ] Verification: `python3 -m unittest discover skills/eod-log/tests`

### Phase 3: Local collectors
- [ ] What: `scripts/collect_local.py <date>` – git commits by `mandy.hale@madecurious.com` across `~/projects` + `~/dev` (incl. `__worktrees`, depth-capped, skip `node_modules`) and Claude session jsonl (`cwd`, `gitBranch`, `timestamp`; UTC → Pacific/Auckland) → normalised activity JSON
- [ ] Commit: script + tests using a temp git repo and fixture jsonl
- [ ] Verification: `python3 -m unittest discover skills/eod-log/tests`; run on a real date, runtime < ~10 s

### Phase 4: SKILL.md workflow
- [ ] What: `SKILL.md` – parse date arg; run collector; fetch Jira/Slack/Calendar via connectors (per `CONNECTORS.md`); normalise to builder input; show table (flagged first); handle replies (`3: KEY` verified in Jira, `5: text`, `7: skip`, loose Jira search); create all events on approval; report what was created
- [ ] Commit: `SKILL.md` (+ any reply-parsing helper, with tests)
- [ ] Verification: unit tests still pass; Manual: real run on today – LLM-driven flow can't be unit tested. Check table looks right, re-run proposes nothing new, events are pink/free/no reminders, events appear in Toggl calendar view

### Phase 5: Docs + version
- [ ] What: entry in `docs/SKILLS.md`; bump version in `plugin.json` + `marketplace.json`
- [ ] Commit: docs + version bump
- [ ] Verification: `python3 -m json.tool` on both json files; versions match (grep)
