# Pre-registered ranking, full week 4, snapshot 2026-11-01

Made by MV2 of Munim, Inc., with AI agents working in his name. Data: CC BY 4.0. Protocol: `../../PREREGISTRATION.md` and `../../PREREGISTRATION_TIMING.md`. Scoring: `../../SCORING.md` (frozen `score_round.py` 0.1.0, release v0.4.1). The AI-label forward test in `../../PREREGISTRATION_AILABEL.md` reads `entries.csv` and `predictions_week4.csv` from this folder.

These files were committed **after the week-4 (Ghost in the Machine) round closed (2026-11-01 07:00 UTC) and before DEV announced its winners**. At the snapshot (2026-11-01 15:22:28 to 16:27:25 UTC) the newest winner announcement on DEV's `devteam` account was the week-3 round's (Slow and Steady, 2026-10-30 20:35 UTC; `rounds.json` lists every announcement seen, and week 4 is not among them). A read of the same listing at about 04:30 UTC on 2026-11-02, when this commit was prepared, still showed week 3 as the newest. The git commit time of this folder is the timestamp of the prediction.

| Round | Entries ranked | Winners DEV advertised | Winners in the top-k by chance (k*k/n) | Round closed |
|---|---|---|---|---|
| week4 (Ghost in the Machine) | 1487 | 21 | about 0.30 | yes, 2026-11-01 07:00 UTC |

`entries.csv` holds every post tagged `hf26challenge` since 2026-10-01; 1,545 of them are week-4 posts. The 1,487 ranked are the English ones with both tags and a readable body, the same filter the pre-registration uses.

This ranking will be scored against the announced winners, whatever it shows, with the same frozen scorer as weeks 1 to 3. Week 4 is also the second of the two rounds for the forward test in `PREREGISTRATION_TIMING.md` (pooled over weeks 3 and 4) and one of the two rounds for `PREREGISTRATION_AILABEL.md` (pooled with the DEV × Kaggle challenge).

## How it was made

`snapshot_round.py` 0.2.0 (at the repo root, with its tests), the same script as week 3, run with `--round week4`. It downloaded the committed `hf26.py` from this repo (`fetch.py`) and ran `hf26.py snapshot` and `hf26.py predict` unchanged: same training data, same model, same features. Every request carried a per-run `item` token so each listing page came fresh from DEV's origin rather than an edge cache. Post bodies were fetched only for posts from 2026-10-26 07:00 UTC on, so earlier posts are listed in `entries.csv` without bodies and are not re-ranked. The script refuses to run before a round's deadline, so it cannot produce a partial ranking labelled as the full one. The job also wrote rankings for weeks 1 and 3; those rounds were announced before the snapshot, so those files are not predictions and are not published.

The refitted model's leave-one-challenge-out backtest is unchanged from weeks 2 and 3: mean winner percentile 0.78 (95% interval 0.75 to 0.81), 151 winners in the top-k against 77.3 by chance.

## AI-disclosure labels in the week-4 field (as frozen at the snapshot)

Of the 1,545 week-4 posts: 1,324 Not disclosed, 166 AI-Assisted, 51 Fully Autonomous, 4 Hand Written (No AI) (`rounds.json`). So about 14% declared AI use. With 51 Fully Autonomous posts (3.3%), 21 random winners would include none of them a little under half the time, so P2 of the AI-label test ("no Fully Autonomous winner") can only say a little whichever way it goes, as that file already warns.

## Files

- `predictions_week4.csv`: `rank, article_id, score, rank_score`. `score` is the logistic model (ranked on it); `rank_score` is the simpler pre-registered alternative, the mean of the feature percentiles. Both will be scored.
- `entries.csv`: every post tagged `hf26challenge` since 2026-10-01 with its measured shape, its AI-disclosure label (`ai_level`, `ai_declared`) and the round it entered. Article ids only, no usernames. `reactions_now`, `comments_now` and `published_ts` are recorded but never used by the model.
- `model.json`, `backtest.json`: the fitted weights and the backtest. `rounds.json`: snapshot metadata, including which announcements DEV had already made and each round's AI-disclosure counts. `REPORT.md`: the generated report.

## Known quirks, stated before scoring

- DEV's own posts that carry the tag (launch and announcement posts) are skipped by id (`official_posts_skipped` in `rounds.json`). Scoring uses the files exactly as committed.
- Six posts published after the week-4 deadline are listed with round `none` and are not ranked.
- The model reads shape, never substance, and cannot see which partner technology an entry used, which decides the partner categories.
- An announced winner missing from the ranking (for example a non-English post) is reported as missing, not counted as a miss.
