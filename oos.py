# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Out-of-sample check: the HF26 shape model on DEV challenges it never saw.

The model in hf26.py is fitted on the 55 challenges in data/posts.csv, whose newest announcement is the
latest one in data/challenges.json (2026-10-09). This script takes EVERY devteam winners announcement
published after that one, except Hacktoberfest rounds (weeks 1-4 are the pre-registered forward test and
are scored there), and ranks that challenge's entries with the same model, refitted unchanged.

This is not a forecast: the winners were already public when it runs. It is out of sample because the
model never saw these challenges, and the selection rule above picks challenges by date alone, so none is
chosen for how it scores. Entries are read after the announcement, so a post edited since then is
measured as edited (the count is reported).

Winners follow the study's convention (every entry linked from the announcement, as in the backtest and
score_round.py); a second count uses only posts embedded as cards. Outputs hold article ids and measured
features, never usernames. Made by MV2 of Munim, Inc., with AI agents working in his name.
"""
import argparse
import csv
import json
import math
import os
import random
import sys
import time
import urllib.parse
import urllib.request
from datetime import timedelta

import hf26

VERSION = "0.1.0"
WINDOW_DAYS = 120  # same as the backtest's rule for a linked post to count as a winner
DRAWS = 200000
# Tags too broad to be a challenge's own tag.
BROAD = {"devchallenge", "ai", "hackathon", "webdev", "programming", "beginners", "javascript", "python",
         "productivity", "opensource", "tutorial", "discuss", "career", "softwaredevelopment", "news",
         "machinelearning", "writing", "api", "react", "agents", "showdev", "hacktoberfest", "hf26challenge"}


def busted(path, token):
    return path + ("&" if "?" in path else "?") + "item=" + token


class BustedClient(hf26.Client):
    """hf26.Client with a per-run `item` token, so listing pages come fresh from DEV's origin."""

    token = "oos" + str(int(time.time()))

    def get(self, path, tries=6):
        return super().get(busted(path, self.token), tries)


def training_cutoff(challenges):
    """Newest announcement time in the training challenges."""
    return max(hf26.parse_time(c["announced"]) for c in challenges if c.get("announced"))


def is_winners_post(title):
    t = (title or "").lower()
    return t.startswith("congrat") and "winner" in t


def select_announcements(articles, after):
    """devteam winners posts published after `after`, Hacktoberfest rounds left out, oldest first."""
    out = []
    for a in articles:
        title = a.get("title") or ""
        if not is_winners_post(title) or not a.get("published_at"):
            continue
        if "hacktoberfest" in title.lower():
            continue
        if hf26.parse_time(a["published_at"]) <= after:
            continue
        out.append(a)
    return sorted(out, key=lambda a: a["published_at"])


def challenge_tag(tags):
    """The challenge's own tag: first non-broad tag, preferring one that contains 'challenge'."""
    cands = [t for t in tags if t not in BROAD]
    named = [t for t in cands if "challenge" in t]
    return (named or cands or [None])[0]


def embedded_keys(markdown):
    return {(u.lower(), s.lower()) for u, s in hf26.LIQUID_RE.findall(markdown or "")}


def hits_tail(n, k, h):
    """P(at least h of k random picks land in the top k of n): hypergeometric upper tail."""
    if k == 0 or n == 0:
        return None
    total = math.comb(n, k)
    return sum(math.comb(k, i) * math.comb(n - k, k - i) for i in range(h, k + 1)) / total


def mean_pct_tail(n, k, observed, draws=DRAWS, seed=2026):
    """Share of random k-subsets of n ranks whose mean percentile is at least `observed`."""
    if k == 0 or n < 2:
        return None
    rng = random.Random(seed)
    pcts = [1 - i / (n - 1) for i in range(n)]
    hit = 0
    for _ in range(draws):
        if sum(rng.sample(pcts, k)) / k >= observed - 1e-12:
            hit += 1
    return hit / draws


def score_set(ranked, winner_ids):
    res = {}
    for by, name in (("rank", "logistic"), ("rank_score", "rank_score")):
        s = hf26.score_predictions(ranked, winner_ids, by=by)
        n, k = s["ranked_entries"], s["winners_in_ranking"]
        s["p_hits_at_least"] = round(hits_tail(n, k, s["hits_top_k"]), 5) if k else None
        # Unrounded mean, from the winners' 1-based ranks, so the tail is not shifted by rounding.
        exact = sum(1 - (r - 1) / max(1, n - 1) for r in s["winner_ranks"]) / k if k else None
        s["p_mean_percentile_at_least"] = mean_pct_tail(n, k, exact) if k else None
        res[name] = s
    return res


