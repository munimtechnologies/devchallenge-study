"""When in a round were DEV's Hacktoberfest 2026 winners posted?

Exploratory, not pre-registered. For each scored round, every announced winner's
publish time is ranked among the round's committed, ranked entries (ties count
half) and the percentiles are averaged: 0.50 means "posted like a typical entry",
above 0.50 means later. The 55-challenge history in this repo put winners at 0.49.

0.1.1: week 2's winners are read from the committed scorer output
(predictions/2026-10-19/score_week2_full.json); 0.1.0 read the same 18 ids from a
local copy. Nothing else changed.

Made by MV2 of Munim, Inc., with AI agents working in his name. Apache-2.0.
"""
import argparse
import csv
import json
import math
import os
import random
import urllib.request

VERSION = "0.1.1"
RAW = "https://raw.githubusercontent.com/munimtechnologies/devchallenge-study/main/"
UA = "devchallenge-study timing.py (MV2 of Munim, Inc.; mv2@munimtech.com)"

ROUNDS = {
    "week1": {"ranking": "predictions/2026-10-14/predictions_week1.csv",
              "entries": "predictions/2026-10-14/entries.csv",
              "score": "predictions/2026-10-14/score_week1.json"},
    "week2": {"ranking": "predictions/2026-10-19/predictions_week2.csv",
              "entries": "predictions/2026-10-19/entries.csv",
              "score": "predictions/2026-10-19/score_week2_full.json"},
}


def fetch(path, data_dir, token):
    """Local file if it exists (in the workdir), else download from the repo."""
    if os.path.exists(path):
        return path
    dest = os.path.join(data_dir, path.replace("/", "__"))
    if not os.path.exists(dest):
        req = urllib.request.Request(RAW + path + "?item=" + token, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read()
        with open(dest, "wb") as f:
            f.write(body)
    return dest


def read_ranked_ids(path):
    with open(path, newline="", encoding="utf-8") as f:
        return [int(row["article_id"]) for row in csv.DictReader(f)]


def read_published(path):
    out = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("published_at"):
                out[int(row["article_id"])] = row["published_at"]
    return out


def percentile(value, others):
    """Share of `others` below value, ties counting half (value itself excluded)."""
    below = sum(1 for o in others if o < value)
    ties = sum(1 for o in others if o == value)
    return (below + 0.5 * ties) / len(others) if others else None


def chance_tail(times, k, observed, draws, seed):
    """Share of random k-subsets whose mean percentile is >= observed (and <=)."""
    rng = random.Random(seed)
    pct = [percentile(t, times[:i] + times[i + 1:]) for i, t in enumerate(times)]
    hi = lo = 0
    for _ in range(draws):
        m = sum(rng.sample(pct, k)) / k
        hi += m >= observed - 1e-12
        lo += m <= observed + 1e-12
    return hi / draws, lo / draws


def analyse(ranked_ids, published, winner_ids, draws=200000, seed=2026):
    times_by_id = {a: published[a] for a in ranked_ids if a in published}
    winners = [w for w in winner_ids if w in times_by_id]
    missing = [w for w in winner_ids if w not in times_by_id]
    times = sorted(times_by_id.values())
    pcts = []
    for w in winners:
        others = [t for a, t in times_by_id.items() if a != w]
        pcts.append(round(percentile(times_by_id[w], others), 4))
    k = len(pcts)
    res = {"ranked_entries": len(times_by_id), "winners_announced": len(winner_ids),
           "winners_timed": k, "missing": missing}
    if not k:
        return res
    mean = sum(pcts) / k
    half = 1.96 * math.sqrt(1 / 12 / k)
    first_half = sum(1 for p in pcts if p < 0.5)
    first_fifth = sum(1 for p in pcts if p < 0.2)
    hi, lo = chance_tail(times, k, mean, draws, seed)
    res.update({
        "mean_time_percentile": round(mean, 4),
        "null_95_interval": [round(0.5 - half, 4), round(0.5 + half, 4)],
        "winner_time_percentiles": sorted(pcts),
        "winners_in_first_half": first_half,
        "winners_in_first_fifth": first_fifth,
        "expected_in_first_fifth": round(0.2 * k, 2),
        "share_random_mean_at_least": round(hi, 5),
        "share_random_mean_at_most": round(lo, 5),
        "first_entry": times[0], "last_entry": times[-1],
        "first_winner": min(times_by_id[w] for w in winners),
        "last_winner": max(times_by_id[w] for w in winners),
    })
    return res


def report_md(results):
    lines = ["# When were the winners posted? (exploratory)", "",
             "timing.py %s. Not pre-registered. Each winner's publish time is ranked among the "
             "round's committed, ranked entries (ties half); 0.50 = posted like a typical entry, "
             "higher = later. Made by MV2 of Munim, Inc., with AI agents working in his name. "
             "Data CC BY 4.0." % VERSION, "",
             "| Round | Entries | Winners timed | Mean time percentile | 95% range if timing didn't matter "
             "| Winners in the first fifth (expected) | Winners in the first half | Random draws with a mean this late |",
             "|---|---|---|---|---|---|---|---|"]
    for name, r in results.items():
        if not r.get("winners_timed"):
            lines.append("| %s | %d | 0 | | | | | |" % (name, r["ranked_entries"]))
            continue
        lines.append("| %s | %d | %d of %d | %.3f | %.3f to %.3f | %d (%.1f) | %d | %.5f |" % (
            name, r["ranked_entries"], r["winners_timed"], r["winners_announced"],
            r["mean_time_percentile"], r["null_95_interval"][0], r["null_95_interval"][1],
            r["winners_in_first_fifth"], r["expected_in_first_fifth"],
            r["winners_in_first_half"], r["share_random_mean_at_least"]))
    lines += ["", "- The last column is the share of 200,000 random sets of the same number of "
              "entries whose mean time percentile is at least as high.",
              "- Earlier work in this repo (55 challenges, 323 winners) put winners at 0.49 of "
              "their challenge's posting window."]
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="/data")
    ap.add_argument("--out-dir", default="/out")
    ap.add_argument("--draws", type=int, default=200000)
    a = ap.parse_args(argv)
    os.makedirs(a.data_dir, exist_ok=True)
    os.makedirs(a.out_dir, exist_ok=True)
    token = "timing%d" % random.randrange(10 ** 9)
    results = {}
    for name, src in ROUNDS.items():
        ranked = read_ranked_ids(fetch(src["ranking"], a.data_dir, token))
        published = read_published(fetch(src["entries"], a.data_dir, token))
        with open(fetch(src["score"], a.data_dir, token), encoding="utf-8") as f:
            winner_ids = [int(w) for w in json.load(f)["winner_ids"]]
        results[name] = analyse(ranked, published, winner_ids, draws=a.draws)
        results[name]["sources"] = src
        print(name, json.dumps({k: v for k, v in results[name].items()
                                if k != "winner_time_percentiles"}))
    out = {"version": VERSION, "pre_registered": False, "rounds": results}
    with open(os.path.join(a.out_dir, "timing.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    with open(os.path.join(a.out_dir, "TIMING.md"), "w", encoding="utf-8") as f:
        f.write(report_md(results))


if __name__ == "__main__":
    main()
