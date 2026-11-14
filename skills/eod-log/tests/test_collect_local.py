import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from collect_local import claude_activity, collect, find_repos, git_activity  # noqa: E402

DAY = date(2026, 11, 5)
ME = "me@example.com"


def git(repo, *args, env=None):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True,
                   env={**os.environ, **(env or {})})


def commit(repo, message, when, author=ME):
    """Commit with fixed author + committer date (ISO with offset)."""
    (repo / "f.txt").write_text(message)
    git(repo, "add", ".")
    git(repo, "-c", f"user.email={author}", "-c", "user.name=T", "commit", "-q", "-m", message,
        env={"GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when})


def make_repo(path, branch="main"):
    path.mkdir(parents=True)
    git(path, "init", "-q", "-b", branch)
    return path


class FindRepos(unittest.TestCase):
    def test_finds_nested_and_skips_junk(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_repo(root / "outer")
            make_repo(root / "outer" / "inner")
            make_repo(root / "outer" / "node_modules" / "pkg")
            make_repo(root / "a" / "b" / "c" / "too-deep")
            (root / "wt").mkdir()
            (root / "wt" / ".git").write_text("gitdir: /elsewhere\n")  # worktree style
            found = {p.relative_to(root).as_posix() for p in find_repos([root])}
            self.assertEqual(found, {"outer", "outer/inner", "wt"})

    def test_missing_root_ignored(self):
        self.assertEqual(find_repos(["/no/such/dir"]), [])


class GitActivity(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = make_repo(Path(self.tmp.name) / "marketplace", branch="DIAMP-1841-emails")

    def tearDown(self):
        self.tmp.cleanup()

    def test_my_commits_on_day_in_local_time(self):
        commit(self.repo, "on day (UTC)", "2026-11-04T20:30:00+00:00")   # 09:30 NZDT on the 5th
        commit(self.repo, "day before", "2026-11-04T09:00:00+13:00")
        commit(self.repo, "someone else", "2026-11-05T10:00:00+13:00", author="x@example.com")
        items = git_activity([self.repo], DAY, ME)
        self.assertEqual(items, [{
            "time": "2026-11-05T09:30:00", "source": "git", "branch": "DIAMP-1841-emails",
            "message": "on day (UTC)", "where": "marketplace",
        }])

    def test_same_commit_in_two_repos_counted_once(self):
        commit(self.repo, "shared", "2026-11-05T10:00:00+13:00")
        self.assertEqual(len(git_activity([self.repo, self.repo], DAY, ME)), 1)


class ClaudeActivity(unittest.TestCase):
    def write_log(self, root, lines, name="proj/s1.jsonl"):
        path = Path(root) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(json.dumps(line) for line in lines) + "\nnot json\n")
        return path

    def entry(self, ts, type_="user", session="s1", branch="DIAMP-1841-x",
              cwd="/Users/me/projects/marketplace"):
        return {"type": type_, "timestamp": ts, "sessionId": session, "gitBranch": branch, "cwd": cwd}

    def test_messages_on_day_one_per_minute(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.write_log(tmp, [
                self.entry("2026-11-04T20:30:05.000Z"),                       # 09:30 NZDT
                self.entry("2026-11-04T20:30:40.000Z", type_="assistant"),    # same minute
                self.entry("2026-11-04T20:31:00.000Z", type_="system"),       # not a message
                self.entry("2026-11-05T11:30:00.000Z"),                       # 00:30 on the 6th
                self.entry("2026-11-04T10:00:00.000Z"),                       # 23:00 on the 4th
            ])
            items = claude_activity(tmp, DAY)
            self.assertEqual(items, [{
                "time": "2026-11-05T09:30:00", "source": "claude", "branch": "DIAMP-1841-x",
                "where": "marketplace", "session": "s1",
            }])

    def test_subagent_logs_included(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.write_log(tmp, [self.entry("2026-11-04T21:00:00.000Z")], name="proj/s1/subagents/a.jsonl")
            self.assertEqual(len(claude_activity(tmp, DAY)), 1)

    def test_old_files_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_log(tmp, [self.entry("2026-11-04T21:00:00.000Z")])
            os.utime(path, (0, 0))
            self.assertEqual(claude_activity(tmp, DAY), [])


class Collect(unittest.TestCase):
    def test_merged_and_sorted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = make_repo(root / "code" / "r", branch="DIAMP-1")
            commit(repo, "c", "2026-11-05T11:00:00+13:00")
            log = root / "claude" / "p" / "s.jsonl"
            log.parent.mkdir(parents=True)
            log.write_text(json.dumps({"type": "user", "timestamp": "2026-11-04T21:00:00Z",
                                       "sessionId": "s", "gitBranch": "DIAMP-1", "cwd": "/x/r"}) + "\n")
            items = collect(DAY, [root / "code"], root / "claude", ME)
            self.assertEqual([(i["time"], i["source"]) for i in items],
                             [("2026-11-05T10:00:00", "claude"), ("2026-11-05T11:00:00", "git")])


if __name__ == "__main__":
    unittest.main()
