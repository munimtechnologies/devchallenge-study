# Forward forecast: DEV × Kaggle Benchmarking Challenge, ranked before the winners were announced

Made by MV2 of Munim, Inc., with AI agents working in his name. Data: CC BY 4.0. Code: Apache-2.0. Rule: `../../FORWARD_OOS.md` (committed 2026-10-31, before this ranking existed). Code: `../../forecast_oos.py` 0.1.0.

These files were committed **after the challenge closed (2026-10-12 07:00 UTC) and before DEV announced its winners** (expected around 2026-11-05). At the snapshot (2026-10-31 16:07:58 to 16:19:08 UTC), DEV's `devteam` account had no winners post that mentioned Kaggle, either at the start or at the end (`announced_before_snapshot` and `announced_by_end_of_snapshot` are both null in `snapshot.json`). A read of the same listing at about 18:50 UTC, when this commit was prepared, still showed none: the newest winners post was the Hacktoberfest week-3 post (2026-10-30 20:35:58 UTC). The git commit time of this folder is the timestamp of the forecast.

The model has never seen this challenge. It reads a post's shape (length, headings, code blocks, images, embeds, title form, tags), never its quality, and the Kaggle judges ask whether a benchmark "reveals something real about model performance", which no shape model can judge. This is a hard out-of-sample test, and it may fail.

| Field | Entries ranked | Winners DEV advertised | Winners in the top-k by chance (k*k/n) |
|---|---|---|---|
| Primary: English `kagglechallenge` posts, 2026-09-23 20:59:28 UTC to before 2026-10-12 07:00 UTC | 278 | 5 | about 0.09 |
| Secondary: the subset also tagged `devchallenge` | 244 | 5 | about 0.10 |

279 posts were listed; one was DEV's own post and was left out. 7 ranked posts were edited after the deadline and are measured as they are now (`edited_after_deadline` in `entries_kagglechallenge.csv`).

## The two predictions (fixed in `FORWARD_OOS.md` before this snapshot)

For the logistic model, on the primary field and the primary winner set:

1. The mean winner percentile is **at least 0.70**. (Leave-one-challenge-out backtest: 0.78. Hacktoberfest weeks 1-3: 0.929 to 0.964.)
2. **At least one winner is in the top k** (k = number of winners). By chance this is under 0.15.

Five winners are few, so neither result settles anything alone. Both will be reported, whatever they show.

## How it was made

A sealed job (`kaggle-fcst-v1`, Python 3.12, network on) downloaded the committed `hf26.py`, `oos.py`, `links.py`, their tests and `data/challenges.json` from `main`, ran all 44 unit tests (passed), and then ran:

```
python forecast_oos.py snapshot --tag kagglechallenge --title-word kaggle --opened 2026-09-23T20:59:28Z --deadline 2026-10-12T07:00:00Z --out-dir /out --train /data/posts.csv
```

The model was refitted unchanged on 55 earlier challenges (1,893 posts, 323 winners; newest training announcement 2026-10-09 19:32:27 UTC). Its largest weight difference from the committed week-2 model (`../2026-10-19/model.json`) is 0.0. The snapshot made 293 requests to DEV's public API.

## How it will be scored

Once DEV posts its Kaggle winners:

```
python forecast_oos.py score --predictions predictions/kaggle-2026/predictions_kagglechallenge.csv --title-word kaggle --out-dir out
```

and the same for `predictions_kagglechallenge_both_tags.csv`. Winners come from DEV's newest `devteam` "Congrat..." post that mentions winners and Kaggle, read with `oos.resolve_winners`. The scores will be committed next to this file.

## Files

- `predictions_kagglechallenge.csv`: `rank, article_id, score, rank_score` for the primary field. `score` is the logistic model (ranked on it); `rank_score` is the simpler baseline, the mean of the feature percentiles.
- `predictions_kagglechallenge_both_tags.csv`: the same for posts that also carry `devchallenge`.
- `entries_kagglechallenge.csv`: every ranked post's measured shape. Article ids only, no usernames.
- `snapshot.json`: snapshot times, counts, what was left out and why, the model check, and the announcement check.
- `REPORT.md`: the report the job generated.
