# Pre-registered predictions for DEV's Hacktoberfest 2026 rounds

Made by MV2 of Munim, Inc., with AI agents working in his name. Code Apache-2.0, text and data CC BY 4.0.

The main study in this repo looks at what winners of 55 past DEV challenges have in common, with hindsight.
Hindsight is cheap. This file sets out a test that is not: rank the entries of a live round **before** DEV
announces its winners, commit the ranking, then score it.

## Protocol

1. `python hf26.py snapshot` lists every post tagged `hf26challenge` through DEV's public API, fetches each
   body and records its shape (words, headings, code blocks, images, embeds, table, video, cover image, title
   features, tag count, AI-disclosure level) and the round it entered. Round comes from the challenge link in
   the post's template line; if that is missing, from the publish time. Reactions, comments and publish time are
   stored for the record and **never used** by the model. Usernames are never stored.
2. `python hf26.py predict` fits an L2-regularised logistic model on the study's past challenges, using each
   feature's percentile *within its own challenge*, then
   - backtests it by leaving one challenge out at a time (winners' mean percentile, 0.50 = no signal; winners
     in the top-k against the number expected by chance), and
   - ranks every English entry with both tags and a readable body for each round that has at least 10.
3. The ranking files (`predictions_<round>.csv`, article ids only) are committed with the snapshot time.
   `rounds.json` lists which announcements DEV had already made at snapshot time, so a ranking made after its
   round's announcement is labelled as not a prediction.
4. When DEV announces a round's winners: `python hf26.py score --predictions predictions_<round>.csv
   --announcement <devteam article id>` counts the announced winners in the top-k (k = winners found in the
   ranking) and their mean percentile, against chance (k*k/n).

## What would count as a result

- Winners in the top-k clearly above chance, in more than one round: shape carries real signal.
- At or near chance: shape is not what DEV's judges reward once a post is in the field. That is also worth
  knowing, and it will be reported the same way.

## Limits stated in advance

- The model sees shape, never substance: it does not read what a post says or whether the project works.
- Partner-category winners are chosen partly for the technology used, which no feature sees.
- Training non-winners are a sample (up to 30 bodies per past challenge); live rounds use every entry found.
- A round's entries keep arriving until its deadline. A snapshot taken earlier misses the rest, and the report
  says how many entries each snapshot covered.
- Winner counts per round are small (about 17 to 18), so one round alone says little.

## Amendment 1 (2026-10-14, before any Hacktoberfest week announcement)

Made after the first rankings were committed (`predictions/2026-10-14/`) and before DEV announced the winners
of week 1 or week 2. Nothing here changes the committed rankings or the model.

- **Scoring covers both orderings.** `score` now reports the logistic ranking (the committed `rank`) and the
  plain baseline (entries re-sorted by the committed `rank_score` column), side by side, with the announced
  winners' article ids and any winners missing from the ranking. The logistic ranking is the primary result.
- **`--announcement auto --round <round>`** finds the round's announcement on DEV's `devteam` account and
  reports `not_announced` if there is none yet.
- **Future snapshots skip DEV's own posts** (launches and announcements by `devteam`), which carry the tag but
  are not entries. They are listed in `rounds.json` as `official_posts_skipped`. The 2026-10-14 files still
  contain three such posts (ranks 246 in week 1; 22 and 77 in week 2); none is in a top-k, and they are
  scored as committed.
