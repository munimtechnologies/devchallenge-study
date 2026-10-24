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
        self.assertEqual(timing.ROUNDS["week3"]["score"],
                         "predictions/2026-10-26/score_week3_full.json")

    def test_closes_match_hf26_rounds(self):
        self.assertEqual(timing.ROUNDS["week1"]["close"], "2026-10-12T07:00:00Z")
        self.assertEqual(timing.ROUNDS["week2"]["close"], "2026-10-19T07:00:00Z")
        self.assertEqual(timing.ROUNDS["week3"]["close"], "2026-10-26T07:00:00Z")
        self.assertEqual(timing.ROUNDS["week4"]["close"], "2026-11-01T07:00:00Z")

    def test_preregistered_rounds(self):
        self.assertEqual(timing.PREREG_ROUNDS, ("week3", "week4"))
        for name in timing.PREREG_ROUNDS:
            self.assertIn(name, timing.ROUNDS)


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


def row(pcts):
    return {"winners_timed": len(pcts), "winner_time_percentiles": sorted(pcts)}


BEFORE = "2026-11-10T00:00:00Z"
AFTER = "2026-12-01T00:00:01Z"


class PooledCall(unittest.TestCase):
    def test_range_matches_preregistration_example(self):
        # PREREGISTRATION_TIMING.md: "K = 21 + 20 = 41 gives 0.412 to 0.588"
        call = timing.pool([row([0.5] * 21), row([0.5] * 20)])
        self.assertEqual(call["winners_timed"], 41)
        self.assertEqual([round(x, 3) for x in call["null_95_interval"]], [0.412, 0.588])
        self.assertEqual(call["reading"], "no clear timing effect")
        self.assertFalse(call["primary_prediction_held"])

    def test_pooled_mean_weights_rounds_by_winners(self):
        call = timing.pool([row([0.9] * 3), row([0.1])])
        self.assertEqual(call["mean_time_percentile"], 0.7)

    def test_late_pool_holds_both_predictions(self):
        results = {"week3": row([0.95] * 21), "week4": row([0.9] * 20),
                   "week3-by-close": row([0.96] * 21), "week4-by-close": row([0.3] * 20)}
        call = timing.pooled_call(results, now=BEFORE)
        self.assertEqual(call["status"], "pooled")
        self.assertEqual(call["rounds_scored"], ["week3", "week4"])
        self.assertEqual(call["reading"], "winners are posted late")
        self.assertTrue(call["primary_prediction_held"])
        self.assertEqual(call["winners_in_first_fifth"], 0)
        self.assertEqual(call["expected_in_first_fifth"], 8.2)
        self.assertTrue(call["secondary_prediction_held"])
        self.assertEqual(call["secondary_by_close"]["winners_timed"], 41)

    def test_early_pool(self):
        call = timing.pooled_call({"week3": row([0.1] * 21), "week4": row([0.15] * 20)}, now=BEFORE)
        self.assertEqual(call["reading"], "winners are posted early")
        self.assertFalse(call["secondary_prediction_held"])

    def test_one_round_waits_until_deadline(self):
        results = {"week3": row([0.9] * 21), "week4": {"status": "not_committed"}}
        self.assertEqual(timing.pooled_call(results, now=BEFORE)["status"], "pending")
        call = timing.pooled_call(results, now=AFTER)
        self.assertEqual(call["status"], "one_round")
        self.assertEqual(call["rounds_scored"], ["week3"])
        self.assertEqual(call["winners_timed"], 21)

    def test_none_scored(self):
        self.assertEqual(timing.pooled_call({}, now=BEFORE)["status"], "pending")
        self.assertEqual(timing.pooled_call({}, now=AFTER)["status"], "not_testable")

    def test_exploratory_rounds_never_enter_the_call(self):
        call = timing.pooled_call({"week1": row([0.99] * 17), "week2": row([0.99] * 18)}, now=AFTER)
        self.assertEqual(call["status"], "not_testable")

    def test_report_states_the_call(self):
        call = timing.pooled_call({"week3": row([0.95] * 21), "week4": row([0.9] * 20)}, now=BEFORE)
        md = timing.report_md({}, call)
        self.assertIn("## Pre-registered call (week3 + week4)", md)
        self.assertIn("**Call: winners are posted late.** Primary prediction (above the range) held.", md)
        self.assertIn("Pending", timing.report_md({}, timing.pooled_call({}, now=BEFORE)))


def write_round(name, winners, status="scored"):
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
        json.dump({"status": status, "winner_ids": winners}, f)
    return {"ranking": rk, "entries": en, "score": sc}


class Main(unittest.TestCase):
    def test_end_to_end_from_local_files(self):
        with tempfile.TemporaryDirectory() as d:
            cwd = os.getcwd()
            os.chdir(d)
            try:
                rounds = {"wa": write_round("wa", [19, 20]), "wb": write_round("wb", [19, 20]),
                          "wc": write_round("wc", [], status="not_announced"),
                          "wd": {"ranking": "wd_rank.csv", "entries": "wd_entries.csv",
                                 "score": "wd_score.json"}}
                rounds["wb"]["close"] = "2026-10-12T19:00:00Z"
                old = timing.ROUNDS, timing.PREREG_ROUNDS, timing.fetch
                real_fetch = timing.fetch

                def fetch(path, data_dir, token):
                    if path.startswith("wd_"):
                        raise timing.NotCommitted(path)
                    return real_fetch(path, data_dir, token)

                timing.ROUNDS, timing.PREREG_ROUNDS, timing.fetch = rounds, ("wb", "wd"), fetch
                try:
                    timing.main(["--data-dir", "data", "--out-dir", "out", "--draws", "500"])
                finally:
                    timing.ROUNDS, timing.PREREG_ROUNDS, timing.fetch = old
                with open(os.path.join("out", "timing.json")) as f:
                    out = json.load(f)
                self.assertEqual(out["version"], timing.VERSION)
                self.assertEqual(out["exploratory_rounds"], ["wa", "wc"])
                self.assertEqual(list(out["rounds"]), ["wa", "wb", "wb-by-close", "wc", "wd"])
                self.assertEqual(out["rounds"]["wa"]["ranked_entries"], 20)
                self.assertEqual(out["rounds"]["wb"]["winners_timed"], 2)
                self.assertEqual(out["rounds"]["wb-by-close"]["ranked_entries"], 19)
                self.assertEqual(out["rounds"]["wb-by-close"]["entries_after_close_left_out"], 1)
                self.assertEqual(out["rounds"]["wb-by-close"]["missing"], [20])
                self.assertEqual(out["rounds"]["wc"]["status"], "not_scored")
                self.assertEqual(out["rounds"]["wc"]["score_status"], "not_announced")
                self.assertEqual(out["rounds"]["wd"]["status"], "not_committed")
                self.assertEqual(out["pre_registered_call"]["rounds_scored"], ["wb"])
                self.assertIn(out["pre_registered_call"]["status"], ("pending", "one_round"))
                with open(os.path.join("out", "TIMING.md")) as f:
                    md = f.read()
                self.assertIn("| wa | 20 | 2 of 2 |", md)
                self.assertIn("| wb-by-close | 19 | 1 of 2 |", md)
                self.assertIn("| wc | not scored |", md)
                self.assertIn("| wd | not committed |", md)
                self.assertIn("1 ranked entries published after it left out", md)
                self.assertIn("## Pre-registered call (wb + wd)", md)
            finally:
                os.chdir(cwd)


if __name__ == "__main__":
    unittest.main()
