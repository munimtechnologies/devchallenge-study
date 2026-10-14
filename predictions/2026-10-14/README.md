# Pre-registered rankings, snapshot 2026-10-14

Made by MV2 of Munim, Inc., with AI agents working in his name. Data: CC BY 4.0. Protocol: `../../PREREGISTRATION.md`.

These files were committed **before DEV announced the winners of either round**. At the snapshot (2026-10-14 16:48 UTC) and at commit time (checked 2026-10-14 ~19:20 UTC), the newest winner announcement on DEV's `devteam` account was the weekend round's (article 4825130, 2026-10-09). The git commit time of this folder is the timestamp of the prediction.

| Round | Entries ranked | Winners DEV advertised | Winners in the top-k by chance (k*k/n) | Round closed |
|---|---|---|---|---|
| week1 (Touch Grass) | 1,797 | 17 | about 0.16 | yes, 2026-10-12 07:00 UTC |
| week2 (Side Hustle) | 333 | 18 | about 0.97 | **no**: open until 2026-10-19 07:00 UTC, so this ranking misses later entries |

The week-1 ranking is the real test. The week-2 ranking is an early partial; a full one will follow after the round closes and before its announcement.

## Files

- `predictions_week1.csv`, `predictions_week2.csv`: `rank, article_id, score, rank_score`. `score` is the logistic model (ranked on it); `rank_score` is the simpler pre-registered alternative, the mean of the feature percentiles. Both will be scored.
- `entries.csv`: every post tagged `hf26challenge` since 2026-10-01 with its measured shape and the round it entered. Article ids only, no usernames. `reactions_now`, `comments_now` and `published_ts` are recorded but never used by the model.
- `model.json`: the fitted weights. `backtest.json`: leave-one-challenge-out results for the 55 past challenges. `rounds.json`: snapshot metadata, including which announcements DEV had already made. `REPORT.md`: the generated report.

## What the backtest does and does not promise

Left out one challenge at a time, the model put winners at a mean percentile of 0.78 (95% interval 0.75 to 0.81) and put 151 of 323 winners in their challenge's top-k, where chance gives 77. But a past challenge's field in the backtest is the winners plus at most 30 sampled other entries. A live round's field is every entry (1,797 in week 1), so finding winners in the top-k is far harder here, and the mean percentile is the steadier measure.

## Known quirks, stated before scoring

- DEV's own posts carry the tag and sit in the files: the week-1 launch post (4802245, rank 246) in week 1, and the week-2 launch post (4839620, rank 22) and the weekend announcement (4825130, rank 77) in week 2. None is in the top-k they could distort. Scoring uses the files exactly as committed.
- The model reads shape, never substance, and cannot see which partner technology an entry used, which decides the partner categories.
- An announced winner missing from a ranking (for example a non-English post) is reported as missing, not counted as a miss.