def fit_model(train_path, l2=1.0):
    if not os.path.exists(train_path):
        hf26.log(f"downloading training data to {train_path}")
        os.makedirs(os.path.dirname(train_path) or ".", exist_ok=True)
        req = urllib.request.Request(hf26.TRAIN_URL, headers={"User-Agent": hf26.UA})
        with urllib.request.urlopen(req, timeout=120) as r, open(train_path, "wb") as f:
            f.write(r.read())
    raw = hf26.load_train(train_path)
    kept = hf26.prepare_train(raw)
    X, y = [], []
    for rs in kept.values():
        for r in rs:
            X.append(hf26.vector(r))
            y.append(int(r["is_winner"]))
    w = hf26.fit_logistic(X, y, l2=l2)
    ids = set()
    for r in raw:
        for col in ("article_id", "id"):
            if r.get(col):
                ids.add(int(r[col]))
                break
    return w, {"train_challenges": len(kept), "train_rows": len(X), "train_winners": sum(y),
               "train_article_ids_known": bool(ids)}, ids


def compare_model(w, path):
    """Largest weight difference against a committed model.json (None if absent)."""
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        m = json.load(f)
    diffs = [abs(round(w[0], 4) - m["bias"])]
    diffs += [abs(round(v, 4) - m["weights"][f]) for f, v in zip(hf26.FEATURES, w[1:])]
    return round(max(diffs), 4)


def field_rows(client, tag, announced, train_ids, budget_s, t0):
    since = announced - timedelta(days=WINDOW_DAYS)
    listing = hf26.list_tag(client, tag, since)
    rows, skipped = [], {"official": 0, "after_announcement": 0, "no_devchallenge_tag": 0,
                         "not_english": 0, "in_training_data": 0, "no_body": 0, "edited_after_announcement": 0}
    for a in listing:
        if not a.get("published_at"):
            continue
        pub = hf26.parse_time(a["published_at"])
        if pub < since:
            continue
        if pub >= announced:
            skipped["after_announcement"] += 1
            continue
        if hf26.is_official(a):
            skipped["official"] += 1
            continue
        if "devchallenge" not in hf26.tags_of(a):
            skipped["no_devchallenge_tag"] += 1
            continue
        if (a.get("language") or "en") != "en":
            skipped["not_english"] += 1
            continue
        if int(a["id"]) in train_ids:
            skipped["in_training_data"] += 1
            continue
        if time.time() - t0 > budget_s:
            skipped["no_body"] += 1
            continue
        d = client.get(f"/articles/{a['id']}")
        if not (isinstance(d, dict) and "body_markdown" in d):
            skipped["no_body"] += 1
            continue
        row = {"article_id": int(a["id"]), "published_at": a["published_at"], "has_body": 1}
        row.update(hf26.meta_features(a))
        row.update(hf26.body_features(d.get("body_markdown") or ""))
        edited = d.get("edited_at")
        row["edited_after_announcement"] = int(bool(edited) and hf26.parse_time(edited) >= announced)
        skipped["edited_after_announcement"] += row["edited_after_announcement"]
        rows.append(row)
    return rows, len(listing), skipped


def resolve_winners(client, ann):
    links = hf26.extract_links(ann.get("body_html"), ann.get("body_markdown"))
    cards = embedded_keys(ann.get("body_markdown"))
    linked, embedded = [], []
    for user, slug in links:
        w = client.get(f"/articles/{urllib.parse.quote(user)}/{urllib.parse.quote(slug)}")
        if isinstance(w, dict) and w.get("id"):
            wid = int(w["id"])
            if wid not in linked:
                linked.append(wid)
            if (user.lower(), slug.lower()) in cards and wid not in embedded:
                embedded.append(wid)
    return linked, embedded


