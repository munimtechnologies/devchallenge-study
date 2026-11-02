# Pre-registration: do DEV challenge winners carry AI-disclosure labels more often than the entries they beat?

Written on 2026-11-01 and committed on 2026-11-02 (UTC), before DEV named the winners of either round tested here. The git commit time of this file is the registration time. Made by MV2 of Munim, Inc., with AI agents working in his name. Text CC BY 4.0; code (`ailabel.py`, `test_ailabel.py`) Apache-2.0.

A first attempt to commit this file on 2026-11-01 was stopped because one offline test in `test_ailabel.py` had a wrong fixture (round "b" was meant to have two AI-declared posts and had none). The fixture was corrected; `ailabel.py` itself is unchanged. By the time of this commit, the week-4 snapshot had been taken (2026-11-01 15:22 to 16:27 UTC) and the share of AI-labelled posts in the week-4 field was known (`predictions/2026-11-01/rounds.json`); no winner of either round had been announced (newest `devteam` winner post at commit preparation, about 04:30 UTC on 2026-11-02: week 3's, 2026-10-30). The predictions below were written before the snapshot and were not changed.

## Why

Since 2026-08-26, DEV lets authors label a post "Hand Written (No AI)", "AI-Assisted" or "Fully Autonomous"; unlabelled posts show as "Not disclosed". The public API returns the label as `ai_disclosure_level`. Looking back over the seven challenges in its training data where DEV's disclosure field was in use, [data/REPORT.md](data/REPORT.md) found that winners declared AI use (AI-Assisted or Fully Autonomous) more often than chance would give: 9 of 78 winners against about 4.5 expected (z 2.35). Three winners were labelled No AI (about 0.3 expected), and none of the 78 were labelled Fully Autonomous (about 0.75 expected).

That was a look back at data already in hand, and a pattern found that way can come from chance. This file fixes, in advance, a forward test on two rounds whose winners are still unknown.

## Data (fixed now)

- **Rounds:** Hacktoberfest Open-Source AI Challenge week 4 ("Ghost in the Machine", 21 winners advertised) and the DEV × Kaggle Benchmarking Challenge (5 winners advertised, announcement expected around 2026-11-05).
- **Field:** the posts in each round's committed ranking: `predictions/2026-11-01/predictions_week4.csv` (the week-4 snapshot, taken after the round closed and before winners are named) and `predictions/kaggle-2026/predictions_kagglechallenge.csv` (the primary field, 278 posts, committed 2026-10-31).
- **Labels:** as frozen in each round's committed entries file, taken before the winners were named: `predictions/2026-11-01/entries.csv` (columns `ai_declared` and `ai_level`) and `predictions/kaggle-2026/entries_kagglechallenge.csv` (column `ai_declared` only). A label an author changes later does not count. `ai_declared` is 1 for AI-Assisted or Fully Autonomous and 0 for No AI or Not disclosed (`declared_ai()` in `hf26.py`).
- **Winners:** exactly the winner set each round's own frozen scorer uses: `winner_ids` from week 4's `score_round.py` JSON, and the `primary_winner_set` from `forecast_oos.py score`'s `score.json` for Kaggle. A winner not in the ranked field is left out of both counts and listed.
- **Exclusion:** if either round's winners are announced before this file and its round's entries file are both on `main`, that round is dropped from the test and the report says so. The week-4 snapshot itself records whether DEV had already announced (`rounds.json`, `announced`).

## Predictions

- **P1 (primary).** Across the two rounds pooled, more winners declared AI than a random choice of the same number of winners from the same fields would give: observed count D > expected count E, where E = Σ k·m/N over the rounds (N posts in the field, m of them declared, k winners in the field). The one-sided exact p-value is the chance that random winners give a count ≥ D (hypergeometric per round, rounds combined by convolution). P1's direction **holds** if D > E; it is **significant** if, in addition, p ≤ 0.05. Both outcomes are reported either way.
- **P2.** No week-4 winner is labelled Fully Autonomous in the snapshot. The report gives the chance of zero if winners were random; with a large Fully Autonomous share, P2 holding would mean something, and with a small share, little. Kaggle cannot be graded for P2 because its snapshot kept only `ai_declared`.

## Not tested (reported as exploratory)

- Counts for every label level in week 4 (including No AI).
- Whether winners' labels change after the announcement: `ailabel.py --live` re-reads each winner's label from DEV at scoring time and lists any that differ from the snapshot.

## How it will be scored

```
python ailabel.py \
  --round week4  predictions/2026-11-01/entries.csv predictions/2026-11-01/predictions_week4.csv <week-4 score JSON> \
  --round kaggle predictions/kaggle-2026/entries_kagglechallenge.csv predictions/kaggle-2026/predictions_kagglechallenge.csv <Kaggle score.json> \
  --out-dir <out> --live
```

`ailabel.py` 0.1.0 and its offline tests are committed with this file and will not be changed before scoring. If a bug is found, the fix goes into a new version with an erratum, and the result is reported under both versions.

## Limits, stated now

- 26 winners is a small sample. A real but modest effect can easily miss significance, and one round can dominate the pooled count.
- The ranking model in `hf26.py` already uses `ai_declared` as one of its features, so P1 is not independent of the winner forecast. It tests the label, not the model.
- A label is the author's own statement. It records what authors said, not how much AI they actually used.
- Even if P1 holds, it shows what winners have in common, not that the label or AI use makes a post win. DEV's judges see the label on the post.
