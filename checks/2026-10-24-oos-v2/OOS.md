# The HF26 shape model on DEV challenges it never saw

oos.py 0.1.1. Every devteam winners post published after the newest challenge in the model's training data (2026-10-09T19:32:27+00:00), Hacktoberfest rounds left out. Not a forecast: the winners were public when this ran; out of sample because the model never saw these challenges. Made by MV2 of Munim, Inc., with AI agents working in his name. Data CC BY 4.0.

Model: refitted unchanged on 55 challenges (1893 posts, 323 winners). Largest weight difference from the committed week-2 model: 0.0.

| Challenge | Tag | Entries ranked | Winners | Model | Winners in top-k (chance) | P(at least) | Mean winner percentile | Share of random sets as high |
|---|---|---|---|---|---|---|---|---|
| Congrats to the Sanity Challenge Winners! | sanitychallenge | 303 | 7 linked | logistic | 2 (0.16) | 0.00912 | 0.888 | 6e-05 |
| Congrats to the Sanity Challenge Winners! | sanitychallenge | 303 | 7 linked | rank_score | 2 (0.16) | 0.00912 | 0.845 | 0.000335 |
| Congrats to the Sanity Challenge Winners! | sanitychallenge | 303 | 5 embedded | logistic | 2 (0.08) | 0.00214 | 0.962 | 0.0 |
| Congrats to the Sanity Challenge Winners! | sanitychallenge | 303 | 5 embedded | rank_score | 0 (0.08) | 1.0 | 0.912 | 0.000105 |

- 'linked' = every entry linked from the announcement (the study's convention, which counts honourable mentions); 'embedded' = only entries shown as cards.
- Entries: English posts with the challenge tag and devchallenge, published in the 120 days before the announcement, DEV's own posts and training-data posts left out.
- Chance for top-k is k*k/n; P(at least) is the exact hypergeometric tail; the last column uses 200,000 random sets.
- Winner links are read with links.py 0.1.0, which also reads usernames containing a hyphen.

- sanitychallenge: listed 339, left out or flagged {"official": 1, "after_announcement": 1, "no_devchallenge_tag": 34, "not_english": 0, "in_training_data": 0, "no_body": 0, "edited_after_announcement": 0}; linked winners missing from the ranking: [].
