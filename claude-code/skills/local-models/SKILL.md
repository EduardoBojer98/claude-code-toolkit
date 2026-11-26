---
name: local-models
description: Check for newer local Ollama models that beat the ones local-llm uses now (general, code, write roles) on this machine's GPU, benchmark them with local-llm-bench, switch the roles to the winners and update the docs. Free, local only, no paid or cloud models. Use when the user types /local-models or asks to check, update or upgrade the local models.
---

# Local models check

Goal: each `local-llm` role (`general`, `code`, `write`) runs the best local model that fits this machine.
Better means: passes that role in `local-llm-bench`, and either the current model fails it, or it is at least
20% faster (tok/s), or equal speed and fits the GPU fully where the current one doesn't. A tie keeps the current
model. Never a `:cloud` model, never anything paid.

## 1. Current state
```bash
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader; free -g | sed -n 2p
ollama list
grep -A4 'case "$MODEL"' ~/Documents/projects/claude-setup/claude-code/bin/local-llm
```
Budget: a model's download size should be at most VRAM minus ~0.8 GB to fit fully at 16k context; up to
VRAM + 1.5 GB is allowed if it splits with the CPU. Anything bigger is out.

## 2. Find candidates (max 4 per run)
Check ollama.com/library (newest first) and the Ollama blog for models released since the current ones. Keep
only: local weights, a tag inside the budget, tool or instruct capable, an open licence that allows commercial
use (client work). For each, note the exact tag, size, release date and source URL. Include at least one
coding-tuned model. No candidates worth testing → report "nothing better" with what you checked, and stop.

## 3. Benchmark
Pull the candidates (`ollama pull <tag>`, tags from the library page only), then run current and candidates
together so the numbers compare:
```bash
local-llm-bench <current general> <current code> <current write> <candidate…> | column -t -s $'\t'
```
A model that fails to load or errors is out. Run a close call (within 20%) a second time.

## 4. Switch roles
For each role with a better model, edit only the `case "$MODEL"` aliases in
`claude-code/bin/local-llm`. Then update:
- `README.md` §5 model table (model, role, tok/s, GPU fit, size, date tested).
- `claude-code/CLAUDE.md` only if a role's purpose changes (normally it doesn't).

Check each role answers:
```bash
for r in general code write; do echo hi | local-llm -m "$r" "Reply OK"; done
bash ~/Documents/projects/claude-setup/scripts/test.sh 2>&1 | local-llm "PASS or FAIL, then failing test names"
```

## 5. Clean up
- `ollama rm` candidates pulled in this run that lost.
- A model that was in use before and got replaced: ask the user before removing it (Alpaca may use it).

## 6. Report
- **Result**: per role: kept `<model>` / switched `<old>` → `<new>` (tok/s old → new, check results).
- **Bench table** as printed.
- **Checked**: sources and dates; candidates skipped and why (too big, licence, cloud only).
- **Changed**: files. Commit with `feat(local-llm): …` or `chore(local-llm): …` only if the user asked; push only
  if asked.
