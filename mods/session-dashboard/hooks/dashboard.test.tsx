import { expect, test } from 'claude-code/testing'

const PANE = {
  plugin: 'session-dashboard',
  component: 'Pane',
  requestId: 'session-dashboard',
  props: {
    title: 'Session',
    isFocused: false,
    bodyColumns: 40,
    placement: 'dock',
    scroll: { offset: 0, bodyRows: 40 },
    view: {},
  },
} as const

test('tool calls and edited files show in the panel, on every surface', async ($, on) => {
  on('command.register', () => ({ value: { command: 'dash' } }))
  on('ui.open', () => ({ value: { isPlaced: true } }))
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('tool.call', () => ({ result: {} }))

  await $.session.start({ cwd: '/', surface: 'desktop', isInteractive: true })
  await $.tool.call({ tool: 'Bash', command: 'ls' })
  await $.tool.call({ tool: 'Edit', file_path: '/repo/src/app/page.tsx', old_string: 'a', new_string: 'b' })
  await $.tool.call({ tool: 'Edit', file_path: '/repo/src/app/page.tsx', old_string: 'b', new_string: 'c' })

  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({ ...PANE, surface })
    expect((await ui.find({ type: 'Text', text: /^Tools · / }))?.text).toBe('Tools · 3')
    // The same file edited twice counts once.
    expect((await ui.find({ type: 'Text', text: /^Files edited/ }))?.text).toBe('Files edited · 1')
    expect((await ui.find({ type: 'Text', text: /page\.tsx/ }))?.text).toBe('…/app/page.tsx')
    await ui.unmount()
  }
})

test('a stats value from an older version is read as blank', async ($, on) => {
  on('state.get', () => ({ value: { value: { calls: 99 }, version: 1 } }))

  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect((await ui.find({ type: 'Text', text: /No tool calls yet/ }))?.text).toBe('No tool calls yet.')
  await ui.unmount()
})

test('subagents, their models and the skills they load show in the panel', async ($, on) => {
  on('command.register', () => ({ value: { command: 'dash' } }))
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('agent.spawn', () => ({ model: 'claude-haiku-5-5', agentId: 'agent-explore-0001' }))
  on('turn.complete', (_, e) => ({ text: e.answer }))
  on('skill.prompt', (_, e) => ({ text: e.text }))
  // A Skill tool call loads its skill inside the call, as in a session.
  on('clock.now', () => ({ value: 1_000 }))
  on('tool.call', async (_, e) => {
    if (e.tool === 'Skill') {
      await $.skill.prompt({ skill: 'debug', text: '# Debug', frontmatter: {}, source: 'userSettings' })
    }
    return { result: {} }
  })

  await $.session.start({ cwd: '/', surface: 'desktop', isInteractive: true })
  await $.agent.spawn({
    prompt: 'find priceWithTax',
    description: 'Find priceWithTax',
    subagentType: 'Explore',
    tool_use_id: 'toolu_1',
    provider: { plugin: 'engine', tier: 'core' },
    parentModel: 'claude-opus-5-5',
    background: false,
    fork: false,
  })
  await $.tool.call({ tool: 'Read', file_path: '/repo/src/price.js', agentId: 'agent-explore-0001' })
  await $.tool.call({ tool: 'Skill', skill: 'debug', agentId: 'agent-explore-0001' })
  await $.tool.call({ tool: 'Skill', skill: 'debug' })
  await $.turn.complete({ answer: 'src/price.js:1', durationMs: 4200, isAborted: false, turnId: 't1', agentId: 'agent-explore-0001', reason: 'answer' })

  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({ ...PANE, surface })
    expect((await ui.find({ type: 'Text', text: /^Agents · / }))?.text).toBe('Agents · 1')
    expect((await ui.find({ type: 'Text', text: /Find priceWithTax/ }))?.text).toContain('Read 1')
    expect((await ui.find({ type: 'Text', text: /^haiku ×/ }))?.text).toBe('haiku ×1')
    expect((await ui.find({ type: 'Text', text: /^✓$/ }))?.text).toBe('✓')
    expect((await ui.find({ type: 'Text', text: /^Skills · / }))?.text).toBe('Skills · 1')
    expect((await ui.find({ type: 'Text', text: /×2 · / }))?.text).toBe('×2 · Explore#0001, lead')
    await ui.unmount()
  }
})

test('draws nothing outside its pane: no band above the prompt, no status line', async ($, on) => {
  let statusWrites = 0
  on('ui.status', () => {
    statusWrites += 1
    return { value: undefined }
  })
  on('command.register', () => ({ value: { command: 'dash' } }))
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('tool.call', () => ({ result: {} }))

  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  await $.tool.call({ tool: 'Edit', file_path: '/repo/a.ts', old_string: 'a', new_string: 'b' })

  const band = await $.ui
    .mount({ plugin: 'session-dashboard', component: 'AbovePrompt', surface: 'terminal', props: { bodyColumns: 80, hasSurvey: false } } as never)
    .catch(() => undefined)
  expect(band ? await band.find({ type: 'Button' }) : undefined).toBeUndefined()
  await band?.unmount()
  expect(statusWrites).toBe(0)
})
