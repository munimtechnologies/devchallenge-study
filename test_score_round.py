# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Offline tests for score_round.py (no network)."""
import json
import os
import tempfile
import unittest
from unittest import mock

import hf26
import score_round

BODY = """We saw [a laptop](https://dev.to/alice/power-cut-laptop-38k8) and [a field app](https://dev.to/bob/field-app-574e).

## 🎉 Congratulations To…

### Overall Winner

{% embed https://dev.to/carol_old/paper-trail-3mf4 %}

## Featured Prize Category Winners

### Best Use of Render
{% embed https://dev.to/dave/golden-hour-5fe8 %}

Prizes: a [badge](https://dev.to/badge/winner) and credits.

## What’s Next?

{% embed https://dev.to/devteam/join-week-3-55ba %}
{% embed https://dev.to/erin/not-a-winner-1abc %}
"""
HTML = '<a href="https://dev.to/carolk/paper-trail-3mf4">Paper Trail</a>'
LISTING = [
    {"id": 9, "path": "/devteam/top-7-1bo6", "title": "Top 7 Featured DEV Posts of the Week"},
    {"id": 7, "path": "/devteam/congrats-side-hustle-1aa1",
     "title": "Congrats to the Hacktoberfest Open-Source AI Challenge: Side Hustle Winners!", "published_at": "P2"},
    {"id": 5, "path": "/devteam/congrats-touch-grass-152c",
     "title": "Congrats to the Hacktoberfest Open-Source AI Challenge: Touch Grass Winners!", "published_at": "P1"},
]


class FakeClient:
    """Answers API paths (the `item` token, if any, stripped) from a dict; anything else is a 404 (None)."""

    def __init__(self, known):
        self.known = known
        self.paths = []
        self.requests = 0

    def get(self, path, tries=6):
        self.paths.append(path)
        self.requests += 1
        return self.known.get(path.split("item=")[0].rstrip("?&"))


def site(body=BODY, listing=LISTING):
    return {
        "/articles?username=devteam&per_page=100&page=1": listing,
        "/articles/7": {"id": 7, "title": LISTING[1]["title"], "published_at": "P2",
                        "body_markdown": body, "body_html": HTML},
        "/articles/carolk/paper-trail-3mf4": {"id": 101},
        "/articles/dave/golden-hour-5fe8": {"id": 102},
        "/articles/alice/power-cut-laptop-38k8": {"id": 103},
    }


class WinnerSection(unittest.TestCase):
    def test_only_winner_headings(self):
        links = hf26.extract_links(score_round.winner_section(BODY))
        self.assertEqual(links, [("carol_old", "paper-trail-3mf4"), ("dave", "golden-hour-5fe8")])

    def test_missing_end_is_none(self):
        self.assertIsNone(score_round.winner_section("### Overall Winner\n{% embed https://dev.to/a/b-c %}\n"))

    def test_missing_start_is_none(self):
        self.assertIsNone(score_round.winner_section("## What's Next\n"))


class FindAnnouncement(unittest.TestCase):
    def test_picks_the_round(self):
        c = FakeClient(site())
        self.assertEqual(score_round.find_announcement(c, "week2"), (7, "devteam/congrats-side-hustle-1aa1", "P2"))
        self.assertEqual(score_round.find_announcement(c, "week1")[0], 5)

    def test_absent(self):
        self.assertIsNone(score_round.find_announcement(FakeClient(site(listing=LISTING[:1])), "week2"))


