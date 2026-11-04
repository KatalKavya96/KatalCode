"""Offline tests for the contest sync (no network). Run: python3 tests.py -v"""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import sync

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures"
LATER = 1_900_000_000  # long after every fixture contest


def fixture(name: str) -> dict:
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))


class SyncTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="katalcode-sync-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.original_root = sync.ROOT
        self.addCleanup(setattr, sync, "ROOT", self.original_root)

    def run_sync(self, fixtures: Path = FIXTURES, env: dict | None = None, now: int = LATER) -> bool:
        return sync.run(fixtures=fixtures, env=env or {}, now=now, root=self.root)

    def read(self, rel: str) -> str:
        return (self.root / rel).read_text(encoding="utf-8")

    def custom(self, **snapshots) -> Path:
        d = Path(tempfile.mkdtemp(prefix="katalcode-fx-"))
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        for name, snap in snapshots.items():
            (d / f"{name}.json").write_text(json.dumps(snap), encoding="utf-8")
        return d

    def test_leetcode_layout_and_statuses(self) -> None:
        self.assertTrue(self.run_sync())
        page = self.read("contests/leetcode/weekly/200/README.md")
        self.assertIn("Fixture A](https://leetcode.com/problems/fixture-a/) | 3 | Accepted in contest (10:00)", page)
        self.assertRegex(page, r"Fixture C.*Upsolved")
        self.assertRegex(page, r"Fixture D.*Not accepted yet")
        self.assertIn("needs import", self.read("contests/leetcode/biweekly/50/README.md"))
        self.assertIn("[LeetCode Weekly Contest 200](./200/)", self.read("contests/leetcode/weekly/README.md"))
        state = json.loads(self.read("data/contest-history.json"))
        self.assertEqual([c["change"] for c in state["leetcode"]["contests"]], [31, 31])

    def test_running_contest_is_not_published(self) -> None:
        start = fixture("leetcode")["history"][2]["contest"]["startTime"]
        self.assertTrue(self.run_sync(now=start + 60))
        self.assertFalse((self.root / "contests/leetcode/weekly/200").exists())
        self.assertTrue((self.root / "contests/leetcode/biweekly/50/README.md").exists())

    def test_full_first_fetch_marks_older_problems_unknown(self) -> None:
        snap = fixture("leetcode")
        snap["recentAc"] = [{"id": f"x{i}", "title": "X", "titleSlug": f"x{i}", "timestamp": str(1761500000 + i)} for i in range(20)]
        self.run_sync(self.custom(leetcode=snap))
        self.assertRegex(self.read("contests/leetcode/weekly/200/README.md"), r"Fixture D.*Unknown")

    def test_leethub_code_becomes_a_draft_editorial(self) -> None:
        hub = Path(tempfile.mkdtemp(prefix="leethub-"))
        self.addCleanup(shutil.rmtree, hub, ignore_errors=True)
        (hub / "3001-fixture-a").mkdir()
        (hub / "3001-fixture-a" / "3001-fixture-a.py").write_text("class Solution:  # my typo kept\n    pass\n")
        (hub / "3001-fixture-a" / "README.md").write_text("copied statement, must not be used")
        # an existing hand-made folder for Q2 must be reused, not duplicated or overwritten
        q2 = self.root / "contests/leetcode/weekly/200/Q2-b-short"
        q2.mkdir(parents=True)
        (q2 / "README.md").write_text("MY EDITORIAL")
        (q2 / "metadata.yaml").write_text("title: x\n")
        (hub / "fixture-b").mkdir()
        (hub / "fixture-b" / "fixture-b.java").write_text("class Solution {}\n")

        self.run_sync(env={"LEETHUB_DIR": str(hub)})
        q1 = self.root / "contests/leetcode/weekly/200/Q1-fixture-a"
        self.assertEqual((q1 / "submission.py").read_text(), "class Solution:  # my typo kept\n    pass\n")
        draft = (q1 / "README.md").read_text()
        self.assertIn("**Draft.**", draft)
        self.assertIn("[Problem statement](https://leetcode.com/problems/fixture-a/)", draft)
        self.assertNotIn("copied statement", draft)
        self.assertFalse((q1 / "metadata.yaml").exists())
        self.assertEqual((q2 / "README.md").read_text(), "MY EDITORIAL")
        self.assertTrue((q2 / "submission.java").exists())
        self.assertFalse((self.root / "contests/leetcode/weekly/200/Q2-fixture-b").exists())
        page = self.read("contests/leetcode/weekly/200/README.md")
        self.assertIn("[Draft](./Q1-fixture-a/)", page)
        self.assertIn("[Editorial](./Q2-b-short/)", page)

    def test_codeforces_results(self) -> None:
        self.run_sync()
        page = self.read("contests/codeforces/9002/README.md")
        self.assertIn("| 3,100 | 2 / 3 | 50:00 | 1288 | +188 |", page)
        self.assertIn("Accepted in contest (10:00)", page)
        self.assertIn("Accepted in contest (50:00, 2 wrong)", page)
        self.assertRegex(page, r"Fixture C.*Upsolved")
        self.assertIn("needs import", self.read("contests/codeforces/9001/README.md"))

    def test_codechef_history_and_parsing(self) -> None:
        self.run_sync()
        self.assertIn("| 2,345 | — / — | — | 1450 | +50 |", self.read("contests/codechef/START200D/README.md"))
        html = '<div class="rating-number">1450</div><script>var all_rating = [{"code":"X","name":"Y","end_date":"2026-01-01 22:00:00","rating":"1400","rank":"9"}];</script>'
        self.assertEqual(sync.cc_parse(html)["history"][0]["code"], "X")
        with self.assertRaisesRegex(RuntimeError, "layout changed"):
            sync.cc_parse("<html></html>")

    def test_resync_keeps_hand_written_text(self) -> None:
        existing = self.root / "contests/codeforces/9002/README.md"
        existing.parent.mkdir(parents=True)
        existing.write_text("# My own title\n\nMY REFLECTION\n")
        self.run_sync()
        text = existing.read_text()
        self.assertTrue(text.startswith("# My own title\n"))
        self.assertIn("MY REFLECTION", text)
        cf = fixture("codeforces")
        cf["rating"][1]["rank"] = 3000
        self.run_sync(self.custom(codeforces=cf))
        text = existing.read_text()
        self.assertIn("| 3,000 |", text)
        self.assertEqual(text.count(sync.START), 1)
        self.assertIn("MY REFLECTION", text)

    def test_accepted_submissions_accumulate(self) -> None:
        self.run_sync()
        self.run_sync(self.custom(leetcode={**fixture("leetcode"), "recentAc": []}))
        self.assertEqual(len(json.loads(self.read("data/contest-history.json"))["leetcode"]["accepted"]), 3)

    def test_one_platform_failing_leaves_others(self) -> None:
        d = self.custom(codechef={"handle": "x"}, codeforces=fixture("codeforces"))
        self.assertFalse(self.run_sync(d))
        self.assertTrue((self.root / "contests/codeforces/9002/README.md").exists())
        self.assertNotIn("codechef", json.loads(self.read("data/contest-history.json")))


if __name__ == "__main__":
    unittest.main()
