import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from build_blocks import build, find_key  # noqa: E402

DAY = "2026-11-05"


def at(hhmm):
    return f"{DAY}T{hhmm}:00"


def act(hhmm, source="git", **fields):
    return {"time": at(hhmm), "source": source, **fields}


def run(activity=(), meetings=(), logged=(), summaries=None, **extra):
    data = {"date": DAY, "activity": list(activity), "meetings": list(meetings),
            "logged": list(logged), "summaries": summaries or {}, **extra}
    return build(data)["blocks"]


def span(block):
    return block["start"][11:16], block["end"][11:16]


def work(blocks):
    """Blocks that came from activity (not unknown gaps)."""
    return [b for b in blocks if "unknown" not in b["flags"]]


class FindKey(unittest.TestCase):
    def test_branch_beats_message(self):
        item = {"branch": "DIAMP-1841-emails", "message": "fix CANZ-2 thing"}
        self.assertEqual(find_key(item), "DIAMP-1841")

    def test_falls_back_through_fields(self):
        self.assertEqual(find_key({"branch": "main", "message": "DIAMP-7 tidy"}), "DIAMP-7")
        self.assertEqual(find_key({"text": "see CANZ-2287"}), "CANZ-2287")
        self.assertEqual(find_key({"key": "DIAMP-1962"}), "DIAMP-1962")

    def test_ignores_lookalikes(self):
        self.assertIsNone(find_key({"message": "convert to UTF-8 and patch CVE-2024"}))

    def test_project_filter(self):
        self.assertIsNone(find_key({"text": "ABC-1"}, projects={"DIAMP"}))
        self.assertEqual(find_key({"text": "ABC-1 DIAMP-2"}, projects={"DIAMP"}), "DIAMP-2")

    def test_none_when_no_key(self):
        self.assertIsNone(find_key({"branch": "main", "message": "wip"}))


class Grouping(unittest.TestCase):
    def test_single_point_is_one_15_min_block_rounded_down(self):
        blocks = work(run([act("09:07", branch="DIAMP-1")]))
        self.assertEqual([span(b) for b in blocks], [("09:00", "09:15")])
        self.assertEqual(blocks[0]["minutes"], 15)

    def test_nearby_points_same_ticket_merge(self):
        # 09:05 and 09:31 – one empty slot between → filled
        blocks = work(run([act("09:05", branch="DIAMP-1"), act("09:31", branch="DIAMP-1")]))
        self.assertEqual([span(b) for b in blocks], [("09:00", "09:45")])

    def test_gap_of_30_min_or_more_not_merged(self):
        # 09:05 and 09:50 – two empty slots (30 min) → separate
        blocks = work(run([act("09:05", branch="DIAMP-1"), act("09:50", branch="DIAMP-1")]))
        self.assertEqual([span(b) for b in blocks], [("09:00", "09:15"), ("09:45", "10:00")])

    def test_different_tickets_not_merged_across_gap(self):
        blocks = work(run([act("09:05", branch="DIAMP-1"), act("09:35", branch="DIAMP-2")]))
        self.assertEqual([b["key"] for b in blocks], ["DIAMP-1", "DIAMP-2"])

    def test_key_beats_no_key_in_same_slot(self):
        blocks = work(run([act("09:01", "slack", text="lol"), act("09:02", "slack", text="ok"),
                           act("09:10", branch="DIAMP-1")]))
        self.assertEqual([(span(b), b["key"]) for b in blocks], [(("09:00", "09:15"), "DIAMP-1")])

    def test_most_activity_wins_slot(self):
        blocks = work(run([act("09:01", branch="DIAMP-1"), act("09:05", branch="DIAMP-2"),
                           act("09:10", branch="DIAMP-2")]))
        self.assertEqual(blocks[0]["key"], "DIAMP-2")

    def test_ignores_other_days(self):
        self.assertEqual(work(run([{"time": "2026-11-04T09:00:00", "source": "git", "branch": "DIAMP-1"}])), [])


