# my-skills

Personal Claude Code skills — the **little-loop** family (take a ticket to one small, reviewable PR, one phase at a time) and **eod-log** (end-of-day time log to calendar/Toggl).

## Quick Navigation

| Document | Purpose |
|----------|---------|
| **[SKILLS.md](./docs/SKILLS.md)** | What each skill does, when it runs, how they fit together |
| **[INSTALLATION.md](./docs/INSTALLATION.md)** | Installing from the marketplace, local testing, updates |
| **[CONTRIBUTING.md](./docs/CONTRIBUTING.md)** | Adding or changing skills, versioning |

## The little-loop family

- `little-loop` — entry point. Grills the ticket, gets a phased plan signed off, dispatches the rest.
- `little-plan` — turns a ticket into a phased plan doc.
- `little-implement` — builds one phase at a time.
- `little-verify` — checks a built phase against the plan, always a fresh agent.
- `little-address` — works through PR review comments, failed checks and Sonar.
- `little-retro` — retro on a finished run, raises a GitHub issue with skill improvements, cleans up the plan doc.

## Other skills

- `eod-log` — end of day: turns Jira, git, Claude and Slack activity into pink 🕒 calendar blocks linked to Jira (Toggl picks them up), flags time with no ticket for you to fill in.

See [`docs/SKILLS.md`](./docs/SKILLS.md) for the full reference.
