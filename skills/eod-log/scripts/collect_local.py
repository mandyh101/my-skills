#!/usr/bin/env python3
"""Collect a day's local activity (git commits + Claude Code sessions) for build_blocks.py.

Usage: collect_local.py <YYYY-MM-DD> [--roots DIR ...] [--claude-dir DIR] [--author EMAIL]

Writes a JSON list of activity items on stdout:
  {"time": "2026-11-05T09:12:00", "source": "git"|"claude",
   "branch": "...", "message": "...", "where": "<repo>", "session": "<id>"}
Times are local Pacific/Auckland, no offset. Stdlib only.
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import date as Date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Pacific/Auckland")
DEFAULT_ROOTS = ("~/projects", "~/dev")
DEFAULT_CLAUDE_DIR = "~/.claude/projects"
DEFAULT_AUTHOR = "mandy.hale@madecurious.com"
MAX_DEPTH = 3                  # ~/projects/<repo>/<nested repo or worktree>
SKIP_DIRS = {"node_modules", "vendor", "dist", "build", "public", "resources", "__pycache__"}
CLAUDE_TYPES = {"user", "assistant"}


def day_bounds(day):
    """Start/end of `day` in local time, as aware datetimes."""
    start = datetime.combine(day, time(), TZ)
    return start, start + timedelta(days=1)


def to_local(dt):
    return dt.astimezone(TZ).replace(tzinfo=None, microsecond=0)


def find_repos(roots, max_depth=MAX_DEPTH):
    """Dirs containing .git (dir, or file for worktrees), up to max_depth below each root."""
    repos = []
    for root in roots:
        root = Path(root).expanduser()
        if not root.is_dir():
            continue
        stack = [(root, 0)]
        while stack:
            path, depth = stack.pop()
            if (path / ".git").exists():
                repos.append(path)
            if depth >= max_depth:
                continue
            try:
                children = [c for c in path.iterdir()
                            if c.is_dir() and not c.is_symlink()
                            and not c.name.startswith(".") and c.name not in SKIP_DIRS]
            except OSError:
                continue
            stack.extend((c, depth + 1) for c in children)
    return sorted(repos)


def git_activity(repos, day, author):
    start, end = day_bounds(day)
    # --since/--until filter on committer date; widen and filter on author date below
    since = (start - timedelta(days=2)).isoformat()
    until = (end + timedelta(days=1)).isoformat()
    seen = set()
    items = []
    for repo in repos:
        try:
            out = subprocess.run(
                ["git", "-C", str(repo), "log", "--all", "--source", f"--author={author}",
                 f"--since={since}", f"--until={until}", "--format=%H%x1f%aI%x1f%S%x1f%s"],
                capture_output=True, text=True, timeout=20,
            ).stdout
        except (OSError, subprocess.TimeoutExpired):
            continue
        for line in out.splitlines():
            parts = line.split("\x1f")
            if len(parts) != 4:
                continue
            sha, authored, source, subject = parts
            when = datetime.fromisoformat(authored)
            if sha in seen or not (start <= when < end):
                continue
            seen.add(sha)
            items.append({
                "time": to_local(when).isoformat(),
                "source": "git",
                "branch": _branch_name(source),
                "message": subject,
                "where": repo.name,
            })
    return items


def _branch_name(ref):
    for prefix in ("refs/heads/", "refs/remotes/origin/", "refs/remotes/"):
        if ref.startswith(prefix):
            return ref[len(prefix):]
    return ref


def claude_activity(claude_dir, day):
    """One item per session per minute, from user/assistant messages on `day`."""
    start, end = day_bounds(day)
    # Local day spans two UTC dates; cheap text filter before parsing JSON
    utc_dates = {start.astimezone(ZoneInfo("UTC")).date().isoformat(),
                 (end - timedelta(seconds=1)).astimezone(ZoneInfo("UTC")).date().isoformat()}
    root = Path(claude_dir).expanduser()
    if not root.is_dir():
        return []
    seen = set()
    items = []
    for path in root.rglob("*.jsonl"):
        try:
            if datetime.fromtimestamp(path.stat().st_mtime, TZ) < start:
                continue  # last written before the day began
            with open(path, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    if not any(d in line for d in utc_dates):
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if entry.get("type") not in CLAUDE_TYPES or "timestamp" not in entry:
                        continue
                    when = datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00"))
                    if not (start <= when < end):
                        continue
                    local = to_local(when).replace(second=0)
                    session = entry.get("sessionId", path.stem)
                    if (session, local) in seen:
                        continue
                    seen.add((session, local))
                    cwd = entry.get("cwd") or ""
                    items.append({
                        "time": local.isoformat(),
                        "source": "claude",
                        "branch": entry.get("gitBranch") or "",
                        "where": Path(cwd).name if cwd else "",
                        "session": session,
                    })
        except OSError:
            continue
    return items


def collect(day, roots, claude_dir, author):
    items = git_activity(find_repos(roots), day, author) + claude_activity(claude_dir, day)
    return sorted(items, key=lambda i: i["time"])


def parse_day(value):
    if value == "today":
        return datetime.now(TZ).date()
    if value == "yesterday":
        return datetime.now(TZ).date() - timedelta(days=1)
    return Date.fromisoformat(value)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("date", nargs="?", default="today", help="YYYY-MM-DD, today or yesterday")
    parser.add_argument("--roots", nargs="+", default=list(DEFAULT_ROOTS))
    parser.add_argument("--claude-dir", default=DEFAULT_CLAUDE_DIR)
    parser.add_argument("--author", default=DEFAULT_AUTHOR)
    args = parser.parse_args(argv)
    items = collect(parse_day(args.date), args.roots, args.claude_dir, args.author)
    json.dump(items, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
