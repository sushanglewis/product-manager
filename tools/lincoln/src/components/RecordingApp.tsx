import { Box, Text } from 'ink'
import React, { useState } from 'react'

import { CancelledScreen } from './CancelledScreen'
import { RecordingScreen } from './RecordingScreen'
import { ReadyScreen } from './ReadyScreen'
import { StopConfirmation } from './StopConfirmation'
import { useKeyHandler } from '../hooks/useKeyHandler'
import { useRecorder } from '../recording/useRecorder'
import { triggerProcessInterview, type TriggerResult } from '../workflow/triggerProcessInterview'

export interface RecordingAppProps {
  workspaceRoot: string
  sessionId: string
  topic: string
  designId: string
  branch: string
  audioMeterStyle?: 'bar' | 'dot' | 'wave'
  recordInterviewPath?: string
}

type AppPhase = 'ready' | 'recording' | 'cancelled'

type WorkflowStatus = 'idle' | 'processing' | 'success' | 'error' | 'skipped'

interface WorkflowState {
  status: WorkflowStatus
  message: string
}

export function RecordingApp({
  workspaceRoot,
  sessionId,
  topic,
  designId,
  branch,
  audioMeterStyle = 'bar',
  recordInterviewPath,
}: RecordingAppProps) {
  const [phase, setPhase] = useState<AppPhase>('ready')
  const [workflow, setWorkflow] = useState<WorkflowState>({ status: 'idle', message: '' })
  const { state, start, stop, cancel } = useRecorder({
    workspaceRoot,
    sessionId,
    topic,
    designId,
    branch,
    recordInterviewPath,
    startOnMount: false,
  })

  useKeyHandler({
    onStop: () => {
      if (phase === 'ready') {
        setPhase('recording')
        start()
      } else if (state.status === 'recording') {
        stop()
      }
    },
    onCancel: () => {
      if (phase === 'ready') {
        setPhase('cancelled')
      } else if (state.status === 'recording') {
        cancel()
      }
    },
  })

  if (phase === 'cancelled' || state.status === 'cancelled') {
    return <CancelledScreen />
  }

  if (state.status === 'stopped') {
    if (workflow.status === 'idle') {
      return (
        <StopConfirmation
          sessionId={sessionId}
          onConfirm={async () => {
            setWorkflow({ status: 'processing', message: 'Running process-interview...' })
            try {
              const result: TriggerResult = await triggerProcessInterview(workspaceRoot, sessionId)
              setWorkflow({ status: result.success ? 'success' : 'error', message: result.message })
            } catch (error) {
              const message = error instanceof Error ? error.message : String(error)
              setWorkflow({ status: 'error', message })
            }
          }}
          onCancel={() => setWorkflow({ status: 'skipped', message: 'process-interview skipped' })}
        />
      )
    }

    return (
      <Box flexDirection="column" padding={1}>
        <Text bold>{workflow.status === 'processing' ? 'Processing' : workflow.status === 'success' ? 'Done' : workflow.status === 'error' ? 'Error' : 'Skipped'}</Text>
        <Text>{workflow.message}</Text>
      </Box>
    )
  }

  if (state.status === 'error') {
    return (
      <Box flexDirection="column" padding={1}>
        <Text bold color="red">Recording error</Text>
        <Text>{state.errorMessage}</Text>
      </Box>
    )
  }

  if (phase === 'ready') {
    return (
      <ReadyScreen
        sessionId={sessionId}
        topic={topic}
        designId={designId}
        branch={branch}
      />
    )
  }

  return (
    <RecordingScreen
      sessionId={sessionId}
      topic={topic}
      designId={designId}
      duration={state.duration}
      amplitude={state.amplitude}
      audioMeterStyle={audioMeterStyle}
    />
  )
}
