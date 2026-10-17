# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Score the committed week-1 ranking against DEV's Touch Grass winners.

`hf26.py score --announcement auto` failed on 2026-10-16 (job hf26-score-w1-v1): `/articles/<id>` for the
announcement came back 404 (no other log line, 3 seconds), most likely a stale edge-cached response. Its link
extractor would also have counted the three entries the announcement's intro mentions as examples.

This keeps the committed scoring (hf26.score_predictions on the committed CSV, both orderings) and changes only
how winners are read: dev.to links between the "Overall Winner" heading and "What's Next", every request with
a per-run `item` token (allowlisted by Forem's CDN, ignored by the API). The committed extractor's result is
reported next to it, labelled.

0.2.0: 0.1.0 (job hf26-score-w1-v2) left the overall winner unresolved. The announcement's markdown embeds it
under the author's earlier username, which the API no longer knows; its HTML links the same slug under the
current username. A winner link that does not resolve is now retried under any other username the body links
with the identical slug, and every such case is listed in the output. MV2 of Munim, Inc.; made with AI agents.
"""
import argparse
import json
import random
import re
import sys
import time
import urllib.parse

import hf26

VERSION = "0.2.0"
ANN_ID = 4863823
ANN_PATH = "devteam/congrats-to-the-hacktoberfest-open-source-ai-challenge-touch-grass-winners-152c"
ADVERTISED = 17  # "$2,450 in Prizes Across 17 Winners"; 1 overall + 6 featured + 10 partner
START_RE = re.compile(r"overall winner", re.I)
END_RE = re.compile(r"what.?s next", re.I)
# Usernames read by hand from the announcement's markdown (2026-10-16), used only as a cross-check.
EXPECTED_USERS = {
    "mike_kim_692aa79c288bfed8", "tanay_singh_1005", "code_neuron58", "soumyadeepdey", "utsavbhattarai007",
    "sbis04", "anshsaini", "dumnicki", "defiantlydefying", "scs0209", "yuvan_shankar", "asiboy6789",
    "aryan_sethi_afdba87340e96", "antoniahp", "nikithakls17sys", "codersacademy006", "anishisbusy",
}


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


def busted(path, token):
    return path + ("&" if "?" in path else "?") + "item=" + token


def lookup(client, user, slug, token):
    w = client.get(busted(f"/articles/{urllib.parse.quote(user)}/{urllib.parse.quote(slug)}", token))
    return int(w["id"]) if isinstance(w, dict) and w.get("id") else None


def resolve(client, links, token, alternates=()):
    """(user, slug) -> article ids, in order.

    A link that does not resolve is tried again under each other username in `alternates` with the same slug
    (a renamed author). Returns (ids, unresolved, renamed)."""
    ids, missing, renamed = [], [], []
    for user, slug in links:
        aid = lookup(client, user, slug, token)
        if aid is None:
            for alt_user, alt_slug in alternates:
                if alt_slug.lower() == slug.lower() and alt_user.lower() != user.lower():
                    aid = lookup(client, alt_user, alt_slug, token)
                    if aid is not None:
                        renamed.append({"link": f"{user}/{slug}", "resolved_as": f"{alt_user}/{alt_slug}", "id": aid})
                        break
        if aid is None:
            missing.append(f"{user}/{slug}")
        elif aid not in ids:
            ids.append(aid)
    return ids, missing, renamed


def chance_tail(n, k, observed, sims=200000, seed=20261016):
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


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--predictions", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--md", default="")
    a = ap.parse_args(argv)

    client = hf26.Client()
    token = "w1score" + str(int(time.time()))
    seen = hf26.announcements_seen(client)
    found = seen.get("week1", {})
    if found.get("announcement_id") not in (None, ANN_ID):
        print("auto search found a different announcement:", found)
        return 1
    ann = client.get(busted(f"/articles/{ANN_ID}", token))
    if not isinstance(ann, dict):
        ann = client.get(busted(f"/articles/{ANN_PATH}", token))
    if not isinstance(ann, dict) or not ann.get("body_markdown"):
        print("announcement not readable by id or path")
        return 1

    section = winner_section(ann["body_markdown"])
    if section is None:
        print("winner section not found")
        return 1
    links = hf26.extract_links(section)
    users = {u.lower() for u, _ in links}
    if len(links) != ADVERTISED:
        print("winner links found:", len(links), "expected", ADVERTISED)
        for u, s in links:
            print(" ", u, s)
        return 1

    # Every dev.to link in the body, as the committed `hf26.py score` would have read it.
    all_links = hf26.extract_links(ann.get("body_html"), ann.get("body_markdown"))
    winner_slugs = {s.lower() for _, s in links}
    alternates = [(u, s) for u, s in all_links if s.lower() in winner_slugs]
    winner_ids, unresolved, renamed = resolve(client, links, token, alternates)

    ranked = hf26.load_field(a.predictions)
    logistic = hf26.score_predictions(ranked, winner_ids, by="rank")
    baseline = hf26.score_predictions(ranked, winner_ids, by="rank_score")
    for block in (logistic, baseline):
        block["chance_tail_mean_percentile"] = chance_tail(
            block["ranked_entries"], block["winners_in_ranking"], block["mean_winner_percentile"] or 0)

    # Links outside the winner headings (not the same post under another username). Not the primary result.
    extra_links = [(u, s) for u, s in all_links if s.lower() not in winner_slugs]
    extra_ids, _, _ = resolve(client, extra_links, token)
    auto_ids = winner_ids + [i for i in extra_ids if i not in winner_ids]

    result = {
        "status": "scored" if not unresolved else "partial", "version": VERSION, "round": "week1",
        "announcement_id": ann.get("id"), "announced": ann.get("published_at"), "scored_at": hf26.now_iso(),
        "predictions": a.predictions,
        "winner_rule": "dev.to links between 'Overall Winner' and \"What's Next\" in the announcement's markdown",
        "winners_advertised": ADVERTISED, "winner_links": [f"{u}/{s}" for u, s in links],
        "cross_check_usernames_match": users == EXPECTED_USERS,
        "cross_check_diff": sorted(users ^ EXPECTED_USERS),
        "renamed_links": renamed, "unresolved_links": unresolved, "winner_ids": winner_ids,
        "logistic": logistic, "rank_score": baseline,
        "committed_extractor": {
            "note": "hf26.extract_links over the whole body; adds links outside the winner headings",
            "extra_links": [f"{u}/{s}" for u, s in extra_links], "winner_ids": auto_ids,
            "logistic": hf26.score_predictions(ranked, auto_ids, by="rank"),
            "rank_score": hf26.score_predictions(ranked, auto_ids, by="rank_score"),
        },
        "requests": client.requests,
    }
    hf26.write_json(a.out, result)
    print(json.dumps(result, indent=2))
    if a.md:
        with open(a.md, "w", encoding="utf-8") as fh:
            fh.write(render_md(result))
    return 0 if not unresolved else 2


def render_md(r):
    def row(name, b):
        return (f"| {name} | {b['ranked_entries']} | {b['winners_in_ranking']} of {b['winners_announced']} | "
                f"{b['hits_top_k']} | {b['expected_hits_if_random']} | {b['mean_winner_percentile']} | "
                f"{b['chance_tail_mean_percentile']} | {', '.join(map(str, b['winner_ranks']))} |")
    lines = [
        "# Week 1 (Touch Grass): the pre-registered forecast, scored",
        "",
        f"score_w1.py {r['version']}. Made by MV2 of Munim, Inc., with AI agents working in his name. Data CC BY 4.0.",
        "",
        f"Announcement: DEV article {r['announcement_id']}, published {r['announced']}. "
        f"Ranking: predictions/2026-10-14/predictions_week1.csv as committed on 2026-10-14, before the announcement.",
        "",
        f"Winners: the {len(r['winner_links'])} dev.to posts under the announcement's winner headings "
        f"(DEV advertised {r['winners_advertised']}). Resolved under the author's current username: "
        f"{len(r['renamed_links'])}. Unresolved: {len(r['unresolved_links'])}. "
        f"Hand cross-check of usernames matches: {r['cross_check_usernames_match']}.",
        "",
        "| Ordering | Entries ranked | Winners in ranking | Winners in top-k | Expected by chance (k*k/n) "
        "| Mean winner percentile (0.50 = no signal) | Chance of a mean this high (exploratory) | Winner ranks |",
        "|---|---|---|---|---|---|---|---|",
        row("Logistic model (primary)", r["logistic"]),
        row("rank_score baseline", r["rank_score"]),
        "",
        "## How to read it",
        "",
        "- The pre-registration sets no number for \"clearly above chance\" and says one round alone says little; "
        "week 2 (Side Hustle) is the second test.",
        "- The last numeric column was not pre-registered: it is the share of 200,000 random placements of the same "
        "number of winners whose mean percentile is at least as high.",
        "- Partner-category winners (10 of 17) are chosen partly for the partner technology used, which no feature sees.",
        "",
        "## Why this is not `hf26.py score --announcement auto`",
        "",
        "- That job (hf26-score-w1-v1) stopped with \"announcement not readable\": the API returned 404 for the "
        "announcement's id, most likely a stale edge-cached response. Here every request carries a per-run `item` token.",
        f"- Its extractor reads every dev.to link in the body, which would add {len(r['committed_extractor']['extra_links'])} "
        "posts the intro mentions as examples, not winners. That reading is kept in score_week1.json "
        "(`committed_extractor`) for comparison. The scoring function and the ranking are unchanged.",
        "- score_w1.py 0.1.0 (job hf26-score-w1-v2) scored only 16 of the 17 winners: the markdown embeds the overall "
        "winner under the author's earlier username, which the API no longer resolves. 0.2.0 retries such a link under "
        "the username the body's HTML uses for the identical slug; each case is listed in `renamed_links`.",
        "",
    ]
    ce = r["committed_extractor"]
    lines += [
        "| Committed extractor (not primary) | Entries ranked | Winners in ranking | Winners in top-k | Expected by chance "
        "| Mean winner percentile | Winner ranks |",
        "|---|---|---|---|---|---|---|",
    ]
    for name, b in (("Logistic", ce["logistic"]), ("rank_score", ce["rank_score"])):
        lines.append(f"| {name} | {b['ranked_entries']} | {b['winners_in_ranking']} of {b['winners_announced']} | "
                     f"{b['hits_top_k']} | {b['expected_hits_if_random']} | {b['mean_winner_percentile']} | "
                     f"{', '.join(map(str, b['winner_ranks']))} |")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    sys.exit(main())
