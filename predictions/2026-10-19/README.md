# Pre-registered ranking, full week 2, snapshot 2026-10-19

Made by MV2 of Munim, Inc., with AI agents working in his name. Data: CC BY 4.0. Protocol: `../../PREREGISTRATION.md`. Scoring: `../../SCORING.md` (frozen `score_round.py` 0.1.0, release v0.4.1).

These files were committed **after the week-2 (Side Hustle) round closed (2026-10-19 07:00 UTC) and before DEV announced its winners**. At the snapshot (2026-10-19 08:29:13 to 09:34:03 UTC) and at commit time (checked 2026-10-19 10:12 UTC), the newest winner announcement on DEV's `devteam` account was the week-1 round's (Touch Grass, 2026-10-16). The git commit time of this folder is the timestamp of the prediction.

| Round | Entries ranked | Winners DEV advertised | Winners in the top-k by chance (k*k/n) | Round closed |
|---|---|---|---|---|
| week2 (Side Hustle) | 1663 | 18 | about 0.19 | yes, 2026-10-19 07:00 UTC |

`entries.csv` holds 1,721 week-2 posts; the 1,663 ranked are the English ones with both tags and a readable body, the same filter the pre-registration uses.

This is the full ranking promised in `../2026-10-14/README.md`, which ranked only the 333 entries posted by 2026-10-14. Both will be scored against the announced winners, whatever they show; the full one is the second test the pre-registration asks for.

## Scored, 2026-10-23

DEV announced the 18 Side Hustle winners on 2026-10-23 at 20:18:31 UTC (article 4907389). The frozen `score_round.py` 0.1.0 (checked byte-identical to commit e6bb93f before it ran) scored this ranking at 21:12 UTC, in job hf26-score-w2-v1. Status `scored`, no flags: 18 winner links under the winner headings, as DEV advertised, none renamed or unresolved.

| Ordering | Winners in the ranking | Winners in the top 18 | Expected by chance | Mean winner percentile (0.50 = no signal) |
|---|---|---|---|---|
| Logistic model (primary) | 18 of 18 | **5** | 0.19 | **0.964** |
| rank_score baseline | 18 of 18 | 3 | 0.19 | 0.954 |

Logistic winner ranks, of 1,663: 2, 3, 11, 12, 15, 22, 24, 28, 29, 34, 44, 54, 57, 78, 92, 161, 186, 257. The middle two winners sit at ranks 29 and 34, 16 of the 18 are in the top tenth, and all 18 are in the top 257. In 200,000 random placements of 18 winners, none reached a mean percentile this high (a check added after the fact, not pre-registered).

Files: `SCORE_week2_full.md` and `score_week2_full.json` (the scorer's own output, unchanged). The early partial ranking of 2026-10-14 was scored by the same job; its result is in `../2026-10-14/SCORE_week2_partial.md`: none of the 18 winners was in it, because every one was published after that snapshot (2026-10-14 16:48 UTC).

## How it was made

`snapshot_w2.py` 0.1.0 (at the repo root, with its tests) ran the committed `hf26.py snapshot` and `hf26.py predict` unchanged: same training data, same model, same features. One thing differs, and only in how pages are read: every request carries a per-run `item` token, so each listing page comes fresh from DEV's origin instead of an edge cache that can be hours old (measured in munimtechnologies/dev-ai-disclosure). Post bodies were fetched only for posts from 2026-10-12 on, so week-1 posts are listed in `entries.csv` without bodies and are not re-ranked here. The job also wrote a ranking of 33 week-1 posts; week 1 was announced before the snapshot, so that file is not a prediction and is not published.

## Files

- `predictions_week2.csv`: `rank, article_id, score, rank_score`. `score` is the logistic model (ranked on it); `rank_score` is the simpler pre-registered alternative, the mean of the feature percentiles. Both are scored.
- `entries.csv`: every post tagged `hf26challenge` since 2026-10-01 with its measured shape and the round it entered. Article ids only, no usernames. `reactions_now`, `comments_now` and `published_ts` are recorded but never used by the model.
- `model.json`, `backtest.json`: the fitted weights and the leave-one-challenge-out backtest (refitted on the same training data). `rounds.json`: snapshot metadata, including which announcements DEV had already made. `REPORT.md`: the generated report.
- `SCORE_week2_full.md`, `score_week2_full.json`: the score, added 2026-10-23.

## Known quirks, stated before scoring

- DEV's own posts that carry the tag (launch and announcement posts) may sit in the files. Scoring uses the files exactly as committed.
- The model reads shape, never substance, and cannot see which partner technology an entry used, which decides the partner categories.
- An announced winner missing from the ranking (for example a non-English post) is reported as missing, not counted as a miss.
