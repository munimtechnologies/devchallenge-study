# Winner links missed because the username has a hyphen

linkaudit.py 0.1.0, run 2026-10-24T16:08:13+00:00. Every winners announcement the study uses, read with hf26.py's link reader and with the corrected one in links.py (ERRATUM_LINKS.md). Article ids only. Made by MV2 of Munim, Inc., with AI agents working in his name. Data CC BY 4.0.

- Announcements read: 63 of 63; with at least one missed link: 2.
- Missed links: 2; of those, winners by job.py's rule: 2; in challenges the model trains on: 1.
- data/challenges.json `links` equal to the old reader's count: 60 of 60 training announcements.

| Announcement | Label | Old reader | Corrected | Missed (article id, rule, card) |
|---|---|---|---|---|
| 2275913 | training | 5 | 6 | 2190411 winner card |
| 4863823 | Hacktoberfest week 1 (forward test) | 21 | 21 | none |
| 4907389 | Hacktoberfest week 2 (forward test) | 18 | 18 | none |
| 4897896 | Sanity Challenge (out of sample) | 6 | 7 | 4797565 winner card |

(Training announcements with no missed link are left out of the table; all are in linkaudit.json.)

## Backtest, committed labels vs corrected labels

| Labels | Model | Challenges | Winners | Mean winner percentile | 95% interval | Hits in top-k | Expected |
|---|---|---|---|---|---|---|---|
| committed | logistic | 55 | 323 | 0.781 | 0.75 to 0.813 | 151 | 77.3 |
| committed | rank | 55 | 323 | 0.755 | 0.724 to 0.787 | 142 | 77.3 |
| corrected | logistic | 55 | 324 | 0.782 | 0.75 to 0.813 | 151 | 77.6 |
| corrected | rank | 55 | 324 | 0.756 | 0.725 to 0.787 | 143 | 77.6 |

Largest change in a model weight (all kept challenges, corrected vs committed): 0.0156.
Changed rows: corrected_rows.csv. The committed model, rankings and scores are not changed.

