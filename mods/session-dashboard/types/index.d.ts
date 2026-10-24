export type Stats = {
  /** When counting started (ms), 0 before the first session.start. */
  startedAt: number
  /** Model requests: main loop and subagents. */
  requests: number
  subagentRequests: number
  input: number
  output: number
  cacheRead: number
  cacheWrite: number
  /** Rough estimate from token counts and a price table, not a bill. */
  costUsd: number
  /** Last model the main loop used. */
  model: string
  /** Main loop's context after its last request, and the model's window. */
  contextTokens: number
  contextMax: number
  toolCalls: number
  toolErrors: number
  /** Calls per tool name. */
  tools: Record<string, number>
  /** Files written or edited, most recent last. */
  files: string[]
  /** Whether the cost alert has fired for the current budget. */
  isBudgetWarned: boolean
}

declare module 'claude-code' {
  interface PluginState {
    'session-dashboard': { stats: Shaped<Stats>; now: number }
  }
}
