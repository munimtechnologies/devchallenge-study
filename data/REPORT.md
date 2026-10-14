# What wins DEV challenges: winners compared with every other entry

Generated 2026-10-14T09:40:18+00:00 from DEV's public API: 55 challenges announced since 2025-01-01, 323 winning posts and 8320 other entries in the same challenge and time window.

## Measures where more or less can be ranked

Percentile 0.50 means winners look like a typical entry; above 0.50 means winners have more of it.

| Measure | Winners | Mean percentile | 95% interval | Winners above the middle |
|---|---|---|---|---|
| reading_time | 323 | 0.75 | 0.72 to 0.79 | 84% |
| title_words | 323 | 0.60 | 0.57 to 0.63 | 64% |
| n_tags | 323 | 0.55 | 0.51 to 0.58 | 73% |
| published_ts | 323 | 0.49 | 0.46 to 0.52 | 49% |
| reactions_now (after announcement) | 323 | 0.81 | 0.78 to 0.85 | 90% |
| comments_now (after announcement) | 323 | 0.74 | 0.70 to 0.77 | 70% |
| words | 323 | 0.78 | 0.74 to 0.81 | 86% |
| headings | 323 | 0.67 | 0.64 to 0.70 | 72% |
| code_blocks | 323 | 0.60 | 0.57 to 0.63 | 51% |
| images | 323 | 0.66 | 0.63 to 0.69 | 64% |
| embeds | 323 | 0.61 | 0.58 to 0.64 | 50% |

## Yes/no measures

| Measure | Winners | Winners with it | Expected if random | Winner rate | Field rate | z |
|---|---|---|---|---|---|---|
| title_has_number | 323 | 86 | 57.65 | 27% | 18% | 4.76 |
| title_has_colon | 323 | 184 | 174.95 | 57% | 54% | 1.03 |
| title_first_person | 323 | 101 | 76.96 | 31% | 24% | 3.38 |
| has_cover | 323 | 258 | 197.38 | 80% | 61% | 7.08 |
| ai_declared | 78 | 9 | 4.48 | 12% | 6% | 2.35 |
| has_video | 323 | 134 | 68.41 | 42% | 21% | 9.68 |
| has_github_embed | 323 | 24 | 16.62 | 7% | 5% | 1.99 |
| has_table | 323 | 94 | 39.4 | 29% | 12% | 9.8 |

## AI disclosure levels (7 challenges where DEV's disclosure field was in use)

| Level | Winners at level | Expected if random | z |
|---|---|---|---|
| fully_autonomous | 0 of 78 | 0.75 | -0.88 |
| no_ai | 3 of 78 | 0.29 | 5.05 |
| not_disclosed | 66 of 78 | 73.23 | -3.66 |
| some_ai | 9 of 78 | 3.72 | 2.95 |

## Limits

- The field is posts carrying the challenge's tag, published between two days before the first winner and two days after the last (and before the announcement). Entries outside that window or without the tag are missed; other posts using the tag are included.
- 'Winners' are posts linked from DEV's announcement, so honourable mentions count too.
- Reactions and comments were counted now, after the announcement sent readers to the winners.
- Body measures use every winner and a random sample of up to 30 other entries per challenge.
- This shows what winners have in common, not what causes a win.
