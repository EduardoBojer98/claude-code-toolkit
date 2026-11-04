import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { AgentRun, Stats } from '../types'

const PANE = 'session-dashboard'
const TITLE = 'Session'
const ACCENT = '#d97757'
const GOOD = '#5fbf8f'
const WARN = '#e0b050'
const BAD = '#e06c75'
const FILE_TOOLS = ['Edit', 'Write', 'MultiEdit', 'NotebookEdit']
const MAX_FILES = 200
const MAX_AGENTS = 60

const blank = (): Stats => ({
  startedAt: 0,
  requests: 0,
  subagentRequests: 0,
  input: 0,
  output: 0,
  cacheRead: 0,
  cacheWrite: 0,
  costUsd: 0,
  model: '',
  contextTokens: 0,
  contextMax: 0,
  toolCalls: 0,
  toolErrors: 0,
  tools: {},
  files: [],
  isBudgetWarned: false,
  agents: {},
  agentOrder: [],
  skills: {},
})

// Change the tag when Stats' fields change: a value stored by an older version
// is then read as blank instead of half-matching.
const stats = atom({ plugin: 'session-dashboard', key: 'stats' } as const, blank(), { shape: 'stats-2' })

// ---------------------------------------------------------------------------
// Cost estimate. USD per million tokens: input, output, cache read, cache write.
// Adapted from savvy-progress (MIT, johnnyvizz), list prices as of 2026-10-10.
// An estimate from token counts, not a bill; on a subscription it is what the
// same usage would cost on the API.

type Price = [number, number, number, number]
type Usage = {
  input_tokens: number
  output_tokens: number
  cache_read_input_tokens: number
  cache_creation_input_tokens: number
}

const PRICES: [RegExp, Price][] = [
  [/(fable|mythos)-5-1/, [10, 50, 0.25, 20]],
  [/fable|mythos/, [10, 50, 1, 20]],
  [/opus-5-5/, [4, 20, 0.2, 8]],
  [/opus/, [5, 25, 0.5, 10]],
  [/sonnet-5-5/, [2, 10, 0.1, 4]],
  [/sonnet-5/, [2, 10, 0.2, 4]],
  [/sonnet/, [3, 15, 0.3, 6]],
  [/haiku-5-5/, [0.1, 0.5, 0.01, 0.2]],
  [/haiku/, [1, 5, 0.1, 2]],
]
const HAIKU_LONG: Price = [0.5, 2.5, 0.05, 1]

const promptOf = (u: Usage): number =>
  (u.input_tokens || 0) + (u.cache_read_input_tokens || 0) + (u.cache_creation_input_tokens || 0)

function costOf(model: string, u: Usage): number {
  const id = model.toLowerCase()
  const price =
    promptOf(u) > 100_000 && /haiku-5-5/.test(id)
      ? HAIKU_LONG
      : (PRICES.find(([re]) => re.test(id))?.[1] ?? [4, 20, 0.2, 8])
  const [i, o, r, w] = price
  return (
    ((u.input_tokens || 0) * i +
      (u.output_tokens || 0) * o +
      (u.cache_read_input_tokens || 0) * r +
      (u.cache_creation_input_tokens || 0) * w) /
    1e6
  )
}

const windowOf = (model: string): number => (/haiku-4|claude-3/i.test(model) ? 200_000 : 1_000_000)

// ---------------------------------------------------------------------------
// Formatting

const money = (usd: number): string => (usd < 10 ? `$${usd.toFixed(2)}` : `$${usd.toFixed(1)}`)

function count(n: number): string {
  if (n >= 1e6) return `${(n / 1e6).toFixed(n >= 1e7 ? 0 : 1)}M`
  if (n >= 1e3) return `${(n / 1e3).toFixed(n >= 1e4 ? 0 : 1)}k`
  return String(n)
}

function duration(ms: number): string {
  const s = Math.max(0, Math.floor(ms / 1000))
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  if (h > 0) return `${h}h ${m}m`
  if (m > 0) return `${m}m ${s % 60}s`
  return `${s}s`
}

const shortModel = (model: string): string => model.replace(/^claude-/, '').replace(/-\d{8}$/, '')

