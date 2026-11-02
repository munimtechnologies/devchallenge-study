# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Offline tests for ailabel.py (no network)."""
import csv
import itertools
import json
import os
import shutil
import tempfile
import unittest

import ailabel as al


def write_csv(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def entry(aid, dec, lv=None):
    row = {"article_id": str(aid), "ai_declared": str(dec)}
    if lv is not None:
        row["ai_level"] = lv
    return row


class Maths(unittest.TestCase):
    def test_hypergeom_small(self):
        p = al.hypergeom(4, 2, 2)
        for got, want in zip(p, [1 / 6, 4 / 6, 1 / 6]):
            self.assertAlmostEqual(got, want)

    def test_hypergeom_sums_to_one_for_a_large_field(self):
        self.assertAlmostEqual(sum(al.hypergeom(1594, 290, 21)), 1.0, places=9)

    def test_comb_matches_known_values(self):
        self.assertEqual(al.comb(10, 3), 120)
        self.assertEqual(al.comb(5, 7), 0)

    def test_convolve_and_tail(self):
        pmf = al.convolve([0.5, 0.5], [0.5, 0.5])
        self.assertEqual(pmf, [0.25, 0.5, 0.25])
        self.assertAlmostEqual(al.upper_tail(pmf, 1), 0.75)
        self.assertEqual(al.upper_tail(pmf, 3), 0.0)
        self.assertEqual(al.upper_tail(pmf, 0), 1.0)

    def test_pooled_p_matches_brute_force(self):
        # Round a: 7 posts, ids 0-6, the first 3 declared. Round b: 5 posts, ids 100-104, the first 2 declared.
        f1 = {i: entry(i, 1 if i < 3 else 0) for i in range(7)}
        f2 = {i: entry(i, 1 if i < 102 else 0) for i in range(100, 105)}
        r1 = al.score_round("a", f1, [0, 1])
        r2 = al.score_round("b", f2, [100, 103])
        pool = al.pooled([r1, r2])
        self.assertEqual(pool["declared_winners"], 3)
        hits = total = 0
        for w1 in itertools.combinations(f1, 2):
            for w2 in itertools.combinations(f2, 2):
                d = sum(al.declared(f1[w]) for w in w1) + sum(al.declared(f2[w]) for w in w2)
                total += 1
                hits += d >= 3
        self.assertAlmostEqual(pool["p_one_sided"], hits / total)
        self.assertAlmostEqual(pool["expected_declared_winners"], 2 * 3 / 7 + 2 * 2 / 5)
        self.assertTrue(pool["p1_direction_held"])


class Rounds(unittest.TestCase):
    def test_missing_winner_is_left_out(self):
        field = {1: entry(1, 1), 2: entry(2, 0), 3: entry(3, 0), 4: entry(4, 0)}
        r = al.score_round("w", field, [1, 99])
        self.assertEqual(r["winners_in_field"], 1)
        self.assertEqual(r["winners_missing_from_field"], [99])
        self.assertEqual(r["declared_winners"], 1)
        self.assertAlmostEqual(r["expected_declared_winners"], 0.25)
        self.assertIsNone(r["levels"])

    def test_levels_and_p2(self):
        lv = ["fully_autonomous", "some_ai", "not_disclosed", "not_disclosed", "no_ai"]
        field = {i: entry(i, 1 if lv[i] in ("fully_autonomous", "some_ai") else 0, lv[i]) for i in range(5)}
        r = al.score_round("w", field, [1, 4])
        self.assertEqual(r["levels"]["some_ai"]["winners"], 1)
        self.assertEqual(r["levels"]["no_ai"]["winners"], 1)
        self.assertEqual(r["levels"]["fully_autonomous"]["winners"], 0)
        self.assertAlmostEqual(r["levels"]["fully_autonomous"]["p_zero_if_random"], 6 / 10)
        second = al.p2([r])
        self.assertTrue(second["gradable"])
        self.assertTrue(second["held"])

    def test_p2_not_gradable_without_levels(self):
        r = al.score_round("k", {1: entry(1, 1), 2: entry(2, 0)}, [1])
        self.assertFalse(al.p2([r])["gradable"])

    def test_build_field_needs_every_ranked_post(self):
        with self.assertRaises(ValueError):
            al.build_field([entry(1, 0)], [{"article_id": "2"}])

    def test_winner_ids_required(self):
        with self.assertRaises(ValueError):
            al.winner_ids({"winners": [1]})
        self.assertEqual(al.winner_ids({"winner_ids": [3, "4"]}), [3, 4])

    def test_winner_ids_from_forecast_oos(self):
        score = {"winner_ids": {"linked": [1, 2, 3], "embedded": [2, 3]}, "primary_winner_set": "embedded"}
        self.assertEqual(al.winner_ids(score), [2, 3])
        with self.assertRaises(ValueError):
            al.winner_ids({"winner_ids": {"linked": [1]}, "primary_winner_set": None})

    def test_declared_reads_float_text(self):
        self.assertEqual(al.declared({"ai_declared": "1.0"}), 1)


class EndToEnd(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir)

    def path(self, name):
        return os.path.join(self.dir, name)

    def test_two_rounds_and_live_check(self):
        lv = ["some_ai", "fully_autonomous", "not_disclosed", "not_disclosed", "no_ai", "not_disclosed"]
        rows = [dict(entry(10 + i, 1 if lv[i] in ("some_ai", "fully_autonomous") else 0, lv[i]), round="week4")
                for i in range(6)]
        write_csv(self.path("e4.csv"), rows, ["article_id", "round", "ai_declared", "ai_level"])
        write_csv(self.path("r4.csv"), [{"rank": i + 1, "article_id": 10 + i} for i in range(6)],
                  ["rank", "article_id"])
        with open(self.path("s4.json"), "w", encoding="utf-8") as fh:
            json.dump({"winner_ids": [10, 12]}, fh)
        write_csv(self.path("ek.csv"), [entry(20 + i, 1 if i == 0 else 0) for i in range(4)],
                  ["article_id", "ai_declared"])
        write_csv(self.path("rk.csv"), [{"rank": i + 1, "article_id": 20 + i} for i in range(4)],
                  ["rank", "article_id"])
        with open(self.path("sk.json"), "w", encoding="utf-8") as fh:
            json.dump({"winner_ids": [20]}, fh)

        def opener(req):
            if req.full_url.endswith("/12"):
                raise OSError("gone")
            return json.dumps({"ai_disclosure_level": "no_ai"}).encode()

        out = self.path("out")
        rc = al.main(["--round", "week4", self.path("e4.csv"), self.path("r4.csv"), self.path("s4.json"),
                      "--round", "kaggle", self.path("ek.csv"), self.path("rk.csv"), self.path("sk.json"),
                      "--out-dir", out, "--live", "--pause", "0"], opener=opener)
        self.assertEqual(rc, 0)
        with open(os.path.join(out, "ailabel.json"), encoding="utf-8") as fh:
            res = json.load(fh)
        self.assertEqual(res["pooled"]["declared_winners"], 2)
        self.assertEqual(res["pooled"]["winners"], 3)
        self.assertEqual(res["p2"]["rounds"], ["week4"])
        self.assertTrue(res["p2"]["held"])
        live = {x["article_id"]: x for x in res["live_relabels"]}
        self.assertTrue(live[10]["changed"])
        self.assertTrue(live[12]["now"].startswith("unavailable"))
        self.assertFalse(live[12]["changed"])
        with open(os.path.join(out, "AILABEL.md"), encoding="utf-8") as fh:
            md = fh.read()
        self.assertIn("P1 (primary)", md)
        self.assertIn("1 of 2 winners' labels differ", md)


if __name__ == "__main__":
    unittest.main()