class MeetingsAndLogged(unittest.TestCase):
    def test_no_overlap_with_meeting(self):
        blocks = work(run([act("09:05", branch="DIAMP-1"), act("09:35", branch="DIAMP-1")],
                          meetings=[{"start": at("09:15"), "end": at("09:30"), "title": "standup"}]))
        self.assertEqual([span(b) for b in blocks], [("09:00", "09:15"), ("09:30", "09:45")])

    def test_activity_during_meeting_dropped(self):
        blocks = work(run([act("10:10", "slack", text="DIAMP-1")],
                          meetings=[{"start": at("10:00"), "end": at("11:00"), "title": "retro"}]))
        self.assertEqual(blocks, [])

    def test_existing_logged_blocks_left_alone(self):
        blocks = work(run([act("09:05", branch="DIAMP-1")],
                          logged=[{"start": at("09:00"), "end": at("10:00"), "title": "🕒 DIAMP-1"}]))
        self.assertEqual(blocks, [])

    def test_meeting_partly_in_slot_blocks_slot(self):
        blocks = work(run([act("09:20", branch="DIAMP-1")],
                          meetings=[{"start": at("09:00"), "end": at("09:20"), "title": "x"}]))
        self.assertEqual([span(b) for b in blocks], [])


class Flags(unittest.TestCase):
    def test_no_jira(self):
        blocks = work(run([act("09:05", branch="main", message="wip")]))
        self.assertEqual(blocks[0]["flags"], ["no-jira"])
        self.assertIsNone(blocks[0]["title"])

    def test_outside_hours(self):
        blocks = work(run([act("16:10", branch="DIAMP-1"), act("08:05", branch="DIAMP-1")]))
        self.assertEqual([(span(b), b["flags"]) for b in blocks],
                         [(("08:00", "08:15"), ["outside-hours"]), (("16:00", "16:15"), ["outside-hours"])])

    def test_block_split_at_window_edge(self):
        acts = [act(t, branch="DIAMP-1") for t in ("14:40", "14:50", "15:05")]
        blocks = work(run(acts))
        self.assertEqual([(span(b), b["flags"]) for b in blocks],
                         [(("14:30", "15:00"), []), (("15:00", "15:15"), ["outside-hours"])])

    def test_short_gap_flagged_unknown(self):
        # Fill the window apart from 10:00–10:45
        meetings = [{"start": at("08:30"), "end": at("10:00"), "title": "a"},
                    {"start": at("10:45"), "end": at("15:00"), "title": "b"}]
        blocks = run(meetings=meetings)
        self.assertEqual([(span(b), b["flags"]) for b in blocks], [(("10:00", "10:45"), ["unknown"])])

    def test_long_gap_is_break(self):
        meetings = [{"start": at("08:30"), "end": at("12:00"), "title": "a"},
                    {"start": at("13:00"), "end": at("15:00"), "title": "b"}]
        self.assertEqual(run(meetings=meetings), [])

    def test_custom_window(self):
        blocks = work(run([act("16:10", branch="DIAMP-1")], window={"start": "09:00", "end": "17:00"}))
        self.assertEqual(blocks[0]["flags"], [])


class Formatting(unittest.TestCase):
    def test_title_with_summary(self):
        blocks = work(run([act("09:05", branch="DIAMP-1841-x")],
                          summaries={"DIAMP-1841": "AGN3: Update emails"}))
        self.assertEqual(blocks[0]["title"], "🕒 DIAMP-1841 · AGN3: Update emails")
        self.assertEqual(blocks[0]["colorId"], "4")

    def test_title_without_summary_and_missing_list(self):
        out = build({"date": DAY, "activity": [act("09:05", branch="DIAMP-9")]})
        block = work(out["blocks"])[0]
        self.assertEqual(block["title"], "🕒 DIAMP-9")
        self.assertEqual(out["missing_summaries"], ["DIAMP-9"])

    def test_description_counts_only_no_text(self):
        acts = [act("09:01", branch="DIAMP-1", message="secret commit msg"),
                act("09:02", branch="DIAMP-1", message="another"),
                act("09:03", "slack", text="DIAMP-1 private DM text", where="DM with someone"),
                act("09:04", "claude", branch="DIAMP-1", session="s1"),
                act("09:06", "claude", branch="DIAMP-1", session="s1"),
                act("09:08", "jira", key="DIAMP-1")]
        block = work(run(acts))[0]
        self.assertEqual(block["description"],
                         "Jira: https://madecurious.atlassian.net/browse/DIAMP-1\n"
                         "2 commits, 1 Claude session, 1 Slack message, 1 Jira update")
        self.assertNotIn("secret", block["description"])
        self.assertNotIn("DM", block["description"])
        self.assertEqual(block["where"], ["DM with someone"])

    def test_output_sorted_by_start(self):
        blocks = run([act("11:05", branch="DIAMP-2"), act("09:05", branch="DIAMP-1")])
        starts = [b["start"] for b in blocks]
        self.assertEqual(starts, sorted(starts))


if __name__ == "__main__":
    unittest.main()
