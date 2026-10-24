# When were the winners posted? (exploratory)

timing.py 0.1.0. Not pre-registered. Each winner's publish time is ranked among the round's committed, ranked entries (ties half); 0.50 = posted like a typical entry, higher = later. Made by MV2 of Munim, Inc., with AI agents working in his name. Data CC BY 4.0.

| Round | Entries | Winners timed | Mean time percentile | 95% range if timing didn't matter | Winners in the first fifth (expected) | Winners in the first half | Random draws with a mean this late |
|---|---|---|---|---|---|---|---|
| week1 | 1797 | 17 of 17 | 0.557 | 0.363 to 0.637 | 2 (3.4) | 7 | 0.20939 |
| week2 | 1663 | 18 of 18 | 0.620 | 0.367 to 0.633 | 0 (3.6) | 5 | 0.03877 |

- The last column is the share of 200,000 random sets of the same number of entries whose mean time percentile is at least as high.
- Earlier work in this repo (55 challenges, 323 winners) put winners at 0.49 of their challenge's posting window.
