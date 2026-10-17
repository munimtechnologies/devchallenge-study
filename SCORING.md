# How later rounds are scored (frozen before the week-2 winners exist)

Week 1 was scored by `score_w1.py`, but its winner-reading rule was settled after DEV's announcement was out: the automatic run got a stale 404, the committed extractor counted 3 intro examples, and a first fix missed a renamed author (see the README). A rule written after the answer is known can be tuned to it, even by accident.

So the rule is now frozen in `score_round.py` 0.1.0 and committed **before** the week-2 (Side Hustle) round closes on 2026-10-19 07:00 UTC, and before any of its winners exist. Every later round (week 2, then weeks 3 and 4 if they are ranked) is scored with this file unchanged. If it ever has to change, the change and the reason will be committed separately, and the frozen version's output will be kept beside it.

Made by MV2 of Munim, Inc., with AI agents working in his name. Code Apache-2.0, data CC BY 4.0.

## What is frozen

- **Which post:** the newest `devteam` post whose title `hf26.announcement_round` maps to the round ("Congrats to the Hacktoberfest ... Winners!"). `--announcement ID` exists only for a title that is not recognised; the output then says `announcement_given: true`. It changes which post is read, never how.
- **Which links are winners:** the dev.to links between the first line containing "Overall Winner" and the next line containing "What's Next", in the announcement's markdown. Nothing outside those lines counts; those links are listed in `links_outside_winner_headings`.
- **Renamed authors:** a winner link that does not resolve is retried under any other username the announcement links with the identical slug. Each case is listed in `renamed_links`.
- **Cache:** every request carries a per-run `item` token, because DEV's edge cache keys on it and its API ignores it.
- **Scoring:** the committed `hf26.score_predictions`, unchanged, for both orderings (logistic model, primary; rank_score baseline). The chance column (200,000 random placements, seed 20261016) is exploratory, as before.
- **Advertised winners:** weekend 17, week 1 17, week 2 18, from each round's "Join" post.

## What it reports

The result is always written; nothing is silently dropped.

| status | meaning |
|---|---|
| `scored` | winner links under the headings = the number DEV advertised, and every link resolved |
| `flagged` | the count differs or a link did not resolve; the reasons are in `flags` and the numbers are still given |
| `not_announced` | no announcement for the round yet; nothing scored |
| `no_winner_section` | the announcement has no "Overall Winner" ... "What's Next" block; nothing scored |
| `unreadable` | the announcement could not be read (exit code 1) |

## Checked before committing

One sealed run on 2026-10-17 04:55 UTC (job hf26-w2-prep-v1, Python 3.12, live DEV API). Its outputs are in [`checks/2026-10-17/`](checks/2026-10-17/):

- **43 offline unit tests pass** (`test_hf26.py`, `test_score_round.py`, and the tests of the week-2 snapshot script).
- **Week 1 reproduces exactly.** `score_round.py --round week1` on the committed `predictions/2026-10-14/predictions_week1.csv` gives status `scored`, the same 17 winner ids (one found under the author's current username) and the same numbers as the committed `score_week1.json`: logistic 3 in the top 17 (0.16 by chance), mean winner percentile 0.937; rank_score 4, 0.913. `check_rescore.py` compares every field and printed `MATCH` (`rescore_week1.json`).
- **A second real announcement reads cleanly.** The weekend round (Build for a Friend, 2026-10-09) was never ranked, so only its winners were read: 17 links under the winner headings, 17 advertised, all resolved, none renamed, no links outside the headings, status `scored` (`winners_weekend.json`).
- **Week 2 has no winners yet.** `score_round.py --round week2` returned `not_announced` (`score_week2_now.json`). DEV's `devteam` listing, read again shortly after 05:15 UTC, still showed no Side Hustle winner post, and the round is open until 2026-10-19 07:00 UTC.

`score_round.py --md` writes a summary whose first line says the scorer was committed before the round's winners were announced. That is true from week 2 on, not for the week-1 check above, so that summary is not included here.

## What happens next

1. After week 2 closes (2026-10-19 07:00 UTC) and before its announcement, a full ranking of the round is committed (the 2026-10-14 ranking covers only the 333 entries posted by then).
2. When DEV announces the week-2 winners, `score_round.py --round week2` is run on both rankings, the partial 2026-10-14 one (labelled partial) and the full one, and both results are committed whatever they show, with status and flags as reported.

```
python score_round.py --round week2 --predictions predictions/2026-10-14/predictions_week2.csv --out score_week2.json --md SCORE_week2.md
python check_rescore.py rescore_week1.json predictions/2026-10-14/score_week1.json
```
