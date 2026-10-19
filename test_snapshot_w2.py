# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Offline tests for snapshot_w2.py (no network)."""
import unittest
from datetime import datetime, timezone
from unittest import mock

import hf26
import snapshot_w2


class Busting(unittest.TestCase):
    def test_busted(self):
        self.assertEqual(snapshot_w2.busted("/articles/1", "t"), "/articles/1?item=t")
        self.assertEqual(snapshot_w2.busted("/articles?tag=x&page=2", "t"), "/articles?tag=x&page=2&item=t")

    def test_client_adds_token_to_every_request(self):
        seen = []
        with mock.patch.object(hf26.Client, "get", lambda self, path, tries=6: seen.append(path)):
            c = snapshot_w2.BustedClient(0)
            c.get("/articles?tag=hf26challenge&per_page=1000&page=3")
            c.get("/articles/42")
        tok = snapshot_w2.BustedClient.token
        self.assertEqual(seen, [f"/articles?tag=hf26challenge&per_page=1000&page=3&item={tok}",
                                f"/articles/42?item={tok}"])


class Deadline(unittest.TestCase):
    def test_closed_at_deadline(self):
        self.assertFalse(snapshot_w2.closed(datetime(2026, 10, 19, 6, 59, 59, tzinfo=timezone.utc)))
        self.assertTrue(snapshot_w2.closed(datetime(2026, 10, 19, 7, 0, 0, tzinfo=timezone.utc)))

    def test_refuses_while_open(self):
        with mock.patch.object(snapshot_w2, "closed", return_value=False), \
                mock.patch.object(hf26, "main") as run:
            self.assertEqual(snapshot_w2.main(["--out-dir", "unused"]), 1)
            run.assert_not_called()

    def test_runs_committed_steps_when_closed(self):
        original = hf26.Client
        try:
            with mock.patch.object(snapshot_w2, "closed", return_value=True), \
                    mock.patch.object(hf26, "main", return_value=0) as run:
                self.assertEqual(snapshot_w2.main(["--out-dir", "o"]), 0)
                self.assertIs(hf26.Client, snapshot_w2.BustedClient)
            snap, pred = [c.args[0] for c in run.call_args_list]
            self.assertEqual(snap[:2], ["snapshot", "--out-dir"])
            self.assertIn(hf26.ROUNDS["week2"][0], snap)
            self.assertEqual(pred[0], "predict")
            self.assertIn("o/entries.csv", pred)
        finally:
            hf26.Client = original


if __name__ == "__main__":
    unittest.main()
