# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
import os
import tempfile
import unittest
from unittest import mock

import forecast_oos as fo
from hf26 import parse_time

OPENED = parse_time("2026-09-23T20:59:28Z")
DEADLINE = parse_time("2026-10-12T07:00:00Z")


def post(id_, when, **kw):
    a = {"id": id_, "published_at": when, "title": "x", "tag_list": ["kagglechallenge", "devchallenge"],
         "user": {"username": "someone"}}
    a.update(kw)
    return a


class Announcement(unittest.TestCase):
    def test_finds_newest_matching_winners_post(self):
        arts = [{"id": 1, "title": "Join the Kaggle Benchmarking Challenge", "published_at": "2026-09-23T20:59:28Z"},
                {"id": 2, "title": "Congrats to the Sanity Challenge Winners!", "published_at": "2026-10-22T15:53:41Z"},
                {"id": 3, "title": "Congrats to the Kaggle Benchmarking Challenge Winners!",
                 "published_at": "2026-11-05T18:00:00Z"}]
        self.assertEqual(fo.find_announcement(arts, "kaggle")["id"], 3)

    def test_none_before_announcement(self):
        arts = [{"id": 1, "title": "Join the Kaggle Benchmarking Challenge", "published_at": "2026-09-23T20:59:28Z"},
                {"id": 4, "title": "Congrats to the Hacktoberfest Open-Source AI Challenge Week 3: Slow and Steady "
                 "Winners!", "published_at": "2026-10-30T20:35:58Z"}]
        self.assertIsNone(fo.find_announcement(arts, "kaggle"))


class Window(unittest.TestCase):
    def test_inside(self):
        self.assertEqual(fo.classify(post(10, "2026-10-12T06:59:04Z"), OPENED, DEADLINE, set()), "ranked")

    def test_edges(self):
        self.assertEqual(fo.classify(post(10, "2026-10-12T07:00:00Z"), OPENED, DEADLINE, set()), "after_deadline")
        self.assertEqual(fo.classify(post(10, "2026-09-23T20:59:27Z"), OPENED, DEADLINE, set()), "before_opened")
        self.assertEqual(fo.classify(post(10, "2026-09-23T20:59:28Z"), OPENED, DEADLINE, set()), "ranked")

    def test_language_training_and_date(self):
        self.assertEqual(fo.classify(post(10, "2026-10-01T00:00:00Z", language="pt"), OPENED, DEADLINE, set()),
                         "not_english")
        self.assertEqual(fo.classify(post(10, "2026-10-01T00:00:00Z"), OPENED, DEADLINE, {10}), "in_training_data")
        self.assertEqual(fo.classify(post(10, None), OPENED, DEADLINE, set()), "no_date")

    def test_devchallenge_tag_not_required(self):
        self.assertEqual(fo.classify(post(10, "2026-10-01T00:00:00Z", tag_list=["kagglechallenge", "ai"]),
                                     OPENED, DEADLINE, set()), "ranked")


class Rankings(unittest.TestCase):
    def test_round_trip_types(self):
        ranked = [{"rank": 1, "article_id": 5, "score": 0.25, "rank_score": 0.9},
                  {"rank": 2, "article_id": 7, "score": -1.5, "rank_score": 0.4}]
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "r.csv")
            fo.write_ranking(p, ranked)
            self.assertEqual(fo.read_ranking(p), ranked)

    def test_primary_is_cards_then_links(self):
        self.assertEqual(fo.primary_winners([1, 2, 3], [2, 3]), ("embedded", [2, 3]))
        self.assertEqual(fo.primary_winners([1, 2, 3], []), ("linked", [1, 2, 3]))


class Refusal(unittest.TestCase):
    def test_refuses_before_deadline(self):
        with tempfile.TemporaryDirectory() as d:
            argv = ["snapshot", "--tag", "kagglechallenge", "--title-word", "kaggle", "--opened",
                    "2026-09-23T20:59:28Z", "--deadline", "2099-01-01T00:00:00Z", "--out-dir", os.path.join(d, "o")]
            with mock.patch("builtins.print"):
                self.assertEqual(fo.main(argv), 1)
            self.assertFalse(os.path.exists(os.path.join(d, "o")))


if __name__ == "__main__":
    unittest.main()