def report(result):
    out = ["# The HF26 shape model on DEV challenges it never saw", "",
           f"oos.py {VERSION}. Every devteam winners post published after the newest challenge in the model's "
           f"training data ({result['training_cutoff']}), Hacktoberfest rounds left out. Not a forecast: the "
           "winners were public when this ran; out of sample because the model never saw these challenges. "
           "Made by MV2 of Munim, Inc., with AI agents working in his name. Data CC BY 4.0.", "",
           f"Model: refitted unchanged on {result['model']['train_challenges']} challenges "
           f"({result['model']['train_rows']} posts, {result['model']['train_winners']} winners). "
           f"Largest weight difference from the committed week-2 model: {result['model_check']}.", ""]
    if not result["challenges"]:
        out += ["No qualifying announcement yet.", ""]
    out += ["| Challenge | Tag | Entries ranked | Winners | Model | Winners in top-k (chance) | P(at least) | "
            "Mean winner percentile | Share of random sets as high |", "|---|---|---|---|---|---|---|---|---|"]
    for c in result["challenges"]:
        if c.get("status") != "scored":
            out.append(f"| {c['title']} | {c.get('tag')} | {c.get('status')} | | | | | | |")
            continue
        for wset in ("linked", "embedded"):
            for model in ("logistic", "rank_score"):
                s = c["scores"][wset][model]
                if not s["winners_in_ranking"]:
                    continue
                out.append(f"| {c['title']} | {c['tag']} | {s['ranked_entries']} | {s['winners_in_ranking']} {wset} | "
                           f"{model} | {s['hits_top_k']} ({s['expected_hits_if_random']}) | {s['p_hits_at_least']} | "
                           f"{s['mean_winner_percentile']} | {s['p_mean_percentile_at_least']} |")
    out += ["", "- 'linked' = every entry linked from the announcement (the study's convention, which counts "
            "honourable mentions); 'embedded' = only entries shown as cards.",
            "- Entries: English posts with the challenge tag and devchallenge, published in the 120 days before "
            "the announcement, DEV's own posts and training-data posts left out.",
            "- Chance for top-k is k*k/n; P(at least) is the exact hypergeometric tail; the last column uses "
            f"{DRAWS:,} random sets.", ""]
    for c in result["challenges"]:
        if c.get("status") == "scored":
            out.append(f"- {c['tag']}: listed {c['listed']}, left out or flagged {json.dumps(c['skipped'])}; "
                       f"linked winners missing from the ranking: {c['scores']['linked']['logistic']['missing_from_ranking']}.")
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--train", default="/data/posts.csv")
    ap.add_argument("--challenges", default="challenges.json")
    ap.add_argument("--model-check", default="model_week2.json")
    ap.add_argument("--budget-minutes", type=float, default=90)
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    t0 = time.time()
    with open(a.challenges, encoding="utf-8") as f:
        cutoff = training_cutoff(json.load(f))
    w, model, train_ids = fit_model(a.train)
    check = compare_model(w, a.model_check)
    hf26.log(f"oos.py {VERSION}; cutoff {cutoff.isoformat()}; model {json.dumps(model)}; weight diff {check}")
    client = BustedClient()
    devteam = client.get("/articles?username=devteam&per_page=100&page=1") or []
    anns = select_announcements(devteam, cutoff)
    hf26.log(f"{len(anns)} announcement(s) after the cutoff: {[x['title'] for x in anns]}")
    result = {"version": VERSION, "run_at": hf26.now_iso(), "training_cutoff": cutoff.isoformat(),
              "model": model, "model_check": check if check is not None else "model.json not committed",
              "challenges": []}
    for i, short in enumerate(anns):
        ann = client.get(f"/articles/{short['id']}")
        c = {"announcement_id": short["id"], "title": short["title"], "announced": short["published_at"]}
        result["challenges"].append(c)
        if not isinstance(ann, dict):
            c["status"] = "announcement not readable"
            continue
        tag = challenge_tag(hf26.tags_of(ann))
        c["tag"] = tag
        if not tag:
            c["status"] = "no challenge tag"
            continue
        announced = hf26.parse_time(ann["published_at"])
        budget_s = a.budget_minutes * 60 * (i + 1) / len(anns)
        rows, listed, skipped = field_rows(client, tag, announced, train_ids, budget_s, t0)
        c.update({"listed": listed, "skipped": skipped, "entries": len(rows)})
        if len(rows) < 10:
            c["status"] = f"field too small ({len(rows)})"
            continue
        linked, embedded = resolve_winners(client, ann)
        ranked = hf26.predict_round(w, rows)
        c["status"] = "scored"
        c["winner_ids"] = {"linked": linked, "embedded": embedded}
        c["scores"] = {"linked": score_set(ranked, linked), "embedded": score_set(ranked, embedded)}
        with open(os.path.join(a.out_dir, f"ranking_{tag}.csv"), "w", newline="", encoding="utf-8") as f:
            wr = csv.DictWriter(f, fieldnames=["rank", "article_id", "score", "rank_score"])
            wr.writeheader()
            wr.writerows(ranked)
        cols = (["article_id", "published_at", "edited_after_announcement"] + hf26.CONT + hf26.BINARY)
        with open(os.path.join(a.out_dir, f"entries_{tag}.csv"), "w", newline="", encoding="utf-8") as f:
            wr = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
            wr.writeheader()
            wr.writerows(sorted(rows, key=lambda r: r["article_id"]))
        hf26.log(json.dumps({k: v for k, v in c.items() if k != "scores"}))
        hf26.log(json.dumps(c["scores"]))
    result["requests"] = client.requests
    result["minutes"] = round((time.time() - t0) / 60, 1)
    hf26.write_json(os.path.join(a.out_dir, "oos.json"), result)
    with open(os.path.join(a.out_dir, "OOS.md"), "w", encoding="utf-8") as f:
        f.write(report(result))
    hf26.log("OOS DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
