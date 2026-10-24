import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { Stats } from '../types'

const PANE = 'session-dashboard'
const TITLE = 'Session'
const ACCENT = '#d97757'
const GOOD = '#5fbf8f'
const WARN = '#e0b050'
const BAD = '#e06c75'
const FILE_TOOLS = ['Edit', 'Write', 'MultiEdit', 'NotebookEdit']
const MAX_FILES = 200

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
})

// Change the tag when Stats' fields change: a value stored by an older version
// is then read as blank instead of half-matching.
const stats = atom({ plugin: 'session-dashboard', key: 'stats' } as const, blank(), { shape: 'stats-1' })
const now = atom({ plugin: 'session-dashboard', key: 'now' } as const, 0)

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

function bar(pct: number, width: number): string {
  const full = Math.round((Math.min(100, Math.max(0, pct)) / 100) * width)
  return '█'.repeat(full) + '░'.repeat(width - full)
}

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
  const at = await $.clock.now()
  await update($, now, () => at)
  await $.ui.open({ id: PANE, title: TITLE })
}

export const register: Register = (on, options) => {
  const showBand = options.band !== 'off'
  const budget = Number(options.budget)
  const hasBudget = Number.isFinite(budget) && budget > 0

  on('session.start', async ($, e, next) => {
    const started = await next(e)
    const at = await $.clock.now()
    // A reload keeps the stored stats; only a fresh session starts the clock.
    await update($, stats, s => (s.startedAt > 0 ? s : { ...blank(), startedAt: at }))
    await update($, now, () => at)

    await $.command.register({
      name: 'dash',
      description: 'Show or hide the session dashboard (tokens, cost, time, tools, files). "/dash reset" starts the counts over',
    })

    // Ticks the elapsed time; one cheap write a second.
    $.clock.every(1000, () => {
      void (async () => {
        const t = await $.clock.now()
        await update($, now, () => t)
      })()
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
    let crossed = false
    await update($, stats, s => {
      const costUsd = s.costUsd + costOf(model, usage)
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
    const ran = await next(e)
    try {
      const args = e as unknown as Record<string, unknown>
      const raw = args.file_path ?? args.notebook_path
      const path = FILE_TOOLS.includes(e.tool) && typeof raw === 'string' ? raw : ''
      const isError = 'deny' in ran || ('isError' in ran && (ran as { isError?: unknown }).isError === true)

      await update($, stats, s => ({
        ...s,
        toolCalls: s.toolCalls + 1,
        toolErrors: s.toolErrors + (isError ? 1 : 0),
        tools: { ...s.tools, [e.tool]: (s.tools[e.tool] ?? 0) + 1 },
        files: path && !isError ? [...s.files.filter(f => f !== path), path].slice(-MAX_FILES) : s.files,
      }))
    } catch {
      // Bookkeeping only: it never costs the tool its result.
    }
    return ran
  })

  // ---- Band above the prompt ------------------------------------------------

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    if (!showBand || e.props.hasSurvey) return next(e)
    const s = await read($, stats)
    if (s.requests === 0 && s.toolCalls === 0) return next(e)

    const t = await read($, now)
    const pct = contextPct(s)
    const { Box, Button, Text } = $.ui.resolve(e)
    const dot = <Text dimColor> · </Text>

    return (
      <Box flexDirection="row">
        <Text color={ACCENT}>◆ </Text>
        <Text weight="bold">{money(s.costUsd)}</Text>
        {dot}
        <Text>{count(tokensOf(s))} tok</Text>
        {dot}
        <Text>{duration(t - s.startedAt)}</Text>
        {dot}
        <Text>{s.toolCalls} tools</Text>
        {s.files.length > 0 && dot}
        {s.files.length > 0 && <Text>{s.files.length} files</Text>}
        {s.contextMax > 0 && dot}
        {s.contextMax > 0 && <Text color={contextColor(pct)}>ctx {pct}%</Text>}
        <Text> </Text>
        <Button key="open-dashboard" label="Dashboard" onPress={() => togglePane($)} />
      </Box>
    )
  })

  // ---- Panel ------------------------------------------------------------------

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Button, Text } = $.ui.resolve(e)
    const s = await read($, stats)
    const t = await read($, now)
    const pct = contextPct(s)
    const rows = e.viewport?.rows ?? 40

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
    const fileRoom = Math.max(3, rows - 34)
    const recentFiles = s.files.slice(-fileRoom).reverse()

    return (
      <Box flexDirection="column" gap={1} paddingX={1}>
        <Box flexDirection="column">
          {heading('h-session', 'Session')}
          {row('time', 'Time', duration(t - s.startedAt))}
          {row('model', 'Model', s.model ? shortModel(s.model) : '—')}
          {row('requests', 'Requests', `${s.requests}${s.subagentRequests ? ` (${s.subagentRequests} subagent)` : ''}`)}
        </Box>

        <Box flexDirection="column">
          {heading('h-cost', 'Cost (estimate)')}
          {row('cost', 'Total', money(s.costUsd), ACCENT)}
          {hasBudget && row('budget', 'Alert at', `$${budget}`, s.costUsd >= budget ? BAD : undefined)}
        </Box>

        <Box flexDirection="column">
          {heading('h-tokens', `Tokens · ${count(tokensOf(s))}`)}
          {row('in', 'Input', count(s.input))}
          {row('out', 'Output', count(s.output))}
          {row('cr', 'Cache read', count(s.cacheRead))}
          {row('cw', 'Cache write', count(s.cacheWrite))}
        </Box>

        {s.contextMax > 0 && (
          <Box flexDirection="column">
            {heading('h-ctx', 'Context')}
            <Text color={contextColor(pct)}>
              {bar(pct, 20)} {pct}%
            </Text>
            <Text dimColor>
              {count(s.contextTokens)} of {count(s.contextMax)}
            </Text>
          </Box>
        )}

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

        <Box flexDirection="row" gap={1}>
          <Button
            key="reset"
            label="Reset"
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
