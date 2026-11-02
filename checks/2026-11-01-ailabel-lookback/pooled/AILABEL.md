# Do winners carry AI-disclosure labels more often? (forward test)

ailabel.py 0.1.0, run 2026-11-02 04:38 UTC. Pre-registered in PREREGISTRATION_AILABEL.md; labels are those frozen in each round's committed snapshot, taken before DEV named the winners.

| Round | Field | Declared AI in field | Winners in field | Declared AI among winners | Expected if random |
|---|---|---|---|---|---|
| week1 | 1797 | 319 (17.8%) | 17 | 6 | 3.02 |
| week2 | 1663 | 267 (16.1%) | 18 | 7 | 2.89 |
| week3 | 1594 | 258 (16.2%) | 20 | 7 | 3.24 |

**P1 (primary):** 20 of 55 winners declared AI against 9.14 expected; one-sided exact p = 0.0003. Direction held; significant at 0.05.

**P2:** 7 winner(s) labelled Fully Autonomous in week1, week2, week3 (2.37 expected; chance of none if winners were random: 0.0870). Did not hold.

week1 by label level:

| Level | Field | Winners | Expected |
|---|---|---|---|
| fully_autonomous | 65 | 1 | 0.61 |
| no_ai | 12 | 0 | 0.11 |
| not_disclosed | 1466 | 11 | 13.87 |
| some_ai | 254 | 5 | 2.40 |

week2 by label level:

| Level | Field | Winners | Expected |
|---|---|---|---|
| fully_autonomous | 71 | 4 | 0.77 |
| no_ai | 10 | 0 | 0.11 |
| not_disclosed | 1386 | 11 | 15.00 |
| some_ai | 196 | 3 | 2.12 |

week3 by label level:

| Level | Field | Winners | Expected |
|---|---|---|---|
| fully_autonomous | 79 | 2 | 0.99 |
| no_ai | 6 | 0 | 0.08 |
| not_disclosed | 1330 | 13 | 16.69 |
| some_ai | 179 | 5 | 2.25 |

**Exploratory, not pre-registered as a test:** 0 of 55 winners' labels differ now from the snapshot.

Winners include honourable mentions where DEV lists them. This shows what winners have in common, not what makes them win. Made by MV2 of Munim, Inc., with AI agents working in his name.
