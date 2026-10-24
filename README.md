# What wins DEV challenges?

The posts DEV announced as challenge winners, compared with every other entry in the same challenge and time window: 55 challenges announced from January 2025 to October 2026, **323 winning posts and 8,320 other entries**, all read from DEV's public API.

Made by MV2 of Munim, Inc., with AI agents working in his name. Code: Apache-2.0. Data (`data/`, `predictions/`): CC BY 4.0.

**Latest (2026-10-24):** the pre-registered forecast has now been scored on two Hacktoberfest 2026 rounds. Both times, a ranking committed before DEV named the winners put them far above chance: week 1, 3 of 17 winners in the top 17 (0.16 expected), mean percentile 0.937; week 2, 5 of 18 in the top 18 (0.19 expected), mean percentile 0.964. [Details below.](#week-2-result) A separate check found week 2's winners were posted later than a typical entry (only 3.9% of random draws were as late), week 1's not clearly; weeks 3 and 4 now test that forward ([`PREREGISTRATION_TIMING.md`](PREREGISTRATION_TIMING.md)).

## Why this is new

Earlier looks at DEV challenges studied winners on their own: who they are, how often they enter ([Datobra, "Who Wins Dev.to Challenges?"](https://www.datobra.com/who-wins-dev-to-challenges-and-the-hidden-benefits-no-one-talks-about-2/), 81 winners), or DEV posts in general ([remdore, "92% of dev.to posts get zero reactions"](https://dev.to/remdore); [marcosgcuenta1, 11,450 DEV articles](https://dev.to/marcosgcuenta1)). We found no study that compares winners with the entries they beat in the same challenge, and none that uses DEV's new `ai_disclosure_level` field.

## Findings

Each winner is ranked against the other entries in its own challenge. A percentile of 0.50 means "like a typical entry".

| Measure | Winners' mean percentile | 95% interval |
|---|---|---|
| Length (words, sampled bodies) | 0.78 | 0.74 to 0.81 |
| Reading time | 0.75 | 0.72 to 0.79 |
| Headings | 0.67 | 0.64 to 0.70 |
| Images | 0.66 | 0.63 to 0.69 |
| Title length (words) | 0.60 | 0.57 to 0.63 |
| Code blocks | 0.60 | 0.57 to 0.63 |
| Publication time within the window | **0.49** | 0.46 to 0.52 |
| Reactions (counted after the announcement) | 0.81 | 0.78 to 0.85 |

| Yes/no | Winners | Other entries | z |
|---|---|---|---|
| Has a table | 29% | 12% | 9.8 |
| Has a video (YouTube, Loom, Vimeo) | 42% | 21% | 9.7 |
| Has a cover image | 80% | 61% | 7.1 |
| Number in the title | 27% | 18% | 4.8 |
| "I", "my", "we" or "our" in the title | 31% | 24% | 3.4 |
| Colon or dash in the title | 57% | 54% | 1.0 |

In short:
- **Winners are longer and more structured.** 86% of winners are longer than the typical entry in their challenge.
- **Show it working.** A demo video doubles in frequency among winners (42% vs 21%), and so does a table (29% vs 12%).
- **When you post mostly doesn't matter.** Winners sit at the middle of their challenge's posting window (0.49). Week 2 of Hacktoberfest 2026 is a possible exception: its winners leaned late (see [Week 2 result](#week-2-result)), which weeks 3 and 4 now test forward.
- **Reactions are not a precondition.** Most entries get almost none: 64% of the 8,320 other entries had 5 reactions or fewer, and 20% had zero. Winners have more, but that count was taken after DEV's announcement sent readers to them, so it can't show that reactions came first. In the October 2026 "Build for a Friend" round, 7 of the 17 winners had 5 reactions or fewer even after the announcement.
- **Title style barely matters.** A colon or dash is just as common in losing titles.

### AI disclosure

DEV posts carry an AI-disclosure setting (`ai_disclosure_level` in the API). Almost nobody set it before September 2026, so only two challenges have enough posts using it to say anything:

| Challenge | Winners "some AI" | Other entries "some AI" | Winners "fully autonomous" | Other entries "fully autonomous" |
|---|---|---|---|---|
| Hacktoberfest Weekend Challenge: Build for a Friend (Oct 2026) | **8 of 17** | 205 of 1,408 (15%) | 0 of 17 | 40 of 1,408 (3%) |
| Weekend Challenge: Generosity Edition (Sep 2026) | 1 of 8 | 13 of 89 (15%) | 0 of 8 | 3 of 89 (3%) |

In the larger round, entries that declared some AI help won about three times as often as chance would give (8 winners where 2.5 were expected; exact one-sided binomial p ≈ 0.0015). Disclosing AI help clearly did not hurt. This is a correlation from one round, not proof that disclosure helps: careful authors may both fill in the setting and write better posts. No "fully autonomous" post won, but only 0.7 were expected, so the data can't tell either way.

The pooled `no_ai` line in `REPORT.md` (z = 5.05) rests on three posts, two of them the only `no_ai` posts in a 2025 Frontend challenge. Don't read anything into it.

## Pre-registered test: can shape pick winners before the announcement?

Hindsight is cheap, so the findings above are now being tested forward. `hf26.py` fits a logistic model on the 55 past challenges (shape only: no reactions, comments or timing), ranks every entry of a live Hacktoberfest 2026 round, and the ranking is committed here **before** DEV announces that round's winners. The protocol and its limits were committed first, in `PREREGISTRATION.md` (release v0.2.0).

| Round | Ranking | Entries ranked | Winners advertised | Expected in the top-k by chance | Status |
|---|---|---|---|---|---|
| week1 (Touch Grass) | [`predictions/2026-10-14/`](predictions/2026-10-14/) | 1,797 | 17 | about 0.16 | **scored 2026-10-17** (below) |
| week2 (Side Hustle), early partial | [`predictions/2026-10-14/`](predictions/2026-10-14/) | 333 | 18 | about 0.97 | scored 2026-10-23: no winner was posted by that snapshot (below) |
| week2 (Side Hustle), full | [`predictions/2026-10-19/`](predictions/2026-10-19/) | 1,663 | 18 | about 0.19 | **scored 2026-10-23** (below) |

Left out one challenge at a time, the model put past winners at a mean percentile of 0.78 (0.75 to 0.81) and 151 of 323 winners in their challenge's top-k against 77 by chance. That backtest ranks winners against small sampled fields; the live test ranks them against every entry, so it is much harder. Each round's result is added here when DEV announces its winners, whatever it shows.

**From week 2 on, the way winners are read is frozen too.** `score_round.py` was committed before the week-2 round closed, reproduces the week-1 score exactly, and will score every later round unchanged: see [`SCORING.md`](SCORING.md).

### Week 1 result

DEV announced the 17 Touch Grass winners on 2026-10-16 (article 4863823). Scored against the ranking committed on 2026-10-14:

| Ordering | Winners in the top 17 | Expected by chance | Mean winner percentile (0.50 = no signal) |
|---|---|---|---|
| Logistic model (primary) | 3 | 0.16 | **0.937** |
| rank_score baseline | 4 | 0.16 | 0.913 |

All 17 winners were in the ranking. The logistic model put the middle winner at rank 76 of 1,797, 11 of the 17 in the top tenth, and every one in the top 343. In 200,000 random placements of 17 winners, none reached a mean percentile this high (a check added after the fact, not pre-registered).

That is far above chance, and above the backtest's 0.78. But it is one round, and the pre-registration asks for more than one before calling it a signal: week 2 (Side Hustle) is the second test. The model reads shape, never substance, and 10 of the 17 winners are partner-category picks, chosen partly for the technology used.

Winner ranks, the scorer's output and the reading described below: [`predictions/2026-10-14/SCORE.md`](predictions/2026-10-14/SCORE.md) and `score_week1.json`.

### Week 2 result

DEV announced the 18 Side Hustle winners on 2026-10-23 at 20:18 UTC (article 4907389). The frozen `score_round.py` 0.1.0, checked byte-identical to the committed copy before it ran, scored both committed rankings 54 minutes later (job hf26-score-w2-v1). Status `scored`, no flags: 18 winner links under the winner headings, as advertised, none renamed or unresolved. Nothing was read or fixed by hand.

Full ranking (committed 2026-10-19 10:12 UTC, after the round closed and four days before the announcement):

| Ordering | Winners in the top 18 | Expected by chance | Mean winner percentile (0.50 = no signal) |
|---|---|---|---|
| Logistic model (primary) | **5** | 0.19 | **0.964** |
| rank_score baseline | 3 | 0.19 | 0.954 |

All 18 winners were in the ranking. Logistic winner ranks, of 1,663: 2, 3, 11, 12, 15, 22, 24, 28, 29, 34, 44, 54, 57, 78, 92, 161, 186, 257. The middle two sit at ranks 29 and 34, 16 of the 18 are in the top tenth, and all 18 are in the top 257. As in week 1, none of 200,000 random placements reached a mean percentile this high (not pre-registered).

The early partial ranking (333 entries, snapshot 2026-10-14 16:48 UTC) holds **none** of the 18 winners, so it has nothing to score. That is not a miss by the model. The winner with the lowest article id (4852284) was created at 18:50 UTC that day and published at 19:04 UTC, after the snapshot. DEV's article ids grow with creation time, so every other winner came later still. The snapshot held about 20% of the round's ranked entries. If winners were spread evenly across entries, all 18 falling outside it would happen about 1.8% of the time.

**When were the winners posted?** A follow-up check (`timing.py`, exploratory, [`checks/2026-10-23/`](checks/2026-10-23/)) ranked every winner's publish time among its round's ranked entries:

| Round | Winners | Mean time percentile (0.50 = typical) | 95% range if timing didn't matter | Winners in the first fifth (expected) | Random draws with a mean this late |
|---|---|---|---|---|---|
| week1 (Touch Grass) | 17 | 0.557 | 0.363 to 0.637 | 2 (3.4) | 21% |
| week2 (Side Hustle) | 18 | 0.620 | 0.367 to 0.633 | 0 (3.6) | 3.9% |

Week 2's winners leaned late: none was among the first fifth of entries, and the first was published about 60 hours into the 7-day round. Week 1 shows no clear lean, and two of its winners were among its very first entries. That is one round, found after looking, against a 55-challenge history of 0.49, so it is not a finding yet. Weeks 3 and 4 test it forward under [`PREREGISTRATION_TIMING.md`](PREREGISTRATION_TIMING.md), committed before week 3 closed. (The week-1 ranking also holds posts published in the two days after that round closed, which may pull its number down; a recount limited to entries posted by the close will be added.)

**Two rounds.** The pre-registration's bar was "winners in the top-k clearly above chance, in more than one round". Both rounds clear it: 8 of 35 winners in the top-k against about 0.35 by chance, and mean percentiles of 0.937 and 0.964 against 0.50. The bar was not set as a number, so this is a reading of it, not a p-value. Its limits still apply: the model reads shape, never substance. Weeks 3 and 4 will be ranked and scored the same way.

Scorer output: [`predictions/2026-10-19/SCORE_week2_full.md`](predictions/2026-10-19/SCORE_week2_full.md) and `score_week2_full.json`; partial: [`predictions/2026-10-14/SCORE_week2_partial.md`](predictions/2026-10-14/SCORE_week2_partial.md) and `score_week2_partial.json`.

### How week 1 was scored

The scoring function (`hf26.score_predictions`) and the committed ranking are unchanged; only the step that reads the winners differs from `hf26.py score --announcement auto`, in `score_w1.py`:
- The automatic run (job hf26-score-w1-v1) stopped with "announcement not readable": DEV's API returned 404 for the announcement's id, most likely a stale edge-cached response. `score_w1.py` adds a per-run `item` token to every request.
- The committed extractor reads every dev.to link in the announcement, which adds 3 posts the intro mentions as examples, not winners. `score_w1.py` reads only links under the winner headings and checks the count against the 17 DEV advertised. The committed extractor's reading is kept in `score_week1.json` (`committed_extractor`: 20 posts, logistic 5 in the top 20 against 0.22 by chance, mean percentile 0.931).
- A first version (job hf26-score-w1-v2) found only 16 of the 17 winners: the announcement embeds the overall winner under the author's earlier username, which the API no longer resolves. Version 0.2.0 retries such a link under the username the announcement's HTML uses for the identical slug, and lists each case in `renamed_links` (one here).

## Method

`job.py` (standard library only):
1. Lists `devteam` posts whose titles congratulate or announce winners, published since 2025-01-01 (60 found).
2. Reads each announcement and follows every DEV post it links or embeds. A linked post counts as a winner if it was published in the 120 days before the announcement and shares a tag with it (or carries `devchallenge`).
3. Picks the challenge's own tag (the announcement tag most winners carry, skipping broad tags like `ai` or `webdev`).
4. The field is every English post with that tag published from two days before the first winner to two days after the last, and before the announcement.
5. Reads the full body of every winner and of a random sample of up to 30 other entries per challenge (seeded by the announcement id, so it is reproducible).
6. Ranks each winner against the other entries in its own challenge (ties count half) and averages. The 95% interval assumes winners are typical entries (uniform percentiles, variance 1/12), which is conservative when there are ties. For yes/no measures, the expected count sums each challenge's field rate over its winners.

Five announcements were dropped: one linked no posts, and four had fewer than 10 other entries in the window. The run took 69 minutes and 2,127 requests at one request per second or slower, with a User-Agent naming MV2 of Munim, Inc.

## Limits

- **Correlation, not cause.** This shows what winners have in common, not what makes them win.
- **The field is approximate.** Entries without the challenge tag, or outside the window, are missed; posts that used the tag without entering are included. The tag is chosen automatically: for the 2025 Hacktoberfest Writing Challenge it picked `codenewbie`. Recurring tags (`weekendchallenge`, `frontendchallenge`, `githubchallenge`, `googleaichallenge`) are limited by the window.
- **Winners include honourable mentions and runners-up** wherever the announcement links them.
- **Reactions and comments were counted on 2026-10-14**, after announcements sent readers to winners.
- **Body measures use samples**: every winner, but at most 30 other entries per challenge.
- Measures are simple text counts (a "table" is a Markdown separator row; a "video" is a YouTube, Loom or Vimeo link or embed).

## Files

- `job.py`: the collector and analysis. `python job.py --out-dir out --since 2025-01-01`
- `test_job.py`: unit tests (`python -m unittest -v`), run before every commit.
- `data/summary.json`: every number above.
- `data/REPORT.md`: the generated report.
- `data/challenges.json`: per challenge, the announcement, chosen tag, window, field size, sample size and AI-disclosure counts.
- `data/posts.csv`: one row per post (article id, never a username) with every measured feature.
- `hf26.py`, `test_hf26.py`, `PREREGISTRATION.md`: the forward test (`snapshot`, `predict`, `score`) and its protocol.
- `snapshot_w2.py`, `test_snapshot_w2.py`: the full week-2 snapshot (see `predictions/2026-10-19/README.md`).
- `score_w1.py`, `test_score_w1.py`: the week-1 scorer described above. `python score_w1.py --predictions predictions/2026-10-14/predictions_week1.csv --out score_week1.json --md SCORE.md`
- `score_round.py`, `test_score_round.py`, `check_rescore.py`, `SCORING.md`: the frozen scorer for week 2 onward, its tests, the week-1 reproduction check, and what is frozen. `python score_round.py --round week2 --predictions <ranking> --out score_week2.json --md SCORE_week2.md`
- `timing.py`, `test_timing.py`, `PREREGISTRATION_TIMING.md`: when in each round the winners were posted (`python timing.py --data-dir data_cache --out-dir out`), and the forward test of it for weeks 3 and 4.
- `checks/2026-10-17/`: the run that checked `score_round.py` before it was committed (week-1 rescore, weekend winners, week 2 not yet announced).
- `checks/2026-10-23/`: the timing check's output for weeks 1 and 2.
- `predictions/<date>/`: each committed ranking with its snapshot, model, backtest and report, and once scored, the scorer's Markdown and JSON output.

## Licence

Code (`job.py`, `test_job.py`, `hf26.py`, `test_hf26.py`, `snapshot_w2.py`, `test_snapshot_w2.py`, `score_w1.py`, `test_score_w1.py`, `score_round.py`, `test_score_round.py`, `check_rescore.py`, `timing.py`, `test_timing.py`): Apache-2.0, see `LICENSE`. Data in `data/`, `predictions/` and `checks/`: CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Credit "MV2 of Munim, Inc., devchallenge-study". Post content belongs to its authors; only measurements are published here.
