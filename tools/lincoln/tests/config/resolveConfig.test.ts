import { mkdirSync, mkdtempSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { describe, expect, test } from 'vitest'
import { resolveConfig } from '../../src/config/resolveConfig'

describe('resolveConfig', () => {
  test('uses defaults when no args and no config files exist', () => {
    const dir = mkdtempSync(join(tmpdir(), 'lincoln-resolve-'))

    const result = resolveConfig({}, { cwd: dir, home: dir, now: new Date('2026-06-28T00:00:00Z') })

    expect(result.sessionId).toMatch(/^2026-06-28-/)
    expect(result.noTui).toBe(false)
  })

  test('CLI args override global config', () => {
    const home = mkdtempSync(join(tmpdir(), 'lincoln-home-'))
    writeFileSync(join(home, '.lincolnrc'), 'default_design_id: global-design\n', 'utf-8')

    const result = resolveConfig(
      { designId: 'cli-design' },
      { cwd: home, home, now: new Date('2026-06-28T00:00:00Z') },
    )

    expect(result.designId).toBe('cli-design')
  })

  test('local config overrides global config', () => {
    const home = mkdtempSync(join(tmpdir(), 'lincoln-home-'))
    const cwd = mkdtempSync(join(tmpdir(), 'lincoln-cwd-'))
    writeFileSync(join(home, '.lincolnrc'), 'default_design_id: global-design\n', 'utf-8')
    writeFileSync(join(cwd, '.lincolnrc'), 'default_design_id: local-design\n', 'utf-8')

    const result = resolveConfig({}, { cwd, home, now: new Date('2026-06-28T00:00:00Z') })

    expect(result.designId).toBe('local-design')
  })

  test('uses global config when no local config or CLI args', () => {
    const home = mkdtempSync(join(tmpdir(), 'lincoln-home-'))
    const cwd = mkdtempSync(join(tmpdir(), 'lincoln-cwd-'))
    writeFileSync(join(home, '.lincolnrc'), 'default_topic: "全局主题"\n', 'utf-8')

    const result = resolveConfig({}, { cwd, home, now: new Date('2026-06-28T00:00:00Z') })

    expect(result.topic).toBe('全局主题')
  })

  test('preserves CLI noTui flag', () => {
    const dir = mkdtempSync(join(tmpdir(), 'lincoln-resolve-'))

    const result = resolveConfig(
      { noTui: true },
      { cwd: dir, home: dir, now: new Date('2026-06-28T00:00:00Z') },
    )

    expect(result.noTui).toBe(true)
  })

  test('appends counter when recording file already exists', () => {
    const dir = mkdtempSync(join(tmpdir(), 'lincoln-resolve-'))
    const recordingsDir = join(dir, 'recordings')
    mkdirSync(recordingsDir)
    writeFileSync(join(recordingsDir, '2026-06-28-recording.m4a'), '', 'utf-8')
    writeFileSync(join(recordingsDir, '2026-06-28-recording-001.m4a'), '', 'utf-8')

    const result = resolveConfig({}, { cwd: dir, home: dir, now: new Date('2026-06-28T00:00:00Z') })

    expect(result.sessionId).toBe('2026-06-28-recording-002')
  })
})
