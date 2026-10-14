# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
import unittest

import job


class TestParsing(unittest.TestCase):
    def test_is_announcement(self):
        self.assertTrue(job.is_announcement("Congrats to the Hacktoberfest Weekend Challenge: Build for a Friend Winners!"))
        self.assertTrue(job.is_announcement("Announcing the Winners of the DEV Weekend Challenge: Earth Day Edition"))
        self.assertTrue(job.is_announcement("Congrats to Our First MLH x DEV Writing Challenge Winner!"))
        self.assertFalse(job.is_announcement("Join the Hacktoberfest Open-Source AI Challenge: Side Hustle! $2,550 in Prizes Across 18 Winners."))
        self.assertFalse(job.is_announcement("A Quick Update on the Summer Bug Smash Winners"))
        self.assertFalse(job.is_announcement(None))

    def test_extract_links(self):
        html = ('<a href="https://dev.to/adk_bbx/phone-calls-are-the-boss-fight-1h6h">x</a> '
                '<a href="https://dev.to/challenges/hacktoberfest-week2-2026-10-12">c</a> '
                '<a href="https://dev.to/devteam/join-the-challenge-4pom">j</a> '
                '<a href="https://dev.to/someone">profile</a> '
                '<a href="https://dev.to/adk_bbx/phone-calls-are-the-boss-fight-1h6h#comments">again</a>')
        md = ("{% embed https://dev.to/highcenburg/tala-free-audio-to-text-2o26 %}\n"
              "{% link muaazsm/rakshak-scam-checker-22ah %}\n"
              "See https://dev.to/t/devchallenge.")
        self.assertEqual(job.extract_links(html, md), [
            ("adk_bbx", "phone-calls-are-the-boss-fight-1h6h"),
            ("highcenburg", "tala-free-audio-to-text-2o26"),
            ("muaazsm", "rakshak-scam-checker-22ah"),
        ])
        self.assertEqual(job.extract_links(None, ""), [])

    def test_tags_of(self):
        self.assertEqual(job.tags_of({"tag_list": "devchallenge, weekendchallenge"}), ["devchallenge", "weekendchallenge"])
        self.assertEqual(job.tags_of({"tag_list": ["a", "b"]}), ["a", "b"])
        self.assertEqual(job.tags_of({}), [])

    def test_choose_tag(self):
        ann = ["devchallenge", "weekendchallenge", "hf26challenge"]
        winners = [["devchallenge", "hf26challenge"], ["hf26challenge", "weekendchallenge"], ["hf26challenge", "ai"]]
        self.assertEqual(job.choose_tag(ann, winners), "hf26challenge")
        # Tie between announcement tags: the one listed first wins.
        self.assertEqual(job.choose_tag(["frontendchallenge", "css"], [["frontendchallenge"], ["frontendchallenge"]]), "frontendchallenge")
        # Announcement carries only generic tags: fall back to the winners' own tag.
        self.assertEqual(job.choose_tag(["devchallenge"], [["wecoded", "career"], ["wecoded"]]), "wecoded")
        self.assertIsNone(job.choose_tag(["devchallenge"], [["ai"], []]))

    def test_declared_ai(self):
        self.assertEqual(job.declared_ai({}), 0)
        self.assertEqual(job.declared_ai({"ai_disclosure_level": "not_disclosed", "ai_disclosure_label": "Not Disclosed"}), 0)
        self.assertEqual(job.declared_ai({"ai_disclosure_level": "some_ai", "ai_disclosure_label": "AI-assisted"}), 1)
        self.assertEqual(job.declared_ai({"ai_disclosure_level": "no_ai", "ai_disclosure_label": "No AI"}), 0)


