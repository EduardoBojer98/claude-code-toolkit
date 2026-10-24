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
