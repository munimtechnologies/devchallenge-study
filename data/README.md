# Data

Generated 2026-10-14T09:40Z by `job.py` from DEV's public API (run `devchallenge-winners-v1`).

- `summary.json`: all results.
- `REPORT.md`: the generated report.
- `challenges.json`: one record per winner announcement since 2025-01-01, with its status, chosen tag, window, field size, sample size and AI-disclosure counts.
- `posts.csv`: one row per post: `challenge_id` (the announcement's article id), `article_id`, `is_winner`, `has_body` (1 if the body was read), `ai_level`, then the measured features. Body features are 0 when `has_body` is 0. `published_ts` is a Unix timestamp. `reactions_now` and `comments_now` were read on 2026-10-14.

Only article ids and measurements are stored, never usernames or post text.

Licence: CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Credit "MV2 of Munim, Inc., devchallenge-study".
