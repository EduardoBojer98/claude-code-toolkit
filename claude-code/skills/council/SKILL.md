---
name: council
description: Build a goal, then loop with a read-only review council (correctness, security, simplicity; Claude reviewers or free OmniRoute models via council-free) until every member approves. A Stop hook blocks finishing until the council approves or the loop is escalated. Use when the user types /council <goal> or asks for work to be reviewed by the council until approved.
---

# Council

You are the developer. Three read-only reviewers judge your work; you iterate until all three say APPROVE.
State lives in `.council/` at the git root. While `.council/status` is `running`, the
`council-gate.sh` Stop hook will not let you finish.

## 0. Start
In the git root (`git rev-parse --show-toplevel`):
```bash
mkdir -p .council && grep -qxF '.council/' .git/info/exclude || echo '.council/' >> .git/info/exclude
printf 'running\n' > .council/status; printf '0\n' > .council/round; rm -f .council/blocks
```
Write `.council/goal.md`: the goal in the user's words, the acceptance check (a command or observable
result), and what is out of scope. Ask the user only if the goal has no checkable outcome.

## 1. Build
Do the work under the normal rules (smallest diff, run the targeted check). Do not commit, push or
deploy until the council approves; the reviewers read the working tree.

## 2. Snapshot the change
```bash
{ git diff HEAD; git ls-files --others --exclude-standard | sed 's/^/UNTRACKED: /'; } > .council/diff.patch
echo $(( $(cat .council/round) + 1 )) > .council/round
```

## 3. Convene
Pick the members once, in round 1, and keep them for every round:

| Code | correctness | security | simplicity |
|---|---|---|---|
| Client code or client data (default when unsure) | `council-correctness` | `council-security` | `council-simplicity` |
| Own/personal code | `council-correctness` | `council-security` | `council-free` (lens `simplicity`) |
| Own code + `--free` in the request | `council-free` | `council-free` | `council-free` |

`council-free` runs on free OmniRoute models (no plan usage, but the providers may train on prompts),
so it never sees client code. A different model family also catches what Claude reviewers miss.
If `council-free` returns `VERDICT: UNAVAILABLE`, rerun that lens on the Claude member for the round.

Spawn the three in parallel (one message, three Agent calls). Brief each with only: "Round N. Review
`.council/diff.patch` against `.council/goal.md`." (for `council-free`, start with "Lens: <lens>.")
For round 2+, add the previous round's open items as `path:line — summary` so they can check the fixes.
Never send your own reasoning or argue for the change; reviewers judge the code alone.

Append each verdict to `.council/feedback.md` under `## Round N`.

## 4. Decide
- All three `VERDICT: APPROVE` → `printf 'approved\n' > .council/status`, run the acceptance check one last
  time, then report.
- Any `CHANGES` → verify each `blocking` item by reading the cited lines. Fix the real ones; for one you
  reject, write one line of why under the round in `feedback.md` and include it in the next brief.
  Nits: fix only if trivial. Go to step 2.
- Round 5 without approval, or the same blocking item survives two fixes → `printf 'escalated\n' >
  .council/status` and report the open items to the user for a decision.
- You need the user's answer to continue → `printf 'waiting-user\n' > .council/status`, ask, and set it
  back to `running` when you resume.

## 5. Report
- **Result**: approved in round N / escalated.
- **Changed**: `path` — one line each.
- **Check**: command → result.
- **Open**: rejected findings with the reason, nits left.
Leave `.council/` in place (it is git-excluded); the gate ignores `approved` and `escalated`.
