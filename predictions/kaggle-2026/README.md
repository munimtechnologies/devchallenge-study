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

## Result (scored 2026-11-06)

DEV announced the winners on 2026-11-05 at 21:12:11 UTC (article 4984085): five winners at $500 each, shown as embedded posts. The sealed job `kaggle-score-v1` ran both scoring commands above unchanged on 2026-11-06 at 04:55 UTC, after all unit tests passed. Its outputs are [score_primary.json](score_primary.json) and [score_both_tags.json](score_both_tags.json).

**Both pre-registered predictions held** (logistic model, primary field, primary winner set = the 5 embedded winners):

| | Prediction | Result | Held? |
|---|---|---|---|
| 1 | Mean winner percentile at least 0.70 | **0.910** (winner ranks 2, 7, 29, 35, 56 of 278); chance of 0.910 or more if winners were random: 0.00015 | **held** |
| 2 | At least one winner in the top 5 | **1** (rank 2); 0.09 expected by chance, chance of at least one: 0.087 | **held** |

Also reported, as set out in advance:

| Field / winner set | Model | Mean winner percentile | Winners in top k |
|---|---|---|---|
| Primary, 5 embedded winners | logistic | 0.910 | 1 of 5 |
| Primary, 5 embedded winners | rank_score baseline | 0.853 | 0 |
| Primary, 8 linked posts | logistic | 0.861 | 3 of 8 |
| Secondary (also `devchallenge`, 244 posts), 5 winners | logistic | 0.904 (ranks 2, 7, 28, 32, 53) | 1 of 5 |

The "linked" set is every challenge entry the post links to. It adds three entries that the post shows as examples of the range of submissions, not as winners, so it is not the primary set. The post's embed of a different, open DEV challenge is not a challenge entry and is left out by `oos.resolve_winners`.

What this does and does not show: a model that only reads a post's shape, trained on 55 earlier DEV challenges, placed all five Kaggle winners within its top 56 of 278 entries (about the top fifth). It did this on a challenge it never saw, judged on a criterion it cannot read. Five winners are a small sample, and one hit in the top 5 is weak evidence on its own (p ≈ 0.09). The mean percentile is the stronger result. The model ranks which posts *look like* DEV winners, not which posts are good.
