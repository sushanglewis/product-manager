import { Text } from 'ink'
import { render } from 'ink-testing-library'
import { EventEmitter } from 'node:events'
import React, { useEffect } from 'react'
import { afterEach, describe, expect, test, vi } from 'vitest'
import { useRecorder, type RecorderController } from '../../src/recording/useRecorder'
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
  })
  return <Text>{state.status}</Text>
}

function TestAppWithRerender({ startOnMount }: { startOnMount?: boolean } = {}) {
  const [count, setCount] = React.useState(0)
  const { state } = useRecorder({
    workspaceRoot: '/workspace',
    sessionId: '2026-06-28-test',
    topic: '',
    designId: '',
    branch: '',
    startOnMount,
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

  test('does not start recorder by default', async () => {
    const { lastFrame, rerender } = render(<TestAppWithRerender />)

    await new Promise(resolve => setTimeout(resolve, 0))
    expect(lastFrame()).toContain('idle')
    expect(spawnRecorderMock).not.toHaveBeenCalled()

    rerender(<TestAppWithRerender />)
    await new Promise(resolve => setTimeout(resolve, 50))

    expect(spawnRecorderMock).not.toHaveBeenCalled()
  })

  test('starts recorder once on mount when startOnMount is true', async () => {
    const { lastFrame, rerender } = render(
      <TestAppWithRerender startOnMount={true} />
    )

    await new Promise(resolve => setTimeout(resolve, 0))
    expect(lastFrame()).toContain('recording')
    expect(spawnRecorderMock).toHaveBeenCalledTimes(1)

    rerender(<TestAppWithRerender startOnMount={true} />)
    await new Promise(resolve => setTimeout(resolve, 50))

    expect(spawnRecorderMock).toHaveBeenCalledTimes(1)
  })

  test('shows error when recorder exits unexpectedly', async () => {
    let recorder: EventEmitter | undefined
    function CaptureRecorder() {
      const { state } = useRecorder({
        workspaceRoot: '/workspace',
        sessionId: '2026-06-28-test',
        topic: '',
        designId: '',
        branch: '',
        startOnMount: true,
      })
      useEffect(() => {
        recorder = spawnRecorderMock.mock.results[0]?.value
      }, [])
      return <Text>{state.status}:{state.errorMessage ?? ''}</Text>
    }

    const { lastFrame } = render(<CaptureRecorder />)
    await new Promise(resolve => setTimeout(resolve, 0))
    expect(lastFrame()).toContain('recording')

    recorder!.emit('exit', 1, null)
    await new Promise(resolve => setTimeout(resolve, 0))

    expect(lastFrame()).toContain('error')
    expect(lastFrame()).toContain('exited unexpectedly')
  })

  test('stays stopped when stop is called and recorder exits with non-zero code', async () => {
    let controller: RecorderController | null = null
    let recorder: EventEmitter | undefined

    function StopController() {
      controller = useRecorder({
        workspaceRoot: '/workspace',
        sessionId: '2026-06-28-test',
        topic: '',
        designId: '',
        branch: '',
        startOnMount: true,
      })
      useEffect(() => {
        recorder = spawnRecorderMock.mock.results[0]?.value
      }, [])
      return <Text>{controller.state.status}</Text>
    }

    const { lastFrame } = render(<StopController />)
    await new Promise(resolve => setTimeout(resolve, 0))
    expect(lastFrame()).toBe('recording')

    const stopPromise = controller!.stop()
    recorder!.emit('exit', 1, null)
    await stopPromise
    await new Promise(resolve => setTimeout(resolve, 0))

    expect(lastFrame()).toBe('stopped')
  })

  test('stays cancelled when cancel is called and recorder exits with non-zero code', async () => {
    let controller: RecorderController | null = null
    let recorder: EventEmitter | undefined

    function CancelController() {
      controller = useRecorder({
        workspaceRoot: '/workspace',
        sessionId: '2026-06-28-test',
        topic: '',
        designId: '',
        branch: '',
        startOnMount: true,
      })
      useEffect(() => {
        recorder = spawnRecorderMock.mock.results[0]?.value
      }, [])
      return <Text>{controller.state.status}</Text>
    }

    const { lastFrame } = render(<CancelController />)
    await new Promise(resolve => setTimeout(resolve, 0))
    expect(lastFrame()).toBe('recording')

    const cancelPromise = controller!.cancel()
    recorder!.emit('exit', null, 'SIGTERM')
    await cancelPromise
    await new Promise(resolve => setTimeout(resolve, 0))

    expect(lastFrame()).toBe('cancelled')
  })
})
