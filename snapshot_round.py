# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""The full ranking of one Hacktoberfest round, taken after the round closed and before DEV announces its winners.

Same method as snapshot_w2.py 0.1.0 (job hf26-snap-w2-v1), with the round as an argument so weeks 3 and 4 use
one script. It runs the committed `hf26.py snapshot` and `hf26.py predict` unchanged (same training data, same
model, same features). One thing differs, and only in how pages are read: every request carries a per-run `item`
token. Forem's CDN keeps `item` in its cache key and the API ignores it, so each page comes fresh from the
origin. Without it, deep listing pages could be hours old (measured in munimtechnologies/dev-ai-disclosure)
and the snapshot could miss the entries posted last.

It refuses to run before the round's deadline, so it can never produce a partial ranking labelled as the full
one. If DEV has already announced the round when the snapshot starts, rounds.json and REPORT.md say so and the
ranking is not a prediction. MV2 of Munim, Inc.; made with AI agents.
"""
import argparse
import sys
import time
from datetime import datetime, timezone

import hf26

VERSION = "0.2.0"


def busted(path, token):
    return path + ("&" if "?" in path else "?") + "item=" + token


class BustedClient(hf26.Client):
    """hf26.Client with a per-run `item` token on every request."""

    token = "snap" + str(int(time.time()))

    def get(self, path, tries=6):
        return super().get(busted(path, self.token), tries)


def closed(round_name, now=None):
    return (now or datetime.now(timezone.utc)) >= hf26.parse_time(hf26.ROUNDS[round_name][1])


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", required=True, choices=["week3", "week4"])
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--train", default="/data/posts.csv")
    ap.add_argument("--budget-minutes", type=float, default=150)
    a = ap.parse_args(argv)
    if not closed(a.round):
        print(f"{a.round} is still open until {hf26.ROUNDS[a.round][1]}; a ranking now would be partial. Nothing done.")
        return 1
    print(f"snapshot_round.py {VERSION}, round {a.round}, item token {BustedClient.token}", flush=True)
    hf26.Client = BustedClient
    # Bodies only from this round on: earlier posts are not ranked here, and their round still follows from publish time.
    rc = hf26.main(["snapshot", "--out-dir", a.out_dir, "--bodies-from", hf26.ROUNDS[a.round][0],
                    "--budget-minutes", str(a.budget_minutes)])
    if rc:
        return rc
    return hf26.main(["predict", "--train", a.train, "--field", f"{a.out_dir}/entries.csv",
                      "--rounds-json", f"{a.out_dir}/rounds.json", "--out-dir", a.out_dir])


if __name__ == "__main__":
    sys.exit(main())
