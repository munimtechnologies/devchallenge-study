# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Audit: winners the study's link reader missed because their DEV username contains a hyphen.

hf26.extract_links, and job.py's reader that built data/posts.csv, accept only letters, digits and
underscores in a username (ERRATUM_LINKS.md). This re-reads every winners announcement the study uses
(the 61 in data/challenges.json, Hacktoberfest weeks 1 and 2, and the Sanity Challenge) with both readers
and lists every link only the corrected reader (links.py) finds.

For training announcements each missed link is put through job.py's own winner rule (published in the 120
days before the announcement, shares a tag with it or carries devchallenge, not an official account). In a
copy of posts.csv every missed winner of a kept challenge is relabelled as a winner (its body is read when
the row had none; a row is added when the post was not in the field), and hf26.backtest runs on the
committed copy and on the corrected one. Nothing committed is changed. Outputs hold article ids, never
usernames: linkaudit.json, LINKAUDIT.md, corrected_rows.csv. MV2 of Munim, Inc.; made with AI agents.
"""
import argparse
import csv
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import timedelta

import hf26
import links

VERSION = "0.1.0"
WINDOW_DAYS = 120
EXTRA = [(4863823, "Hacktoberfest week 1 (forward test)"), (4907389, "Hacktoberfest week 2 (forward test)"),
         (4897896, "Sanity Challenge (out of sample)")]


class BustedClient(hf26.Client):
    """hf26.Client with a per-run `item` token, so responses come fresh from DEV's origin."""

    token = "la" + str(int(time.time()))

    def get(self, path, tries=6):
        return super().get(path + ("&" if "?" in path else "?") + "item=" + self.token, tries)


def builder_rule(w, ann):
    """job.py's test for a linked post to count as a winner; 'winner' or the reason it does not."""
    if not (isinstance(w, dict) and w.get("id") and w.get("published_at")):
        return "not readable"
    at = hf26.parse_time(ann["published_at"])
    wt = hf26.parse_time(w["published_at"])
    if not (at - timedelta(days=WINDOW_DAYS) <= wt <= at):
        return "outside 120 days"
    if ((w.get("user") or {}).get("username") or "").lower() in hf26.SKIP_USERS:
        return "official account"
    if not set(hf26.tags_of(w)) & (set(hf26.tags_of(ann)) | {"devchallenge"}):
        return "no shared tag"
    return "winner"


def load_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def corrected_rows(rows, fixes):
    """Copy of posts.csv rows with each fix relabelled as a winner (or added). Returns (rows, changes)."""
    out = [dict(r) for r in rows]
    cols = list(rows[0].keys())
    index = {(r["challenge_id"], r["article_id"]): r for r in out}
    changes = []
    for fx in fixes:
        cid, aid, art = str(fx["challenge_id"]), str(fx["article_id"]), fx["article"]
        r = index.get((cid, aid))
        if r is None:
            r = {c: "0" for c in cols}
            r.update({"challenge_id": cid, "article_id": aid})
            out.append(r)
            index[(cid, aid)] = r
            action, was = "added", None
        else:
            action, was = "relabelled", {"is_winner": r["is_winner"], "has_body": r["has_body"]}
        r["is_winner"] = "1"
        if action == "added" or r["has_body"] != "1":
            feats = hf26.meta_features(art)
            feats.update(hf26.body_features(art.get("body_markdown")))
            for k, v in feats.items():
                if k in r:
                    r[k] = str(v)
            r["has_body"] = "1"
            r["ai_level"] = hf26.ai_level(art)
        changes.append({"challenge_id": int(cid), "article_id": int(aid), "action": action, "before": was})
    return out, changes


def backtest(rows):
    kept = hf26.prepare_train([dict(r) for r in rows if int(r["has_body"]) == 1])
    summary, per = hf26.backtest(kept)
    X, y = [], []
    for rs in kept.values():
        for r in rs:
            X.append(hf26.vector(r))
            y.append(int(r["is_winner"]))
    return summary, per, hf26.fit_logistic(X, y), set(kept)


