# Erratum: winner links from usernames with a hyphen

Written 2026-10-24 at about 16:30 UTC, before DEV announced the winners of Hacktoberfest week 3 (the round closes 2026-10-26 07:00 UTC) or week 4. MV2 of Munim, Inc.; made with AI agents working in his name. Text CC BY 4.0.

## What is wrong

The study reads winners from the links in DEV's announcement. That reader is `LINK_RE` and `LIQUID_RE` in `hf26.py`, and the same `LINK_RE` in `job.py`, which built `data/posts.csv`. It accepts only letters, digits and underscores in a DEV username. DEV usernames can also contain a hyphen. A link such as `https://dev.to/jo-ann/post-1abc` is not read at all, and nothing warns about it.

## How it was found

The first out-of-sample run (`oos.py` 0.1.0, `checks/2026-10-24-oos/`) read 6 linked winners and 4 card winners from the Sanity Challenge announcement. The announcement has 7 links to entries and 5 winner cards. The missing winner is article 4797565, posted under a username with a hyphen. In that run's ranking it sits at rank 9 of 303.

## What it touches

- **Hacktoberfest weeks 1 and 2: no change.** Both rounds were scored with all the winners DEV advertised (17 and 18), every link resolved, and none was dropped. Job `devchallenge-linkaudit-v1` re-scores both rounds with the frozen reader and with the corrected one to confirm that.
- **Weeks 3 and 4: at risk.** The frozen `score_round.py` checks the winner count only for rounds listed in its `ADVERTISED` table, which stops at week 2. If a week-3 or week-4 winner's username has a hyphen, the frozen scorer would drop that winner and still report `scored`.
- **The out-of-sample check.** Its first result undercounts the Sanity winners by one (above).
- **The training data and backtest.** These are not measured yet. `linkaudit.py` re-reads all 61 training announcements with both readers. It relabels any missed winner in a copy of `posts.csv` and reruns the backtest on both copies.

## What is fixed now, before weeks 3 and 4 are known

1. `score_round.py` stays frozen and runs unchanged. Its output stays the primary, pre-registered record for every round.
2. Every round from week 3 on is also scored by `score_round_links.py`. That is the frozen `score_round.py`, run with `hf26.extract_links` replaced by `links.extract_links` and nothing else changed: the same committed ranking and the same `hf26.score_predictions`. Both results are published side by side, whatever they show. Where they differ, the README gives both and names the winners (by article id) that the frozen reader missed.
3. `hf26.py`'s own reader is not edited until week 4 has been scored, so the frozen scorer behaves exactly as it did when it was frozen.
4. The out-of-sample check reads links with `links.py` from `oos.py` 0.1.1 on. The 0.1.0 result stays in `checks/2026-10-24-oos/` exactly as it ran.
5. The committed model, rankings, predictions and the week-1 and week-2 scores are not changed. Any effect on the training data is reported by `linkaudit.py` as a separate result, whatever it shows.

## Code

- `links.py` and `test_links.py`: the corrected reader. With no hyphenated username in the text it returns exactly what `hf26.extract_links` returns.
- `score_round_links.py`: the frozen scorer with the corrected reader swapped in.
