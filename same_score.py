# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Compare a committed score file with a re-run: status, winners and both scores must be identical.

python same_score.py <committed.json> <rerun.json> <label>   prints SAME <label> or DIFF <label> <fields>.
Run times, request counts and file paths are ignored. MV2 of Munim, Inc.; made with AI agents.
"""
import json
import sys

FIELDS = ("status", "winner_ids", "logistic", "rank_score")


def differences(a, b):
    return [f for f in FIELDS if a.get(f) != b.get(f)]


def main(argv):
    with open(argv[0], encoding="utf-8") as f:
        a = json.load(f)
    with open(argv[1], encoding="utf-8") as f:
        b = json.load(f)
    diff = differences(a, b)
    print(("SAME " + argv[2]) if not diff else ("DIFF " + argv[2] + " " + ",".join(diff)), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