def audit_announcement(client, ann_id, label, train_index, kept_ids):
    ann = client.get(f"/articles/{ann_id}")
    rec = {"announcement_id": ann_id, "label": label}
    if not isinstance(ann, dict):
        rec["status"] = "not readable"
        return rec, []
    html, md = ann.get("body_html"), ann.get("body_markdown")
    rec.update({"title": ann.get("title"), "announced": ann.get("published_at"),
                "old_links": len(hf26.extract_links(html, md)), "new_links": len(links.extract_links(html, md)),
                "missed": []})
    fixes = []
    for user, slug in links.missed_by_old_reader(html, md):
        w = client.get(f"/articles/{urllib.parse.quote(user)}/{urllib.parse.quote(slug)}")
        rule = builder_rule(w, ann)
        m = {"article_id": int(w["id"]) if isinstance(w, dict) and w.get("id") else None, "rule": rule,
             "card": (user.lower(), slug.lower()) in links.embedded_keys(md)}
        if m["article_id"]:
            row = train_index.get((str(ann_id), str(m["article_id"])))
            m["published_at"] = w.get("published_at")
            m["posts_csv"] = {"is_winner": int(row["is_winner"]), "has_body": int(row["has_body"])} if row else None
            m["challenge_kept"] = str(ann_id) in kept_ids
            if rule == "winner" and m["challenge_kept"]:
                fixes.append({"challenge_id": ann_id, "article_id": m["article_id"], "article": w})
        rec["missed"].append(m)
    rec["status"] = "ok"
    return rec, fixes


