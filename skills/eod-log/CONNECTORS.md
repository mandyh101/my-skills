# Connector calls

Exact call shapes for `/eod-log`, confirmed in the Phase 1 spike (2026-11-06). All times `Pacific/Auckland`.

## Fixed ids

| What | Value |
|---|---|
| Atlassian cloud id | `da048ffb-bf95-4f80-9ba3-b1565a904916` (`madecurious.atlassian.net`) |
| Jira account id | `712020:2f4bee2d-1512-464f-b387-30859ebbd473` |
| Slack user id | `U08S5S9UH0R` |
| Calendar | primary (`mandy.hale@madecurious.com`) |

Ids are mine. Look them up again if the skill is ever shared (`atlassianUserInfo`, Slack tool description, `list_calendars`).

## Google Calendar

**Read meetings + existing 🕒 blocks:** `list_events`

```
startTime: <date>T00:00:00
endTime:   <date+1>T00:00:00
orderBy:   startTime
pageSize:  250
```

- 🕒 block = `summary` starts with `🕒`. Everything else with a time = meeting
- Skip all-day events, events I declined, and `transparency: transparent` events that aren't 🕒 (they don't block time)

**Create a block:** `create_event`

```
summary:             🕒 DIAMP-1841 · AGN3: Update agency registration email contents (x4)
startTime / endTime: local time, no offset, no Z (e.g. 2026-11-05T09:00:00)
colorId:             "4"                    # Flamingo – confirmed
availability:        AVAILABILITY_FREE      # → transparency: transparent – confirmed
useDefaultReminders: false                  # with no overrideReminders = no reminders – confirmed
notificationLevel:   NONE
description:         <Jira link + general summary>
```

Don't set `timeZone` (server uses mine). No `attendees`.

## Jira

**Tickets I touched on a date:** `searchJiraIssuesUsingJql`

```
jql: issuekey in updatedBy("<account id>", "<date>", "<date>") ORDER BY updated DESC
fields: ["summary", "updated", "status"]
maxResults: 50
```

- `currentUser()` **can't** be nested inside `updatedBy()` (JQL error) – pass the account id
- Both dates are inclusive
- `updated` is the last update by *anyone* – not my activity time

**My activity times on a ticket:** `getJiraIssue` per key

```
issueIdOrKey: <key>
expand: changelog
fields: ["summary", "comment"]
responseContentFormat: markdown
updateHistory: false
```

- Activity = changelog `histories[]` where `author.accountId` = mine and `created` is on the date, plus comments by me on the date
- **Ignore** histories whose only items are `WorklogId` / `timespent` / `timeestimate`. That's me logging time, not working on it
- Changelog defaults to 10 most recent histories – enough for one day; note if `total > maxResults`
- Responses are **very** large: every history includes avatars, and description edits include the full old + new text. In the first real run, 2 of 5 tickets went over 80k characters. Always do this step in a subagent that returns only `[{key, time}]`

**Check a key I give at review:** `getJiraIssue` with `fields: ["summary"]`. A 404 means the key doesn't exist

**Loose search at review** (`3: the husky ticket`):

```
jql: text ~ "<words>" AND (assignee = currentUser() OR issuekey in updatedBy("<account id>", "-14d")) ORDER BY updated DESC
```

(`currentUser()` is fine outside `updatedBy()`.) Suggest the top 3, then confirm.

## Slack

**My posts on a date:** `slack_search_public_and_private`

```
filters:               from:<@U08S5S9UH0R> on:<date>
natural_language_query: ""
sort:                  timestamp
sort_dir:              asc
response_format:       concise
limit:                 20
```

- Covers channels, private channels, group DMs and DMs; thread replies included
- Returns up to 20 per page. **Follow the `cursor`** until none is left (a busy day goes over 20)
- Each result line: `<channel or DM> - Mandy Hale: <text> <YYYY-MM-DD HH:MM:SS NZDT>`. Times are already local
- Text is used **only** for Jira key matching. Never copied into the calendar
- Most messages have no key → flagged at review, as decided

## Not found / limits

- No Toggl connector (expected – out of scope)
