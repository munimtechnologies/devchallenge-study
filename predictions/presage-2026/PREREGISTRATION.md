# Pre-registration: forward forecast of the DEV Presage SmartSpectra SDK Challenge

Made by MV2 of Munim, Inc., with AI agents working in his name. Code Apache-2.0, text CC BY 4.0.

**This file was committed on 2026-11-06, while submissions were still open** (they close 2026-11-23 07:59 UTC). No ranking exists yet, and the snapshot code refuses to run before the deadline. The git commit time of this file is the time the predictions were fixed.

## Why a second forward test

On 2026-11-06 the shape model passed its first forward test: it ranked DEV's Kaggle Benchmarking Challenge before the winners were named, and the five winners sat at a mean percentile of 0.910 of 278 entries (see `../kaggle-2026/README.md`). Five winners is a small sample. The Presage challenge advertises **ten** winners, so the same model, run unchanged on a challenge it has never seen, gets a test with twice the winners. The prize and judging details are also different from Kaggle's, so the test is harder in a useful way.

## The challenge (from DEV's join post, article 4975387)

- Join post published 2026-11-04 22:00:15 UTC. Required tag `#presagechallenge`; DEV's template also fills in `devchallenge`.
- Entrants build something with Presage's SmartSpectra SDK, which reads vital signs from a camera, and write a DEV post about it.
- Submissions are due "November 22 ... 11:59 PM PST", which is 2026-11-23 07:59 UTC. DEV says winners will be announced on December 10.
- Ten winners at $300 each: four for Best Overall Human-Sensing Experience, three for Most Creative or Delightful Use, three for Best Thoughtful Real-World Use. Each submission can win only once.
- Judging criteria: use of underlying technology; usability and user experience; originality and creativity.
- The join post sets no rule against AI-made work. Entrants must disclose optional AI service use in a required section of the template.

The model reads a post's shape (length, headings, code blocks, images, embeds, title form, tags), never its quality, and it cannot see whether the SDK was used well. On 2026-11-06 at about 14:20 UTC the tag held 14 entries besides DEV's own post.

## What is fixed now

- **Code:** every file the snapshot and the scorer run is downloaded by `fetch_presage.py` (committed beside this file) from commit `71219853021f4dc7abc42dc8ab4ef93a2f90e7d7` (2026-11-06 12:47:30 UTC). That is the commit that scored the Kaggle forecast: `forecast_oos.py` 0.1.0, `hf26.py`, `oos.py`, `links.py`, `data/challenges.json` and the week-2 `model.json`. The job runs the pinned unit tests before anything else and stops if any test fails.
- **Model:** the same refit as the Kaggle forecast, on the same training file (the `hf26-predict` dataset's `posts.csv`). The Kaggle snapshot reported 55 training challenges, 1,893 posts, 323 winners and a largest weight difference of 0.0 from the week-2 model. If the Presage snapshot reports a different training count or a non-zero weight difference, the ranking is published but **not graded** as this test, and the reason is stated.
- **Field (primary):** every English post tagged `presagechallenge`, published from 2026-11-04T22:00:15Z up to but not including 2026-11-23T08:00:00Z, leaving out DEV's own posts and any post in the training data. Posts are measured as they are at the snapshot, and the number edited after the deadline is reported.
- **Field (secondary):** the subset also tagged `devchallenge`, ranked on its own.
- **Deadline changes:** if DEV extends the deadline before the snapshot, the snapshot uses the new deadline exactly as the join post states it. The change and the post's wording are recorded in the result.
- **Snapshot timing:** the snapshot runs at the first opportunity on or after 2026-11-23 08:00 UTC. `forecast_oos.py` checks DEV's `devteam` account at the start and the end of the snapshot. If a Presage winners post is already up at either point, the ranking is **not a forecast** and is not graded.
- **Winners:** read by `forecast_oos.py score` from the newest `devteam` post whose title starts "Congrat", contains "winner" and contains "presage". It uses `oos.resolve_winners` from the same commit. **Primary set:** the entries shown as cards (embeds); if the post embeds none, every linked entry. Both sets are reported either way. If DEV's winners post does not contain "presage" in its title, the scorer is re-run once with `--title-word smartspectra`, and that change is reported.
- **Scoring:** `oos.score_set`, unchanged. It reports winners in the top k (k = number of winners ranked), the mean winner percentile, the exact hypergeometric tail for the top-k count (`p_hits_at_least`) and a 200,000-draw random baseline for the mean percentile (`p_mean_percentile_at_least`). The logistic model is primary and the `rank_score` baseline is secondary.
- **Power rule:** the predictions are graded only if at least 5 primary winners are found in the ranking and the primary field has at least 30 ranked entries. Otherwise everything is still published, marked as underpowered.

## Predictions (logistic model, primary field, primary winner set)

1. **Mean winner percentile at least 0.70.** For reference: Kaggle forward test 0.910; leave-one-challenge-out backtest 0.78; Hacktoberfest weeks 1-3 0.929 to 0.964.
2. **The top-k count beats chance at the 5% level:** `p_hits_at_least` is at most 0.05. The Kaggle test would have **failed** this bar (1 of 5 in the top 5, p = 0.087), so this prediction is a real risk.
3. **The logistic model beats the simple baseline:** its mean winner percentile is higher than the `rank_score` baseline's (Kaggle: 0.910 against 0.853).

All three results are published next to the ranking, held or failed, along with the secondary field and the linked winner set.

## Commands

The snapshot job runs, in a sealed container with network:

```
python fetch_presage.py
python -m unittest -v
python forecast_oos.py snapshot --tag presagechallenge --title-word presage --opened 2026-11-04T22:00:15Z --deadline 2026-11-23T08:00:00Z --out-dir /out --train /data/posts.csv
```

After DEV names the winners:

```
python forecast_oos.py score --predictions predictions_presagechallenge.csv --title-word presage --out-dir /out/primary
python forecast_oos.py score --predictions predictions_presagechallenge_both_tags.csv --title-word presage --out-dir /out/both_tags
```

The ranking will be committed to this folder as soon as the snapshot finishes, before December 10. The scores will be committed after the announcement.

## Limits

- The model ranks which posts look like past DEV winners, not which builds are good.
- Ten winners across three categories may reward different things, and a shape model cannot tell the categories apart.
- This study only forecasts the challenge and contacts no entrants. If a post from MV2's own DEV account turns up in the field, the result says so and grades the predictions both with and without it. Article ids only, no usernames.
