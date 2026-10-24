import csv
import json
import os
import tempfile
import unittest

import timing


class Percentile(unittest.TestCase):
    def test_ties_half(self):
        self.assertEqual(timing.percentile("b", ["a", "b", "c", "d"]), 0.375)

    def test_empty(self):
        self.assertIsNone(timing.percentile("a", []))


class Rounds(unittest.TestCase):
    def test_sources_are_committed_repo_files(self):
        for name, src in timing.ROUNDS.items():
            for key in ("ranking", "entries", "score"):
                self.assertTrue(src[key].startswith("predictions/"), (name, key))
        self.assertEqual(timing.ROUNDS["week2"]["score"],
                         "predictions/2026-10-19/score_week2_full.json")

    def test_closes_match_hf26_rounds(self):
        self.assertEqual(timing.ROUNDS["week1"]["close"], "2026-10-12T07:00:00Z")
        self.assertEqual(timing.ROUNDS["week2"]["close"], "2026-10-19T07:00:00Z")


class Analyse(unittest.TestCase):
    def setUp(self):
        self.ids = list(range(1, 101))
        self.pub = {i: "2026-10-%02dT%02d:00:00Z" % (12 + i // 24, i % 24) for i in self.ids}

    def test_late_winners_score_high(self):
        r = timing.analyse(self.ids, self.pub, [96, 97, 98, 99, 100, 555], draws=2000)
        self.assertEqual(r["winners_timed"], 5)
        self.assertEqual(r["missing"], [555])
        self.assertGreater(r["mean_time_percentile"], 0.95)
        self.assertEqual(r["winners_in_first_fifth"], 0)
        self.assertEqual(r["winners_in_first_half"], 0)
        self.assertLess(r["share_random_mean_at_least"], 0.01)
        self.assertGreater(r["share_random_mean_at_most"], 0.99)
        self.assertEqual(r["first_winner"], self.pub[96])
        self.assertNotIn("close", r)

    def test_early_winners_score_low(self):
        r = timing.analyse(self.ids, self.pub, [1, 2, 3], draws=2000)
        self.assertLess(r["mean_time_percentile"], 0.05)
        self.assertEqual(r["winners_in_first_fifth"], 3)
        self.assertGreater(r["share_random_mean_at_least"], 0.99)

    def test_unranked_entries_ignored(self):
        pub = dict(self.pub)
        pub[999] = "2030-01-01T00:00:00Z"
        r = timing.analyse(self.ids, pub, [50], draws=100)
        self.assertEqual(r["ranked_entries"], 100)
        self.assertEqual(r["last_entry"], self.pub[100])

    def test_no_winners_timed(self):
        r = timing.analyse(self.ids, self.pub, [555], draws=100)
        self.assertEqual(r["winners_timed"], 0)
        self.assertNotIn("mean_time_percentile", r)
        self.assertIn("| week9 | 100 | 0 |", timing.report_md({"week9": r}))

    def test_close_drops_later_entries_and_raises_percentile(self):
        close = self.pub[50]
        full = timing.analyse(self.ids, self.pub, [40, 45], draws=500)
        cut = timing.analyse(self.ids, self.pub, [40, 45], draws=500, close=close)
        self.assertEqual(cut["ranked_entries"], 50)
        self.assertEqual(cut["entries_after_close_left_out"], 50)
        self.assertEqual(cut["close"], close)
        self.assertEqual(cut["last_entry"], close)
        self.assertGreater(cut["mean_time_percentile"], full["mean_time_percentile"])

    def test_winner_after_close_counts_as_missing(self):
        r = timing.analyse(self.ids, self.pub, [10, 90], draws=100, close=self.pub[50])
        self.assertEqual(r["winners_timed"], 1)
        self.assertEqual(r["missing"], [90])


class Main(unittest.TestCase):
    def test_end_to_end_from_local_files(self):
        with tempfile.TemporaryDirectory() as d:
            cwd = os.getcwd()
            os.chdir(d)
            try:
                rounds = {}
                for name in ("wa", "wb"):
                    rk, en, sc = name + "_rank.csv", name + "_entries.csv", name + "_score.json"
                    with open(rk, "w", newline="") as f:
                        w = csv.writer(f)
                        w.writerow(["rank", "article_id", "score", "rank_score"])
                        for i in range(1, 21):
                            w.writerow([i, i, 0.5, 0.5])
                    with open(en, "w", newline="") as f:
                        w = csv.writer(f)
                        w.writerow(["article_id", "round", "published_at"])
                        for i in range(1, 22):
                            w.writerow([i, name, "2026-10-12T%02d:00:00Z" % i])
                        w.writerow([22, name, ""])
                    with open(sc, "w") as f:
                        json.dump({"winner_ids": [19, 20]}, f)
                    rounds[name] = {"ranking": rk, "entries": en, "score": sc}
                rounds["wb"]["close"] = "2026-10-12T19:00:00Z"
                old = timing.ROUNDS
                timing.ROUNDS = rounds
                try:
                    timing.main(["--data-dir", "data", "--out-dir", "out", "--draws", "500"])
                finally:
                    timing.ROUNDS = old
                with open(os.path.join("out", "timing.json")) as f:
                    out = json.load(f)
                self.assertFalse(out["pre_registered"])
                self.assertEqual(list(out["rounds"]), ["wa", "wb", "wb-by-close"])
                self.assertEqual(out["rounds"]["wa"]["ranked_entries"], 20)
                self.assertEqual(out["rounds"]["wb"]["winners_timed"], 2)
                self.assertEqual(out["rounds"]["wb-by-close"]["ranked_entries"], 19)
                self.assertEqual(out["rounds"]["wb-by-close"]["entries_after_close_left_out"], 1)
                self.assertEqual(out["rounds"]["wb-by-close"]["missing"], [20])
                with open(os.path.join("out", "TIMING.md")) as f:
                    md = f.read()
                self.assertIn("| wa | 20 | 2 of 2 |", md)
                self.assertIn("| wb-by-close | 19 | 1 of 2 |", md)
                self.assertIn("1 ranked entries published after it left out", md)
            finally:
                os.chdir(cwd)


if __name__ == "__main__":
    unittest.main()
