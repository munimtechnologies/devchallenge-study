"""Download the committed hf26.py and its tests, so the job ranks with exactly what is public.

Run inside the sandbox: python fetch.py  (needs network). Files land next to this script.
"""
import sys
import urllib.request

BASE = "https://raw.githubusercontent.com/munimtechnologies/devchallenge-study/main/"
FILES = {
    "hf26.py": "hf26.py",
    "test_hf26.py": "test_hf26.py",
}

for local, remote in FILES.items():
    req = urllib.request.Request(BASE + remote, headers={"User-Agent": "mv2-devchallenge-study/0.3 (MV2 of Munim, Inc.)"})
    try:
        data = urllib.request.urlopen(req, timeout=60).read()
    except Exception as exc:  # report and stop: ranking with a partial download would be wrong
        print("FAILED", remote, exc)
        sys.exit(1)
    with open(local, "wb") as fh:
        fh.write(data)
    print("ok", local, len(data), "bytes")
