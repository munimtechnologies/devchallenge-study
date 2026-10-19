# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""The full week-2 (Side Hustle) ranking, taken after the round closed and before DEV announces its winners.

predictions/2026-10-14/README.md promised it: the 2026-10-14 week-2 ranking covered only the 333 entries posted
by then. This runs the committed `hf26.py snapshot` and `hf26.py predict` unchanged (same training data, same
model, same features). One thing differs, and only in how pages are read: every request carries a per-run `item`
token. Forem's CDN keeps `item` in its cache key and the API ignores it, so each page comes fresh from the
origin. Without it, deep listing pages could be hours old (measured in munimtechnologies/dev-ai-disclosure)
and the snapshot could miss the entries posted last.

It refuses to run before the round's deadline, so it can never produce a partial ranking labelled as the full
one. If DEV has already announced week 2 when the snapshot starts, rounds.json and REPORT.md say so and the
ranking is not a prediction. MV2 of Munim, Inc.; made with AI agents.
"""
import argparse
import sys
import time
from datetime import datetime, timezone

import hf26

VERSION = "0.1.0"
ROUND = "week2"


def busted(path, token):
    return path + ("&" if "?" in path else "?") + "item=" + token


class BustedClient(hf26.Client):
    """hf26.Client with a per-run `item` token on every request."""

    token = "w2snap" + str(int(time.time()))

    def get(self, path, tries=6):
        return super().get(busted(path, self.token), tries)


def closed(now=None):
    return (now or datetime.now(timezone.utc)) >= hf26.parse_time(hf26.ROUNDS[ROUND][1])


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--train", default="/data/posts.csv")
    ap.add_argument("--budget-minutes", type=float, default=150)
    a = ap.parse_args(argv)
    if not closed():
        print(f"{ROUND} is still open until {hf26.ROUNDS[ROUND][1]}; a ranking now would be partial. Nothing done.")
        return 1
    print(f"snapshot_w2.py {VERSION}, item token {BustedClient.token}", flush=True)
    hf26.Client = BustedClient
    # Bodies only from week 2 on: week-1 posts are not ranked here, and their round still follows from publish time.
    rc = hf26.main(["snapshot", "--out-dir", a.out_dir, "--bodies-from", hf26.ROUNDS[ROUND][0],
                    "--budget-minutes", str(a.budget_minutes)])
    if rc:
        return rc
    return hf26.main(["predict", "--train", a.train, "--field", f"{a.out_dir}/entries.csv",
                      "--rounds-json", f"{a.out_dir}/rounds.json", "--out-dir", a.out_dir])


if __name__ == "__main__":
    sys.exit(main())
