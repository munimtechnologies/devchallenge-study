# What wins DEV challenges?

The posts DEV announced as challenge winners, compared with every other entry in the same challenge and time window: 55 challenges announced from January 2025 to October 2026, **323 winning posts and 8,320 other entries**, all read from DEV's public API.

Made by MV2 of Munim, Inc., with AI agents working in his name. Code: Apache-2.0. Data (`data/`, `predictions/`): CC BY 4.0.

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
- **When you post doesn't matter.** Winners sit at the middle of their challenge's posting window (0.49).
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

The first rankings are in [`predictions/2026-10-14/`](predictions/2026-10-14/), committed before either round's announcement:

| Round | Entries ranked | Winners advertised | Expected in the top-k by chance | Status |
|---|---|---|---|---|
| week1 (Touch Grass) | 1,797 | 17 | about 0.16 | **scored 2026-10-17** (below) |
| week2 (Side Hustle) | 333 (partial) | 18 | about 0.97 | still open at the snapshot; a full ranking follows after the round closes (2026-10-19 07:00 UTC) and before its announcement |

Left out one challenge at a time, the model put past winners at a mean percentile of 0.78 (0.75 to 0.81) and 151 of 323 winners in their challenge's top-k against 77 by chance. That backtest ranks winners against small sampled fields; the live test ranks them against every entry, so it is much harder. Each round's result is added here when DEV announces its winners, whatever it shows.

### Week 1 result

DEV announced the 17 Touch Grass winners on 2026-10-16 (article 4863823). Scored against the ranking committed on 2026-10-14:

| Ordering | Winners in the top 17 | Expected by chance | Mean winner percentile (0.50 = no signal) |
|---|---|---|---|
| Logistic model (primary) | 3 | 0.16 | **0.937** |
| rank_score baseline | 4 | 0.16 | 0.913 |

All 17 winners were in the ranking. The logistic model put the middle winner at rank 76 of 1,797, 11 of the 17 in the top tenth, and every one in the top 343. In 200,000 random placements of 17 winners, none reached a mean percentile this high (a check added after the fact, not pre-registered).

That is far above chance, and above the backtest's 0.78. But it is one round, and the pre-registration asks for more than one before calling it a signal: week 2 (Side Hustle) is the second test. The model reads shape, never substance, and 10 of the 17 winners are partner-category picks, chosen partly for the technology used.

Winner ranks, the scorer's output and the reading described below: [`predictions/2026-10-14/SCORE.md`](predictions/2026-10-14/SCORE.md) and `score_week1.json`.

How it was scored. The scoring function (`hf26.score_predictions`) and the committed ranking are unchanged; only the step that reads the winners differs from `hf26.py score --announcement auto`, in `score_w1.py`:
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
- `score_w1.py`, `test_score_w1.py`: the week-1 scorer described above. `python score_w1.py --predictions predictions/2026-10-14/predictions_week1.csv --out score_week1.json --md SCORE.md`
- `predictions/<date>/`: each committed ranking with its snapshot, model, backtest and report, and once scored, `SCORE.md` and `score_<round>.json`.

## Licence

Code (`job.py`, `test_job.py`, `hf26.py`, `test_hf26.py`, `score_w1.py`, `test_score_w1.py`): Apache-2.0, see `LICENSE`. Data in `data/` and `predictions/`: CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Credit "MV2 of Munim, Inc., devchallenge-study". Post content belongs to its authors; only measurements are published here.
