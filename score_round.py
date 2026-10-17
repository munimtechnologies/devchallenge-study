# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Score a committed ranking against the winners DEV announces for a Hacktoberfest round.

score_w1.py scored week 1, but its winner-reading rule was settled after the announcement was out (twice:
a stale-cache 404, then a renamed author). This file fixes the same rule for later rounds BEFORE their
winners are known, so nothing about how winners are read can be tuned to the result:

- The announcement is the devteam post whose title `hf26.announcement_round` maps to the round. Every
  request carries a per-run `item` token (Forem's CDN keeps it in the cache key; the API ignores it).
- Winners are the dev.to links between the first line containing "Overall Winner" and the next line
  containing "What's Next", in the announcement's markdown. Nothing outside those lines counts.
- A winner link that does not resolve is retried under any other username the body links with the identical
  slug (an author who renamed); each case is listed.
- The ranking is scored with the committed hf26.score_predictions, both orderings, unchanged.
- The result is always written. status is "scored" when the number of winner links equals the number DEV
  advertised and every link resolved; otherwise "flagged", with the reason, and the numbers are still given.
  "not_announced" and "no_winner_section" are written as such and score nothing.

Checked against week 1: with --round week1 it must reproduce predictions/2026-10-14/score_week1.json.
MV2 of Munim, Inc.; made with AI agents.
"""
import argparse
import json
import random
import re
import sys
import time
import urllib.parse

import hf26

VERSION = "0.1.0"
# From each round's "Join" post: "$2,450 in Prizes Across 17 Winners", "$2,550 in Prizes Across 18 Winners".
ADVERTISED = {"weekend": 17, "week1": 17, "week2": 18}
START_RE = re.compile(r"overall winner", re.I)
END_RE = re.compile(r"what.?s next", re.I)
SEED = 20261016  # the seed score_w1.py used, so week 1 reproduces exactly


def busted(path, token):
    return path + ("&" if "?" in path else "?") + "item=" + token


class BustedClient(hf26.Client):
    """hf26.Client with a per-run `item` token on every request."""

    token = "score" + str(int(time.time()))

    def get(self, path, tries=6):
        return super().get(busted(path, self.token), tries)


def find_announcement(client, rnd):
    """(id, path, published_at) of the newest devteam post announcing `rnd`'s winners, or None."""
    for a in client.get("/articles?username=devteam&per_page=100&page=1") or []:
        if hf26.announcement_round(a.get("title")) == rnd:
            return a.get("id"), (a.get("path") or "").lstrip("/"), a.get("published_at")
    return None


def winner_section(markdown):
    """Text from the first 'Overall Winner' line up to the next "What's Next" line, or None."""
    lines = (markdown or "").splitlines()
    start = next((i for i, l in enumerate(lines) if START_RE.search(l)), None)
    if start is None:
        return None
    end = next((i for i in range(start + 1, len(lines)) if END_RE.search(lines[i])), None)
    if end is None:
        return None
    return "\n".join(lines[start:end])


def lookup(client, user, slug):
    w = client.get(f"/articles/{urllib.parse.quote(user)}/{urllib.parse.quote(slug)}")
    return int(w["id"]) if isinstance(w, dict) and w.get("id") else None


def resolve(client, links, alternates=()):
    """(user, slug) -> article ids, in order.

    A link that does not resolve is tried again under each other username in `alternates` with the same slug
    (a renamed author). Returns (ids, unresolved, renamed)."""
    ids, missing, renamed = [], [], []
    for user, slug in links:
        aid = lookup(client, user, slug)
        if aid is None:
            for alt_user, alt_slug in alternates:
                if alt_slug.lower() == slug.lower() and alt_user.lower() != user.lower():
                    aid = lookup(client, alt_user, alt_slug)
                    if aid is not None:
                        renamed.append({"link": f"{user}/{slug}", "resolved_as": f"{alt_user}/{alt_slug}", "id": aid})
                        break
        if aid is None:
            missing.append(f"{user}/{slug}")
        elif aid not in ids:
            ids.append(aid)
    return ids, missing, renamed


def chance_tail(n, k, observed, sims=200000, seed=SEED):
    """Exploratory, not pre-registered: P(mean percentile >= observed) for k winners placed at random."""
    if not k or n < 2:
        return None
    rng = random.Random(seed)
    hit = 0
    for _ in range(sims):
        pos = rng.sample(range(n), k)
        if sum(1 - p / (n - 1) for p in pos) / k >= observed - 1e-12:
            hit += 1
    return round(hit / sims, 4)


def read_winners(client, rnd, ann_id=None):
    """Everything about the round's winners that does not depend on a ranking.

    ann_id names the announcement by hand, for a title `hf26.announcement_round` does not recognise; the
    output says so. It changes which post is read, never how its winners are read."""
    out = {"version": VERSION, "round": rnd, "checked_at": hf26.now_iso(), "advertised": ADVERTISED.get(rnd),
           "announcement_given": bool(ann_id)}
    found = (ann_id, "", None) if ann_id else find_announcement(client, rnd)
    if not found:
        out["status"] = "not_announced"
        return out
    ann_id, path, published = found
    ann = client.get(f"/articles/{ann_id}")
    if not isinstance(ann, dict) and path:
        ann = client.get(f"/articles/{path}")
    if not isinstance(ann, dict) or not ann.get("body_markdown"):
        out.update({"announcement_id": ann_id, "status": "unreadable"})
        return out
    out.update({"announcement_id": ann.get("id"), "announcement_title": ann.get("title"),
                "announced": ann.get("published_at") or published})
    section = winner_section(ann["body_markdown"])
    if section is None:
        out["status"] = "no_winner_section"
        return out
    links = hf26.extract_links(section)
    all_links = hf26.extract_links(ann.get("body_html"), ann.get("body_markdown"))
    slugs = {s.lower() for _, s in links}
    alternates = [(u, s) for u, s in all_links if s.lower() in slugs]
    ids, unresolved, renamed = resolve(client, links, alternates)
    reasons = []
    if out["advertised"] is not None and len(links) != out["advertised"]:
        reasons.append(f"{len(links)} winner links, {out['advertised']} advertised")
    if unresolved:
        reasons.append(f"{len(unresolved)} winner links unresolved")
    out.update({"status": "flagged" if reasons else "scored", "flags": reasons,
                "winner_rule": "dev.to links between 'Overall Winner' and \"What's Next\" in the announcement's markdown",
                "winner_links": [f"{u}/{s}" for u, s in links], "renamed_links": renamed,
                "unresolved_links": unresolved, "winner_ids": ids,
                "links_outside_winner_headings": [f"{u}/{s}" for u, s in all_links if s.lower() not in slugs]})
    return out


def score(result, ranked):
    for by, key in (("rank", "logistic"), ("rank_score", "rank_score")):
        block = hf26.score_predictions(ranked, result["winner_ids"], by=by)
        block["chance_tail_mean_percentile"] = chance_tail(
            block["ranked_entries"], block["winners_in_ranking"], block["mean_winner_percentile"] or 0)
        result[key] = block
    return result


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", required=True, choices=sorted(hf26.ROUNDS))
    ap.add_argument("--predictions", default="", help="committed predictions_<round>.csv; omit to read winners only")
    ap.add_argument("--announcement", type=int, default=None,
                    help="devteam announcement id, only if its title is not recognised automatically")
    ap.add_argument("--out", required=True)
    ap.add_argument("--md", default="")
    a = ap.parse_args(argv)

    client = BustedClient()
    print(f"score_round.py {VERSION}, round {a.round}, item token {client.token}", flush=True)
    result = read_winners(client, a.round, a.announcement)
    if a.predictions and result["status"] in ("scored", "flagged"):
        result["predictions"] = a.predictions
        score(result, hf26.load_field(a.predictions))
    result["requests"] = client.requests
    hf26.write_json(a.out, result)
    print(json.dumps(result, indent=2))
    if a.md and "logistic" in result:
        with open(a.md, "w", encoding="utf-8") as fh:
            fh.write(render_md(result))
    return 1 if result["status"] == "unreadable" else 0


def render_md(r):
    def row(name, b):
        return (f"| {name} | {b['ranked_entries']} | {b['winners_in_ranking']} of {b['winners_announced']} | "
                f"{b['hits_top_k']} | {b['expected_hits_if_random']} | {b['mean_winner_percentile']} | "
                f"{b['chance_tail_mean_percentile']} | {', '.join(map(str, b['winner_ranks']))} |")
    return "\n".join([
        f"# {r['round']}: the committed ranking, scored",
        "",
        f"score_round.py {r['version']}, committed before this round's winners were announced. "
        "Made by MV2 of Munim, Inc., with AI agents working in his name. Data CC BY 4.0.",
        "",
        f"Announcement: DEV article {r['announcement_id']}, published {r['announced']}. Ranking: `{r['predictions']}`.",
        "",
        f"Status: **{r['status']}**{' (' + '; '.join(r['flags']) + ')' if r['flags'] else ''}. "
        f"Winner links under the winner headings: {len(r['winner_links'])} (DEV advertised {r['advertised']}). "
        f"Resolved under the author's current username: {len(r['renamed_links'])}. "
        f"Unresolved: {len(r['unresolved_links'])}.",
        "",
        "| Ordering | Entries ranked | Winners in ranking | Winners in top-k | Expected by chance (k*k/n) "
        "| Mean winner percentile (0.50 = no signal) | Chance of a mean this high (exploratory) | Winner ranks |",
        "|---|---|---|---|---|---|---|---|",
        row("Logistic model (primary)", r["logistic"]),
        row("rank_score baseline", r["rank_score"]),
        "",
        "- Winners missing from the ranking (posted after its snapshot, not English, or without both tags) are not "
        "scored; their count is the gap between the two numbers in the third column.",
        "- The last numeric column was not pre-registered: the share of 200,000 random placements of the same number "
        "of winners whose mean percentile is at least as high.",
        "",
    ])


if __name__ == "__main__":
    sys.exit(main())
