# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Look back (exploratory, not a pre-registered test): run ailabel.py on Hacktoberfest weeks 1-3, whose winners
are already known, using the snapshots, rankings and frozen score files committed in predictions/.

  python lookback.py --out-dir out     (needs network: downloads the committed files from GitHub)

Each round is scored on its own (a round whose files lack a needed column or winner list is reported, not
guessed), then the rounds that worked are pooled, with --live to list labels changed since the snapshot.
MV2 of Munim, Inc.; made with AI agents. Apache-2.0.
"""
import argparse
import os
import sys
import traceback
import urllib.request

import ailabel

BASE = "https://raw.githubusercontent.com/munimtechnologies/devchallenge-study/main/predictions/"
ROUNDS = [
    ("week1", "2026-10-14", "entries.csv", "predictions_week1.csv", "score_week1.json"),
    ("week2", "2026-10-19", "entries.csv", "predictions_week2.csv", "score_week2_full.json"),
    ("week3", "2026-10-26", "entries.csv", "predictions_week3.csv", "score_week3_full.json"),
]


def download(folder, name, dest_dir):
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, name)
    req = urllib.request.Request(BASE + folder + "/" + name, headers={"User-Agent": ailabel.USER_AGENT})
    data = urllib.request.urlopen(req, timeout=120).read()
    with open(dest, "wb") as fh:
        fh.write(data)
    print("ok", folder + "/" + name, len(data), "bytes", flush=True)
    return dest


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args(argv)
    worked = []
    for name, folder, entries, ranking, score in ROUNDS:
        out = os.path.join(a.out_dir, name)
        try:
            src = os.path.join(a.out_dir, "inputs", folder)
            paths = [download(folder, f, src) for f in (entries, ranking, score)]
            ailabel.main(["--round", name] + paths + ["--out-dir", out])
            worked.append([name] + paths)
        except Exception:
            os.makedirs(out, exist_ok=True)
            with open(os.path.join(out, "ERROR.txt"), "w", encoding="utf-8") as fh:
                fh.write(traceback.format_exc())
            print("FAILED", name, flush=True)
            traceback.print_exc()
    if not worked:
        return 1
    args = []
    for w in worked:
        args += ["--round"] + w
    return ailabel.main(args + ["--out-dir", os.path.join(a.out_dir, "pooled"), "--live"])


if __name__ == "__main__":
    sys.exit(main())
