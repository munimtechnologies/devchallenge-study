# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
import math
import unittest

import oos
from hf26 import parse_time


def ann(title, when, id_=1):
    return {"id": id_, "title": title, "published_at": when}


class Selection(unittest.TestCase):
    cutoff = parse_time("2026-10-09T19:32:27Z")

    def test_cutoff_is_newest_training_announcement(self):
        ch = [{"announced": "2026-09-24T19:32:35Z"}, {"announced": "2026-10-09T19:32:27Z"}, {"announced": None}]
        self.assertEqual(oos.training_cutoff(ch), self.cutoff)

    def test_only_winner_posts_after_cutoff_without_hacktoberfest(self):
        arts = [
            ann("Congrats to the Sanity Challenge Winners!", "2026-10-22T15:53:41Z", 2),
            ann("Congrats to the Hacktoberfest Open-Source AI Challenge Week 2: Side Hustle Winners!",
                "2026-10-23T20:18:31Z", 3),
            ann("Congrats to the Hacktoberfest Weekend Challenge: Build for a Friend Winners!",
                "2026-10-09T19:32:27Z", 4),
            ann("Join the Sanity Challenge", "2026-10-01T00:00:00Z", 5),
            ann("What was your win this week!?", "2026-10-23T13:00:00Z", 6),
            ann("Congrats to the Old Challenge Winners!", "2026-10-01T00:00:00Z", 7),
        ]
        self.assertEqual([a["id"] for a in oos.select_announcements(arts, self.cutoff)], [2])

    def test_oldest_first(self):
        arts = [ann("Congrats to the B Winners!", "2026-10-30T00:00:00Z", 9),
                ann("Congrats to the A Winners!", "2026-10-20T00:00:00Z", 8)]
        self.assertEqual([a["id"] for a in oos.select_announcements(arts, self.cutoff)], [8, 9])


class Tag(unittest.TestCase):
    def test_challenge_named_tag_wins(self):
        self.assertEqual(oos.challenge_tag(["devchallenge", "sanitychallenge", "sanity", "ai"]), "sanitychallenge")

    def test_first_specific_tag(self):
        self.assertEqual(oos.challenge_tag(["devchallenge", "bugsmash", "webdev"]), "bugsmash")

    def test_none(self):
        self.assertIsNone(oos.challenge_tag(["devchallenge", "ai"]))


class Stats(unittest.TestCase):
    def test_hits_tail_bounds(self):
        self.assertAlmostEqual(oos.hits_tail(100, 5, 0), 1.0)
        self.assertAlmostEqual(oos.hits_tail(100, 5, 5), 1 / math.comb(100, 5))

    def test_hits_tail_one(self):
        # P(at least one of 2 picks in the top 2 of 4) = 1 - C(2,2)/C(4,2)
        self.assertAlmostEqual(oos.hits_tail(4, 2, 1), 1 - 1 / 6)

    def test_mean_pct_tail(self):
        self.assertEqual(oos.mean_pct_tail(50, 3, 0.9, draws=2000), oos.mean_pct_tail(50, 3, 0.9, draws=2000))
        self.assertLess(oos.mean_pct_tail(50, 3, 1.0, draws=20000), 0.01)
        self.assertGreater(oos.mean_pct_tail(50, 3, 0.5, draws=20000), 0.4)
        self.assertEqual(oos.mean_pct_tail(50, 3, 0.0, draws=1000), 1.0)

    def test_score_set_top_winner(self):
        ranked = [{"rank": i, "article_id": 100 + i, "score": -i, "rank_score": 1 / i} for i in range(1, 21)]
        s = oos.score_set(ranked, [101, 999])
        self.assertEqual(s["logistic"]["hits_top_k"], 1)
        self.assertEqual(s["logistic"]["missing_from_ranking"], [999])
        self.assertAlmostEqual(s["logistic"]["p_hits_at_least"], 0.05)
        self.assertLess(s["logistic"]["p_mean_percentile_at_least"], 0.1)


class Embeds(unittest.TestCase):
    def test_cards_only(self):
        md = "Intro [x](https://dev.to/alice/a-post-1)\n{% embed https://dev.to/Bob/b-post-2 %}\n"
        self.assertEqual(oos.embedded_keys(md), {("bob", "b-post-2")})

    def test_hyphenated_username_card(self):
        # 0.1.0 missed this shape: the Sanity Challenge's fifth card winner (ERRATUM_LINKS.md).
        md = "{% embed https://dev.to/jo-ann/post-1abc %}\n"
        self.assertEqual(oos.embedded_keys(md), {("jo-ann", "post-1abc")})


class Winners(unittest.TestCase):
    def test_resolve_reads_hyphenated_usernames(self):
        class Fake:
            def get(self, path):
                return {"/articles/jo-ann/post-1abc": {"id": 4797565},
                        "/articles/alice/a-post-1": {"id": 11}}.get(path)

        a = {"body_html": "", "body_markdown": "[x](https://dev.to/alice/a-post-1)\n"
                                               "{% embed https://dev.to/jo-ann/post-1abc %}\n"}
        self.assertEqual(oos.resolve_winners(Fake(), a), ([11, 4797565], [4797565]))


if __name__ == "__main__":
    unittest.main()
