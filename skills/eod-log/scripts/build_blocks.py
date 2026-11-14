#!/usr/bin/env python3
"""Turn a day's activity into proposed 🕒 calendar blocks.

Reads JSON on stdin, writes JSON on stdout. Stdlib only.

Input (all times local Pacific/Auckland, ISO, no offset):
{
  "date": "2026-11-05",
  "window": {"start": "08:30", "end": "15:00"},        # optional, these are the defaults
  "projects": ["DIAMP", "CANZ"],                       # optional: only accept keys with these prefixes
  "activity": [
    {"time": "2026-11-05T09:12:00", "source": "git|claude|slack|jira",
     "key": "DIAMP-1", "branch": "...", "message": "...", "text": "...",   # any of these, all optional
     "where": "marketplace", "session": "abc"}                             # optional, for review hints/counts
  ],
  "meetings": [{"start": "...", "end": "...", "title": "..."}],
  "logged":   [{"start": "...", "end": "...", "title": "🕒 ..."}],       # existing 🕒 blocks
  "summaries": {"DIAMP-1": "Ticket summary"},
  "now": "2026-11-05T14:03:00"                          # optional: no "unknown" gaps after this
}

Output:
{
  "blocks": [{"start", "end", "minutes", "key", "title", "description", "colorId",
              "flags": [...], "sources": {...}, "where": [...], "suggestion": ...}],
  "missing_summaries": ["DIAMP-2"]
}

Flags: "no-jira" (activity, no key), "unknown" (gap < 60 min), "outside-hours".
"suggestion": for no-jira blocks, a name for the work taken from git/Claude branch (or repo when the
branch is generic) – never from Slack. None if nothing tangible.
"""
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date as Date, datetime, time, timedelta

SLOT = 15                      # minutes
SLOTS_PER_DAY = 24 * 60 // SLOT
MERGE_GAP = 30                 # same-ticket gaps shorter than this get filled
BREAK_GAP = 60                 # empty gaps this long or longer are breaks, not flagged
DEFAULT_WINDOW = ("08:30", "15:00")
COLOUR_FLAMINGO = "4"
JIRA_BROWSE = "https://madecurious.atlassian.net/browse/"
TITLE_PREFIX = "🕒 "

KEY_RE = re.compile(r"\b([A-Z][A-Z0-9]+)-(\d+)\b")
# Things that look like Jira keys but aren't
NOT_PROJECTS = {"UTF", "CVE", "ISO", "SHA", "RFC", "GPT", "TLS", "HTTP", "PR", "AES", "MD", "IE"}

# Branch names that say nothing about the work
GENERIC_BRANCHES = {"", "HEAD", "main", "master", "develop", "dev"}

# Where to look for a key, in priority order
KEY_FIELDS = ("branch", "message", "text", "key")

SOURCE_LABELS = {
    "git": ("commit", "commits"),
    "claude": ("Claude session", "Claude sessions"),
    "slack": ("Slack message", "Slack messages"),
    "jira": ("Jira update", "Jira updates"),
}


def find_key(item, projects=None):
    for field in KEY_FIELDS:
        value = item.get(field)
        if not value:
            continue
        for prefix, num in KEY_RE.findall(value):
            if prefix in NOT_PROJECTS:
                continue
            if projects and prefix not in projects:
                continue
            return f"{prefix}-{num}"
    return None


def _slot_of(dt, day):
    """Slot index for a datetime on `day`, or None if it's another day."""
    if dt.date() != day:
        return None
    return (dt.hour * 60 + dt.minute) // SLOT


