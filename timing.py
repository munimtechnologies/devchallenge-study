"""When in a round were DEV's Hacktoberfest 2026 winners posted?

For each scored round, every announced winner's publish time is ranked among the
round's committed, ranked entries (ties count half) and the percentiles are
averaged: 0.50 means "posted like a typical entry", above 0.50 means later. The
55-challenge history in this repo put winners at 0.49. Weeks 1 and 2 are
exploratory; weeks 3 and 4 are the forward test in PREREGISTRATION_TIMING.md.

0.1.1: week 2's winners are read from the committed scorer output
(predictions/2026-10-19/score_week2_full.json); 0.1.0 read the same 18 ids from a
local copy. Nothing else changed.

0.2.0: each round is also counted a second time ("<round>-by-close") using only
the ranked entries published by the round's close (hf26.ROUNDS end), since a
ranking taken days after the close also holds posts that came too late to enter.
The all-entries rows are unchanged.

0.3.0: written before any week-3 data existed. Adds weeks 3 and 4 and computes the
pre-registered call (pooled_call): the mean over all timed winners of both rounds,
against 0.5 +/- 1.96 * sqrt(1 / (12K)), plus the pooled first-fifth count; the
by-close pool is reported as secondary. A round whose files are not committed yet,
or whose score status is not "scored", is listed and skipped. analyse() and the
weeks 1-2 numbers are unchanged.

Made by MV2 of Munim, Inc., with AI agents working in his name. Apache-2.0.
"""
import argparse
import csv
import json
import math
import os
import random
import urllib.error
import urllib.request
from datetime import datetime, timezone

VERSION = "0.3.0"
RAW = "https://raw.githubusercontent.com/munimtechnologies/devchallenge-study/main/"
UA = "devchallenge-study timing.py (MV2 of Munim, Inc.; mv2@munimtech.com)"

# Closes match hf26.ROUNDS (DEV's 23:59 PDT cutoff, one minute later in UTC).
# Weeks 3 and 4: the folders their full rankings and frozen-scorer output are committed to.
ROUNDS = {
    "week1": {"ranking": "predictions/2026-10-14/predictions_week1.csv",
              "entries": "predictions/2026-10-14/entries.csv",
              "score": "predictions/2026-10-14/score_week1.json",
              "close": "2026-10-12T07:00:00Z"},
    "week2": {"ranking": "predictions/2026-10-19/predictions_week2.csv",
              "entries": "predictions/2026-10-19/entries.csv",
              "score": "predictions/2026-10-19/score_week2_full.json",
              "close": "2026-10-19T07:00:00Z"},
    "week3": {"ranking": "predictions/2026-10-26/predictions_week3.csv",
              "entries": "predictions/2026-10-26/entries.csv",
              "score": "predictions/2026-10-26/score_week3_full.json",
              "close": "2026-10-26T07:00:00Z"},
    "week4": {"ranking": "predictions/2026-11-01/predictions_week4.csv",
              "entries": "predictions/2026-11-01/entries.csv",
              "score": "predictions/2026-11-01/score_week4_full.json",
              "close": "2026-11-01T07:00:00Z"},
}

# PREREGISTRATION_TIMING.md (committed 2026-10-24, before week 3 closed): the call is made on these
# rounds pooled. If only one is scored "by 2026-11-30", the call is made on it alone; if none, not testable.
PREREG_ROUNDS = ("week3", "week4")
PREREG_DEADLINE = "2026-12-01T00:00:00Z"
READINGS = {"late": "winners are posted late", "none": "no clear timing effect",
            "early": "winners are posted early"}


class NotCommitted(Exception):
    """A round file is not in the repo yet (404)."""


