# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Read dev.to post links from a winners announcement, including usernames that contain a hyphen.

hf26.py's LINK_RE and LIQUID_RE (and job.py's LINK_RE, which built data/posts.csv) accept only letters,
digits and underscores in the username, so a link such as https://dev.to/jo-ann/post-1abc is skipped
without a trace (one Sanity Challenge winner was). Found 2026-10-24; see ERRATUM_LINKS.md.

This module is the corrected reader. Everything else is exactly hf26.extract_links: the same skip list,
a slug must contain "-", links come out in order of first appearance, de-duplicated case-insensitively.
With no hyphenated username in the text it returns exactly what hf26.extract_links returns.
Standard library only, so its tests run without hf26.py. MV2 of Munim, Inc.; made with AI agents.
"""
import re

VERSION = "0.1.0"
USER = r"([A-Za-z0-9_][A-Za-z0-9_-]*)"
SLUG = r"([A-Za-z0-9][A-Za-z0-9_-]*)"
LINK_RE = re.compile(r"https?://dev\.to/" + USER + "/" + SLUG)
LIQUID_RE = re.compile(r"\{%\s*(?:link|embed)\s+(?:https?://dev\.to/)?" + USER + "/" + SLUG + r"\s*%\}")
# Same as hf26.SKIP_USERS.
SKIP_USERS = {
    "devteam", "challenges", "page", "t", "settings", "enter", "search", "api",
    "top", "latest", "videos", "listings", "badge", "badges", "pod", "help",
    "s", "dashboard", "new", "mlh-hackathon", "admin", "sponsors", "about",
}


def extract_links(*texts):
    seen, out = set(), []
    for text in texts:
        if not text:
            continue
        for rx in (LINK_RE, LIQUID_RE):
            for user, slug in rx.findall(text):
                if user.lower() in SKIP_USERS or "-" not in slug:
                    continue
                key = (user.lower(), slug.lower())
                if key in seen:
                    continue
                seen.add(key)
                out.append((user, slug))
    return out


def embedded_keys(markdown):
    """(user, slug) of every post shown as a card ({% embed %} or {% link %}), lower-cased."""
    return {(u.lower(), s.lower()) for u, s in LIQUID_RE.findall(markdown or "")}


def missed_by_old_reader(*texts):
    """Links this reader finds that hf26.extract_links does not: exactly those with a hyphen in the username."""
    return [(u, s) for u, s in extract_links(*texts) if "-" in u]
