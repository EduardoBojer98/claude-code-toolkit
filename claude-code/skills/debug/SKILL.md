---
name: debug
description: Root-cause debugging workflow - reproduce, isolate, prove the cause, then make the smallest fix and a regression check. Use when something is broken, failing, erroring, slow or behaving unexpectedly (PHP/WordPress/Lando, Shopify Liquid, React/Vite, Node, CI).
---

# Debug

Goal: a fix for the proven cause, not a patch over a symptom.

## 1. Pin down the symptom
- Exact error text, where it shows (browser console, PHP log, CI step, terminal), and when it started.
- Expected vs actual. Smallest input or URL that triggers it.
- `git log --oneline -10` and `git diff` — did a recent change introduce it?

## 2. Reproduce
- Reproduce with one command or one request before touching code. If you can't, collect more
  evidence (logs, versions) instead of guessing.
- Stack-specific commands and log locations: [references/stack-diagnostics.md](references/stack-diagnostics.md).
  Read only the section for the stack in use.

## 3. Isolate
- Read the code path from the entry point to the failure (`path:line`), not the whole module.
- Form 1–3 hypotheses, each with a check that would disprove it. Run the cheapest check first.
- Bisect when the cause is unclear: recent commits (`git bisect`), plugins/apps (disable half),
  config (revert half), input (halve it).
- Delegate log/test noise to the `test-runner` agent; keep hypotheses here.

## 4. Fix
- State the cause in one sentence with evidence before editing.
- Smallest change at the cause. No unrelated cleanup.
- Add or update a test that fails without the fix when the project has tests; otherwise give a manual
  reproduction step that now passes.

## 5. Verify and report
- Re-run the reproduction and the nearest related tests/lint.
- Report: cause (with `path:line`), fix, verification run, and anything still unexplained.

Stop and ask when: the fix needs a data migration, touches production, or the cause is in a
third-party plugin/app/package (propose an override or upstream report instead of editing it).