def fetch(path, data_dir, token):
    """Local file if it exists (in the workdir), else download from the repo."""
    if os.path.exists(path):
        return path
    dest = os.path.join(data_dir, path.replace("/", "__"))
    if not os.path.exists(dest):
        req = urllib.request.Request(RAW + path + "?item=" + token, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                body = r.read()
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise NotCommitted(path)
            raise
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


def analyse(ranked_ids, published, winner_ids, draws=200000, seed=2026, close=None):
    times_by_id = {a: published[a] for a in ranked_ids if a in published}
    after_close = 0
    if close:
        after_close = sum(1 for t in times_by_id.values() if t > close)
        times_by_id = {a: t for a, t in times_by_id.items() if t <= close}
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
    if close:
        res.update({"close": close, "entries_after_close_left_out": after_close})
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


def pool(rows):
    """Mean over every timed winner of `rows` (each round weighted by its K) and its 95% null range."""
    pcts = [p for r in rows for p in r["winner_time_percentiles"]]
    k = len(pcts)
    mean = sum(pcts) / k
    half = 1.96 * math.sqrt(1 / 12 / k)
    reading = "late" if mean > 0.5 + half else "early" if mean < 0.5 - half else "none"
    first_fifth = sum(1 for p in pcts if p < 0.2)
    return {"winners_timed": k, "mean_time_percentile": round(mean, 4),
            "null_95_interval": [round(0.5 - half, 4), round(0.5 + half, 4)],
            "reading": READINGS[reading], "primary_prediction_held": reading == "late",
            "winners_in_first_fifth": first_fifth, "expected_in_first_fifth": round(0.2 * k, 2),
            "secondary_prediction_held": first_fifth < 0.2 * k}


def pooled_call(results, now=None):
    """The pre-registered call, from the all-entries rows of PREREG_ROUNDS; by-close pool is secondary."""
    now = now or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    scored = [n for n in PREREG_ROUNDS if results.get(n, {}).get("winners_timed")]
    res = {"rounds": list(PREREG_ROUNDS), "rounds_scored": scored, "deadline": PREREG_DEADLINE}
    if len(scored) < len(PREREG_ROUNDS) and now < PREREG_DEADLINE:
        res["status"] = "pending"
        return res
    if not scored:
        res["status"] = "not_testable"
        return res
    res["status"] = "pooled" if len(scored) == len(PREREG_ROUNDS) else "one_round"
    res.update(pool([results[n] for n in scored]))
    by_close = [results[n + "-by-close"] for n in scored
                if results.get(n + "-by-close", {}).get("winners_timed")]
    if by_close:
        res["secondary_by_close"] = pool(by_close)
    return res


def report_md(results, call=None):
    lines = ["# When were the winners posted?", "",
             "timing.py %s. Weeks 1 and 2 are exploratory; weeks 3 and 4 are the forward test in "
             "PREREGISTRATION_TIMING.md, decided only by the pooled call below. Each winner's publish "
             "time is ranked among the round's committed, ranked entries (ties half); 0.50 = posted like "
             "a typical entry, higher = later. Made by MV2 of Munim, Inc., with AI agents working in his "
             "name. Data CC BY 4.0." % VERSION, "",
             "| Round | Entries | Winners timed | Mean time percentile | 95% range if timing didn't matter "
             "| Winners in the first fifth (expected) | Winners in the first half | Random draws with a mean this late |",
             "|---|---|---|---|---|---|---|---|"]
    for name, r in results.items():
        if "status" in r:
            lines.append("| %s | %s | | | | | | |" % (name, r["status"].replace("_", " ")))
            continue
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
              "- \"-by-close\" rows use only the ranked entries published by the round's close."]
    for name, r in results.items():
        if "close" in r:
            lines.append("- %s: close %s, %d ranked entries published after it left out." % (
                name, r["close"], r["entries_after_close_left_out"]))
    lines.append("- Earlier work in this repo (55 challenges, 323 winners) put winners at 0.49 of "
                 "their challenge's posting window.")
    if call:
        lines += ["", "## Pre-registered call (%s)" % " + ".join(call["rounds"]), ""]
        if call["status"] == "pending":
            lines.append("Pending: scored so far: %s. The call waits for both rounds, or for %s if only "
                         "one is scored by then." % (", ".join(call["rounds_scored"]) or "none",
                                                     call["deadline"]))
        elif call["status"] == "not_testable":
            lines.append("Not testable: neither round was scored by %s." % call["deadline"])
        else:
            label = "pooled" if call["status"] == "pooled" else "one round only (%s)" % call["rounds_scored"][0]
            lines += ["- Basis: %s, %d timed winners." % (label, call["winners_timed"]),
                      "- Mean time percentile %.3f; 95%% range if timing didn't matter %.3f to %.3f." % (
                          call["mean_time_percentile"], call["null_95_interval"][0],
                          call["null_95_interval"][1]),
                      "- **Call: %s.** Primary prediction (above the range) %s." % (
                          call["reading"], "held" if call["primary_prediction_held"] else "did not hold"),
                      "- Secondary: %d winners in the first fifth against %.1f expected; prediction "
                      "(fewer) %s." % (call["winners_in_first_fifth"], call["expected_in_first_fifth"],
                                       "held" if call["secondary_prediction_held"] else "did not hold")]
            sec = call.get("secondary_by_close")
            if sec:
                lines.append("- Secondary, entries published by each close only: mean %.3f, range %.3f "
                             "to %.3f, %s." % (sec["mean_time_percentile"], sec["null_95_interval"][0],
                                               sec["null_95_interval"][1], sec["reading"]))
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
        try:
            ranked = read_ranked_ids(fetch(src["ranking"], a.data_dir, token))
            published = read_published(fetch(src["entries"], a.data_dir, token))
            with open(fetch(src["score"], a.data_dir, token), encoding="utf-8") as f:
                score = json.load(f)
        except NotCommitted as exc:
            results[name] = {"status": "not_committed", "missing_file": str(exc), "sources": src}
            print(name, "not committed yet:", exc)
            continue
        if score.get("status") != "scored":
            results[name] = {"status": "not_scored", "score_status": score.get("status"), "sources": src}
            print(name, "score status is", score.get("status"))
            continue
        winner_ids = [int(w) for w in score["winner_ids"]]
        runs = [(name, None)]
        if src.get("close"):
            runs.append((name + "-by-close", src["close"]))
        for label, close in runs:
            results[label] = analyse(ranked, published, winner_ids, draws=a.draws, close=close)
            results[label]["sources"] = src
            print(label, json.dumps({k: v for k, v in results[label].items()
                                     if k != "winner_time_percentiles"}))
    call = pooled_call(results)
    print("pre-registered call", json.dumps(call))
    out = {"version": VERSION, "exploratory_rounds": [n for n in ROUNDS if n not in PREREG_ROUNDS],
           "pre_registered_call": call, "rounds": results}
    with open(os.path.join(a.out_dir, "timing.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    with open(os.path.join(a.out_dir, "TIMING.md"), "w", encoding="utf-8") as f:
        f.write(report_md(results, call))


if __name__ == "__main__":
    main()
