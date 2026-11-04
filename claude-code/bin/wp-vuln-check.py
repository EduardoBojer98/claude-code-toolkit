#!/usr/bin/env python3
"""Check installed WordPress plugins against wpvulnerability.net (free, no key).
Reads `wp plugin list --format=json` on stdin; only slugs and versions leave the machine.
  lando wp plugin list --format=json | python3 wp-vuln-check.py
Exit 1 when an installed version is affected."""
import json
import re
import sys
import urllib.request

API = "https://www.wpvulnerability.net/plugin/{}/"


def ver(v):
    return tuple(int(x) for x in re.findall(r"\d+", v or ""))


def affected(version, op):
    """True when `version` falls inside one advisory's operator range."""
    v = ver(version)
    lo, hi = op.get("min_version"), op.get("max_version")
    if lo and not (v > ver(lo) if op.get("min_operator") == "gt" else v >= ver(lo)):
        return False
    if hi and not (v <= ver(hi) if op.get("max_operator") == "le" else v < ver(hi)):
        return False
    return bool(lo or hi or op.get("unfixed") == "1")


def main():
    hits = 0
    for p in json.load(sys.stdin):
        slug, version = p.get("name"), p.get("version")
        if not slug or not version:
            continue
        try:
            with urllib.request.urlopen(API.format(slug), timeout=15) as r:
                data = json.load(r).get("data") or {}
        except Exception as e:  # premium/custom plugins are not in the database
            print(f"  ?  {slug} {version}: lookup failed ({e.__class__.__name__})")
            continue
        for vuln in data.get("vulnerability") or []:
            if affected(version, vuln.get("operator") or {}):
                hits += 1
                print(f"  !  {slug} {version}: {vuln.get('name')}")
    print(f"WordPress plugins: {hits} affected advisories")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
