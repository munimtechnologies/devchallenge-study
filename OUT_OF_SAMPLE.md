# Out-of-sample check: the shape model on DEV challenges it never saw

Written 2026-10-24, before any result of this check existed. MV2 of Munim, Inc.; made with AI agents working in his name. Text CC BY 4.0.

## Why

The Hacktoberfest 2026 forecast (`PREREGISTRATION.md`) tests the shape model on one event, round after round.
The 55-challenge backtest tests it on past challenges, but those challenges trained the model.
This check asks a third question: does the same model, unchanged, rank winners well in DEV challenges that came after its training data?

## Which challenges (fixed rule)

- Every devteam post whose title starts "Congrat" and contains "winner", published after the newest announcement in `data/challenges.json` (2026-10-09T19:32:27Z).
- Hacktoberfest rounds are left out, because weeks 1 to 4 are scored by the forward test.
- No challenge is added or dropped by hand. On 2026-10-24 the only one is the Sanity Challenge (announced 2026-10-22).
- Later announcements that meet the rule are added in the order they appear, whatever they show.

## How

- Model: `hf26.py`'s logistic model, refitted on the same training data with the same settings. The job reports the largest weight difference from the committed week-2 model.
- Entries: English posts with the challenge's own tag and `devchallenge`, published in the 120 days before the announcement. DEV's own posts and any post in the training data are left out.
- Winners: every entry linked from the announcement, the study's usual convention, which counts honourable mentions. A second count uses only entries shown as cards.
- Scores: winners in the top k (k = number of winners) against chance k*k/n, with the exact hypergeometric tail; the winners' mean percentile against 200,000 random sets. The plain `rank_score` baseline is reported too.

## What this is not

- It is not a forecast. The winners were public when it ran.
- Entries are read after the announcement, so a post edited since then is measured as edited. The job counts those posts.
- One challenge with a few winners can only show a large effect. Treat it as one data point next to the forward test, not as a test on its own.

Code: `oos.py` and `test_oos.py`, added with the first result.
