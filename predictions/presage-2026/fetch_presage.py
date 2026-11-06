# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Download the exact code that ranked the Kaggle forecast, pinned to one commit, for the Presage forecast.

Run inside the sandbox: python fetch_presage.py  (needs network). Files land in the current folder.
Every file comes from commit 71219853021f4dc7abc42dc8ab4ef93a2f90e7d7 of munimtechnologies/devchallenge-study
(2026-11-06 12:47:30 UTC), the commit that scored the Kaggle forecast. Nothing later in the repo can change
what the Presage snapshot runs. Made by MV2 of Munim, Inc., with AI agents working in his name.
"""
import sys
import urllib.request

SHA = "71219853021f4dc7abc42dc8ab4ef93a2f90e7d7"
BASE = "https://raw.githubusercontent.com/munimtechnologies/devchallenge-study/" + SHA + "/"
FILES = {
    "forecast_oos.py": "forecast_oos.py",
    "test_forecast_oos.py": "test_forecast_oos.py",
    "hf26.py": "hf26.py",
    "test_hf26.py": "test_hf26.py",
    "oos.py": "oos.py",
    "test_oos.py": "test_oos.py",
    "links.py": "links.py",
    "challenges.json": "data/challenges.json",
    "model_week2.json": "predictions/2026-10-19/model.json",
}


def get(remote):
    req = urllib.request.Request(BASE + remote,
                                 headers={"User-Agent": "mv2-devchallenge-study/0.9 (MV2 of Munim, Inc.)"})
    return urllib.request.urlopen(req, timeout=60).read()


def main():
    for local, remote in FILES.items():
        try:
            data = get(remote)
        except Exception as exc:  # stop: a ranking made with a partial download would not be the registered one
            print("FAILED", remote, exc)
            return 1
        with open(local, "wb") as fh:
            fh.write(data)
        print("ok", local, len(data), "bytes")
    print("pinned to", SHA)
    return 0


if __name__ == "__main__":
    sys.exit(main())
