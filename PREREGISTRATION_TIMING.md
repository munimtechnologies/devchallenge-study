# Pre-registration: were the winners posted late? (weeks 3 and 4)

Committed 2026-10-24, before Hacktoberfest 2026 week 3 (Slow and Steady) closes on 2026-10-26 at 07:00 UTC and before any week-3 or week-4 winner is known. Made by MV2 of Munim, Inc., with AI agents working in his name. CC BY 4.0.

## Why

Across 55 past DEV challenges (323 winners), winners sat at the middle of their challenge's posting window (mean percentile 0.49). In Hacktoberfest 2026 the exploratory timing check (`timing.py`, `checks/2026-10-23/`) found:

| Round | Winners | Mean time percentile | 95% range if timing didn't matter | Winners in the first fifth (expected) | Random draws with a mean this late |
|---|---|---|---|---|---|
| week 1 (Touch Grass) | 17 | 0.557 | 0.363 to 0.637 | 2 (3.4) | 21% |
| week 2 (Side Hustle) | 18 | 0.620 | 0.367 to 0.633 | 0 (3.6) | 3.9% |

Week 2 leans late; week 1 doesn't clearly. That was found after looking, in one round, so it is a question, not a result. Weeks 3 and 4 test it forward. The forecast model in `hf26.py` never uses timing, so this test cannot change any ranking.

## What will be measured

For each of week 3 and week 4:
- **Entries:** every entry in that round's committed full ranking (taken after the round closes, as for week 2).
- **Winners:** the `winner_ids` in the frozen `score_round.py` 0.1.0 output for that round, used only if its status is `scored`.
- **Measure:** `timing.py` (0.1.1 or a later version whose all-entries numbers are unchanged): each winner's publish time is ranked among the round's other ranked entries (ties count half) and the ranks are averaged (`mean_time_percentile`). It also reports winners in the first fifth and the share of 200,000 random draws with a mean at least as late.

**Pooled statistic (primary):** the mean over all timed winners of weeks 3 and 4 together, i.e. each round's mean weighted by its number of timed winners K. Its 95% range if timing didn't matter is 0.5 ± 1.96 × sqrt(1 / (12K)). For example, K = 21 + 20 = 41 gives 0.412 to 0.588.

## Predictions

1. **Primary:** the pooled mean is above the upper end of that range. Reading: above it means "winners are posted late" (confirmed forward); inside it means "no clear timing effect" (the 55-challenge history stands and week 2 was likely noise); below it means "winners are posted early".
2. **Secondary:** pooled, fewer winners fall in the first fifth of entries than the 0.2K expected.
3. Each round's own mean, range and random-draw share are reported too, but the call is made on the pooled number only.

## Rules

- If only one of the two rounds reaches status `scored` by 2026-11-30, the call is made on that round alone, with its own range, and is labelled as one round.
- If neither does, this test is reported as not testable.
- The result is published here whatever it shows. No other split (by category, by time of day, by entries posted after the close) changes the call; any such split is labelled exploratory.
- Known limit: entries are taken from the committed ranking, which may hold a few posts published just after the close. A second count restricted to entries published by each round's close will be reported next to it, labelled secondary.