def report(res):
    out = ["# Winner links missed because the username has a hyphen", "",
           f"linkaudit.py {VERSION}, run {res['run_at']}. Every winners announcement the study uses, read with "
           "hf26.py's link reader and with the corrected one in links.py (ERRATUM_LINKS.md). Article ids only. "
           "Made by MV2 of Munim, Inc., with AI agents working in his name. Data CC BY 4.0.", "",
           f"- Announcements read: {res['announcements_read']} of {res['announcements']}; "
           f"with at least one missed link: {res['announcements_with_missed']}.",
           f"- Missed links: {res['missed_links']}; of those, winners by job.py's rule: {res['missed_winners']}; "
           f"in challenges the model trains on: {res['fixes']}.",
           f"- data/challenges.json `links` equal to the old reader's count: {res['links_count_matches']} of "
           f"{res['training_read']} training announcements.", "",
           "| Announcement | Label | Old reader | Corrected | Missed (article id, rule, card) |", "|---|---|---|---|---|"]
    for r in res["announcements_detail"]:
        if r.get("status") != "ok":
            out.append(f"| {r['announcement_id']} | {r['label']} | {r.get('status')} | | |")
            continue
        if not r["missed"] and r["label"] == "training":
            continue
        miss = "; ".join(f"{m['article_id']} {m['rule']}{' card' if m['card'] else ''}" for m in r["missed"]) or "none"
        out.append(f"| {r['announcement_id']} | {r['label']} | {r['old_links']} | {r['new_links']} | {miss} |")
    out += ["", "(Training announcements with no missed link are left out of the table; all are in linkaudit.json.)", ""]
    bt = res["backtest"]
    out += ["## Backtest, committed labels vs corrected labels", ""]
    if not res["fixes"]:
        out += ["No training winner was missed, so the training data and the backtest are unchanged.", ""]
    else:
        out += ["| Labels | Model | Challenges | Winners | Mean winner percentile | 95% interval | Hits in top-k | Expected |",
                "|---|---|---|---|---|---|---|---|"]
        for name in ("committed", "corrected"):
            for model in ("logistic", "rank"):
                s = bt[name][model]
                out.append(f"| {name} | {model} | {s['challenges']} | {s['winners']} | {s['mean_winner_percentile']} | "
                           f"{s['ci95'][0]} to {s['ci95'][1]} | {s['hits_top_k']} | {s['expected_hits_if_random']} |")
        out += ["", f"Largest change in a model weight (all kept challenges, corrected vs committed): {bt['weight_change']}.",
                "Changed rows: corrected_rows.csv. The committed model, rankings and scores are not changed.", ""]
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--train", default="/data/posts.csv")
    ap.add_argument("--challenges", default="challenges.json")
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    t0 = time.time()
    if not os.path.exists(a.train):
        hf26.log(f"downloading training data to {a.train}")
        os.makedirs(os.path.dirname(a.train) or ".", exist_ok=True)
        req = urllib.request.Request(hf26.TRAIN_URL, headers={"User-Agent": hf26.UA})
        with urllib.request.urlopen(req, timeout=120) as r, open(a.train, "wb") as f:
            f.write(r.read())
    rows = load_rows(a.train)
    train_index = {(r["challenge_id"], r["article_id"]): r for r in rows}
    bt_old, per_old, w_old, kept_ids = backtest(rows)
    kept_ids = {str(c) for c in kept_ids}
    hf26.log(f"committed backtest: {json.dumps(bt_old)}")
    with open(a.challenges, encoding="utf-8") as f:
        challenges = json.load(f)

    client = BustedClient()
    detail, fixes, matches, training_read = [], [], 0, 0
    todo = [(c["announcement_id"], "training", c) for c in challenges] + [(i, lab, None) for i, lab in EXTRA]
    for ann_id, label, c in todo:
        rec, fx = audit_announcement(client, ann_id, label, train_index, kept_ids)
        if c is not None:
            rec["challenges_json_links"] = c.get("links")
            if rec.get("status") == "ok":
                training_read += 1
                matches += int(c.get("links") == rec["old_links"])
        detail.append(rec)
        fixes += fx
        hf26.log(json.dumps({k: v for k, v in rec.items() if k != "title"}))

    res = {"version": VERSION, "links_version": links.VERSION, "run_at": hf26.now_iso(),
           "announcements": len(todo), "announcements_read": sum(r.get("status") == "ok" for r in detail),
           "training_read": training_read, "links_count_matches": matches,
           "announcements_with_missed": sum(bool(r.get("missed")) for r in detail),
           "missed_links": sum(len(r.get("missed") or []) for r in detail),
           "missed_winners": sum(m["rule"] == "winner" for r in detail for m in r.get("missed") or []),
           "fixes": len(fixes), "announcements_detail": detail}
    bt = {"committed": bt_old}
    if fixes:
        new_rows, changes = corrected_rows(rows, fixes)
        bt_new, per_new, w_new, _ = backtest(new_rows)
        bt["corrected"] = bt_new
        bt["weight_change"] = round(max(abs(x - y) for x, y in zip(w_old, w_new)), 4)
        bt["changes"] = changes
        cols = list(rows[0].keys())
        changed = {(str(ch["challenge_id"]), str(ch["article_id"])) for ch in changes}
        with open(os.path.join(a.out_dir, "corrected_rows.csv"), "w", newline="", encoding="utf-8") as f:
            wr = csv.DictWriter(f, fieldnames=cols)
            wr.writeheader()
            wr.writerows(r for r in new_rows if (r["challenge_id"], r["article_id"]) in changed)
        hf26.log(f"corrected backtest: {json.dumps(bt_new)}; weight change {bt['weight_change']}")
    res["backtest"] = bt
    res["requests"] = client.requests
    res["minutes"] = round((time.time() - t0) / 60, 1)
    hf26.write_json(os.path.join(a.out_dir, "linkaudit.json"), res)
    with open(os.path.join(a.out_dir, "LINKAUDIT.md"), "w", encoding="utf-8") as f:
        f.write(report(res))
    hf26.log("LINKAUDIT DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