def _slot_range(start, end, day):
    """Slots touched by [start, end) on `day`."""
    day_start = datetime.combine(day, time())
    first = max(0, int((start - day_start).total_seconds() // 60) // SLOT)
    end_min = (end - day_start).total_seconds() / 60
    last = min(SLOTS_PER_DAY, -int(-end_min // SLOT))  # ceil
    return range(first, last)


def _slot_time(day, slot):
    return datetime.combine(day, time()) + timedelta(minutes=slot * SLOT)


def _hhmm_slot(hhmm):
    h, m = map(int, hhmm.split(":"))
    return (h * 60 + m) // SLOT


def _describe(key, sources):
    parts = []
    for source in ("git", "claude", "slack", "jira"):
        n = sources.get(source, 0)
        if n:
            one, many = SOURCE_LABELS[source]
            parts.append(f"{n} {one if n == 1 else many}")
    lines = []
    if key:
        lines.append(f"Jira: {JIRA_BROWSE}{key}")
    if parts:
        lines.append(", ".join(parts))
    return "\n".join(lines)


def build(data):
    day = Date.fromisoformat(data["date"])
    win = data.get("window") or {}
    win_start = _hhmm_slot(win.get("start", DEFAULT_WINDOW[0]))
    win_end = _hhmm_slot(win.get("end", DEFAULT_WINDOW[1]))
    projects = set(data.get("projects") or []) or None
    summaries = data.get("summaries") or {}

    # Slots taken by meetings or existing 🕒 blocks are off-limits
    blocked = set()
    for event in (data.get("meetings") or []) + (data.get("logged") or []):
        start = datetime.fromisoformat(event["start"])
        end = datetime.fromisoformat(event["end"])
        blocked.update(_slot_range(start, end, day))

    # Vote: which ticket owns each slot. A key always beats no key.
    votes = defaultdict(Counter)
    slot_items = defaultdict(list)
    for item in data.get("activity") or []:
        slot = _slot_of(datetime.fromisoformat(item["time"]), day)
        if slot is None or slot in blocked:
            continue
        key = find_key(item, projects)
        votes[slot][key] += 1
        slot_items[slot].append((key, item))

    owner = {}
    for slot, counter in votes.items():
        keyed = [k for k in counter if k]  # insertion order, so ties go to the first seen
        owner[slot] = max(keyed, key=counter.__getitem__) if keyed else None

    # Fill short gaps between slots owned by the same ticket
    max_fill = MERGE_GAP // SLOT - (1 if MERGE_GAP % SLOT == 0 else 0)
    owned = sorted(owner)
    for a, b in zip(owned, owned[1:]):
        gap = range(a + 1, b)
        if (0 < len(gap) <= max_fill and owner[a] == owner[b] and owner[a] is not None
                and not any(s in blocked for s in gap)
                and not _crosses_window(a, b, win_start, win_end)):
            for s in gap:
                owner[s] = owner[a]

    blocks = []

    # Runs of same-owner slots → activity blocks (split at window edges)
    for run_start, run_end, key in _runs(owner, win_start, win_end):
        sources = Counter()
        sessions = defaultdict(set)
        where = set()
        branches, repos = Counter(), Counter()
        for s in range(run_start, run_end):
            for item_key, item in slot_items.get(s, []):
                if item_key != key:
                    continue
                src = item.get("source", "")
                if src == "claude" and item.get("session"):
                    sessions[src].add(item["session"])
                else:
                    sources[src] += 1
                if item.get("where"):
                    where.add(item["where"])
                if key is None and src in ("git", "claude"):
                    branch = item.get("branch") or ""
                    if branch not in GENERIC_BRANCHES:
                        branches[branch] += 1
                    elif item.get("where"):
                        repos[item["where"]] += 1
        for src, ids in sessions.items():
            sources[src] += len(ids)

        flags = []
        if key is None:
            flags.append("no-jira")
        if run_end <= win_start or run_start >= win_end:
            flags.append("outside-hours")
        block = _block(day, run_start, run_end, key, summaries, flags, dict(sources), sorted(where))
        names = branches or repos  # a real branch name beats a repo name
        if names:
            block["suggestion"] = names.most_common(1)[0][0]
        blocks.append(block)

    # Empty, unblocked gaps inside the window (and before `now`, if given)
    gap_end = win_end
    if data.get("now"):
        now = datetime.fromisoformat(data["now"])
        if now.date() < day:
            gap_end = win_start
        elif now.date() == day:
            gap_end = min(win_end, (now.hour * 60 + now.minute) // SLOT)
    taken = blocked | set(owner)
    s = win_start
    while s < gap_end:
        if s in taken:
            s += 1
            continue
        e = s
        while e < gap_end and e not in taken:
            e += 1
        if (e - s) * SLOT < BREAK_GAP:
            blocks.append(_block(day, s, e, None, summaries, ["unknown"], {}, []))
        s = e

    blocks.sort(key=lambda b: b["start"])
    missing = sorted({b["key"] for b in blocks if b["key"] and b["key"] not in summaries})
    return {"blocks": blocks, "missing_summaries": missing}


def _crosses_window(a, b, win_start, win_end):
    return (a < win_start <= b) or (a < win_end <= b)


def _runs(owner, win_start, win_end):
    slots = sorted(owner)
    i = 0
    while i < len(slots):
        start = slots[i]
        key = owner[start]
        j = i
        while (j + 1 < len(slots) and slots[j + 1] == slots[j] + 1 and owner[slots[j + 1]] == key
               and slots[j + 1] not in (win_start, win_end)):
            j += 1
        yield start, slots[j] + 1, key
        i = j + 1


def _block(day, start_slot, end_slot, key, summaries, flags, sources, where):
    title = None
    if key:
        summary = summaries.get(key)
        title = f"{TITLE_PREFIX}{key} · {summary}" if summary else f"{TITLE_PREFIX}{key}"
    return {
        "start": _slot_time(day, start_slot).isoformat(timespec="seconds"),
        "end": _slot_time(day, end_slot).isoformat(timespec="seconds"),
        "minutes": (end_slot - start_slot) * SLOT,
        "key": key,
        "title": title,
        "description": _describe(key, sources),
        "colorId": COLOUR_FLAMINGO,
        "flags": flags,
        "sources": sources,
        "where": where,
        "suggestion": None,
    }


def main():
    json.dump(build(json.load(sys.stdin)), sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
