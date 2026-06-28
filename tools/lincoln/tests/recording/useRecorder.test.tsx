import { Text } from 'ink'
import { render } from 'ink-testing-library'
import { EventEmitter } from 'node:events'
import React, { useState } from 'react'
import { afterEach, describe, expect, test, vi } from 'vitest'
import { useRecorder } from '../../src/recording/useRecorder'
import { spawnRecorder as spawnRecorderMock } from '../../src/recording/spawnRecorder'

vi.mock('../../src/recording/spawnRecorder', () => {
  const { EventEmitter } = require('node:events')

  function createMockRecorder() {
    const recorder = new EventEmitter()
    recorder.stop = vi.fn(() => Promise.resolve())
    recorder.cancel = vi.fn(() => Promise.resolve())
    return recorder
  }

  return {
    spawnRecorder: vi.fn(() => createMockRecorder()),
  }
})

function TestApp() {
  const { state } = useRecorder({
    workspaceRoot: '/workspace',
    sessionId: '2026-06-28-test',
    topic: '',
    designId: '',
    branch: '',
    startOnMount: false,
  })
  return <Text>{state.status}</Text>
}

function TestAppWithRerender() {
  const [count, setCount] = useState(0)
  const { state } = useRecorder({
    workspaceRoot: '/workspace',
    sessionId: '2026-06-28-test',
    topic: '',
    designId: '',
    branch: '',
    startOnMount: true,
  })

  return <Text>{state.status}:{count}</Text>
}

describe('useRecorder', () => {
  afterEach(() => {
    vi.clearAllMocks()
  })

  test('starts in idle state', () => {
    const { lastFrame } = render(<TestApp />)

    expect(lastFrame()).toBe('idle')
    expect(spawnRecorderMock).not.toHaveBeenCalled()
  })

  test('starts recorder once on mount and survives parent re-renders', async () => {
    const { lastFrame, rerender } = render(<TestAppWithRerender />)

    await new Promise(resolve => setTimeout(resolve, 0))
    expect(lastFrame()).toContain('recording')
    expect(spawnRecorderMock).toHaveBeenCalledTimes(1)

    rerender(<TestAppWithRerender />)
    await new Promise(resolve => setTimeout(resolve, 50))

    expect(spawnRecorderMock).toHaveBeenCalledTimes(1)
  })
})