class TestFeatures(unittest.TestCase):
    def test_meta_features(self):
        a = {"title": "I built my parents a scam checker: 39 letters", "reading_time_minutes": 7,
             "public_reactions_count": 12, "comments_count": 3, "cover_image": "https://x/y.png",
             "tag_list": ["devchallenge", "hf26challenge"], "published_at": "2026-10-04T12:00:00Z",
             "ai_disclosure_level": "some_ai"}
        f = job.meta_features(a)
        self.assertEqual(f["reading_time"], 7)
        self.assertEqual(f["title_has_number"], 1)
        self.assertEqual(f["title_has_colon"], 1)
        self.assertEqual(f["title_first_person"], 1)
        self.assertEqual(f["has_cover"], 1)
        self.assertEqual(f["n_tags"], 2)
        self.assertEqual(f["ai_declared"], 1)
        g = job.meta_features({"title": "Paste-Safe", "published_at": "2026-10-04T12:00:00Z"})
        self.assertEqual((g["title_has_number"], g["title_first_person"], g["has_cover"], g["ai_declared"]), (0, 0, 0, 0))

    def test_body_features(self):
        md = ("## What I Built\n\nSome words here.\n\n```js\n# not a heading\nconst a = 1;\n```\n\n"
              "![shot](https://x/y.png)\n\n{% github owner/repo %}\n\n{% embed https://youtu.be/abc %}\n\n"
              "| a | b |\n|---|---|\n| 1 | 2 |\n\n### Demo\n")
        f = job.body_features(md)
        self.assertEqual(f["headings"], 2)
        self.assertEqual(f["code_blocks"], 1)
        self.assertEqual(f["images"], 1)
        self.assertEqual(f["embeds"], 2)
        self.assertEqual(f["has_video"], 1)
        self.assertEqual(f["has_github_embed"], 1)
        self.assertEqual(f["has_table"], 1)
        self.assertNotIn("const", md.split("```")[0])
        self.assertEqual(job.body_features(None)["words"], 0)

    def test_percentile_vs(self):
        self.assertEqual(job.percentile_vs(5, [1, 2, 3, 4]), 1.0)
        self.assertEqual(job.percentile_vs(0, [1, 2, 3, 4]), 0.0)
        self.assertEqual(job.percentile_vs(2, [1, 2, 3, 4]), 0.375)
        self.assertIsNone(job.percentile_vs(1, []))


class TestAnalyse(unittest.TestCase):
    def rows(self):
        rows = []
        for cid in (1, 2):
            for i in range(10):
                r = {"challenge_id": cid, "article_id": cid * 100 + i, "is_winner": 0, "has_body": int(i < 6),
                     "ai_level": "some_ai" if i < 3 else "not_disclosed"}
                for f in job.CONT_META + job.CONT_BODY:
                    r[f] = i
                for f in job.BIN_META + job.BIN_BODY:
                    r[f] = int(i < 5)
                r["ai_declared"] = int(i < 3)
                rows.append(r)
            w = {"challenge_id": cid, "article_id": cid * 100 + 99, "is_winner": 1, "has_body": 1,
                 "ai_level": "not_disclosed"}
            for f in job.CONT_META + job.CONT_BODY:
                w[f] = 100
            for f in job.BIN_META + job.BIN_BODY:
                w[f] = 1
            w["ai_declared"] = 0
            rows.append(w)
        return rows

    def test_analyse(self):
        res = job.analyse(self.rows())
        rt = res["continuous"]["reading_time"]
        self.assertEqual(rt["winners"], 2)
        self.assertEqual(rt["mean_percentile"], 1.0)
        self.assertEqual(res["continuous"]["words"]["winners"], 2)
        self.assertIn("note", res["continuous"]["reactions_now"])
        cover = res["binary"]["has_cover"]
        self.assertEqual((cover["winners"], cover["winners_with"], cover["expected_if_random"]), (2, 2, 1.0))
        ai = res["binary"]["ai_declared"]
        self.assertEqual((ai["winners"], ai["winners_with"]), (2, 0))
        self.assertEqual(ai["expected_if_random"], 0.6)
        self.assertEqual(res["ai_levels"]["some_ai"]["winners_at_level"], 0)
        self.assertEqual(res["ai_levels"]["not_disclosed"]["winners_at_level"], 2)
        self.assertEqual(res["challenges_with_disclosure_field"], 2)
        text = job.report(dict(res, meta={"generated": "now", "challenges_used": 2, "since": "2025-01-01",
                                          "winners": 2, "entries": 20}))
        self.assertIn("| reading_time | 2 | 1.00 |", text)
        self.assertIn("| some_ai | 0 of 2 |", text)


if __name__ == "__main__":
    unittest.main()
