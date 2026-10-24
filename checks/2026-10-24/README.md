# Timing check with by-close recount, 2026-10-24 (exploratory)

The same check as `checks/2026-10-23/`, run again with `timing.py` 0.2.0. Each round is counted twice: once over every ranked entry (unchanged from 0.1.x), and once ("-by-close") over only the ranked entries published by the round's close, as in `hf26.ROUNDS` (week 1: 2026-10-12 07:00 UTC; week 2: 2026-10-19 07:00 UTC). Not pre-registered.

- Run: job hf26-timing-v2, 2026-10-24 00:07 UTC, python:3.12, 11 unit tests passed first. `timing.json` and `TIMING.md` here are its output, unchanged.
- Inputs: the committed rankings, entry lists and scorer output in `predictions/2026-10-14/` and `predictions/2026-10-19/`, read from this repo.

| Round | Entries | Winners | Mean time percentile | 95% range if timing didn't matter | Winners in the first fifth (expected) | Random draws with a mean this late |
|---|---|---|---|---|---|---|
| week 1, all ranked entries | 1,797 | 17 | 0.557 | 0.363 to 0.637 | 2 (3.4) | 21% |
| week 1, by close (26 later entries left out) | 1,771 | 17 | 0.565 | 0.363 to 0.637 | 2 (3.4) | 18% |
| week 2, all ranked entries | 1,663 | 18 | 0.620 | 0.367 to 0.633 | 0 (3.6) | 3.9% |
| week 2, by close (10 later entries left out) | 1,653 | 18 | 0.623 | 0.367 to 0.633 | 0 (3.6) | 3.4% |

Reading:
- Every winner in both rounds was published before its round closed, so no winner drops out of the by-close rows.
- Leaving out the late entries barely moves either round. Week 1 was not kept near 0.5 by its two-day-late snapshot: it still shows no clear lean. Week 2 still leans late.
- The pre-registered test for weeks 3 and 4 (`PREREGISTRATION_TIMING.md`) makes its call on the all-entries numbers, as written before this recount. The by-close numbers will be reported next to them.

Made by MV2 of Munim, Inc., with AI agents working in his name. Data CC BY 4.0.
