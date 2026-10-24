# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""The frozen score_round.py, run with the corrected link reader (see ERRATUM_LINKS.md).

Nothing in score_round.py changes. For the length of this run, hf26.extract_links is replaced by
links.extract_links (usernames may contain a hyphen); score_round.main then runs with the same arguments.
Its output is the second count ERRATUM_LINKS.md fixes next to the frozen scorer's, for weeks 3 and 4:
    python score_round_links.py --round week3 --predictions <ranking> --out score_week3_links.json --md SCORE_week3_links.md
MV2 of Munim, Inc.; made with AI agents.
"""
import sys

import hf26
import links
import score_round


def use_corrected_reader():
    # score_round looks hf26.extract_links up at call time, so swapping the attribute is enough.
    hf26.extract_links = links.extract_links


if __name__ == "__main__":
    use_corrected_reader()
    print(f"score_round_links: hf26.extract_links -> links.extract_links {links.VERSION}", flush=True)
    sys.exit(score_round.main())
