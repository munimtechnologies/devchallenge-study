# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Offline tests for snapshot_round.py (no network)."""
import unittest
from datetime import datetime, timezone
from unittest import mock

import hf26
import snapshot_round


class Busting(unittest.TestCase):
    def test_busted(self):
        self.assertEqual(snapshot_round.busted("/articles/1", "t"), "/articles/1?item=t")
        self.assertEqual(snapshot_round.busted("/articles?tag=x&page=2", "t"), "/articles?tag=x&page=2&item=t")

    def test_client_adds_token_to_every_request(self):
        seen = []
        with mock.patch.object(hf26.Client, "get", lambda self, path, tries=6: seen.append(path)):
            c = snapshot_round.BustedClient(0)
            c.get("/articles?tag=hf26challenge&per_page=1000&page=3")
            c.get("/articles/42")
        tok = snapshot_round.BustedClient.token
        self.assertEqual(seen, [f"/articles?tag=hf26challenge&per_page=1000&page=3&item={tok}",
                                f"/articles/42?item={tok}"])


class Deadline(unittest.TestCase):
    def test_week3_closes_2026_10_26_0700(self):
        self.assertFalse(snapshot_round.closed("week3", datetime(2026, 10, 26, 6, 59, 59, tzinfo=timezone.utc)))
        self.assertTrue(snapshot_round.closed("week3", datetime(2026, 10, 26, 7, 0, 0, tzinfo=timezone.utc)))

    def test_week4_closes_2026_11_01_0700(self):
        self.assertFalse(snapshot_round.closed("week4", datetime(2026, 11, 1, 6, 59, 59, tzinfo=timezone.utc)))
        self.assertTrue(snapshot_round.closed("week4", datetime(2026, 11, 1, 7, 0, 0, tzinfo=timezone.utc)))

    def test_only_weeks_3_and_4(self):
        with self.assertRaises(SystemExit):
            snapshot_round.main(["--round", "week2", "--out-dir", "unused"])

    def test_refuses_while_open(self):
        with mock.patch.object(snapshot_round, "closed", return_value=False), \
                mock.patch.object(hf26, "main") as run:
            self.assertEqual(snapshot_round.main(["--round", "week3", "--out-dir", "unused"]), 1)
            run.assert_not_called()

    def test_runs_committed_steps_when_closed(self):
        original = hf26.Client
        try:
            with mock.patch.object(snapshot_round, "closed", return_value=True), \
                    mock.patch.object(hf26, "main", return_value=0) as run:
                self.assertEqual(snapshot_round.main(["--round", "week3", "--out-dir", "o"]), 0)
                self.assertIs(hf26.Client, snapshot_round.BustedClient)
            snap, pred = [c.args[0] for c in run.call_args_list]
            self.assertEqual(snap[:2], ["snapshot", "--out-dir"])
            self.assertIn(hf26.ROUNDS["week3"][0], snap)
            self.assertEqual(pred[0], "predict")
            self.assertIn("o/entries.csv", pred)
        finally:
            hf26.Client = original


if __name__ == "__main__":
    unittest.main()
