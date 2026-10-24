# Weeks 1 and 2 rescored with the corrected link reader

Job devchallenge-linkaudit-v1, 2026-10-24 16:00 to 16:08 UTC. Made by MV2 of Munim, Inc., with AI agents working in his name. CC BY 4.0.

Before any rescoring, the job checked that `score_round.py` on main is byte-identical to the frozen copy (e6bb93f). It then scored both committed rankings twice, once with the frozen `score_round.py` and once with `score_round_links.py` (the same scorer with `links.py` 0.1.0's reader), and compared the results with `same_score.py`. That script ignores only run times and request counts.

| Comparison | Result |
|---|---|
| week 1: frozen reader vs corrected reader | SAME |
| week 2: frozen reader vs corrected reader | SAME |
| week 1: committed `score_week1.json` vs corrected reader | SAME |
| week 2: committed `score_week2_full.json` vs corrected reader | SAME |

Both rounds' winner sets, ranks and scores are unchanged: week 1 has 17 winners, logistic 3 in the top 17, mean percentile 0.937; week 2 has 18 winners, logistic 5 in the top 18, mean percentile 0.964. No winner in either round has a hyphen in the username. The rescore JSON files duplicate the committed score files, so they are not added here.
