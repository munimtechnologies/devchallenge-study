# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Offline tests for hf26.py: no network, DEV's API is replaced by a stub."""
import csv
import json
import os
import tempfile
import unittest
from argparse import Namespace
from unittest import mock

import hf26


def shape_row(article_id, words, **extra):
    row = {f: 0 for f in hf26.CONT + hf26.BINARY}
    row.update({"article_id": article_id, "words": words})
    row.update(extra)
    return row


class RoundTests(unittest.TestCase):
    def test_template_link_decides_round(self):
        body = "*This is a submission for [Side Hustle](https://dev.to/challenges/hacktoberfest-week2-2026-10-12)*"
        pub = hf26.parse_time("2026-10-13T12:00:00Z")
        self.assertEqual(hf26.round_of(body, pub), "week2")

    def test_publish_time_when_no_body(self):
        self.assertEqual(hf26.round_of(None, hf26.parse_time("2026-10-08T12:00:00Z")), "week1")
        self.assertEqual(hf26.round_of("", hf26.parse_time("2026-10-05T23:00:00Z")), "weekend+week1")
        self.assertEqual(hf26.round_of("", hf26.parse_time("2026-12-01T00:00:00Z")), "none")

    def test_announcement_round(self):
        weekend = "Congrats to the Hacktoberfest Weekend Challenge: Build for a Friend Winners!"
        week1 = "Congrats to the Hacktoberfest Week 1: Touch Grass Winners!"
        self.assertEqual(hf26.announcement_round(weekend), "weekend")
        self.assertEqual(hf26.announcement_round(week1), "week1")
        self.assertIsNone(hf26.announcement_round("Join the Hacktoberfest Week 1: $2,450 in prizes across 17 winners"))
        self.assertIsNone(hf26.announcement_round("Congrats to the Summer Bug Smash Winners!"))


class FeatureTests(unittest.TestCase):
    def test_body_features(self):
        md = ("# Title\n\nSome words here.\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n"
              "```py\nx = 1\n```\n\n![img](http://x/y.png)\n\n{% youtube abc %}\n")
        f = hf26.body_features(md)
        self.assertEqual(f["headings"], 1)
        self.assertEqual(f["code_blocks"], 1)
        self.assertEqual(f["images"], 1)
        self.assertEqual(f["embeds"], 1)
        self.assertEqual(f["has_video"], 1)
        self.assertEqual(f["has_table"], 1)
        self.assertEqual(f["has_github_embed"], 0)
        plain = hf26.body_features("Just a sentence with no extras.")
        self.assertEqual(plain["has_table"], 0)
        self.assertEqual(plain["has_video"], 0)

    def test_declared_ai(self):
        self.assertEqual(hf26.declared_ai({"ai_disclosure_level": "some_ai"}), 1)
        self.assertEqual(hf26.declared_ai({"ai_disclosure_level": "no_ai"}), 0)
        self.assertEqual(hf26.declared_ai({}), 0)

    def test_extract_links(self):
        text = ("see https://dev.to/alice/my-cool-post-1abc and https://dev.to/devteam/some-thing-abc "
                "and {% embed https://dev.to/bob/other-post-2x %}")
        self.assertEqual(hf26.extract_links(text, None),
                         [("alice", "my-cool-post-1abc"), ("bob", "other-post-2x")])

    def test_is_official(self):
        self.assertTrue(hf26.is_official({"user": {"username": "devteam"}}))
        self.assertTrue(hf26.is_official({"user": {"username": "jess"}, "organization": {"username": "devteam"}}))
        self.assertFalse(hf26.is_official({"user": {"username": "alice"}}))
        self.assertFalse(hf26.is_official({}))


class MathTests(unittest.TestCase):
    def test_pct_in(self):
        vals = [1.0, 2.0, 3.0, 4.0]
        self.assertAlmostEqual(hf26.pct_in(vals, 2.5), 0.5)
        self.assertAlmostEqual(hf26.pct_in(vals, 2.0), 0.375)
        self.assertAlmostEqual(hf26.pct_in(vals, 2.0, exclude_self=True), 1 / 3)

    def test_solve(self):
        x = hf26.solve([[2.0, 0.0], [0.0, 4.0]], [2.0, 8.0])
        self.assertAlmostEqual(x[0], 1.0)
        self.assertAlmostEqual(x[1], 2.0)

    def test_logistic_learns_direction(self):
        X = [[0.1], [0.2], [0.8], [0.9]]
        w = hf26.fit_logistic(X, [0, 0, 1, 1])
        self.assertGreater(w[1], 0)
        self.assertGreater(hf26.score_with(w, [0.9]), hf26.score_with(w, [0.1]))

    def test_evaluate_ranking(self):
        ev = hf26.evaluate_ranking([(0.9, 1), (0.8, 0), (0.3, 0), (0.1, 0)])
        self.assertEqual(ev["hits_top_k"], 1)
        self.assertAlmostEqual(ev["mean_winner_percentile"], 1.0)
        self.assertAlmostEqual(ev["expected_hits"], 0.25)
        self.assertIsNone(hf26.evaluate_ranking([(0.9, 0), (0.1, 0)]))