// Last two path segments: enough to tell files apart, short enough for a row.
function shortPath(path: string): string {
  const parts = path.split(/[\\/]/).filter(Boolean)
  return parts.length <= 2 ? path : `…/${parts.slice(-2).join('/')}`
}

const tokensOf = (s: Stats): number => s.input + s.output + s.cacheRead + s.cacheWrite
const contextPct = (s: Stats): number => (s.contextMax > 0 ? Math.round((s.contextTokens / s.contextMax) * 100) : 0)
const contextColor = (pct: number): string => (pct >= 80 ? BAD : pct >= 50 ? WARN : GOOD)
// Share of prompt tokens served from the prompt cache: high is cheap and fast.
const cacheHitPct = (s: Stats): number => {
  const prompt = s.input + s.cacheRead + s.cacheWrite
  return prompt > 0 ? Math.round((s.cacheRead / prompt) * 100) : 0
}

function bar(pct: number, width: number): string {
  const full = Math.round((Math.min(100, Math.max(0, pct)) / 100) * width)
  return '█'.repeat(full) + '░'.repeat(width - full)
}

// Model family for a row: "haiku", "sonnet", "opus", "fable", or the id as given.
const family = (model: string): string => /haiku|sonnet|opus|fable|mythos/i.exec(model)?.[0].toLowerCase() ?? shortModel(model)

const agentLabel = (s: Stats, id: string): string => (s.agents[id] ? `${s.agents[id].type}#${id.slice(-4)}` : `agent#${id.slice(-4)}`)

const STATUS_MARK: Record<AgentRun['status'], [string, string]> = {
  running: ['●', WARN],
  done: ['✓', GOOD],
  failed: ['✗', BAD],
  aborted: ['■', BAD],
}

const agentCost = (s: Stats): number => s.agentOrder.reduce((sum, id) => sum + (s.agents[id]?.costUsd ?? 0), 0)
const runningCount = (s: Stats): number => s.agentOrder.filter(id => s.agents[id]?.status === 'running').length

// Agents in start order, each followed by the agents it spawned, with their depth.
function agentTree(s: Stats): [string, number][] {
  const out: [string, number][] = []
  const walk = (parent: string, depth: number) => {
    for (const id of s.agentOrder) {
      if ((s.agents[id]?.parent ?? '') === parent) {
        out.push([id, depth])
        walk(id, depth + 1)
      }
    }
  }
  walk('', 0)
  // Agents whose parent was dropped from the list still show, at the top level.
  for (const id of s.agentOrder) if (!out.some(([o]) => o === id)) out.push([id, 0])
  return out
}

function addAgent(s: Stats, id: string, run: AgentRun): Stats {
  const order = [...s.agentOrder.filter(o => o !== id), id]
  const dropped = order.length > MAX_AGENTS ? order.slice(0, order.length - MAX_AGENTS) : []
  const agents = { ...s.agents, [id]: run }
  for (const d of dropped) delete agents[d]
  return { ...s, agents, agentOrder: order.slice(-MAX_AGENTS) }
}

const patchAgent = (s: Stats, id: string | undefined, fn: (a: AgentRun) => AgentRun): Stats =>
  id && s.agents[id] ? { ...s, agents: { ...s.agents, [id]: fn(s.agents[id]) } } : s

// ---------------------------------------------------------------------------

async function togglePane($: EngineInterface): Promise<boolean> {
  const isOpen = (await $.ui.panes()).some(p => p.id === PANE)
  if (isOpen) {
    await $.ui.close({ id: PANE })
    return false
  }
  await openPane($)
  return true
}

async function openPane($: EngineInterface): Promise<void> {
  await $.ui.open({ id: PANE, title: TITLE })
}

