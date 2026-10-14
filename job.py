#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""What wins DEV challenges?

Compares the posts DEV announced as challenge winners with every other entry in
the same challenge, using only DEV's public API (no key). Nothing personal is
kept: the outputs hold article ids and measured features, never usernames.

Made by MV2 of Munim, Inc., with AI agents working in his name.
"""
import argparse
import csv
import json
import math
import os
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

API = "https://dev.to/api"
UA = "mv2-devchallenge-study/0.1 (MV2 of Munim, Inc.; munimversion2@gmail.com)"
PAUSE = 1.0
MAX_LINKS = 60
MAX_TAG_PAGES = 60
MIN_FIELD = 10

# Tags too broad to say which challenge a post was entered in.
GENERIC_TAGS = {
    "devchallenge", "ai", "webdev", "programming", "javascript", "typescript",
    "python", "opensource", "beginners", "tutorial", "react", "css", "html",
    "career", "productivity", "showdev", "hacktoberfest", "machinelearning",
    "news", "discuss", "frontend", "node", "java", "go", "rust", "devops",
    "privacy", "security", "llm", "gemini", "api", "cloud", "learning",
}
# First path segments on dev.to that are not authors.
SKIP_USERS = {
    "devteam", "challenges", "page", "t", "settings", "enter", "search", "api",
    "top", "latest", "videos", "listings", "badge", "badges", "pod", "help",
    "s", "dashboard", "new", "mlh-hackathon", "admin", "sponsors", "about",
}

CONT_META = ["reading_time", "title_words", "n_tags", "published_ts",
             "reactions_now", "comments_now"]
CONT_BODY = ["words", "headings", "code_blocks", "images", "embeds"]
BIN_META = ["title_has_number", "title_has_colon", "title_first_person",
            "has_cover", "ai_declared"]
BIN_BODY = ["has_video", "has_github_embed", "has_table"]
AFTER_ANNOUNCEMENT = {"reactions_now", "comments_now"}

LINK_RE = re.compile(r"https?://dev\.to/([A-Za-z0-9_]+)/([A-Za-z0-9][A-Za-z0-9_-]*)")
LIQUID_RE = re.compile(
    r"\{%\s*(?:link|embed)\s+(?:https?://dev\.to/)?([A-Za-z0-9_]+)/([A-Za-z0-9][A-Za-z0-9_-]*)\s*%\}")


def log(msg):
    print(msg, flush=True)


def parse_time(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def tags_of(article):
    t = article.get("tag_list")
    if isinstance(t, str):
        return [x.strip() for x in t.split(",") if x.strip()]
    return [str(x) for x in (t or [])]


def is_announcement(title):
    t = title or ""
    return bool(re.match(r"(?i)\s*(congrat|announcing)", t)) and bool(re.search(r"(?i)winner", t))


def extract_links(*texts):
    """(user, slug) pairs of dev.to posts linked or embedded in the texts, in order."""
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


def choose_tag(ann_tags, winner_tags):
    """The challenge's own tag: the announcement tag most winners carry."""
    counts = {}
    for tags in winner_tags:
        for t in set(tags):
            if t not in GENERIC_TAGS:
                counts[t] = counts.get(t, 0) + 1
    cands = [t for t in ann_tags if t not in GENERIC_TAGS]
    if cands:
        best = max(cands, key=lambda t: (counts.get(t, 0), -cands.index(t)))
        if counts.get(best, 0) * 2 >= max(1, len(winner_tags)):
            return best
    if counts:
        return max(sorted(counts), key=lambda t: counts[t])
    return None


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


def percentile_vs(x, others):
    """Share of others below x, ties counted half. 0.5 = typical."""
    if not others:
        return None
    lt = sum(1 for o in others if o < x)
    eq = sum(1 for o in others if o == x)
    return (lt + 0.5 * eq) / len(others)


