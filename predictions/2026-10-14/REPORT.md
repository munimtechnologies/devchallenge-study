# Can post shape pick DEV challenge winners before they are announced?

Model fitted 2026-10-14T17:32:22+00:00 on 55 past challenges (1893 posts with bodies, 323 winners). Features are within-challenge percentiles of shape measures plus yes/no measures; reactions, comments and publish time are never used.

## Weights (logistic, L2-regularised)

| Feature | Weight |
|---|---|
| words_pct | +1.636 |
| reading_time_pct | +1.092 |
| has_table | +0.822 |
| images_pct | +0.814 |
| embeds_pct | +0.708 |
| n_tags_pct | +0.586 |
| code_blocks_pct | -0.507 |
| title_words_pct | +0.376 |
| has_video | +0.363 |
| title_first_person | +0.303 |
| has_cover | +0.297 |
| title_has_colon | -0.257 |
| headings_pct | +0.226 |
| has_github_embed | -0.192 |
| title_has_number | +0.171 |
| ai_declared | +0.057 |

## Backtest: leave one challenge out

Each past challenge is ranked by a model fitted on the others. 0.50 means winners rank like any other entry; top-k counts winners among the k highest-ranked posts, where k is that challenge's number of winners.

| Model | Challenges | Winners | Mean winner percentile | 95% interval | Winners in top-k | Expected if random |
|---|---|---|---|---|---|---|
| logistic | 55 | 323 | 0.78 | 0.75 to 0.81 | 151 | 77.3 |
| rank | 55 | 323 | 0.76 | 0.72 to 0.79 | 142 | 77.3 |

## Pre-registered rankings

- **week1**: 1797 English entries with both tags and a readable body, snapshot 2026-10-14T16:48:07+00:00, winners not yet announced at snapshot time. Ranking in `predictions_week1.csv` (article ids only).
- **week2**: 333 English entries with both tags and a readable body, snapshot 2026-10-14T16:48:07+00:00, winners not yet announced at snapshot time. Ranking in `predictions_week2.csv` (article ids only).

## How it will be scored

When DEV announces a round's winners, `hf26.py score` counts how many of them sit in the top-k of the committed ranking (k = number of winners) and the winners' mean percentile, against chance. A ranking committed after an announcement is not a prediction and is marked as such above.

## Limits

- Shape, not substance: the model never reads what a post says or whether the project works.
- Training non-winners are a sample of up to 30 bodies per challenge; live rounds use every entry.
- Partner-category winners are picked partly for the technology used, which no feature sees.
- A round's entries keep arriving until its deadline; a snapshot before the deadline misses the rest.
