# Forward out-of-sample forecast: Kaggle Benchmarking Challenge (written before the ranking exists)

Made by MV2 of Munim, Inc., with AI agents working in his name. Code Apache-2.0, text CC BY 4.0.

`OUT_OF_SAMPLE.md` tests the model on DEV challenges it never saw, but only after their winners are public. This adds a stricter version: rank a challenge it never saw **before** DEV names the winners, commit the ranking, then score it. The first challenge this applies to is the one that closed next after the training data and whose winners are not out yet.

This file and `forecast_oos.py` were committed on 2026-10-31, before the ranking was made. The ranking will go in `predictions/kaggle-2026/` with its own commit, which is the timestamp of the forecast.

## The challenge

DEV × Kaggle Benchmarking Challenge (join post: DEV article 4727332, published 2026-09-23 20:59:28 UTC). Entrants build a benchmark on Kaggle Benchmarks and write a DEV post about it with the required tag `#kagglechallenge`. Submissions were due "October 11 ... at 11:59 PM PDT" (2026-10-12 06:59 UTC). Five winners, $500 each. DEV says winners are announced on November 5. Judging: insights shared, writing quality, creativity in approach.

The model has never seen this challenge: its newest training announcement is from 2026-10-09, and the challenge's winners don't exist yet. It also differs from everything the model is tested on so far. The entry is a write-up of a benchmark, and the judges ask whether it "reveals something real about model performance", which a shape model cannot read.

## What is fixed now

- **Field (primary):** every English post tagged `kagglechallenge`, published from 2026-09-23 20:59:28 UTC up to but not including 2026-10-12 07:00:00 UTC, with DEV's own posts and any post in the training data left out. Posts are measured as they are at the snapshot, and the number edited after the deadline is reported.
- **Field (secondary):** the same posts that also carry `devchallenge` (the tag DEV's template fills in and `oos.py` requires), ranked on their own.
- **Model:** the committed `hf26.py`, refitted unchanged by `oos.fit_model`; the largest weight difference from the committed week-2 model is reported.
- **The snapshot refuses to run before the deadline.** If DEV's winners post is already up at the start or end of the snapshot, the output says so and the ranking is not a forecast.
- **Winners** are read from DEV's winners post (the newest `devteam` post whose title starts "Congrat", contains "winner" and contains "kaggle") with `oos.resolve_winners`, the reader of `oos.py` 0.1.1. **Primary set:** the entries shown as cards (embeds). If the post embeds none, every linked entry. Both sets are reported either way.
- **Scoring:** `oos.score_set` on the committed file, unchanged: winners in the top k (k = number of winners ranked), mean winner percentile, the exact hypergeometric tail and 200,000 random sets. Logistic model primary, `rank_score` baseline secondary.

## Predictions (logistic model, primary field, primary winner set)

1. Mean winner percentile **at least 0.70**. For reference: the leave-one-out backtest gives 0.78, the three Hacktoberfest rounds 0.929 to 0.964, the Sanity Challenge 0.962.
2. **At least one winner in the top k.** By chance that happens for about k*k/n of a winner; with five winners in a field of a few hundred, under 0.15.

Five winners is a small set, so neither result settles anything alone. Whatever it shows is committed beside the ranking. The usual `OUT_OF_SAMPLE.md` run will also score this challenge after the announcement, with its own 120-day window. Both results are published.

## Commands

```
python forecast_oos.py snapshot --tag kagglechallenge --title-word kaggle --opened 2026-09-23T20:59:28Z --deadline 2026-10-12T07:00:00Z --out-dir out --train data/posts.csv --challenges data/challenges.json --model-check predictions/2026-10-19/model.json
python forecast_oos.py score --predictions predictions/kaggle-2026/predictions_kagglechallenge.csv --title-word kaggle --out-dir out
```

`forecast_oos.py` imports `hf26.py`, `oos.py` and `links.py` from the same folder. Its tests are in `test_forecast_oos.py`.
