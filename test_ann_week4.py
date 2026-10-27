# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Week-4 (Ghost in the Machine) winners posts are recognised by theme."""
import unittest

import hf26


class AnnWeek4Tests(unittest.TestCase):
    def test_week4_winners_title_by_theme(self):
        t = "Congrats to the Hacktoberfest Open-Source AI Challenge: Ghost in the Machine Winners!"
        self.assertEqual(hf26.announcement_round(t), "week4")

    def test_week4_winners_title_by_number(self):
        t = "Congrats to the Hacktoberfest Open-Source AI Challenge Week 4: Ghost in the Machine Winners!"
        self.assertEqual(hf26.announcement_round(t), "week4")

    def test_week4_launch_post_is_not_an_announcement(self):
        t = ("Join the Hacktoberfest Open-Source AI Challenge: Ghost in the Machine! "
             "$2,850 in Prizes Across 21 Winners.")
        self.assertIsNone(hf26.announcement_round(t))

    def test_earlier_rounds_unchanged(self):
        t2 = "Congrats to the Hacktoberfest Open-Source AI Challenge Week 2: Side Hustle Winners!"
        t3 = "Congrats to the Hacktoberfest Open-Source AI Challenge: Slow and Steady Winners!"
        self.assertEqual(hf26.announcement_round(t2), "week2")
        self.assertEqual(hf26.announcement_round(t3), "week3")


if __name__ == "__main__":
    unittest.main()