def summarize_pcts(pcts):
    n = len(pcts)
    if n == 0:
        return {"winners": 0}
    mean = sum(pcts) / n
    # Under "winners are like any other entry" each percentile is ~Uniform(0,1),
    # variance 1/12; ties only shrink it, so this interval is conservative.
    se = math.sqrt(1 / (12 * n))
    return {
        "winners": n,
        "mean_percentile": round(mean, 3),
        "ci95": [round(mean - 1.96 * se, 3), round(mean + 1.96 * se, 3)],
        "share_above_middle": round(sum(1 for p in pcts if p > 0.5) / n, 3),
    }


def analyse(rows):
    by_c = {}
    for r in rows:
        by_c.setdefault(r["challenge_id"], []).append(r)
    live = {cid for cid, rs in by_c.items() if any(r["ai_level"] != "not_disclosed" for r in rs)}
    res = {"continuous": {}, "binary": {}, "ai_levels": {}}
    for f in CONT_META + CONT_BODY:
        body = f in CONT_BODY
        pcts = []
        for rs in by_c.values():
            others = [r[f] for r in rs if not r["is_winner"] and (r["has_body"] or not body)]
            if len(others) < 5:
                continue
            for r in rs:
                if r["is_winner"] and (r["has_body"] or not body):
                    pcts.append(percentile_vs(r[f], others))
        res["continuous"][f] = summarize_pcts(pcts)
        if f in AFTER_ANNOUNCEMENT:
            res["continuous"][f]["note"] = "measured after the winners were announced"
    for f in BIN_META + BIN_BODY:
        body = f in BIN_BODY
        obs = exp = var = 0.0
        n = 0
        for cid, rs in by_c.items():
            if f == "ai_declared" and cid not in live:
                continue
            others = [r[f] for r in rs if not r["is_winner"] and (r["has_body"] or not body)]
            if len(others) < 5:
                continue
            p = sum(others) / len(others)
            for r in rs:
                if r["is_winner"] and (r["has_body"] or not body):
                    obs += r[f]
                    exp += p
                    var += p * (1 - p)
                    n += 1
        res["binary"][f] = {
            "winners": n,
            "winners_with": int(obs),
            "expected_if_random": round(exp, 2),
            "winner_rate": round(obs / n, 3) if n else None,
            "field_rate": round(exp / n, 3) if n else None,
            "z": round((obs - exp) / math.sqrt(var), 2) if var > 0 else None,
        }
    # Every disclosure level seen, where DEV's disclosure field was in use.
    levels = sorted({r["ai_level"] for cid in live for r in by_c[cid]})
    for lv in levels:
        obs = exp = var = 0.0
        n = 0
        for cid in live:
            rs = by_c[cid]
            others = [int(r["ai_level"] == lv) for r in rs if not r["is_winner"]]
            if len(others) < 5:
                continue
            p = sum(others) / len(others)
            for r in rs:
                if r["is_winner"]:
                    obs += int(r["ai_level"] == lv)
                    exp += p
                    var += p * (1 - p)
                    n += 1
        res["ai_levels"][lv] = {
            "winners": n, "winners_at_level": int(obs), "expected_if_random": round(exp, 2),
            "z": round((obs - exp) / math.sqrt(var), 2) if var > 0 else None,
        }
    res["challenges_with_disclosure_field"] = len(live)
    return res


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


def list_tag(client, tag, since, cache):
    if tag in cache:
        return cache[tag]
    out, old_pages = [], 0
    for page in range(1, MAX_TAG_PAGES + 1):
        batch = client.get(f"/articles?tag={urllib.parse.quote(tag)}&per_page=1000&page={page}")
        if not isinstance(batch, list) or not batch:
            break
        out.extend(batch)
        if all(parse_time(a["published_at"]) < since for a in batch if a.get("published_at")):
            old_pages += 1
            if old_pages >= 2:
                break
        else:
            old_pages = 0
    cache[tag] = out
    log(f"  tag {tag}: {len(out)} posts listed")
    return out


