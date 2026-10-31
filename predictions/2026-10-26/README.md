# Pre-registered ranking, full week 3, snapshot 2026-10-26

Made by MV2 of Munim, Inc., with AI agents working in his name. Data: CC BY 4.0. Protocol: `../../PREREGISTRATION.md` and `../../PREREGISTRATION_TIMING.md`. Scoring: `../../SCORING.md` (frozen `score_round.py` 0.1.0, release v0.4.1).

These files were committed **after the week-3 (Slow and Steady) round closed (2026-10-26 07:00 UTC) and before DEV announced its winners**. At the snapshot (2026-10-26 08:30:00 to 09:27:13 UTC) the newest winner announcement on DEV's `devteam` account was the week-2 round's (Side Hustle, 2026-10-23 20:18 UTC; `rounds.json` lists every announcement seen). A cache-busted read of the same listing at about 14:35 UTC, when this commit was prepared, still showed week 2 as the newest. The git commit time of this folder is the timestamp of the prediction.

| Round | Entries ranked | Winners DEV advertised | Winners in the top-k by chance (k*k/n) | Round closed |
|---|---|---|---|---|
| week3 (Slow and Steady) | 1594 | 21 | about 0.28 | yes, 2026-10-26 07:00 UTC |

`entries.csv` holds every post tagged `hf26challenge` since 2026-10-01; 1,651 of them are week-3 posts. The 1,594 ranked are the English ones with both tags and a readable body, the same filter the pre-registration uses.

This ranking will be scored against the announced winners, whatever it shows, with the same frozen scorer as weeks 1 and 2. Week 3 is also the first of the two rounds for the forward test in `PREREGISTRATION_TIMING.md`; that test is pooled over weeks 3 and 4, so a week-3 timing result alone is not its answer.

### Week 3 result

DEV announced the week-3 winners on 2026-10-30 at 20:35:58 UTC (article 4949434), four days after this folder was committed. The ranking was scored on 2026-10-31 in a sealed job that downloaded `score_round.py` from `main` and from the frozen commit `e6bb93f`, stopped unless the two were byte-identical (they were), ran the scorer's tests (passed), and then scored the file exactly as committed here.

| Reader | Winners found | Ordering | Winners in the top-k | Expected by chance | Mean winner percentile (0.50 = no signal) |
|---|---|---|---|---|---|
| Frozen `score_round.py` 0.1.0 (pre-registered) | 20 of 21 | Logistic model (primary) | **4** | 0.25 | **0.927** |
| | | rank_score baseline | 5 | 0.25 | 0.921 |
| Corrected link reader (`ERRATUM_LINKS.md`, committed 2026-10-24) | 21 of 21 | Logistic model (primary) | **4** | 0.28 | **0.929** |
| | | rank_score baseline | 5 | 0.28 | 0.922 |

- Every winner was in the ranking: none was missing because of language, tags or posting time.
- Logistic winner ranks, of 1,594 (corrected reader): 4, 6, 13, 19, 23, 26, 29, 32, 36, 38, 40, 68, 94, 95, 101, 105, 117, 219, 430, 438, 447. 17 of the 21 are in the top tenth (rank 159 or better), and all 21 are in the top 447 (the top 28%).
- The frozen reader found 20 winner links, not 21: it is the heading-based reader whose known gap `ERRATUM_LINKS.md` describes. The one winner it missed sits at logistic rank 38. Both counts are published, and the hit count is 4 under either.
- Exploratory, not pre-registered: in 200,000 random placements of the same number of winners, none reached a mean percentile this high.
- Three rounds now: 12 of 56 winners in the top-k against about 0.63 by chance (weeks 1 and 2: 8 of 35; week 3: 4 of 21).
- Limits: the model reads a post's shape, never its quality, and it cannot see which partner technology an entry used. A high mean percentile says winners share a shape the model can measure; it does not say the model knows why they won.

Files: `SCORE_week3_full.md` and `score_week3_full.json` (frozen reader), `SCORE_week3_links.md` and `score_week3_links.json` (corrected reader). The timing test (`PREREGISTRATION_TIMING.md`) is not answered by week 3 alone; it is scored once week 4's winners are announced.

## How it was made

`snapshot_round.py` 0.2.0 (at the repo root, with its tests) is `snapshot_w2.py` 0.1.0 with the round as an argument. It downloaded the committed `hf26.py` from this repo (`fetch.py`) and ran `hf26.py snapshot` and `hf26.py predict` unchanged: same training data, same model, same features. As in week 2, every request carried a per-run `item` token so each listing page came fresh from DEV's origin rather than an edge cache. Post bodies were fetched only for posts from 2026-10-19 07:00 UTC on, so earlier posts are listed in `entries.csv` without bodies and are not re-ranked. The job also wrote a ranking of 35 week-2 posts; week 2 was announced before the snapshot, so that file is not a prediction and is not published. The script refuses to run before a round's deadline, so it cannot produce a partial ranking labelled as the full one.

The refitted model's leave-one-challenge-out backtest is unchanged from week 2: mean winner percentile 0.78 (95% interval 0.75 to 0.81), 151 winners in the top-k against 77.3 by chance.

## Files

- `predictions_week3.csv`: `rank, article_id, score, rank_score`. `score` is the logistic model (ranked on it); `rank_score` is the simpler pre-registered alternative, the mean of the feature percentiles. Both will be scored.
- `entries.csv`: every post tagged `hf26challenge` since 2026-10-01 with its measured shape and the round it entered. Article ids only, no usernames. `reactions_now`, `comments_now` and `published_ts` are recorded but never used by the model.
- `model.json`, `backtest.json`: the fitted weights and the backtest. `rounds.json`: snapshot metadata, including which announcements DEV had already made and each round's AI-disclosure counts. `REPORT.md`: the generated report.
- `SCORE_week3_full.md`, `score_week3_full.json`, `SCORE_week3_links.md`, `score_week3_links.json`: the week-3 scores (see "Week 3 result" above).

## Known quirks, stated before scoring

- DEV's own posts that carry the tag (launch and announcement posts) are skipped by id (`official_posts_skipped` in `rounds.json`). Scoring uses the files exactly as committed.
- Two week-4 posts already existed at the snapshot; they are listed, not ranked.
- The model reads shape, never substance, and cannot see which partner technology an entry used, which decides the partner categories.
- An announced winner missing from the ranking (for example a non-English post) is reported as missing, not counted as a miss.