class RankingTests(unittest.TestCase):
    def test_predict_round_orders_by_weight(self):
        rows = [shape_row(1, 100), shape_row(2, 500), shape_row(3, 300)]
        w = [0.0] + [1.0 if f == "words_pct" else 0.0 for f in hf26.FEATURES]
        out = hf26.predict_round(w, rows)
        self.assertEqual([o["article_id"] for o in out], [2, 3, 1])
        self.assertEqual([o["rank"] for o in out], [1, 2, 3])

    def test_score_predictions(self):
        ranked = [{"rank": str(i + 1), "article_id": str(a)} for i, a in enumerate([10, 20, 30, 40])]
        res = hf26.score_predictions(ranked, [10, 30, 99])
        self.assertEqual(res["winners_announced"], 3)
        self.assertEqual(res["winners_in_ranking"], 2)
        self.assertEqual(res["missing_from_ranking"], [99])
        self.assertEqual(res["hits_top_k"], 1)
        self.assertAlmostEqual(res["expected_hits_if_random"], 1.0)
        self.assertEqual(res["winner_ranks"], [1, 3])

    def test_score_by_rank_score_reorders(self):
        ranked = [{"rank": "1", "article_id": "10", "rank_score": "0.2"},
                  {"rank": "2", "article_id": "20", "rank_score": "0.9"},
                  {"rank": "3", "article_id": "30", "rank_score": "0.5"}]
        self.assertEqual(hf26.order_ids(ranked), [10, 20, 30])
        self.assertEqual(hf26.order_ids(ranked, by="rank_score"), [20, 30, 10])
        res = hf26.score_predictions(ranked, [20], by="rank_score")
        self.assertEqual(res["hits_top_k"], 1)
        self.assertEqual(res["winner_ranks"], [1])

    def test_backtest_finds_planted_signal(self):
        rows = []
        for cid in ("c1", "c2", "c3"):
            for i in range(6):
                rows.append(shape_row(i, 100 + 50 * i, challenge_id=cid, is_winner=0, has_body=1))
            for i in range(2):
                rows.append(shape_row(100 + i, 5000 + i, challenge_id=cid, is_winner=1, has_body=1))
        kept = hf26.prepare_train(rows)
        self.assertEqual(len(kept), 3)
        summary, per_challenge = hf26.backtest(kept)
        self.assertEqual(summary["logistic"]["challenges"], 3)
        self.assertGreater(summary["logistic"]["mean_winner_percentile"], 0.8)
        self.assertEqual(len(per_challenge), 3)

    def test_prepare_train_drops_thin_challenges(self):
        rows = [shape_row(i, 100 + i, challenge_id="thin", is_winner=0, has_body=1) for i in range(3)]
        rows.append(shape_row(9, 900, challenge_id="thin", is_winner=1, has_body=1))
        self.assertEqual(hf26.prepare_train(rows), {})


def article(aid, published, username="alice"):
    return {"id": aid, "title": "My 5 tools: a demo", "published_at": published,
            "tag_list": ["devchallenge", "hf26challenge"], "cover_image": "x",
            "reading_time_minutes": 4, "public_reactions_count": 3, "comments_count": 0,
            "language": "en", "ai_disclosure_level": "some_ai", "user": {"username": username}}


class StubClient:
    def __init__(self, pause=1.0):
        self.requests = 0

    def get(self, path, tries=6):
        self.requests += 1
        if path.startswith("/articles?username=devteam"):
            return []
        if path.startswith("/articles?tag=hf26challenge"):
            if path.endswith("page=1"):
                return [article(1, "2026-10-08T12:00:00Z"), article(2, "2026-10-14T12:00:00Z"),
                        article(3, "2026-10-12T19:00:00Z", username="devteam")]
            return []
        if path == "/articles/1":
            return {"body_markdown": "[x](https://dev.to/challenges/hacktoberfest-week1-2026-10-05)\n# Hi\nwords"}
        if path == "/articles/2":
            return {"body_markdown": "[x](https://dev.to/challenges/hacktoberfest-week2-2026-10-12)\nwords"}
        return None