class ReadWinners(unittest.TestCase):
    def setUp(self):
        self.ads = mock.patch.dict(score_round.ADVERTISED, {"week2": 2})
        self.ads.start()

    def tearDown(self):
        self.ads.stop()

    def test_scored_with_renamed_author(self):
        r = score_round.read_winners(FakeClient(site()), "week2")
        self.assertEqual(r["status"], "scored")
        self.assertEqual(r["winner_ids"], [101, 102])
        self.assertEqual(r["renamed_links"], [{"link": "carol_old/paper-trail-3mf4",
                                               "resolved_as": "carolk/paper-trail-3mf4", "id": 101}])
        self.assertIn("alice/power-cut-laptop-38k8", r["links_outside_winner_headings"])
        self.assertNotIn("carolk/paper-trail-3mf4", r["links_outside_winner_headings"])

    def test_count_mismatch_is_flagged_not_dropped(self):
        with mock.patch.dict(score_round.ADVERTISED, {"week2": 3}):
            r = score_round.read_winners(FakeClient(site()), "week2")
        self.assertEqual(r["status"], "flagged")
        self.assertEqual(r["flags"], ["2 winner links, 3 advertised"])
        self.assertEqual(r["winner_ids"], [101, 102])

    def test_unresolved_is_flagged(self):
        s = site()
        del s["/articles/dave/golden-hour-5fe8"]
        r = score_round.read_winners(FakeClient(s), "week2")
        self.assertEqual(r["status"], "flagged")
        self.assertEqual(r["unresolved_links"], ["dave/golden-hour-5fe8"])

    def test_not_announced(self):
        r = score_round.read_winners(FakeClient(site(listing=LISTING[:1])), "week2")
        self.assertEqual(r["status"], "not_announced")
        self.assertNotIn("winner_ids", r)

    def test_no_winner_section(self):
        r = score_round.read_winners(FakeClient(site(body="Winners below.\n## What's Next\n")), "week2")
        self.assertEqual(r["status"], "no_winner_section")

    def test_announcement_given_by_hand(self):
        r = score_round.read_winners(FakeClient(site(listing=[])), "week2", 7)
        self.assertTrue(r["announcement_given"])
        self.assertEqual((r["status"], r["announcement_id"]), ("scored", 7))


class Main(unittest.TestCase):
    def run_main(self, known, args):
        fake = FakeClient(known)
        with tempfile.TemporaryDirectory() as d, \
                mock.patch.object(hf26.Client, "get", lambda self, path, tries=6: fake.get(path)), \
                mock.patch.object(score_round, "chance_tail", return_value=0.0):
            out = os.path.join(d, "s.json")
            rc = score_round.main(args + ["--out", out, "--md", os.path.join(d, "s.md")])
            with open(out, encoding="utf-8") as fh:
                result = json.load(fh)
            md = os.path.exists(os.path.join(d, "s.md"))
        return rc, result, md, fake

    def test_every_request_busted(self):
        _, _, _, fake = self.run_main(site(listing=LISTING[:1]), ["--round", "week2"])
        self.assertTrue(fake.paths)
        self.assertTrue(all("item=" + score_round.BustedClient.token in p for p in fake.paths))

    def test_not_announced_written_exit_zero(self):
        rc, result, md, _ = self.run_main(site(listing=LISTING[:1]), ["--round", "week2", "--predictions", "p.csv"])
        self.assertEqual((rc, result["status"], md), (0, "not_announced", False))

    def test_scores_both_orderings(self):
        with tempfile.TemporaryDirectory() as d:
            pred = os.path.join(d, "predictions_week2.csv")
            with open(pred, "w", encoding="utf-8") as fh:
                fh.write("rank,article_id,score,rank_score\n1,102,0.9,0.1\n2,200,0.8,0.9\n3,101,0.7,0.5\n4,201,0.1,0.2\n")
            with mock.patch.dict(score_round.ADVERTISED, {"week2": 2}):
                rc, r, md, _ = self.run_main(site(), ["--round", "week2", "--predictions", pred])
        self.assertEqual((rc, r["status"], md), (0, "scored", True))
        self.assertEqual(r["logistic"]["winner_ranks"], [1, 3])
        self.assertEqual(r["logistic"]["hits_top_k"], 1)
        self.assertEqual(r["rank_score"]["winner_ranks"], [2, 4])

    def test_unreadable_exit_one(self):
        s = site()
        del s["/articles/7"]
        rc, r, _, _ = self.run_main(s, ["--round", "week2"])
        self.assertEqual((rc, r["status"]), (1, "unreadable"))


class Helpers(unittest.TestCase):
    def test_busted(self):
        self.assertEqual(score_round.busted("/articles/1", "t"), "/articles/1?item=t")
        self.assertEqual(score_round.busted("/articles?page=1", "t"), "/articles?page=1&item=t")

    def test_advertised(self):
        self.assertEqual(score_round.ADVERTISED["week1"], 17)
        self.assertEqual(score_round.ADVERTISED["week2"], 18)

    def test_chance_tail_bounds(self):
        self.assertEqual(score_round.chance_tail(100, 5, 0.0, sims=1000), 1.0)
        self.assertEqual(score_round.chance_tail(100, 5, 1.01, sims=1000), 0.0)
        self.assertIsNone(score_round.chance_tail(100, 0, 0.5))


if __name__ == "__main__":
    unittest.main()
