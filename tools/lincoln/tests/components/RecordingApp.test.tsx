import { render } from 'ink-testing-library'
import React from 'react'
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest'
import { RecordingApp } from '../../src/components/RecordingApp'
import type { RecorderController, RecorderState } from '../../src/recording/useRecorder'

const idleState: RecorderState = {
  status: 'idle',
  duration: 0,
  amplitude: 0,
  errorMessage: null,
}

const recordingState: RecorderState = {
  status: 'recording',
  duration: 83,
  amplitude: 0.65,
  errorMessage: null,
}

let currentController: RecorderController

vi.mock('../../src/recording/useRecorder', () => ({
  useRecorder: vi.fn(() => currentController),
}))

vi.mock('../../src/workflow/triggerProcessInterview', () => ({
  triggerProcessInterview: vi.fn(() => Promise.resolve({ success: true, message: 'done' })),
}))

async function tick() {
  return new Promise(resolve => setTimeout(resolve, 0))
}

describe('RecordingApp', () => {
  beforeEach(() => {
    currentController = {
      state: { ...idleState },
      start: vi.fn(() => {
        currentController.state = { ...recordingState }
      }),
      stop: vi.fn(() => {
        currentController.state = { status: 'stopped', duration: 83, amplitude: 0, errorMessage: null }
        return Promise.resolve()
      }),
      cancel: vi.fn(() => {
        currentController.state = { status: 'cancelled', duration: 0, amplitude: 0, errorMessage: null }
        return Promise.resolve()
      }),
    }
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  test('renders ready screen initially', () => {
    const { lastFrame } = render(
      <RecordingApp
        workspaceRoot="/workspace"
        sessionId="2026-06-28-test"
        topic="测试访谈"
        designId="test-design"
        branch="main"
        audioMeterStyle="bar"
      />,
    )

    expect(lastFrame()).toContain('Lincoln Recorder')
    expect(lastFrame()).toContain('Session: 2026-06-28-test')
    expect(lastFrame()).toContain('Topic: 测试访谈')
    expect(lastFrame()).toContain('[ Enter ] 开始录音')
  })

  test('starts recording when Enter is pressed from ready screen', async () => {
    const { lastFrame, stdin, rerender } = render(
      <RecordingApp
        workspaceRoot="/workspace"
        sessionId="2026-06-28-test"
        topic=""
        designId=""
        branch=""
        audioMeterStyle="bar"
      />,
    )

    await tick()
    expect(lastFrame()).toContain('[ Enter ] 开始录音')

    stdin.write('\r')
    await tick()
    expect(currentController.start).toHaveBeenCalled()

    rerender(
      <RecordingApp
        workspaceRoot="/workspace"
        sessionId="2026-06-28-test"
        topic=""
        designId=""
        branch=""
        audioMeterStyle="bar"
      />,
    )
    await tick()

    expect(lastFrame()).toContain('Recording')
  })

  test('shows cancelled screen when q is pressed from ready screen', async () => {
    const { lastFrame, stdin } = render(
      <RecordingApp
        workspaceRoot="/workspace"
        sessionId="2026-06-28-test"
        topic=""
        designId=""
        branch=""
        audioMeterStyle="bar"
      />,
    )

    await tick()
    stdin.write('q')
    await tick()

    expect(lastFrame()).toContain('cancelled')
    expect(currentController.start).not.toHaveBeenCalled()
  })

  test('calls stop when Enter is pressed during recording', async () => {
    const { stdin, rerender } = render(
      <RecordingApp
        workspaceRoot="/workspace"
        sessionId="2026-06-28-test"
        topic=""
        designId=""
        branch=""
        audioMeterStyle="bar"
      />,
    )

    await tick()
    stdin.write('\r')
    await tick()
    expect(currentController.start).toHaveBeenCalled()

    rerender(
      <RecordingApp
        workspaceRoot="/workspace"
        sessionId="2026-06-28-test"
        topic=""
        designId=""
        branch=""
        audioMeterStyle="bar"
      />,
    )
    await tick()

    stdin.write('\r')
    await tick()

    expect(currentController.stop).toHaveBeenCalled()
  })

  test('calls cancel when q is pressed during recording', async () => {
    const { stdin, rerender } = render(
      <RecordingApp
        workspaceRoot="/workspace"
        sessionId="2026-06-28-test"
        topic=""
        designId=""
        branch=""
        audioMeterStyle="bar"
      />,
    )

    await tick()
    stdin.write('\r')
    await tick()

    rerender(
      <RecordingApp
        workspaceRoot="/workspace"
        sessionId="2026-06-28-test"
        topic=""
        designId=""
        branch=""
        audioMeterStyle="bar"
      />,
    )
    await tick()

    stdin.write('q')
    await tick()

    expect(currentController.cancel).toHaveBeenCalled()
  })

  test('shows confirmation screen when stopped', async () => {
    currentController.state = { status: 'stopped', duration: 120, amplitude: 0, errorMessage: null }

    const { lastFrame } = render(
      <RecordingApp
        workspaceRoot="/workspace"
        sessionId="2026-06-28-test"
        topic=""
        designId=""
        branch=""
        audioMeterStyle="bar"
      />,
    )

    await tick()
    expect(lastFrame()).toContain('process-interview')
    expect(lastFrame()).toContain('Yes')
  })

  test('triggers process-interview when y is pressed on stopped screen', async () => {
    const { triggerProcessInterview } = await import('../../src/workflow/triggerProcessInterview')
    currentController.state = { status: 'stopped', duration: 120, amplitude: 0, errorMessage: null }

    const { stdin, lastFrame } = render(
      <RecordingApp
        workspaceRoot="/workspace"
        sessionId="2026-06-28-test"
        topic=""
        designId=""
        branch=""
        audioMeterStyle="bar"
      />,
    )

    await tick()
    stdin.write('y')
    await tick()

    expect(triggerProcessInterview).toHaveBeenCalledWith('/workspace', '2026-06-28-test')
    expect(lastFrame()).toContain('Done')
  })

  test('skips process-interview when n is pressed on stopped screen', async () => {
    const { triggerProcessInterview } = await import('../../src/workflow/triggerProcessInterview')
    currentController.state = { status: 'stopped', duration: 120, amplitude: 0, errorMessage: null }

    const { stdin, lastFrame } = render(
      <RecordingApp
        workspaceRoot="/workspace"
        sessionId="2026-06-28-test"
        topic=""
        designId=""
        branch=""
        audioMeterStyle="bar"
      />,
    )

    await tick()
    stdin.write('n')
    await tick()

    expect(triggerProcessInterview).not.toHaveBeenCalled()
    expect(lastFrame()).toContain('skipped')
  })
})
