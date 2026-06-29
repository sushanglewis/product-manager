import { useCallback, useEffect, useRef, useState } from 'react'

import { spawnRecorder, type RecorderProcess, type SpawnRecorderOptions } from './spawnRecorder'

export interface UseRecorderOptions extends Omit<SpawnRecorderOptions, 'recordInterviewPath'> {
  recordInterviewPath?: string
  startOnMount?: boolean
}

export interface RecorderState {
  status: 'idle' | 'recording' | 'stopped' | 'cancelled' | 'error'
  duration: number
  amplitude: number
  errorMessage: string | null
}

export interface RecorderController {
  state: RecorderState
  start: () => void
  stop: () => Promise<void>
  cancel: () => Promise<void>
}

function mockAmplitude(duration: number): number {
  return 0.5 + 0.4 * Math.sin(duration * 0.8)
}

export function useRecorder(options: UseRecorderOptions): RecorderController {
  const {
    startOnMount = false,
    workspaceRoot,
    sessionId,
    topic,
    designId,
    branch,
    recordInterviewPath,
  } = options
  const [state, setState] = useState<RecorderState>({
    status: 'idle',
    duration: 0,
    amplitude: 0,
    errorMessage: null,
  })

  const recorderRef = useRef<RecorderProcess | null>(null)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)
  const durationRef = useRef(0)
  const terminatingRef = useRef(false)

  const clearRecordingInterval = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
  }, [])

  const start = useCallback(() => {
    if (recorderRef.current) {
      return
    }

    terminatingRef.current = false
    setState({ status: 'recording', duration: 0, amplitude: 0.3, errorMessage: null })
    durationRef.current = 0

    try {
      const recorder = spawnRecorder({
        workspaceRoot,
        sessionId,
        topic,
        designId,
        branch,
        recordInterviewPath,
      })
      recorderRef.current = recorder

      recorder.on('ready', () => {
        // Recording is active
      })

      recorder.on('error', error => {
        setState(s => ({ ...s, status: 'error', errorMessage: error.message }))
        clearRecordingInterval()
      })

      recorder.on('exit', (code, signal) => {
        recorderRef.current = null
        clearRecordingInterval()

        if (terminatingRef.current) {
          return
        }

        const reason = code !== null && code !== undefined
          ? `record-interview exited unexpectedly with code ${code}`
          : `record-interview exited unexpectedly with signal ${signal}`
        setState(s => ({ ...s, status: 'error', errorMessage: reason }))
      })

      intervalRef.current = setInterval(() => {
        durationRef.current += 1
        setState(s => ({
          ...s,
          duration: durationRef.current,
          amplitude: mockAmplitude(durationRef.current),
        }))
      }, 1000)
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error)
      setState(s => ({ ...s, status: 'error', errorMessage: message }))
    }
  }, [workspaceRoot, sessionId, topic, designId, branch, recordInterviewPath, clearRecordingInterval])

  const stop = useCallback(async () => {
    const recorder = recorderRef.current
    if (!recorder) return

    terminatingRef.current = true
    clearRecordingInterval()
    setState(s => ({ ...s, status: 'stopped' }))
    await recorder.stop()
  }, [clearRecordingInterval])

  const cancel = useCallback(async () => {
    const recorder = recorderRef.current
    if (!recorder) return

    terminatingRef.current = true
    clearRecordingInterval()
    setState(s => ({ ...s, status: 'cancelled' }))
    await recorder.cancel()
  }, [clearRecordingInterval])

  useEffect(() => {
    if (startOnMount) {
      start()
    }

    return () => {
      clearRecordingInterval()
      if (recorderRef.current) {
        recorderRef.current.cancel().catch(() => {})
        recorderRef.current = null
      }
    }
  }, [startOnMount, start, clearRecordingInterval])

  return { state, start, stop, cancel }
}
