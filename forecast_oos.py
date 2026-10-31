# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""A forward out-of-sample forecast: the HF26 shape model on a DEV challenge it never saw, ranked BEFORE
DEV names that challenge's winners.

oos.py ranks challenges after their winners are public. This script does the same for one challenge whose
submissions have closed but whose winners are not announced yet, so the ranking can be committed first and
scored later. The model is the committed one, refitted unchanged (oos.fit_model). The field is fixed in
advance by the challenge's own tag and its submission window, read from DEV's join post, not from winners.

    python forecast_oos.py snapshot --tag kagglechallenge --title-word kaggle \
        --opened 2026-09-23T20:59:28Z --deadline 2026-10-12T07:00:00Z --out-dir out
    python forecast_oos.py score --predictions predictions_kagglechallenge.csv --title-word kaggle --out-dir out

`snapshot` refuses to run before the deadline. If DEV has already announced the winners when it runs, the
output says so and the ranking is not a forecast. `score` reads the winners exactly as oos.py 0.1.1 does.
Outputs hold article ids and measured features, never usernames. Made by MV2 of Munim, Inc., with AI agents
working in his name.
"""
import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime, timezone

import hf26
import oos

VERSION = "0.1.0"


def find_announcement(articles, word):
    """Newest devteam winners post whose title contains `word` (case-insensitive), or None."""
    hits = [a for a in articles
            if oos.is_winners_post(a.get("title")) and word.lower() in (a.get("title") or "").lower()
            and a.get("published_at")]
    return max(hits, key=lambda a: a["published_at"]) if hits else None


def classify(a, opened, deadline, train_ids):
    """Why a listed post is or is not ranked. 'ranked' means it enters the field."""
    if not a.get("published_at"):
        return "no_date"
    pub = hf26.parse_time(a["published_at"])
    if pub < opened:
        return "before_opened"
    if pub >= deadline:
        return "after_deadline"
    if hf26.is_official(a):
        return "official"
    if (a.get("language") or "en") != "en":
        return "not_english"
    if int(a["id"]) in train_ids:
        return "in_training_data"
    return "ranked"


def field_rows(client, tag, opened, deadline, train_ids, budget_s, t0):
    listing = hf26.list_tag(client, tag, opened)
    rows = []
    skipped = {"no_date": 0, "before_opened": 0, "after_deadline": 0, "official": 0, "not_english": 0,
               "in_training_data": 0, "no_body": 0}
    edited = 0
    for a in listing:
        why = classify(a, opened, deadline, train_ids)
        if why != "ranked":
            skipped[why] += 1
            continue
        if time.time() - t0 > budget_s:
            skipped["no_body"] += 1
            continue
        d = client.get(f"/articles/{a['id']}")
        if not (isinstance(d, dict) and "body_markdown" in d):
            skipped["no_body"] += 1
            continue
        row = {"article_id": int(a["id"]), "published_at": a["published_at"], "has_body": 1,
               "has_devchallenge_tag": int("devchallenge" in hf26.tags_of(a))}
        row.update(hf26.meta_features(a))
        row.update(hf26.body_features(d.get("body_markdown") or ""))
        e = d.get("edited_at")
        row["edited_after_deadline"] = int(bool(e) and hf26.parse_time(e) >= deadline)
        edited += row["edited_after_deadline"]
        rows.append(row)
    return rows, len(listing), skipped, edited


def write_ranking(path, ranked):
    with open(path, "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=["rank", "article_id", "score", "rank_score"])
        wr.writeheader()
        wr.writerows(ranked)


def read_ranking(path):
    with open(path, newline="", encoding="utf-8") as f:
        return [{"rank": int(r["rank"]), "article_id": int(r["article_id"]), "score": float(r["score"]),
                 "rank_score": float(r["rank_score"])} for r in csv.DictReader(f)]


def primary_winners(linked, embedded):
    """Pre-registered: the winners are the entries shown as cards; if the post embeds none, every linked entry."""
    return ("embedded", embedded) if embedded else ("linked", linked)


def snapshot(a):
    opened, deadline = hf26.parse_time(a.opened), hf26.parse_time(a.deadline)
    if datetime.now(timezone.utc) < deadline:
        print(f"submissions are open until {a.deadline}; a ranking now would be partial. Nothing done.")
        return 1
    os.makedirs(a.out_dir, exist_ok=True)
    t0 = time.time()
    with open(a.challenges, encoding="utf-8") as f:
        cutoff = oos.training_cutoff(json.load(f))
    w, model, train_ids = oos.fit_model(a.train)
    check = oos.compare_model(w, a.model_check)
    client = oos.BustedClient()
    started = hf26.now_iso()
    devteam = client.get("/articles?username=devteam&per_page=100&page=1") or []
    ann_before = find_announcement(devteam, a.title_word)
    hf26.log(f"forecast_oos.py {VERSION}; tag {a.tag}; cutoff {cutoff.isoformat()}; model {json.dumps(model)}; "
             f"weight diff {check}; announced already: {bool(ann_before)}")
    rows, listed, skipped, edited = field_rows(client, a.tag, opened, deadline, train_ids, a.budget_minutes * 60, t0)
    devteam = client.get("/articles?username=devteam&per_page=100&page=1") or []
    ann_after = find_announcement(devteam, a.title_word)
    ranked = hf26.predict_round(w, rows) if rows else []
    both = [r for r in rows if r["has_devchallenge_tag"]]
    ranked_both = hf26.predict_round(w, both) if both else []
    write_ranking(os.path.join(a.out_dir, f"predictions_{a.tag}.csv"), ranked)
    write_ranking(os.path.join(a.out_dir, f"predictions_{a.tag}_both_tags.csv"), ranked_both)
    cols = ["article_id", "published_at", "has_devchallenge_tag", "edited_after_deadline"] + hf26.CONT + hf26.BINARY
    with open(os.path.join(a.out_dir, f"entries_{a.tag}.csv"), "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        wr.writeheader()
        wr.writerows(sorted(rows, key=lambda r: r["article_id"]))
    meta = {"version": VERSION, "tag": a.tag, "title_word": a.title_word, "opened": a.opened,
            "deadline": a.deadline, "snapshot_started": started, "snapshot_finished": hf26.now_iso(),
            "training_cutoff": cutoff.isoformat(), "model": model,
            "model_check": check if check is not None else "model.json not committed",
            "listed": listed, "skipped": skipped, "ranked": len(rows), "ranked_both_tags": len(both),
            "edited_after_deadline": edited,
            "announced_before_snapshot": ann_before["id"] if ann_before else None,
            "announced_by_end_of_snapshot": ann_after["id"] if ann_after else None,
            "requests": client.requests}
    hf26.write_json(os.path.join(a.out_dir, "snapshot.json"), meta)
    forecast = not ann_after
    lines = [f"# Forward forecast: #{a.tag}, ranked before the winners were announced", "",
             f"forecast_oos.py {VERSION}. Made by MV2 of Munim, Inc., with AI agents working in his name. Data CC BY 4.0.",
             "",
             ("No winners post for this challenge was on DEV's `devteam` account at the start or the end of the "
              "snapshot, so this ranking is a forecast." if forecast else
              f"**Not a forecast:** DEV's winners post (article {ann_after['id']}) was already up during the snapshot."),
             "",
             f"- Field: English posts tagged `{a.tag}`, published from {a.opened} to before {a.deadline}; DEV's own "
             "posts and training-data posts left out.",
             f"- Listed {listed}; ranked {len(rows)} ({len(both)} also tagged `devchallenge`); left out {json.dumps(skipped)}.",
             f"- {edited} ranked posts were edited after the deadline; they are measured as they are now.",
             f"- Model: refitted unchanged on {model['train_challenges']} challenges ({model['train_rows']} posts, "
             f"{model['train_winners']} winners); largest weight difference from the committed week-2 model: {meta['model_check']}.",
             f"- Snapshot {started} to {meta['snapshot_finished']}, {client.requests} requests.", ""]
    with open(os.path.join(a.out_dir, "REPORT.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    hf26.log("SNAPSHOT DONE")
    return 0


def score(a):
    os.makedirs(a.out_dir, exist_ok=True)
    client = oos.BustedClient()
    devteam = client.get("/articles?username=devteam&per_page=100&page=1") or []
    short = find_announcement(devteam, a.title_word)
    result = {"version": VERSION, "predictions": a.predictions, "run_at": hf26.now_iso()}
    if not short:
        result["status"] = "not_announced"
        hf26.write_json(os.path.join(a.out_dir, "score.json"), result)
        print("not announced yet")
        return 0
    ann = client.get(f"/articles/{short['id']}")
    if not isinstance(ann, dict):
        result["status"] = "unreadable"
        hf26.write_json(os.path.join(a.out_dir, "score.json"), result)
        return 1
    linked, embedded = oos.resolve_winners(client, ann)
    which, winners = primary_winners(linked, embedded)
    ranked = read_ranking(a.predictions)
    result.update({"status": "scored", "announcement_id": short["id"], "announced": ann.get("published_at"),
                   "winner_ids": {"linked": linked, "embedded": embedded}, "primary_winner_set": which,
                   "scores": {"primary": oos.score_set(ranked, winners),
                              "linked": oos.score_set(ranked, linked),
                              "embedded": oos.score_set(ranked, embedded)}})
    hf26.write_json(os.path.join(a.out_dir, "score.json"), result)
    p = result["scores"]["primary"]["logistic"]
    hf26.log(f"primary ({which}): {p['winners_in_ranking']} winners ranked, {p['hits_top_k']} in top-k "
             f"({p['expected_hits_if_random']} by chance), mean percentile {p['mean_winner_percentile']}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("snapshot")
    s.add_argument("--tag", required=True)
    s.add_argument("--title-word", required=True)
    s.add_argument("--opened", required=True)
    s.add_argument("--deadline", required=True)
    s.add_argument("--out-dir", required=True)
    s.add_argument("--train", default="/data/posts.csv")
    s.add_argument("--challenges", default="challenges.json")
    s.add_argument("--model-check", default="model_week2.json")
    s.add_argument("--budget-minutes", type=float, default=60)
    c = sub.add_parser("score")
    c.add_argument("--predictions", required=True)
    c.add_argument("--title-word", required=True)
    c.add_argument("--out-dir", required=True)
    a = ap.parse_args(argv)
    return snapshot(a) if a.cmd == "snapshot" else score(a)


if __name__ == "__main__":
    sys.exit(main())
