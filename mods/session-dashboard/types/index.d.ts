export type AgentRun = {
  /** Agent type it was spawned as (`Explore`, `implementer`, `general-purpose`, …). */
  type: string
  /** The Agent call's short task description. */
  description: string
  /** Model it ran on (resolved id, or the alias a hook gave). */
  model: string
  /** Id of the agent that spawned it; '' when the main session did. */
  parent: string
  status: 'running' | 'done' | 'failed' | 'aborted'
  isBackground: boolean
  /** When it started (ms) and how long it ran (ms, set when it ends). */
  startedAt: number
  durationMs: number
  requests: number
  tokens: number
  costUsd: number
  toolCalls: number
  /** Calls per tool name inside this agent. */
  tools: Record<string, number>
  /** Skills this agent loaded. */
  skills: string[]
}

export type SkillUse = {
  count: number
  /** Where the skill comes from (`userSettings`, `plugin`, `syncedSkills`, …). */
  source: string
  /** Who loaded it: 'lead', 'you' (slash command or preload) or an agent label. */
  by: Record<string, number>
}

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
  /** Subagents by id, and their ids in start order. */
  agents: Record<string, AgentRun>
  agentOrder: string[]
  /** Skills loaded this session, by name. */
  skills: Record<string, SkillUse>
}

declare module 'claude-code' {
  interface PluginState {
    'session-dashboard': { stats: Shaped<Stats>; now: number }
  }
}
