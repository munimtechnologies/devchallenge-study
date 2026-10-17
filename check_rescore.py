# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Does score_round.py --round week1 reproduce the committed score_week1.json? Prints MATCH or every difference.

Usage: python check_rescore.py <new.json> <committed score_week1.json>
MV2 of Munim, Inc.; made with AI agents.
"""
import json
import sys

KEYS = ["ranked_entries", "winners_announced", "winners_in_ranking", "missing_from_ranking", "hits_top_k",
        "expected_hits_if_random", "mean_winner_percentile", "winner_ranks", "chance_tail_mean_percentile"]

new, old = (json.load(open(p, encoding="utf-8")) for p in sys.argv[1:3])
diffs = []
if new.get("status") != "scored":
    diffs.append(f"status {new.get('status')} {new.get('flags')}")
if new.get("winner_ids") != old.get("winner_ids"):
    diffs.append(f"winner_ids {new.get('winner_ids')} vs {old.get('winner_ids')}")
if new.get("announcement_id") != old.get("announcement_id"):
    diffs.append(f"announcement_id {new.get('announcement_id')} vs {old.get('announcement_id')}")
for block in ("logistic", "rank_score"):
    for k in KEYS:
        a, b = (new.get(block) or {}).get(k), (old.get(block) or {}).get(k)
        if a != b:
            diffs.append(f"{block}.{k} {a} vs {b}")
print("MATCH" if not diffs else "DIFF\n" + "\n".join(diffs))
sys.exit(1 if diffs else 0)