def find_announcements(client, since):
    anns = []
    for page in range(1, 21):
        batch = client.get(f"/articles?username=devteam&per_page=1000&page={page}")
        if not isinstance(batch, list) or not batch:
            break
        for a in batch:
            if a.get("published_at") and is_announcement(a.get("title")) \
                    and parse_time(a["published_at"]) >= since:
                anns.append(a)
        if all(parse_time(a["published_at"]) < since for a in batch if a.get("published_at")):
            break
    anns.sort(key=lambda a: a["published_at"])
    return anns


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="out")
    ap.add_argument("--since", default="2025-01-01")
    ap.add_argument("--bodies-per-challenge", type=int, default=30)
    ap.add_argument("--budget-minutes", type=float, default=140)
    ap.add_argument("--pause", type=float, default=PAUSE)
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)
    t0 = time.time()
    since = parse_time(args.since + "T00:00:00Z")
    client = Client(args.pause)

    anns = find_announcements(client, since)
    log(f"{len(anns)} winner announcements since {args.since}")
    tag_cache, rows, challenges = {}, [], []
    for ann in anns:
        minutes = (time.time() - t0) / 60
        if minutes > args.budget_minutes + 15:
            log("time budget used up; stopping")
            break
        rec = {"announcement_id": ann["id"], "title": ann.get("title"),
               "announced": ann["published_at"], "status": ""}
        challenges.append(rec)
        detail = client.get(f"/articles/{ann['id']}")
        if not detail:
            rec["status"] = "announcement not readable"
            continue
        ann_time = parse_time(detail["published_at"])
        ann_tags = tags_of(detail)
        links = extract_links(detail.get("body_html"), detail.get("body_markdown"))
        rec["links"] = len(links)
        winners = []
        for user, slug in links[:MAX_LINKS]:
            w = client.get(f"/articles/{urllib.parse.quote(user)}/{urllib.parse.quote(slug)}")
            if not isinstance(w, dict) or not w.get("published_at"):
                continue
            wt = parse_time(w["published_at"])
            if not (ann_time - timedelta(days=120) <= wt <= ann_time):
                continue
            if ((w.get("user") or {}).get("username") or "").lower() in SKIP_USERS:
                continue
            if not set(tags_of(w)) & (set(ann_tags) | {"devchallenge"}):
                continue
            if any(x["id"] == w["id"] for x in winners):
                continue
            winners.append(w)
        rec["winners"] = len(winners)
        tag = choose_tag(ann_tags, [tags_of(w) for w in winners])
        rec["tag"] = tag
        if not winners or not tag:
            rec["status"] = "no winners or tag found"
            continue
        wtimes = [parse_time(w["published_at"]) for w in winners]
        start = min(wtimes) - timedelta(days=2)
        end = min(max(wtimes) + timedelta(days=2), ann_time)
        rec["window"] = [start.isoformat(), end.isoformat()]
        win_ids = {w["id"] for w in winners}
        field = []
        for a in list_tag(client, tag, since - timedelta(days=60), tag_cache):
            if not a.get("published_at") or a["id"] in win_ids or a["id"] == ann["id"]:
                continue
            if ((a.get("user") or {}).get("username") or "").lower() in SKIP_USERS:
                continue
            if (a.get("language") or "en") != "en":
                continue
            if start <= parse_time(a["published_at"]) <= end:
                field.append(a)
        rec["field"] = len(field)
        if len(field) < MIN_FIELD:
            rec["status"] = f"field too small ({len(field)})"
            continue
        for w in winners:
            row = {"challenge_id": ann["id"], "article_id": w["id"], "is_winner": 1,
                   "has_body": 1, "ai_level": ai_level(w)}
            row.update(meta_features(w))
            row.update(body_features(w.get("body_markdown")))
            rows.append(row)
        rng = random.Random(int(ann["id"]))
        sample_ids = {a["id"] for a in rng.sample(field, min(args.bodies_per_challenge, len(field)))}
        bodies = 0
        for a in field:
            row = {"challenge_id": ann["id"], "article_id": a["id"], "is_winner": 0,
                   "has_body": 0, "ai_level": ai_level(a)}
            row.update(meta_features(a))
            row.update({k: 0 for k in CONT_BODY + BIN_BODY})
            if a["id"] in sample_ids and (time.time() - t0) / 60 < args.budget_minutes:
                d = client.get(f"/articles/{a['id']}")
                if isinstance(d, dict) and "body_markdown" in d:
                    row.update(body_features(d.get("body_markdown")))
                    row["has_body"] = 1
                    bodies += 1
            rows.append(row)
        rec["bodies"] = bodies
        rec["ai_levels"] = {}
        for a in winners + field:
            lv = ai_level(a)
            rec["ai_levels"][lv] = rec["ai_levels"].get(lv, 0) + 1
        rec["status"] = "ok"
        log(f"{ann['published_at'][:10]} {tag}: {len(winners)} winners vs {len(field)} entries "
            f"({bodies} bodies); requests so far {client.requests}")

    result = analyse(rows)
    result["meta"] = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "since": args.since, "announcements": len(anns),
        "challenges_used": sum(1 for c in challenges if c["status"] == "ok"),
        "winners": sum(r["is_winner"] for r in rows),
        "entries": sum(1 - r["is_winner"] for r in rows),
        "requests": client.requests,
        "minutes": round((time.time() - t0) / 60, 1),
    }
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    with open(os.path.join(args.out_dir, "challenges.json"), "w", encoding="utf-8") as f:
        json.dump(challenges, f, indent=2)
    cols = ["challenge_id", "article_id", "is_winner", "has_body", "ai_level"] + \
        CONT_META + CONT_BODY + BIN_META + BIN_BODY
    with open(os.path.join(args.out_dir, "posts.csv"), "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        wr.writeheader()
        wr.writerows(rows)
    with open(os.path.join(args.out_dir, "REPORT.md"), "w", encoding="utf-8") as f:
        f.write(report(result))
    log(json.dumps(result["meta"]))
    return 0


def report(res):
    m = res["meta"]
    out = [
        "# What wins DEV challenges: winners compared with every other entry",
        "",
        f"Generated {m['generated']} from DEV's public API: {m['challenges_used']} challenges "
        f"announced since {m['since']}, {m['winners']} winning posts and {m['entries']} other entries "
        f"in the same challenge and time window.",
        "",
        "## Measures where more or less can be ranked",
        "",
        "Percentile 0.50 means winners look like a typical entry; above 0.50 means winners have more of it.",
        "",
        "| Measure | Winners | Mean percentile | 95% interval | Winners above the middle |",
        "|---|---|---|---|---|",
    ]
    for f, s in res["continuous"].items():
        if not s.get("winners"):
            continue
        note = " (after announcement)" if s.get("note") else ""
        out.append(f"| {f}{note} | {s['winners']} | {s['mean_percentile']:.2f} | "
                   f"{s['ci95'][0]:.2f} to {s['ci95'][1]:.2f} | {s['share_above_middle']:.0%} |")
    out += ["", "## Yes/no measures", "",
            "| Measure | Winners | Winners with it | Expected if random | Winner rate | Field rate | z |",
            "|---|---|---|---|---|---|---|"]
    for f, s in res["binary"].items():
        if not s.get("winners"):
            continue
        out.append(f"| {f} | {s['winners']} | {s['winners_with']} | {s['expected_if_random']} | "
                   f"{s['winner_rate']:.0%} | {s['field_rate']:.0%} | {s['z']} |")
    out += ["", f"## AI disclosure levels ({res['challenges_with_disclosure_field']} challenges "
            "where DEV's disclosure field was in use)", "",
            "| Level | Winners at level | Expected if random | z |", "|---|---|---|---|"]
    for lv, s in res["ai_levels"].items():
        out.append(f"| {lv} | {s['winners_at_level']} of {s['winners']} | {s['expected_if_random']} | {s['z']} |")
    out += ["", "## Limits", "",
            "- The field is posts carrying the challenge's tag, published between two days before the "
            "first winner and two days after the last (and before the announcement). Entries outside "
            "that window or without the tag are missed; other posts using the tag are included.",
            "- 'Winners' are posts linked from DEV's announcement, so honourable mentions count too.",
            "- Reactions and comments were counted now, after the announcement sent readers to the winners.",
            "- Body measures use every winner and a random sample of up to 30 other entries per challenge.",
            "- This shows what winners have in common, not what causes a win.",
            ""]
    return "\n".join(out)


if __name__ == "__main__":
    sys.exit(main())
