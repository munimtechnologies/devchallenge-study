# Week 1 (Touch Grass): the pre-registered forecast, scored

score_w1.py 0.2.0. Made by MV2 of Munim, Inc., with AI agents working in his name. Data CC BY 4.0.

Announcement: DEV article 4863823, published 2026-10-16T17:38:26Z. Ranking: predictions/2026-10-14/predictions_week1.csv as committed on 2026-10-14, before the announcement.

Winners: the 17 dev.to posts under the announcement's winner headings (DEV advertised 17). Resolved under the author's current username: 1. Unresolved: 0. Hand cross-check of usernames matches: True.

| Ordering | Entries ranked | Winners in ranking | Winners in top-k | Expected by chance (k*k/n) | Mean winner percentile (0.50 = no signal) | Chance of a mean this high (exploratory) | Winner ranks |
|---|---|---|---|---|---|---|---|
| Logistic model (primary) | 1797 | 17 of 17 | 3 | 0.16 | 0.937 | 0.0 | 8, 14, 16, 20, 21, 27, 30, 70, 76, 78, 100, 192, 193, 207, 214, 325, 343 |
| rank_score baseline | 1797 | 17 of 17 | 4 | 0.16 | 0.913 | 0.0 | 8, 9, 11, 13, 29, 43, 47, 56, 61, 73, 90, 107, 162, 183, 389, 530, 858 |

## How to read it

- The pre-registration sets no number for "clearly above chance" and says one round alone says little; week 2 (Side Hustle) is the second test.
- The last numeric column was not pre-registered: it is the share of 200,000 random placements of the same number of winners whose mean percentile is at least as high.
- Partner-category winners (10 of 17) are chosen partly for the partner technology used, which no feature sees.

## Why this is not `hf26.py score --announcement auto`

- That job (hf26-score-w1-v1) stopped with "announcement not readable": the API returned 404 for the announcement's id, most likely a stale edge-cached response. Here every request carries a per-run `item` token.
- Its extractor reads every dev.to link in the body, which would add 3 posts the intro mentions as examples, not winners. That reading is kept in score_week1.json (`committed_extractor`) for comparison. The scoring function and the ranking are unchanged.
- score_w1.py 0.1.0 (job hf26-score-w1-v2) scored only 16 of the 17 winners: the markdown embeds the overall winner under the author's earlier username, which the API no longer resolves. 0.2.0 retries such a link under the username the body's HTML uses for the identical slug; each case is listed in `renamed_links`.

| Committed extractor (not primary) | Entries ranked | Winners in ranking | Winners in top-k | Expected by chance | Mean winner percentile | Winner ranks |
|---|---|---|---|---|---|---|
| Logistic | 1797 | 20 of 20 | 5 | 0.22 | 0.931 | 8, 14, 15, 16, 20, 21, 27, 30, 49, 70, 76, 78, 100, 192, 193, 207, 214, 325, 343, 502 |
| rank_score | 1797 | 20 of 20 | 4 | 0.22 | 0.916 | 8, 9, 11, 13, 25, 29, 43, 47, 56, 61, 73, 74, 90, 107, 162, 183, 266, 389, 530, 858 |
