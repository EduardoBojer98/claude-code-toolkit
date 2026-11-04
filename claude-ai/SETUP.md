# claude.ai setup (web and desktop app)

What to paste where, so claude.ai works like Claude Code: same standards, short answers, little waste.
Nothing here is applied automatically. Menu names were checked against support.claude.com on 2026-11-04;
if a label moved, search the Settings page for the bold word.

## 1. Personal preferences (every chat)

**Settings → General → "What personal preferences should Claude consider in responses?"** Paste:

```text
I'm a full-stack web developer (WordPress with ACF/SCF and Elementor, WooCommerce, Shopify Liquid,
nopCommerce, React + Vite + TypeScript + Tailwind, plain HTML/CSS/JS). I work on Linux (CachyOS, fish).
- Answer first, then the reasoning only if it matters. Plain English, short paragraphs, no filler.
- Code: smallest change that works, match the existing project style, no new dependency without a reason.
- Never invent APIs, options or versions; say when you are unsure and check docs (Context7) first.
- For web work, follow my web-dev-standards skill (accessibility, performance, security floors).
- Don't claim something works unless it was run or checked.
```

Why: preferences load into every chat, so they hold only what applies to all of them (about 120 tokens).
Stack detail lives in the `web-dev-standards` skill, which loads only when a web task needs it.

## 2. Projects (one per client or per long-running job)

**Projects → New project**, then **Set project instructions** (top right). Paste and fill in:

```text
Client: <name>. Site: <URL>. Stack: <WordPress + Elementor | Shopify theme <name> | React + Vite | …>.
Versions: <PHP / WP / theme / Node>. Brand: <colours, fonts, tone in one line>.
Rules: <don't touch the parent theme / checkout / …>. Editors: <who edits content and how skilled>.
Done means: works at 375/768/1280, WCAG 2.2 AA, no console errors, security-scan clean before deploy.
```

- **Knowledge:** add only files you'll reference often (style guide, sitemap, a key template). Remove
  them when the job ends: knowledge counts against every chat in the project, and large knowledge
  switches the project to retrieval (support.claude.com/en/articles/9519177).
- One project per client keeps memory and files from mixing between clients.

## 3. Memory

**Settings → Your Claude → Memory** (support.claude.com/en/articles/11817273):
- Keep **memory on**; it saves you repeating your stack.
- Each project has its own memory. For client projects turn **off "Use account memory"** in the
  project so one client's details never appear in another's chats.
- Use **incognito** chats for anything with client data you don't want remembered.
- Once a month: open the memory summary and delete stale facts (old versions, finished clients).

## 4. Styles

Use the built-in **Concise** style (style menu under the message box) for quick questions and code
fixes; **Normal** for planning and explanations. No custom style needed: your preferences already set tone.

## 5. Skills (Settings → Capabilities → Skills; some accounts show "Features")

| Skill | Version | Upload |
|---|---|---|
| `web-dev-standards` | 2.4 | zip `skills/web-dev-standards` **with** its `references/` folder |
| `toolkit-maintainer` | 1.4 | zip `skills/toolkit-maintainer` |

```bash
cd ~/Documents/projects/claude-setup/skills
zip -r ~/web-dev-standards.zip web-dev-standards
zip -r ~/toolkit-maintainer.zip toolkit-maintainer
```

Upload each zip (**Upload skill**), replacing the old version (the account had 2.1 and 1.2 on 2026-11-01).
Or, in a claude.ai chat, paste the full `SKILL.md` and say *"save this as my web-dev-standards skill through a
skill card"*; for web-dev-standards the zip is better because the card alone would drop `references/`.

Leave the built-in `frontend-design` skill on: it is the design skill on claude.ai (Impeccable is used
in Claude Code only).

## 6. Writing a good request (both apps)

1. **What and where:** "Add a sticky header to `header.php` and `assets/css/header.css`", not "improve the header".
2. **What done looks like:** "no layout shift, works at 375px, keyboard reachable".
3. **Constraints:** "no new plugin", "keep the Elementor widget editable".
4. **One task per chat.** New topic → new chat (claude.ai) or `/clear` (Claude Code). Long chats re-send everything each turn.
5. Paste the exact error or a screenshot instead of describing it.
6. Turn off web search and extended thinking for simple questions; turn them on for research and hard bugs.
