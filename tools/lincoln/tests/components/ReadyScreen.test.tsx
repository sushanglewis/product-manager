import { render } from 'ink-testing-library'
import React from 'react'
import { describe, expect, test } from 'vitest'
import { ReadyScreen } from '../../src/components/ReadyScreen'

describe('ReadyScreen', () => {
  test('renders title and session info', () => {
    const { lastFrame } = render(
      <ReadyScreen
        sessionId="2026-06-28-test"
        topic="测试访谈"
        designId="checkout-redesign"
        branch="main"
      />,
    )

    expect(lastFrame()).toContain('Lincoln Recorder')
    expect(lastFrame()).toContain('Session: 2026-06-28-test')
    expect(lastFrame()).toContain('Topic: 测试访谈')
    expect(lastFrame()).toContain('Design: checkout-redesign')
    expect(lastFrame()).toContain('Branch: main')
  })

  test('hides empty optional fields', () => {
    const { lastFrame } = render(
      <ReadyScreen
        sessionId="2026-06-28-test"
        topic=""
        designId=""
        branch=""
      />,
    )

    expect(lastFrame()).toContain('Session: 2026-06-28-test')
    expect(lastFrame()).not.toContain('Topic:')
    expect(lastFrame()).not.toContain('Design:')
    expect(lastFrame()).not.toContain('Branch:')
  })

  test('shows start and exit hints', () => {
    const { lastFrame } = render(
      <ReadyScreen
        sessionId="2026-06-28-test"
        topic=""
        designId=""
        branch=""
      />,
    )

    expect(lastFrame()).toContain('[ Enter ] 开始录音')
    expect(lastFrame()).toContain('[ Q ] 退出')
  })
})
