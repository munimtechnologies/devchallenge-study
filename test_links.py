# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
import re
import unittest

import links

# hf26.py 0.6.x's readers, copied here so the comparison runs without hf26.py.
OLD_LINK_RE = re.compile(r"https?://dev\.to/([A-Za-z0-9_]+)/([A-Za-z0-9][A-Za-z0-9_-]*)")
OLD_LIQUID_RE = re.compile(
    r"\{%\s*(?:link|embed)\s+(?:https?://dev\.to/)?([A-Za-z0-9_]+)/([A-Za-z0-9][A-Za-z0-9_-]*)\s*%\}")


def old_extract(*texts):
    seen, out = set(), []
    for text in texts:
        if not text:
            continue
        for rx in (OLD_LINK_RE, OLD_LIQUID_RE):
            for user, slug in rx.findall(text):
                if user.lower() in links.SKIP_USERS or "-" not in slug:
                    continue
                key = (user.lower(), slug.lower())
                if key in seen:
                    continue
                seen.add(key)
                out.append((user, slug))
    return out


# Shaped like the Sanity Challenge winners post (2026-10-22): two inline links, then cards.
SANITY_MD = (
    "Thanks to everyone who entered the [Sanity Challenge](https://dev.to/devteam/join-the-sanity-challenge-514m)!\n"
    "Narrowing this field down was tough: see [this one](https://dev.to/alice/drum-bun-2d0g) "
    "and [that one](https://dev.to/bob_b/faux-pas-atlas-4b6n).\n\n"
    "## Path One Winners\n{% embed https://dev.to/carol/clockwrit-5ee3 %}\n"
    "## Path Two Winners\n{% embed https://dev.to/jo-ann/post-1abc %}\n"
    "{% embed https://dev.to/dave/a-wine-cellar-4i55 %}\n"
    "## What's Next?\n{% embed https://dev.to/events/challenges/hacktoberfest-week4-2026-10-26 %}\n"
    "Prizes include [DEV++](https://dev.to/++).\n"
)


class Reader(unittest.TestCase):
    def test_hyphenated_username_is_read(self):
        self.assertEqual(links.extract_links("[x](https://dev.to/jo-ann/post-1abc)"), [("jo-ann", "post-1abc")])
        self.assertEqual(old_extract("[x](https://dev.to/jo-ann/post-1abc)"), [])

    def test_liquid_with_and_without_domain(self):
        md = "{% embed https://dev.to/jo-ann/post-1abc %}\n{% link some-one/post-1 %}"
        self.assertEqual(links.extract_links(md), [("jo-ann", "post-1abc"), ("some-one", "post-1")])

    def test_announcement_shape(self):
        got = links.extract_links(SANITY_MD)
        self.assertEqual(got, [("alice", "drum-bun-2d0g"), ("bob_b", "faux-pas-atlas-4b6n"),
                               ("carol", "clockwrit-5ee3"), ("jo-ann", "post-1abc"), ("dave", "a-wine-cellar-4i55")])
        self.assertEqual(len(old_extract(SANITY_MD)), 4)
        self.assertEqual(links.missed_by_old_reader(SANITY_MD), [("jo-ann", "post-1abc")])

    def test_cards(self):
        # The events card (three path parts) is neither a card key nor a winner link.
        self.assertEqual(links.embedded_keys(SANITY_MD),
                         {("carol", "clockwrit-5ee3"), ("jo-ann", "post-1abc"), ("dave", "a-wine-cellar-4i55")})
        self.assertNotIn(("events", "challenges"), links.extract_links(SANITY_MD))

    def test_skips_like_hf26(self):
        md = ("https://dev.to/devteam/a-b https://dev.to/t/some-tag https://dev.to/mlh-hackathon/x-y "
              "https://dev.to/alice/nohyphen https://dev.to/challenges/sanity-2026")
        self.assertEqual(links.extract_links(md), [])

    def test_dedup_across_html_and_markdown(self):
        html = '<a href="https://dev.to/Jo-Ann/post-1abc">x</a>'
        md = "{% embed https://dev.to/jo-ann/post-1abc %}"
        self.assertEqual(links.extract_links(html, md), [("Jo-Ann", "post-1abc")])

    def test_same_as_old_reader_without_hyphenated_users(self):
        md = SANITY_MD.replace("jo-ann", "joann")
        html = '<a href="https://dev.to/carol/clockwrit-5ee3">c</a> <a href="/alice">@alice</a>'
        self.assertEqual(links.extract_links(html, md), old_extract(html, md))
        self.assertEqual(links.missed_by_old_reader(html, md), [])

    def test_old_reader_misses_only_hyphenated(self):
        new = links.extract_links(SANITY_MD)
        old = old_extract(SANITY_MD)
        self.assertEqual([x for x in new if x not in old], links.missed_by_old_reader(SANITY_MD))


if __name__ == "__main__":
    unittest.main()
