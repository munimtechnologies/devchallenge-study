# week2: the committed ranking, scored

score_round.py 0.1.0, committed before this round's winners were announced. Made by MV2 of Munim, Inc., with AI agents working in his name. Data CC BY 4.0.

Announcement: DEV article 4907389, published 2026-10-23T20:18:31Z. Ranking: `predictions_week2_full_2026-10-19.csv`.

Status: **scored**. Winner links under the winner headings: 18 (DEV advertised 18). Resolved under the author's current username: 0. Unresolved: 0.

| Ordering | Entries ranked | Winners in ranking | Winners in top-k | Expected by chance (k*k/n) | Mean winner percentile (0.50 = no signal) | Chance of a mean this high (exploratory) | Winner ranks |
|---|---|---|---|---|---|---|---|
| Logistic model (primary) | 1663 | 18 of 18 | 5 | 0.19 | 0.964 | 0.0 | 2, 3, 11, 12, 15, 22, 24, 28, 29, 34, 44, 54, 57, 78, 92, 161, 186, 257 |
| rank_score baseline | 1663 | 18 of 18 | 3 | 0.19 | 0.954 | 0.0 | 8, 10, 13, 19, 20, 21, 28, 31, 38, 47, 59, 63, 67, 75, 91, 221, 252, 332 |

- Winners missing from the ranking (posted after its snapshot, not English, or without both tags) are not scored; their count is the gap between the two numbers in the third column.
- The last numeric column was not pre-registered: the share of 200,000 random placements of the same number of winners whose mean percentile is at least as high.
