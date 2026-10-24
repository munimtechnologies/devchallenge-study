# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
import unittest

import hf26
import linkaudit
import same_score

ANN = {"published_at": "2026-10-22T15:53:41Z", "tag_list": "devchallenge, sanitychallenge"}


def art(when, tags="devchallenge, sanitychallenge", user="someone", id_=7):
    return {"id": id_, "published_at": when, "tag_list": tags, "user": {"username": user},
            "title": "A post: 3 things", "reading_time_minutes": 4, "body_markdown": "# Hi\n\nSome words here.\n"}


class Rule(unittest.TestCase):
    def test_winner(self):
        self.assertEqual(linkaudit.builder_rule(art("2026-10-04T20:46:15Z"), ANN), "winner")

    def test_reasons(self):
        self.assertEqual(linkaudit.builder_rule(None, ANN), "not readable")
        self.assertEqual(linkaudit.builder_rule(art("2026-05-01T00:00:00Z"), ANN), "outside 120 days")
        self.assertEqual(linkaudit.builder_rule(art("2026-10-23T00:00:00Z"), ANN), "outside 120 days")
        self.assertEqual(linkaudit.builder_rule(art("2026-10-04T00:00:00Z", user="devteam"), ANN), "official account")
        self.assertEqual(linkaudit.builder_rule(art("2026-10-04T00:00:00Z", tags="webdev"), ANN), "no shared tag")


class Relabel(unittest.TestCase):
    cols = ["challenge_id", "article_id", "is_winner", "has_body", "ai_level", "reading_time", "words", "title_words"]

    def rows(self):
        return [dict(zip(self.cols, v)) for v in (["1", "7", "0", "0", "not_disclosed", "4", "0", "5"],
                                                  ["1", "8", "1", "1", "not_disclosed", "9", "900", "6"])]

    def test_relabel_reads_body(self):
        rows = self.rows()
        out, ch = linkaudit.corrected_rows(rows, [{"challenge_id": 1, "article_id": 7, "article": art("2026-10-04T00:00:00Z")}])
        r = [x for x in out if x["article_id"] == "7"][0]
        # A row without a body gets every measure read afresh ("A post: 3 things" is 4 title words).
        self.assertEqual((r["is_winner"], r["has_body"], r["words"], r["title_words"]), ("1", "1", "4", "4"))
        self.assertEqual(ch[0]["action"], "relabelled")
        self.assertEqual(ch[0]["before"], {"is_winner": "0", "has_body": "0"})
        self.assertEqual(rows[0]["is_winner"], "0")  # the committed rows are not touched

    def test_add_missing_row(self):
        out, ch = linkaudit.corrected_rows(self.rows(), [{"challenge_id": 1, "article_id": 9, "article": art("2026-10-04T00:00:00Z", id_=9)}])
        self.assertEqual(len(out), 3)
        self.assertEqual(ch[0]["action"], "added")
        self.assertEqual(out[-1]["is_winner"], "1")
        self.assertEqual(set(out[-1]), set(self.cols))


class Same(unittest.TestCase):
    def test_same_ignores_times(self):
        a = {"status": "scored", "checked_at": "x", "winner_ids": [1, 2], "logistic": {"hits_top_k": 1}, "rank_score": {}}
        b = dict(a, checked_at="y", requests=9)
        self.assertEqual(same_score.differences(a, b), [])
        self.assertEqual(same_score.differences(a, dict(b, winner_ids=[1])), ["winner_ids"])


class Uses(unittest.TestCase):
    def test_hf26_reader_still_old(self):
        self.assertEqual(hf26.extract_links("https://dev.to/jo-ann/post-1abc"), [])


if __name__ == "__main__":
    unittest.main()
