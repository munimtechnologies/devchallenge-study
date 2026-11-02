# Look-back: AI-disclosure labels among Hacktoberfest weeks 1-3 winners

**This is a look-back, not the pre-registered test.** The winners of these three rounds were already public when this was run. The pre-registered test ([PREREGISTRATION_AILABEL.md](../../PREREGISTRATION_AILABEL.md)) covers week 4 and the DEV × Kaggle Benchmarking Challenge, whose winners had not been named, and it will be scored once they are. The headings inside the `AILABEL.md` files say "forward test" because that is the fixed template of `ailabel.py` 0.1.0, which is not edited before scoring. Read them as look-back results.

Run 2026-11-02 04:37 to 04:39 UTC with `python lookback.py --out-dir out` (`lookback.py` in the repository root), using `ailabel.py` 0.1.0 unchanged. Labels come from each round's committed snapshot (`predictions/2026-10-14`, `2026-10-19`, `2026-10-26`), taken before DEV named that round's winners. Winners are the `winner_ids` in each round's frozen score file. Made by MV2 of Munim, Inc., with AI agents working in his name. Text CC BY 4.0; code Apache-2.0.

## Result

| Round | Posts in field | Declared AI in field | Winners in field | Declared AI among winners | Expected if random | One-sided exact p |
|---|---|---|---|---|---|---|
| Week 1 | 1,797 | 319 (17.8%) | 17 | 6 | 3.02 | 0.065 |
| Week 2 | 1,663 | 267 (16.1%) | 18 | 7 | 2.89 | 0.016 |
| Week 3 | 1,594 | 258 (16.2%) | 20 | 7 | 3.24 | 0.031 |
| **Pooled** | | | **55** | **20** | **9.14** | **0.0003** |

"Declared AI" means the author labelled the post AI-Assisted or Fully Autonomous. By label level:

| Level | Week 1 winners (expected) | Week 2 | Week 3 | Total |
|---|---|---|---|---|
| Fully Autonomous | 1 (0.61) | 4 (0.77) | 2 (0.99) | **7 (2.37)** |
| AI-Assisted | 5 (2.40) | 3 (2.12) | 5 (2.25) | **13 (6.77)** |
| Hand Written (No AI) | 0 (0.11) | 0 (0.11) | 0 (0.08) | 0 (0.30) |
| Not disclosed | 11 (13.87) | 11 (15.00) | 13 (16.69) | 35 (45.56) |

None of the 55 winners' labels has changed since the snapshot (checked live with `--live`).

## What it means, and what it doesn't

- In these three rounds, winners declared AI use about **2.2 times** as often as random winners from the same fields would have (20 against 9.1). Every round points the same way, and two of the three clear p = 0.05 on their own.
- **Fully Autonomous posts won 7 times against 2.4 expected.** That is the opposite of what the older look-back in [data/REPORT.md](../../data/REPORT.md) found over seven earlier challenges (none of 78 winners labelled Fully Autonomous, against about 0.75 expected), and the opposite of the pre-registered P2 for week 4 ("no week-4 winner is labelled Fully Autonomous"). P2 was written before this look-back was run and stays as written. This look-back says P2 is more likely to fail than to hold.
- The Hacktoberfest Open-Source AI Challenge is itself about AI, so declaring AI use may simply fit the brief. These rounds cannot separate "the label helps" from "the posts that use AI well are the ones that win here".
- A label is the author's own statement. DEV's judges see it on the post.
- This shows what winners have in common, not what makes them win.

## Files

- `week1/`, `week2/`, `week3/`, `pooled/`: `AILABEL.md` and `ailabel.json` from `ailabel.py` 0.1.0, unchanged.
- The inputs are the committed files under `predictions/` named above. `lookback.py` downloads them from this repository's `main` branch.