// Draws only inside its own /dash pane: no band above the prompt and no status line, both of which
// other plugins (ponytail) own. The only thing shown outside the pane is the opt-in cost toast.
export const register: Register = (on, options) => {
  const budget = Number(options.budget)
  const hasBudget = Number.isFinite(budget) && budget > 0
  // Skill tool calls waiting for their skill.prompt: skill name -> caller loop ('' = main).
  const skillCallers = new Map<string, string>()

  on('session.start', async ($, e, next) => {
    const started = await next(e)
    const at = await $.clock.now()
    // A reload keeps the stored stats; only a fresh session starts the clock.
    await update($, stats, s => (s.startedAt > 0 ? s : { ...blank(), startedAt: at }))

    await $.command.register({
      name: 'dash',
      description: 'Show or hide the session dashboard (agents, skills, tokens, cost, time, tools, files). "/dash reset" starts the counts over',
    })
    return started
  })

  on('command.run', { command: 'dash' }, async ($, e) => {
    const arg = (e.args ?? '').trim().toLowerCase()
    if (arg === 'reset') {
      const at = await $.clock.now()
      await update($, stats, () => ({ ...blank(), startedAt: at }))
      return { text: 'Session dashboard reset.' }
    }
    if (arg === 'open') {
      await openPane($)
      return { text: 'Session dashboard opened.' }
    }
    const isOpen = await togglePane($)
    return { text: isOpen ? 'Session dashboard opened.' : 'Session dashboard closed.' }
  })

  // Every model request, main loop and subagents: tokens, cost, context.
  on('turn.step', async function* ($, e, next) {
    const result = yield* next(e)
    const usage = result.usage
    if (!usage) return result

    const model = usage.model || e.model
    const isMain = !e.agentId
    const stepCost = costOf(model, usage)
    let crossed = false
    await update($, stats, prev => {
      const s = patchAgent(prev, e.agentId, a => ({
        ...a,
        model: model || a.model,
        requests: a.requests + 1,
        tokens: a.tokens + promptOf(usage) + (usage.output_tokens || 0),
        costUsd: a.costUsd + stepCost,
      }))
      const costUsd = s.costUsd + stepCost
      crossed = hasBudget && !s.isBudgetWarned && costUsd >= budget
      return {
        ...s,
        requests: s.requests + 1,
        subagentRequests: s.subagentRequests + (isMain ? 0 : 1),
        input: s.input + (usage.input_tokens || 0),
        output: s.output + (usage.output_tokens || 0),
        cacheRead: s.cacheRead + (usage.cache_read_input_tokens || 0),
        cacheWrite: s.cacheWrite + (usage.cache_creation_input_tokens || 0),
        costUsd,
        isBudgetWarned: s.isBudgetWarned || crossed,
        ...(isMain
          ? {
              model,
              contextTokens: promptOf(usage) + (usage.output_tokens || 0),
              contextMax: windowOf(model),
            }
          : {}),
      }
    })
    if (crossed) $.ui.toast(`Session cost passed $${budget} (estimate)`)
    return result
  })

  on('tool.call', async ($, e, next) => {
    const args = e as unknown as Record<string, unknown>
    // The Skill tool loads its skill inside the call: note who asked, for skill.prompt.
    if (e.tool === 'Skill' && typeof args.skill === 'string') skillCallers.set(args.skill, e.agentId ?? '')
    const ran = await next(e)
    try {
      const raw = args.file_path ?? args.notebook_path
      const path = FILE_TOOLS.includes(e.tool) && typeof raw === 'string' ? raw : ''
      const isError = 'deny' in ran || ('isError' in ran && (ran as { isError?: unknown }).isError === true)

      await update($, stats, prev => {
        const s = patchAgent(prev, e.agentId, a => ({
          ...a,
          toolCalls: a.toolCalls + 1,
          tools: { ...a.tools, [e.tool]: (a.tools[e.tool] ?? 0) + 1 },
        }))
        return {
          ...s,
          toolCalls: s.toolCalls + 1,
          toolErrors: s.toolErrors + (isError ? 1 : 0),
          tools: { ...s.tools, [e.tool]: (s.tools[e.tool] ?? 0) + 1 },
          files: path && !isError ? [...s.files.filter(f => f !== path), path].slice(-MAX_FILES) : s.files,
        }
      })
    } catch {
      // Bookkeeping only: it never costs the tool its result.
    }
    return ran
  })

  // A subagent starts: its type, model and who spawned it.
  on('agent.spawn', async ($, e, next) => {
    const started = await next(e)
    if (started.deny !== undefined || !started.agentId) return started
    const id = started.agentId
    try {
      const at = await $.clock.now()
      await update($, stats, s =>
        addAgent(s, id, {
          type: e.subagentType,
          description: e.description,
          model: started.model || e.model || e.parentModel,
          parent: e.parentAgentId ?? '',
          status: 'running',
          isBackground: e.background,
          startedAt: at,
          durationMs: 0,
          requests: 0,
          tokens: 0,
          costUsd: 0,
          toolCalls: 0,
          tools: {},
          skills: [],
        }),
      )
    } catch {
      // Bookkeeping only.
    }
    return started
  })

  // A subagent's loop ends: how it ended and how long it took.
  on('turn.complete', async ($, e, next) => {
    const done = await next(e)
    if (e.agentId) {
      const status: AgentRun['status'] = e.isAborted ? 'aborted' : e.reason === 'answer' ? 'done' : 'failed'
      try {
        await update($, stats, s => patchAgent(s, e.agentId, a => ({ ...a, status, durationMs: e.durationMs })))
      } catch {
        // Bookkeeping only.
      }
    }
    return done
  })

  // A skill's text is loaded: by the main session, an agent, or you (slash command / preload).
  on('skill.prompt', async ($, e, next) => {
    const loaded = await next(e)
    const caller = skillCallers.get(e.skill)
    skillCallers.delete(e.skill)
    try {
      await update($, stats, prev => {
        const s = caller ? patchAgent(prev, caller, a => ({ ...a, skills: [...new Set([...a.skills, e.skill])] })) : prev
        const who = caller === undefined ? 'you' : caller === '' ? 'lead' : agentLabel(s, caller)
        const use = s.skills[e.skill] ?? { count: 0, source: e.pluginName ?? e.source, by: {} }
        return {
          ...s,
          skills: { ...s.skills, [e.skill]: { ...use, count: use.count + 1, by: { ...use.by, [who]: (use.by[who] ?? 0) + 1 } } },
        }
      })
    } catch {
      // Bookkeeping only.
    }
    return loaded
  })

  // ---- Panel ------------------------------------------------------------------

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Button, Text } = $.ui.resolve(e)
    const s = await read($, stats)
    // The pane redraws when the stats change; elapsed time is read then, so no timer is needed.
    const t = await $.clock.now().catch(() => s.startedAt)
    const pct = contextPct(s)
    const rows = e.viewport?.rows ?? 40
    const hit = cacheHitPct(s)

    const heading = (key: string, text: string) => (
      <Text key={key} color={ACCENT} weight="bold">
        {text}
      </Text>
    )
    const row = (key: string, label: string, value: string, color?: string) => (
      <Box key={key} flexDirection="row" justifyContent="space-between">
        <Text dimColor>{label}</Text>
        <Text color={color}>{value}</Text>
      </Box>
    )

    const topTools = Object.entries(s.tools)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 8)
    const tree = agentTree(s).slice(-12)
    const fileRoom = Math.max(3, rows - 40 - tree.length * 2 - Math.min(10, Object.keys(s.skills).length))
    const recentFiles = s.files.slice(-fileRoom).reverse()
    const subCost = agentCost(s)
    const skillRows = Object.entries(s.skills).sort((a, b) => b[1].count - a[1].count)
    const byModel: Record<string, number> = {}
    for (const id of s.agentOrder) {
      const a = s.agents[id]
      if (a) byModel[family(a.model)] = (byModel[family(a.model)] ?? 0) + 1
    }

    return (
      <Box flexDirection="column" gap={1} paddingX={1}>
        <Text dimColor>
          {s.model ? shortModel(s.model) : 'no model yet'} · {duration(t - s.startedAt)} · {s.requests} requests
          {s.subagentRequests ? ` (${s.subagentRequests} by agents)` : ''}
        </Text>

        <Box flexDirection="column">
          {heading('h-ctx', 'Context')}
          {s.contextMax > 0 ? (
            <Text color={contextColor(pct)}>
              {bar(pct, 20)} {pct}% · {count(s.contextTokens)} of {count(s.contextMax)}
            </Text>
          ) : (
            <Text dimColor>Shows after the first request.</Text>
          )}
          {pct >= 80 && <Text dimColor>Nearly full: /compact at a break, or /clear for a new task.</Text>}
        </Box>

        <Box flexDirection="column">
          {heading('h-cost', 'Cost (estimate)')}
          {row('cost', 'Total', money(s.costUsd), ACCENT)}
          {s.agentOrder.length > 0 &&
            row('agents-split', 'Lead / agents', `${money(Math.max(0, s.costUsd - subCost))} / ${money(subCost)}`)}
          {hasBudget && row('budget', 'Alert at', `$${budget}`, s.costUsd >= budget ? BAD : undefined)}
        </Box>

        <Box flexDirection="column">
          {heading('h-tokens', `Tokens · ${count(tokensOf(s))}`)}
          {row('in', 'Input', count(s.input))}
          {row('out', 'Output', count(s.output))}
          {row('cache', 'Cache read / write', `${count(s.cacheRead)} / ${count(s.cacheWrite)}`)}
          {row('hit', 'Cache hit', `${hit}%`, hit >= 70 ? GOOD : hit >= 40 ? WARN : undefined)}
        </Box>

        <Box flexDirection="column">
          {heading(
            'h-agents',
            `Agents · ${s.agentOrder.length}${runningCount(s) ? ` (${runningCount(s)} running)` : ''}`,
          )}
          {s.agentOrder.length === 0 && <Text dimColor>No subagents yet: the main session did everything.</Text>}
          {s.agentOrder.length > 0 &&
            row(
              'agents-models',
              'By model',
              Object.entries(byModel)
                .map(([m, n]) => `${m} ×${n}`)
                .join('  '),
            )}
          {tree.map(([id, depth]) => {
            const a = s.agents[id]
            if (!a) return null
            const [mark, color] = STATUS_MARK[a.status]
            const ran = a.status === 'running' ? t - a.startedAt : a.durationMs
            const top = Object.entries(a.tools)
              .sort((x, y) => y[1] - x[1])
              .slice(0, 3)
              .map(([n, c]) => `${n} ${c}`)
              .join(', ')
            const pad = '  '.repeat(depth)
            return (
              <Box key={`agent-${id}`} flexDirection="column">
                <Box flexDirection="row" justifyContent="space-between">
                  <Text>
                    {pad}
                    <Text color={color}>{mark}</Text> {a.type}
                    <Text dimColor> · {family(a.model)}</Text>
                    {a.isBackground ? <Text dimColor> · bg</Text> : null}
                  </Text>
                  <Text dimColor>
                    {duration(ran)} · {count(a.tokens)} tok · {money(a.costUsd)}
                  </Text>
                </Box>
                <Text dimColor>
                  {pad}  {a.description}
                  {a.toolCalls ? ` — ${a.toolCalls} tools${top ? `: ${top}` : ''}` : ''}
                  {a.skills.length ? ` — skills: ${a.skills.join(', ')}` : ''}
                </Text>
              </Box>
            )
          })}
          {s.agentOrder.length > tree.length && <Text dimColor>+{s.agentOrder.length - tree.length} earlier</Text>}
        </Box>

        <Box flexDirection="column">
          {heading('h-skills', `Skills · ${skillRows.length}`)}
          {skillRows.length === 0 && <Text dimColor>No skills loaded yet.</Text>}
          {skillRows.slice(0, 10).map(([name, use]) =>
            row(
              `skill-${name}`,
              name,
              `×${use.count} · ${Object.entries(use.by)
                .map(([who, n]) => (n > 1 ? `${who} ×${n}` : who))
                .join(', ')}`,
            ),
          )}
        </Box>

        <Box flexDirection="column">
          {heading('h-tools', `Tools · ${s.toolCalls}${s.toolErrors ? ` (${s.toolErrors} failed)` : ''}`)}
          {topTools.length === 0 && <Text dimColor>No tool calls yet.</Text>}
          {topTools.map(([name, n]) => row(`tool-${name}`, name, String(n)))}
        </Box>

        <Box flexDirection="column">
          {heading('h-files', `Files edited · ${s.files.length}`)}
          {recentFiles.length === 0 && <Text dimColor>None yet.</Text>}
          {recentFiles.map(f => (
            <Text key={`file-${f}`}>{shortPath(f)}</Text>
          ))}
          {s.files.length > recentFiles.length && <Text dimColor>+{s.files.length - recentFiles.length} more</Text>}
        </Box>

        <Box flexDirection="row">
          <Button
            key="reset"
            label="Reset counts"
            onPress={async () => {
              const at = await $.clock.now()
              await update($, stats, () => ({ ...blank(), startedAt: at }))
            }}
          />
        </Box>
      </Box>
    )
  })
}
