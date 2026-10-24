# Timing check, 2026-10-23 (exploratory)

When in each round were the Hacktoberfest 2026 winners posted? Each winner's publish time is ranked among the round's committed, ranked entries (ties count half): 0.50 means "posted like a typical entry", higher means later. Not pre-registered: this check was written after week 2's early partial snapshot turned out to hold none of the 18 winners.

- Run: job hf26-timing-v1, 2026-10-23 22:26 UTC, python:3.12, 7 unit tests passed first. `timing.json` and `TIMING.md` here are its output, unchanged.
- Code: `timing.py` 0.1.0 at the time. `timing.py` 0.1.1 read week 2's winners from `predictions/2026-10-19/score_week2_full.json` instead of a local copy of the same 18 ids. Nothing else changed, so it gives the same numbers. `timing.py` 0.2.0 adds the by-close recount (see `checks/2026-10-24/`).

| Round | Entries | Winners | Mean time percentile | 95% range if timing didn't matter | Winners in the first fifth (expected) | Winners in the first half | Random draws with a mean this late |
|---|---|---|---|---|---|---|---|
| week 1 (Touch Grass) | 1,797 | 17 | 0.557 | 0.363 to 0.637 | 2 (3.4) | 7 | 21% |
| week 2 (Side Hustle) | 1,663 | 18 | 0.620 | 0.367 to 0.633 | 0 (3.6) | 5 | 3.9% |

Reading:
- Week 2's winners lean late. Their mean sits just inside the two-sided range, but only 3.9% of random draws of 18 entries are as late, and none of the 18 was among the first fifth of entries (3.6 expected). The first winner was published on 2026-10-14 at 19:04 UTC, about 60 hours into a 7-day round.
- Week 1 shows no clear lean (21% of random draws are as late). Two of its winners were among the very first entries.
- So it is one round, found after looking. Across 55 past challenges, winners sat at 0.49. Weeks 3 and 4 test it forward: see `PREREGISTRATION_TIMING.md`.

Limit: the week-1 ranking was taken on 2026-10-14, two days after that round closed (2026-10-12 07:00 UTC), and its entries run to 2026-10-14 14:41 UTC. Posts published after the close sit at the late end and push winners' percentiles down, so week 1's 0.557 could understate how late its winners were. The recount restricted to entries published by each round's close is in `checks/2026-10-24/`: week 1 moves only to 0.565 (18% of random draws as late), week 2 to 0.623 (3.4%).
