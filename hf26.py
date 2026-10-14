#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Pre-registered predictions for DEV's Hacktoberfest 2026 challenge rounds.

The companion study (job.py in this repo) found what DEV challenge winners have
in common with hindsight. This tool asks the harder question: can the same
measures pick winners BEFORE DEV announces them?

  snapshot  lists every post carrying the challenge tag, fetches each body,
            records its shape (words, headings, tables, video, cover, ...) and
            which round it entered. Reactions are recorded but never used to
            predict.
  predict   fits a logistic model on the study's 55 past challenges (within-
            challenge percentiles of the shape measures, no reactions, no
            timing), backtests it by leaving one challenge out at a time, then
            ranks the entries of each open round. The ranking is committed to
            the repo before the announcement, so it can be scored honestly.
  score     after DEV's announcement: how many announced winners were in the
            top-k of the committed ranking, against what chance would give.

Uses only DEV's public API (no key). Outputs hold article ids and measured
features, never usernames. Made by MV2 of Munim, Inc., with AI agents working
in his name.
"""
import argparse
import bisect
import csv
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

API = "https://dev.to/api"
UA = "mv2-devchallenge-study/0.2 (MV2 of Munim, Inc.; munimversion2@gmail.com)"
PAUSE = 1.0
MAX_TAG_PAGES = 60
TRAIN_URL = "https://raw.githubusercontent.com/munimtechnologies/devchallenge-study/main/data/posts.csv"

# DEV's deadlines are 23:59 PDT, which is 06:59 UTC the next day.
ROUNDS = {
    "weekend": ("2026-10-01T00:00:00Z", "2026-10-06T07:00:00Z"),
    "week1": ("2026-10-05T07:00:00Z", "2026-10-12T07:00:00Z"),
    "week2": ("2026-10-12T07:00:00Z", "2026-10-19T07:00:00Z"),
    "week3": ("2026-10-19T07:00:00Z", "2026-10-26T07:00:00Z"),
    "week4": ("2026-10-26T07:00:00Z", "2026-11-01T07:00:00Z"),
}
ROUND_RE = re.compile(r"challenges/hacktoberfest-(weekend|week[1-4])-2026-\d\d-\d\d")
ANN_WORDS = {
    "weekend": ("weekend",),
    "week1": ("week 1", "week1", "touch grass"),
    "week2": ("week 2", "week2", "side hustle"),
    "week3": ("week 3", "week3"),
    "week4": ("week 4", "week4"),
}
SKIP_USERS = {
    "devteam", "challenges", "page", "t", "settings", "enter", "search", "api",
    "top", "latest", "videos", "listings", "badge", "badges", "pod", "help",
    "s", "dashboard", "new", "mlh-hackathon", "admin", "sponsors", "about",
}

# Shape measures. CONT are ranked within a challenge (percentiles); BINARY are 0/1.
CONT = ["reading_time", "title_words", "n_tags", "words", "headings",
        "code_blocks", "images", "embeds"]
BINARY = ["title_has_number", "title_has_colon", "title_first_person",
          "has_cover", "ai_declared", "has_video", "has_github_embed", "has_table"]
FEATURES = [f + "_pct" for f in CONT] + BINARY
# Recorded for the record, never used by the model.
NOT_USED = ["reactions_now", "comments_now", "published_ts"]

LINK_RE = re.compile(r"https?://dev\.to/([A-Za-z0-9_]+)/([A-Za-z0-9][A-Za-z0-9_-]*)")
LIQUID_RE = re.compile(
    r"\{%\s*(?:link|embed)\s+(?:https?://dev\.to/)?([A-Za-z0-9_]+)/([A-Za-z0-9][A-Za-z0-9_-]*)\s*%\}")


def log(msg):
    print(msg, flush=True)


def parse_time(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def tags_of(article):
    t = article.get("tag_list")
    if isinstance(t, str):
        return [x.strip() for x in t.split(",") if x.strip()]
    return [str(x) for x in (t or [])]


def ai_level(article):
    return article.get("ai_disclosure_level") or "not_disclosed"


def declared_ai(article):
    level = ai_level(article)
    label = article.get("ai_disclosure_label") or ""
    if level == "not_disclosed":
        return 0
    if re.search(r"(?i)(no[_ ]?ai|\bnone\b|human)", level + " " + label):
        return 0
    return 1


def meta_features(a):
    title = a.get("title") or ""
    return {
        "reading_time": a.get("reading_time_minutes") or 0,
        "reactions_now": a.get("public_reactions_count") or 0,
        "comments_now": a.get("comments_count") or 0,
        "title_words": len(title.split()),
        "title_has_number": int(bool(re.search(r"\d", title))),
        "title_has_colon": int(":" in title or " - " in title or "—" in title),
        "title_first_person": int(bool(re.search(r"(?i)\b(i|i'm|i've|my|we|our)\b", title))),
        "has_cover": int(bool(a.get("cover_image"))),
        "n_tags": len(tags_of(a)),
        "ai_declared": declared_ai(a),
        "published_ts": parse_time(a["published_at"]).timestamp(),
    }


def body_features(md):
    md = md or ""
    fences = len(re.findall(r"(?m)^\s*```", md))
    text = re.sub(r"```.*?```", " ", md, flags=re.S)
    return {
        "words": len(re.findall(r"[A-Za-z0-9']+", text)),
        "headings": len(re.findall(r"(?m)^#{1,6}\s", text)),
        "code_blocks": fences // 2,
        "images": len(re.findall(r"!\[[^\]]*\]\(", md)),
        "embeds": len(re.findall(r"\{%\s*(?!end)\w+", md)),
        "has_video": int(bool(re.search(
            r"(?i)youtube\.com|youtu\.be|loom\.com|vimeo\.com|\{%\s*(youtube|vimeo|loom)", md))),
        "has_github_embed": int(bool(re.search(r"\{%\s*github", md))),
        "has_table": int(bool(re.search(r"(?m)^\s*\|?\s*:?-{3,}:?\s*\|", text))),
    }


def round_of(body_md, published):
    """Which Hacktoberfest round a post entered.

    The post's own template line links the round's challenge page; that wins.
    Without a body, the publish time decides, and a time inside two windows
    (the weekend deadline overlaps the first hours of week 1) gives both names
    joined by '+'.
    """
    m = ROUND_RE.search(body_md or "")
    if m:
        return m.group(1)
    hits = [r for r, (s, e) in ROUNDS.items() if parse_time(s) <= published < parse_time(e)]
    return "+".join(hits) if hits else "none"


def announcement_round(title):
    """Round named by a devteam winner announcement, or None."""
    t = (title or "").lower()
    if "hacktoberfest" not in t or "winner" not in t or not t.startswith("congrat"):
        return None
    for r, words in ANN_WORDS.items():
        if any(w in t for w in words):
            return r
    return None


def extract_links(*texts):
    seen, out = set(), []
    for text in texts:
        if not text:
            continue
        for rx in (LINK_RE, LIQUID_RE):
            for user, slug in rx.findall(text):
                if user.lower() in SKIP_USERS or "-" not in slug:
                    continue
                key = (user.lower(), slug.lower())
                if key in seen:
                    continue
                seen.add(key)
                out.append((user, slug))
    return out


class Client:
    def __init__(self, pause=PAUSE):
        self.pause = pause
        self.requests = 0

    def get(self, path, tries=6):
        url = API + path
        for i in range(tries):
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    data = json.load(r)
                self.requests += 1
                time.sleep(self.pause)
                return data
            except urllib.error.HTTPError as e:
                self.requests += 1
                if e.code == 404:
                    time.sleep(self.pause)
                    return None
                if e.code in (429, 500, 502, 503, 504):
                    wait = 5 * (i + 1)
                    try:
                        wait = max(wait, int(e.headers.get("Retry-After") or 0))
                    except ValueError:
                        pass
                    time.sleep(min(wait, 120))
                    continue
                log(f"HTTP {e.code} for {url}")
                return None
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
                log(f"retry {i + 1} for {url}: {e}")
                time.sleep(5 * (i + 1))
        return None


def list_tag(client, tag, since):
    out, old_pages, seen = [], 0, set()
    for page in range(1, MAX_TAG_PAGES + 1):
        batch = client.get(f"/articles?tag={urllib.parse.quote(tag)}&per_page=1000&page={page}")
        if not isinstance(batch, list) or not batch:
            break
        fresh = [a for a in batch if a.get("id") not in seen]
        seen.update(a.get("id") for a in fresh)
        out.extend(fresh)
        if all(parse_time(a["published_at"]) < since for a in batch if a.get("published_at")):
            old_pages += 1
            if old_pages >= 2:
                break
        else:
            old_pages = 0
    log(f"  tag {tag}: {len(out)} posts listed")
    return out


def announcements_seen(client):
    """Rounds whose winners devteam has already announced, with the time."""
    seen = {}
    batch = client.get("/articles?username=devteam&per_page=100&page=1")
    for a in batch or []:
        r = announcement_round(a.get("title"))
        if r and r not in seen:
            seen[r] = {"announcement_id": a.get("id"), "announced": a.get("published_at")}
    return seen


ENTRY_COLS = (["article_id", "round", "published_at", "snapshot_at", "language",
               "has_devchallenge_tag", "ai_level", "has_body"]
              + CONT + NOT_USED + BINARY)


def snapshot(args):
    os.makedirs(args.out_dir, exist_ok=True)
    t0 = time.time()
    since = parse_time(args.since + "T00:00:00Z")
    bodies_from = parse_time(args.bodies_from)
    client = Client(args.pause)
    started = now_iso()
    seen_anns = announcements_seen(client)
    log(f"announcements already out: {json.dumps(seen_anns)}")
    listing = list_tag(client, args.tag, since)
    rows, counts = [], {}
    for a in listing:
        if not a.get("published_at"):
            continue
        pub = parse_time(a["published_at"])
        if pub < since:
            continue
        row = {"article_id": a["id"], "published_at": a["published_at"], "snapshot_at": started,
               "language": a.get("language") or "en",
               "has_devchallenge_tag": int("devchallenge" in tags_of(a)),
               "ai_level": ai_level(a), "has_body": 0}
        row.update(meta_features(a))
        row.update({k: 0 for k in ["words", "headings", "code_blocks", "images", "embeds",
                                   "has_video", "has_github_embed", "has_table"]})
        body = None
        if pub >= bodies_from and (time.time() - t0) / 60 < args.budget_minutes:
            d = client.get(f"/articles/{a['id']}")
            if isinstance(d, dict) and "body_markdown" in d:
                body = d.get("body_markdown") or ""
                row.update(body_features(body))
                row["has_body"] = 1
        row["round"] = round_of(body, pub)
        rows.append(row)
        c = counts.setdefault(row["round"], {"entries": 0, "bodies": 0, "ai_levels": {}})
        c["entries"] += 1
        c["bodies"] += row["has_body"]
        c["ai_levels"][row["ai_level"]] = c["ai_levels"].get(row["ai_level"], 0) + 1
        if len(rows) % 200 == 0:
            log(f"  {len(rows)} posts, {client.requests} requests, {(time.time() - t0) / 60:.1f} min")
    rows.sort(key=lambda r: (r["round"], r["published_at"]))
    with open(os.path.join(args.out_dir, "entries.csv"), "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=ENTRY_COLS, extrasaction="ignore")
        wr.writeheader()
        wr.writerows(rows)
    meta = {"snapshot_at": started, "finished_at": now_iso(), "tag": args.tag, "since": args.since,
            "bodies_from": args.bodies_from, "announcements_seen": seen_anns,
            "rounds": counts, "posts": len(rows), "requests": client.requests,
            "minutes": round((time.time() - t0) / 60, 1)}
    with open(os.path.join(args.out_dir, "rounds.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    log(json.dumps({k: v for k, v in meta.items() if k != "rounds"}))
    return 0


# ---------------------------------------------------------------- modelling

def pct_in(sorted_vals, x, exclude_self=False):
    """Share of sorted_vals below x, ties counted half. 0.5 = typical."""
    n = len(sorted_vals) - (1 if exclude_self else 0)
    if n <= 0:
        return 0.5
    lt = bisect.bisect_left(sorted_vals, x)
    eq = bisect.bisect_right(sorted_vals, x) - lt - (1 if exclude_self else 0)
    return (lt + 0.5 * eq) / n


def add_percentiles(rows, reference):
    """Percentile features for rows, ranked against reference rows (same group).

    A row that is itself in the reference is ranked against the others.
    """
    ref_ids = {id(r) for r in reference}
    sorted_by = {f: sorted(float(r[f]) for r in reference) for f in CONT}
    for r in rows:
        inside = id(r) in ref_ids
        for f in CONT:
            r[f + "_pct"] = pct_in(sorted_by[f], float(r[f]), exclude_self=inside)


def vector(r):
    return [float(r[f]) for f in FEATURES]


def solve(A, b):
    """Gaussian elimination with partial pivoting; A is modified."""
    n = len(b)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for c in range(n):
        p = max(range(c, n), key=lambda i: abs(M[i][c]))
        M[c], M[p] = M[p], M[c]
        if abs(M[c][c]) < 1e-12:
            M[c][c] = 1e-12
        for i in range(c + 1, n):
            f = M[i][c] / M[c][c]
            if f:
                for j in range(c, n + 1):
                    M[i][j] -= f * M[c][j]
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        x[i] = (M[i][n] - sum(M[i][j] * x[j] for j in range(i + 1, n))) / M[i][i]
    return x


def sigmoid(z):
    z = max(-30.0, min(30.0, z))
    return 1.0 / (1.0 + math.exp(-z))


def fit_logistic(X, y, l2=1.0, iters=20):
    """L2-regularised logistic regression by Newton's method. Returns [bias] + weights."""
    d = len(X[0]) + 1
    w = [0.0] * d
    rows = [[1.0] + list(x) for x in X]
    for _ in range(iters):
        g = [0.0] * d
        H = [[0.0] * d for _ in range(d)]
        for x, yi in zip(rows, y):
            p = sigmoid(sum(wj * xj for wj, xj in zip(w, x)))
            r = p - yi
            s = p * (1.0 - p)
            for j in range(d):
                xj = x[j]
                if xj == 0.0:
                    continue
                g[j] += r * xj
                sx = s * xj
                Hj = H[j]
                for k in range(j, d):
                    Hj[k] += sx * x[k]
        for j in range(d):
            for k in range(j + 1, d):
                H[k][j] = H[j][k]
        for j in range(1, d):
            g[j] += l2 * w[j]
            H[j][j] += l2
        step = solve(H, g)
        w = [wj - sj for wj, sj in zip(w, step)]
        if max(abs(s) for s in step) < 1e-7:
            break
    return w