class AnnouncedStub(StubClient):
    """DEV after the week-1 announcement, which links two winners."""

    def get(self, path, tries=6):
        self.requests += 1
        if path.startswith("/articles?username=devteam"):
            return [{"id": 900, "title": "Congrats to the Hacktoberfest Week 1: Touch Grass Winners!",
                     "published_at": "2026-10-15T19:00:00Z"}]
        if path == "/articles/900":
            return {"id": 900, "published_at": "2026-10-15T19:00:00Z",
                    "body_html": '<a href="https://dev.to/alice/first-post-1a">x</a> '
                                 '<a href="https://dev.to/bob/second-post-2b">y</a> '
                                 '<a href="https://dev.to/alice/first-post-1a">again</a>'}
        if path == "/articles/alice/first-post-1a":
            return {"id": 30}
        if path == "/articles/bob/second-post-2b":
            return {"id": 77}
        return None


def write_predictions(path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=["rank", "article_id", "score", "rank_score"])
        wr.writeheader()
        for i, (aid, rs) in enumerate([(10, 0.9), (20, 0.1), (30, 0.8), (40, 0.2)], 1):
            wr.writerow({"rank": i, "article_id": aid, "score": 1.0 - i / 10, "rank_score": rs})


class SnapshotTests(unittest.TestCase):
    def test_snapshot_writes_entries_without_usernames(self):
        with tempfile.TemporaryDirectory() as out:
            args = Namespace(tag="hf26challenge", since="2026-10-01", bodies_from="2026-10-05T07:00:00Z",
                             budget_minutes=5, pause=0, out_dir=out)
            with mock.patch.object(hf26, "Client", StubClient):
                self.assertEqual(hf26.snapshot(args), 0)
            with open(os.path.join(out, "entries.csv"), newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual([r["round"] for r in rows], ["week1", "week2"])
            self.assertEqual(rows[0]["has_body"], "1")
            self.assertEqual(rows[0]["title_has_number"], "1")
            self.assertEqual(rows[0]["ai_level"], "some_ai")
            self.assertNotIn("username", rows[0])
            with open(os.path.join(out, "rounds.json"), encoding="utf-8") as f:
                meta = json.load(f)
            self.assertEqual(meta["posts"], 2)
            self.assertEqual(meta["official_posts_skipped"], [3])


class ScoreTests(unittest.TestCase):
    def run_score(self, client_cls):
        with tempfile.TemporaryDirectory() as d:
            preds = os.path.join(d, "predictions_week1.csv")
            write_predictions(preds)
            out = os.path.join(d, "score.json")
            with mock.patch.object(hf26, "Client", client_cls):
                code = hf26.main(["score", "--predictions", preds, "--round", "week1",
                                  "--out", out, "--pause", "0"])
            with open(out, encoding="utf-8") as f:
                return code, json.load(f)

    def test_auto_reports_not_announced(self):
        code, res = self.run_score(StubClient)
        self.assertEqual(code, 0)
        self.assertEqual(res["status"], "not_announced")
        self.assertEqual(res["round"], "week1")

    def test_auto_finds_announcement_and_scores_both_orders(self):
        code, res = self.run_score(AnnouncedStub)
        self.assertEqual(code, 0)
        self.assertEqual(res["status"], "scored")
        self.assertEqual(res["announcement_id"], 900)
        self.assertEqual(res["winner_ids"], [30, 77])
        self.assertEqual(res["logistic"]["winners_in_ranking"], 1)
        self.assertEqual(res["logistic"]["missing_from_ranking"], [77])
        self.assertEqual(res["logistic"]["winner_ranks"], [3])
        self.assertEqual(res["logistic"]["hits_top_k"], 0)
        self.assertEqual(res["rank_score"]["winner_ranks"], [2])

    def test_auto_needs_round(self):
        with mock.patch.object(hf26, "Client", StubClient):
            self.assertEqual(hf26.main(["score", "--predictions", "x.csv"]), 2)


if __name__ == "__main__":
    unittest.main()
