# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Do DEV challenge winners carry AI-disclosure labels more often than the entries they beat?

The forward test pre-registered in PREREGISTRATION_AILABEL.md. For each round it reads three committed files:
the snapshot's entries CSV (labels as they stood before the winners were named), the ranking CSV (which posts
form the field) and the frozen scorer's JSON (`winner_ids`). It then counts winners whose post declared AI use
(`ai_declared` = 1: DEV's "AI-assisted" or "Fully Autonomous" label) and compares that count with what a random
choice of the same number of winners from the same field would give (hypergeometric, exact, rounds pooled by
convolution).

  python ailabel.py --round week4 ENTRIES.csv RANKING.csv SCORE.json [--round NAME E R S ...] --out-dir out
  python ailabel.py ... --live      # also re-read each winner's label from DEV now (exploratory; needs network)

Writes out/AILABEL.md and out/ailabel.json. Standard library only. Made by MV2 of Munim, Inc., with AI agents
working in his name. Apache-2.0.
"""
import argparse
import csv
import json
import os
import sys
import time
import urllib.request

VERSION = "0.1.0"
ALPHA = 0.05
LEVELS = ["not_disclosed", "no_ai", "some_ai", "fully_autonomous"]
USER_AGENT = "mv2-devchallenge-study/ailabel (MV2 of Munim, Inc.; github.com/munimtechnologies/devchallenge-study)"


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def read_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def as_int(value):
    return int(float(str(value).strip()))


def build_field(entries, ranking):
    """article_id -> entry row, for every post in the ranking. A ranked post missing from entries is an error."""
    by_id = {}
    for row in entries:
        by_id[as_int(row["article_id"])] = row
    field = {}
    for row in ranking:
        aid = as_int(row["article_id"])
        if aid not in by_id:
            raise ValueError("ranked post %d is not in the entries file" % aid)
        field[aid] = by_id[aid]
    return field


def declared(row):
    return as_int(row["ai_declared"])


def level(row):
    value = (row.get("ai_level") or "").strip()
    return value or None


def winner_ids(score):
    """score_round.py writes a flat list; forecast_oos.py writes {"linked": [...], "embedded": [...]} plus
    "primary_winner_set", the set its own pre-registered scoring uses. Use exactly that set."""
    if "winner_ids" not in score:
        raise ValueError("score JSON has no winner_ids (status: %s)" % score.get("status"))
    ids = score["winner_ids"]
    if isinstance(ids, dict):
        which = score.get("primary_winner_set")
        if which not in ids:
            raise ValueError("score JSON names no usable primary_winner_set")
        ids = ids[which]
    return [as_int(w) for w in ids]


def comb(n, k):
    if k < 0 or k > n:
        return 0
    out = 1
    for i in range(1, k + 1):
        out = out * (n - k + i) // i
    return out


def hypergeom(N, m, k):
    """P(X = x) for x = 0..k: x marked posts among k drawn without replacement from N posts, m of them marked."""
    total = comb(N, k)
    return [comb(m, x) * comb(N - m, k - x) / total for x in range(k + 1)]


def convolve(a, b):
    out = [0.0] * (len(a) + len(b) - 1)
    for i, p in enumerate(a):
        for j, q in enumerate(b):
            out[i + j] += p * q
    return out


def upper_tail(pmf, d):
    return min(1.0, sum(pmf[d:])) if d < len(pmf) else 0.0


def score_round(name, field, winners):
    in_field = [w for w in winners if w in field]
    missing = [w for w in winners if w not in field]
    N, k = len(field), len(in_field)
    m = sum(declared(r) for r in field.values())
    d = sum(declared(field[w]) for w in in_field)
    out = {
        "round": name, "field": N, "winners_listed": len(winners), "winners_in_field": k,
        "winners_missing_from_field": missing, "declared_in_field": m, "declared_winners": d,
        "expected_declared_winners": k * m / N if N else 0.0,
        "field_share_declared": m / N if N else 0.0,
        "winner_share_declared": d / k if k else None,
        "pmf": hypergeom(N, m, k) if N else [1.0],
        "levels": None,
    }
    if all(level(r) is not None for r in field.values()) and N:
        levels = {}
        for lv in sorted({level(r) for r in field.values()} | set(LEVELS)):
            mf = sum(1 for r in field.values() if level(r) == lv)
            mw = sum(1 for w in in_field if level(field[w]) == lv)
            levels[lv] = {"field": mf, "winners": mw, "expected": k * mf / N,
                          "p_zero_if_random": hypergeom(N, mf, k)[0]}
        out["levels"] = levels
    return out


def pooled(rounds):
    pmf = [1.0]
    for r in rounds:
        pmf = convolve(pmf, r["pmf"])
    D = sum(r["declared_winners"] for r in rounds)
    E = sum(r["expected_declared_winners"] for r in rounds)
    K = sum(r["winners_in_field"] for r in rounds)
    p = upper_tail(pmf, D)
    return {"winners": K, "declared_winners": D, "expected_declared_winners": E, "p_one_sided": p,
            "p1_direction_held": D > E, "p1_significant": D > E and p <= ALPHA}


def p2(rounds):
    """Pre-registered P2: no winner labelled Fully Autonomous, in rounds whose snapshot kept the level."""
    graded = [r for r in rounds if r["levels"] is not None]
    if not graded:
        return {"gradable": False}
    fa = sum(r["levels"]["fully_autonomous"]["winners"] for r in graded)
    p0 = 1.0
    for r in graded:
        p0 *= r["levels"]["fully_autonomous"]["p_zero_if_random"]
    return {"gradable": True, "rounds": [r["round"] for r in graded], "fully_autonomous_winners": fa,
            "expected": sum(r["levels"]["fully_autonomous"]["expected"] for r in graded),
            "p_zero_if_random": p0, "held": fa == 0}


def fetch_level(aid, opener=None, pause=1.0):
    req = urllib.request.Request("https://dev.to/api/articles/%d" % aid, headers={"User-Agent": USER_AGENT})
    open_ = opener or (lambda r: urllib.request.urlopen(r, timeout=60).read())
    try:
        data = json.loads(open_(req))
    except Exception as exc:  # a deleted or unreachable post is reported, not guessed
        return "unavailable: %s" % type(exc).__name__
    finally:
        if pause:
            time.sleep(pause)
    return data.get("ai_disclosure_level") or "not_disclosed"


def relabels(rounds_fields, opener=None, pause=1.0):
    """Exploratory: each winner's label now versus in the snapshot."""
    rows = []
    for name, field, winners in rounds_fields:
        for w in winners:
            if w not in field or level(field[w]) is None:
                continue
            now = fetch_level(w, opener, pause)
            rows.append({"round": name, "article_id": w, "snapshot": level(field[w]), "now": now,
                         "changed": not now.startswith("unavailable") and now != level(field[w])})
    return rows


def fmt_p(p):
    return "%.4f" % p if p >= 0.0001 else "%.1e" % p


def report(rounds, pool, second, live):
    lines = ["# Do winners carry AI-disclosure labels more often? (forward test)", "",
             "ailabel.py %s, run %s UTC. Pre-registered in PREREGISTRATION_AILABEL.md; labels are those frozen in "
             "each round's committed snapshot, taken before DEV named the winners." %
             (VERSION, time.strftime("%Y-%m-%d %H:%M", time.gmtime())), "",
             "| Round | Field | Declared AI in field | Winners in field | Declared AI among winners | Expected if random |",
             "|---|---|---|---|---|---|"]
    for r in rounds:
        lines.append("| %s | %d | %d (%.1f%%) | %d | %d | %.2f |" % (
            r["round"], r["field"], r["declared_in_field"], 100 * r["field_share_declared"],
            r["winners_in_field"], r["declared_winners"], r["expected_declared_winners"]))
    lines += ["", "**P1 (primary):** %d of %d winners declared AI against %.2f expected; one-sided exact p = %s. "
              "Direction %s; %s at %.2f." % (
                  pool["declared_winners"], pool["winners"], pool["expected_declared_winners"],
                  fmt_p(pool["p_one_sided"]), "held" if pool["p1_direction_held"] else "did not hold",
                  "significant" if pool["p1_significant"] else "not significant", ALPHA)]
    if second["gradable"]:
        lines += ["", "**P2:** %d winner(s) labelled Fully Autonomous in %s (%.2f expected; chance of none if "
                  "winners were random: %s). %s." % (
                      second["fully_autonomous_winners"], ", ".join(second["rounds"]), second["expected"],
                      fmt_p(second["p_zero_if_random"]), "Held" if second["held"] else "Did not hold")]
    else:
        lines += ["", "**P2:** not gradable (no round kept the label level)."]
    for r in rounds:
        if r["winners_missing_from_field"]:
            lines += ["", "%s: %d winner(s) not in the ranked field, left out of both counts: %s" % (
                r["round"], len(r["winners_missing_from_field"]),
                ", ".join(str(w) for w in r["winners_missing_from_field"]))]
        if r["levels"]:
            lines += ["", "%s by label level:" % r["round"], "",
                      "| Level | Field | Winners | Expected |", "|---|---|---|---|"]
            for lv, c in r["levels"].items():
                lines.append("| %s | %d | %d | %.2f |" % (lv, c["field"], c["winners"], c["expected"]))
    if live is not None:
        changed = [x for x in live if x["changed"]]
        lines += ["", "**Exploratory, not pre-registered as a test:** %d of %d winners' labels differ now from the "
                  "snapshot." % (len(changed), len(live))]
        for x in changed:
            lines.append("- %s %d: %s -> %s" % (x["round"], x["article_id"], x["snapshot"], x["now"]))
    lines += ["", "Winners include honourable mentions where DEV lists them. This shows what winners have in common, "
              "not what makes them win. Made by MV2 of Munim, Inc., with AI agents working in his name.", ""]
    return "\n".join(lines)


def main(argv=None, opener=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", nargs=4, action="append", required=True,
                    metavar=("NAME", "ENTRIES", "RANKING", "SCORE_JSON"))
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--pause", type=float, default=1.0)
    a = ap.parse_args(argv)
    rounds, rf = [], []
    for name, entries, ranking, score in a.round:
        field = build_field(read_csv(entries), read_csv(ranking))
        winners = winner_ids(read_json(score))
        rounds.append(score_round(name, field, winners))
        rf.append((name, field, winners))
    pool = pooled(rounds)
    second = p2(rounds)
    live = relabels(rf, opener, a.pause) if a.live else None
    os.makedirs(a.out_dir, exist_ok=True)
    result = {"version": VERSION, "alpha": ALPHA, "pooled": pool, "p2": second, "live_relabels": live,
              "rounds": [{k: v for k, v in r.items() if k != "pmf"} for r in rounds]}
    with open(os.path.join(a.out_dir, "ailabel.json"), "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=1)
    text = report(rounds, pool, second, live)
    with open(os.path.join(a.out_dir, "AILABEL.md"), "w", encoding="utf-8") as fh:
        fh.write(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
