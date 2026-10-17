# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Offline tests for score_w1.py (no network)."""
import unittest

import hf26
import score_w1

SAMPLE = """We saw [a laptop](https://dev.to/alice/power-cut-laptop-38k8) and [a field app](https://dev.to/bob/field-app-574e).

## 🎉 Congratulations To…

### Overall Winner

{% embed https://dev.to/carol/paper-trail-3mf4 %}

### Featured Category Winners

**Best Use of Render**
{% embed https://dev.to/dave/golden-hour-5fe8 %}

Prizes: a [badge](https://dev.to/badge/winner) and credits.

## What’s Next?

{% embed https://dev.to/devteam/join-week-2-55ba %}
{% embed https://dev.to/erin/not-a-winner-1abc %}
"""


class FakeClient:
    """Answers /articles/<user>/<slug>?item=... from a dict; anything else is a 404 (None)."""

    def __init__(self, known):
        self.known = known
        self.paths = []

    def get(self, path):
        self.paths.append(path)
        aid = self.known.get(path.split("?")[0])
        return {"id": aid} if aid else None


class WinnerSection(unittest.TestCase):
    def test_only_winner_headings(self):
        links = hf26.extract_links(score_w1.winner_section(SAMPLE))
        self.assertEqual(links, [("carol", "paper-trail-3mf4"), ("dave", "golden-hour-5fe8")])

    def test_whole_body_adds_intro_examples(self):
        users = [u for u, _ in hf26.extract_links(SAMPLE)]
        self.assertIn("alice", users)
        self.assertIn("erin", users)

    def test_missing_end_is_none(self):
        self.assertIsNone(score_w1.winner_section("### Overall Winner\n{% embed https://dev.to/a/b-c %}\n"))

    def test_missing_start_is_none(self):
        self.assertIsNone(score_w1.winner_section("## What's Next\n"))

    def test_straight_apostrophe_end(self):
        text = "### Overall Winner\n{% embed https://dev.to/a/b-c %}\n## What's Next?\n{% embed https://dev.to/x/y-z %}\n"
        self.assertEqual(hf26.extract_links(score_w1.winner_section(text)), [("a", "b-c")])


class Resolve(unittest.TestCase):
    def test_plain(self):
        c = FakeClient({"/articles/dave/golden-hour-5fe8": 2})
        self.assertEqual(score_w1.resolve(c, [("dave", "golden-hour-5fe8")], "t"), ([2], [], []))
        self.assertEqual(c.paths, ["/articles/dave/golden-hour-5fe8?item=t"])

    def test_renamed_author_resolves_by_identical_slug(self):
        c = FakeClient({"/articles/carolk/paper-trail-3mf4": 1, "/articles/dave/golden-hour-5fe8": 2})
        links = [("carol_old", "paper-trail-3mf4"), ("dave", "golden-hour-5fe8")]
        alternates = [("carolk", "paper-trail-3mf4"), ("carol_old", "paper-trail-3mf4"), ("dave", "golden-hour-5fe8")]
        ids, missing, renamed = score_w1.resolve(c, links, "t", alternates)
        self.assertEqual(ids, [1, 2])
        self.assertEqual(missing, [])
        self.assertEqual(renamed, [{"link": "carol_old/paper-trail-3mf4", "resolved_as": "carolk/paper-trail-3mf4", "id": 1}])

    def test_different_slug_is_not_used(self):
        c = FakeClient({"/articles/carolk/paper-trail-9zz9": 1})
        ids, missing, renamed = score_w1.resolve(c, [("carol_old", "paper-trail-3mf4")], "t",
                                                 [("carolk", "paper-trail-9zz9")])
        self.assertEqual((ids, missing, renamed), ([], ["carol_old/paper-trail-3mf4"], []))

    def test_duplicate_id_counted_once(self):
        c = FakeClient({"/articles/a/x-1": 5, "/articles/b/x-1": 5})
        self.assertEqual(score_w1.resolve(c, [("a", "x-1"), ("b", "x-1")], "t")[0], [5])


class Scoring(unittest.TestCase):
    def test_week1_by_hand(self):
        # 17 winners at the logistic ranks found by hand on 2026-10-16 in a field of 1797.
        ranks = [8, 14, 16, 20, 21, 27, 30, 70, 76, 78, 100, 192, 193, 207, 214, 325, 343]
        ranked = [{"rank": str(i + 1), "article_id": str(1000 + i), "rank_score": "0"} for i in range(1797)]
        out = hf26.score_predictions(ranked, [1000 + r - 1 for r in ranks], by="rank")
        self.assertEqual(out["hits_top_k"], 3)
        self.assertEqual(out["expected_hits_if_random"], 0.16)
        self.assertEqual(out["mean_winner_percentile"], 0.937)
        self.assertEqual(out["winner_ranks"], ranks)


class Helpers(unittest.TestCase):
    def test_busted(self):
        self.assertEqual(score_w1.busted("/articles/1", "t"), "/articles/1?item=t")
        self.assertEqual(score_w1.busted("/articles?page=1", "t"), "/articles?page=1&item=t")

    def test_chance_tail_bounds(self):
        self.assertEqual(score_w1.chance_tail(100, 5, 0.0, sims=1000), 1.0)
        self.assertEqual(score_w1.chance_tail(100, 5, 1.01, sims=1000), 0.0)
        self.assertIsNone(score_w1.chance_tail(100, 0, 0.5))

    def test_expected_users(self):
        self.assertEqual(len(score_w1.EXPECTED_USERS), score_w1.ADVERTISED)


if __name__ == "__main__":
    unittest.main()
