# week3: the committed ranking, scored

score_round.py 0.1.0, committed before this round's winners were announced. Made by MV2 of Munim, Inc., with AI agents working in his name. Data CC BY 4.0.

Announcement: DEV article 4949434, published 2026-10-30T20:35:58Z. Ranking: `predictions_week3_full_2026-10-26.csv`.

Status: **scored**. Winner links under the winner headings: 20 (DEV advertised None). Resolved under the author's current username: 0. Unresolved: 0.

| Ordering | Entries ranked | Winners in ranking | Winners in top-k | Expected by chance (k*k/n) | Mean winner percentile (0.50 = no signal) | Chance of a mean this high (exploratory) | Winner ranks |
|---|---|---|---|---|---|---|---|
| Logistic model (primary) | 1594 | 20 of 20 | 4 | 0.25 | 0.927 | 0.0 | 4, 6, 13, 19, 23, 26, 29, 32, 36, 40, 68, 94, 95, 101, 105, 117, 219, 430, 438, 447 |
| rank_score baseline | 1594 | 20 of 20 | 5 | 0.25 | 0.921 | 0.0 | 9, 12, 14, 18, 20, 27, 34, 36, 66, 68, 84, 91, 92, 102, 112, 258, 283, 284, 345, 596 |

- Winners missing from the ranking (posted after its snapshot, not English, or without both tags) are not scored; their count is the gap between the two numbers in the third column.
- The last numeric column was not pre-registered: the share of 200,000 random placements of the same number of winners whose mean percentile is at least as high.