def score_with(w, x):
    return w[0] + sum(wj * xj for wj, xj in zip(w[1:], x))


def rank_score(x):
    """Baseline: plain mean of the features (all in 0..1), no fitting."""
    return sum(x) / len(x)


def load_train(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if int(r["has_body"]) != 1:
                continue
            rows.append(r)
    return rows


def prepare_train(rows):
    """Within-challenge percentiles; keeps challenges with >= 5 non-winner bodies."""
    by_c = {}
    for r in rows:
        by_c.setdefault(r["challenge_id"], []).append(r)
    kept = {}
    for cid, rs in by_c.items():
        others = [r for r in rs if int(r["is_winner"]) == 0]
        if len(others) < 5 or not any(int(r["is_winner"]) for r in rs):
            continue
        add_percentiles(rs, others)
        kept[cid] = rs
    return kept


def evaluate_ranking(scored):
    """scored: list of (score, is_winner). Winners' percentile and top-k hits."""
    k = sum(w for _, w in scored)
    n = len(scored)
    if k == 0 or n <= k:
        return None
    other = sorted(s for s, w in scored if not w)
    pcts = [pct_in(other, s) for s, w in scored if w]
    top = sorted(scored, key=lambda t: -t[0])[:k]
    hits = sum(w for _, w in top)
    return {"winners": k, "rows": n, "mean_winner_percentile": sum(pcts) / k,
            "hits_top_k": hits, "expected_hits": k * k / n}


def backtest(kept, l2=1.0):
    """Leave one challenge out: train on the rest, rank the held-out one."""
    out = {"logistic": [], "rank": []}
    per_challenge = []
    for cid, rs in kept.items():
        X, y = [], []
        for ocid, ors in kept.items():
            if ocid == cid:
                continue
            for r in ors:
                X.append(vector(r))
                y.append(int(r["is_winner"]))
        w = fit_logistic(X, y, l2=l2)
        lg = evaluate_ranking([(score_with(w, vector(r)), int(r["is_winner"])) for r in rs])
        rk = evaluate_ranking([(rank_score(vector(r)), int(r["is_winner"])) for r in rs])
        if lg is None:
            continue
        out["logistic"].append(lg)
        out["rank"].append(rk)
        per_challenge.append({"challenge_id": cid, "winners": lg["winners"], "rows": lg["rows"],
                              "logistic_percentile": round(lg["mean_winner_percentile"], 3),
                              "logistic_hits": lg["hits_top_k"],
                              "rank_percentile": round(rk["mean_winner_percentile"], 3),
                              "rank_hits": rk["hits_top_k"],
                              "expected_hits": round(lg["expected_hits"], 2)})
    summary = {}
    for name, evs in out.items():
        wins = sum(e["winners"] for e in evs)
        mean = sum(e["mean_winner_percentile"] * e["winners"] for e in evs) / max(1, wins)
        se = math.sqrt(1 / (12 * max(1, wins)))
        summary[name] = {
            "challenges": len(evs), "winners": wins,
            "mean_winner_percentile": round(mean, 3),
            "ci95": [round(mean - 1.96 * se, 3), round(mean + 1.96 * se, 3)],
            "hits_top_k": sum(e["hits_top_k"] for e in evs),
            "expected_hits_if_random": round(sum(e["expected_hits"] for e in evs), 1),
        }
    return summary, per_challenge


def load_field(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows


def predict_round(w, rows):
    """Rank a round's entries. Returns rows sorted best first with scores."""
    add_percentiles(rows, rows)
    out = []
    for r in rows:
        x = vector(r)
        out.append({"article_id": int(r["article_id"]), "score": round(score_with(w, x), 4),
                    "rank_score": round(rank_score(x), 4)})
    out.sort(key=lambda o: (-o["score"], o["article_id"]))
    for i, o in enumerate(out, 1):
        o["rank"] = i
    return out


def predict(args):
    os.makedirs(args.out_dir, exist_ok=True)
    train_path = args.train
    if not os.path.exists(train_path):
        log(f"downloading training data to {train_path}")
        os.makedirs(os.path.dirname(train_path) or ".", exist_ok=True)
        req = urllib.request.Request(TRAIN_URL, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=120) as r, open(train_path, "wb") as f:
            f.write(r.read())
    kept = prepare_train(load_train(train_path))
    X, y = [], []
    for rs in kept.values():
        for r in rs:
            X.append(vector(r))
            y.append(int(r["is_winner"]))
    w = fit_logistic(X, y, l2=args.l2)
    model = {"features": FEATURES, "bias": round(w[0], 4),
             "weights": {f: round(v, 4) for f, v in zip(FEATURES, w[1:])},
             "l2": args.l2, "train_challenges": len(kept), "train_rows": len(X),
             "train_winners": sum(y), "not_used": NOT_USED, "fitted_at": now_iso()}
    log(f"model fitted on {len(kept)} challenges, {len(X)} rows, {sum(y)} winners")
    bt, per_c = backtest(kept, l2=args.l2) if not args.skip_backtest else ({}, [])
    log(f"backtest: {json.dumps(bt)}")
    with open(os.path.join(args.out_dir, "model.json"), "w", encoding="utf-8") as f:
        json.dump(model, f, indent=2)
    with open(os.path.join(args.out_dir, "backtest.json"), "w", encoding="utf-8") as f:
        json.dump({"summary": bt, "per_challenge": per_c}, f, indent=2)

    field = load_field(args.field) if args.field and os.path.exists(args.field) else []
    rounds_meta = {}
    if args.rounds_json and os.path.exists(args.rounds_json):
        with open(args.rounds_json, encoding="utf-8") as f:
            rounds_meta = json.load(f)
    preds = {}
    for rnd in sorted({r["round"] for r in field}):
        if rnd in ("weekend", "none") or "+" in rnd:
            continue
        rows = [r for r in field if r["round"] == rnd and int(r["has_body"]) == 1
                and int(r["has_devchallenge_tag"]) == 1 and (r.get("language") or "en") == "en"]
        if len(rows) < 10:
            continue
        ranked = predict_round(w, rows)
        preds[rnd] = ranked
        with open(os.path.join(args.out_dir, f"predictions_{rnd}.csv"), "w", newline="",
                  encoding="utf-8") as f:
            wr = csv.DictWriter(f, fieldnames=["rank", "article_id", "score", "rank_score"])
            wr.writeheader()
            wr.writerows(ranked)
        log(f"{rnd}: ranked {len(ranked)} entries")
    with open(os.path.join(args.out_dir, "REPORT.md"), "w", encoding="utf-8") as f:
        f.write(report(model, bt, preds, rounds_meta))
    return 0


def report(model, bt, preds, rounds_meta):
    out = ["# Can post shape pick DEV challenge winners before they are announced?", "",
           f"Model fitted {model['fitted_at']} on {model['train_challenges']} past challenges "
           f"({model['train_rows']} posts with bodies, {model['train_winners']} winners). "
           "Features are within-challenge percentiles of shape measures plus yes/no measures; "
           "reactions, comments and publish time are never used.", "",
           "## Weights (logistic, L2-regularised)", "", "| Feature | Weight |", "|---|---|"]
    for f, v in sorted(model["weights"].items(), key=lambda kv: -abs(kv[1])):
        out.append(f"| {f} | {v:+.3f} |")
    if bt:
        out += ["", "## Backtest: leave one challenge out", "",
                "Each past challenge is ranked by a model fitted on the others. "
                "0.50 means winners rank like any other entry; top-k counts winners among the k "
                "highest-ranked posts, where k is that challenge's number of winners.", "",
                "| Model | Challenges | Winners | Mean winner percentile | 95% interval | Winners in top-k | Expected if random |",
                "|---|---|---|---|---|---|---|"]
        for name, s in bt.items():
            out.append(f"| {name} | {s['challenges']} | {s['winners']} | {s['mean_winner_percentile']:.2f} | "
                       f"{s['ci95'][0]:.2f} to {s['ci95'][1]:.2f} | {s['hits_top_k']} | "
                       f"{s['expected_hits_if_random']} |")
    out += ["", "## Pre-registered rankings", ""]
    seen = (rounds_meta or {}).get("announcements_seen", {})
    snap = (rounds_meta or {}).get("snapshot_at", "")
    for rnd, ranked in preds.items():
        status = "announced before this snapshot" if rnd in seen else "not yet announced at snapshot time"
        out.append(f"- **{rnd}**: {len(ranked)} English entries with both tags and a readable body, "
                   f"snapshot {snap}, winners {status}. Ranking in `predictions_{rnd}.csv` "
                   "(article ids only).")
    out += ["", "## How it will be scored", "",
            "When DEV announces a round's winners, `hf26.py score` counts how many of them sit in the "
            "top-k of the committed ranking (k = number of winners) and the winners' mean percentile, "
            "against chance. A ranking committed after an announcement is not a prediction and is "
            "marked as such above.", "",
            "## Limits", "",
            "- Shape, not substance: the model never reads what a post says or whether the project works.",
            "- Training non-winners are a sample of up to 30 bodies per challenge; live rounds use every entry.",
            "- Partner-category winners are picked partly for the technology used, which no feature sees.",
            "- A round's entries keep arriving until its deadline; a snapshot before the deadline misses the rest.",
            ""]
    return "\n".join(out)


def score(args):
    client = Client(args.pause)
    ann = client.get(f"/articles/{args.announcement}")
    if not isinstance(ann, dict):
        log("announcement not readable")
        return 1
    links = extract_links(ann.get("body_html"), ann.get("body_markdown"))
    winner_ids = []
    for user, slug in links:
        w = client.get(f"/articles/{urllib.parse.quote(user)}/{urllib.parse.quote(slug)}")
        if isinstance(w, dict) and w.get("id"):
            winner_ids.append(int(w["id"]))
    ranked = load_field(args.predictions)
    result = score_predictions(ranked, winner_ids)
    result.update({"announcement_id": ann.get("id"), "announced": ann.get("published_at"),
                   "scored_at": now_iso(), "predictions": args.predictions})
    log(json.dumps(result, indent=2))
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
    return 0


def score_predictions(ranked, winner_ids):
    """ranked: rows with rank and article_id (best first). Chance = k*k/n."""
    ids = [int(r["article_id"]) for r in sorted(ranked, key=lambda r: int(r["rank"]))]
    n = len(ids)
    present = [w for w in winner_ids if w in ids]
    k = len(present)
    pos = {a: i for i, a in enumerate(ids)}
    hits = sum(1 for w in present if pos[w] < k)
    pcts = [1 - pos[w] / max(1, n - 1) for w in present]
    return {"ranked_entries": n, "winners_announced": len(winner_ids), "winners_in_ranking": k,
            "hits_top_k": hits, "expected_hits_if_random": round(k * k / n, 2) if n else None,
            "mean_winner_percentile": round(sum(pcts) / k, 3) if k else None,
            "winner_ranks": sorted(pos[w] + 1 for w in present)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("snapshot")
    s.add_argument("--tag", default="hf26challenge")
    s.add_argument("--since", default="2026-10-01")
    s.add_argument("--bodies-from", default=ROUNDS["week1"][0])
    s.add_argument("--budget-minutes", type=float, default=120)
    s.add_argument("--pause", type=float, default=PAUSE)
    s.add_argument("--out-dir", default="out")
    s.set_defaults(func=snapshot)
    p = sub.add_parser("predict")
    p.add_argument("--train", default="/data/posts.csv")
    p.add_argument("--field", default="")
    p.add_argument("--rounds-json", default="")
    p.add_argument("--out-dir", default="out")
    p.add_argument("--l2", type=float, default=1.0)
    p.add_argument("--skip-backtest", action="store_true")
    p.set_defaults(func=predict)
    c = sub.add_parser("score")
    c.add_argument("--predictions", required=True)
    c.add_argument("--announcement", required=True, help="devteam announcement article id")
    c.add_argument("--out", default="")
    c.add_argument("--pause", type=float, default=PAUSE)
    c.set_defaults(func=score)
    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
