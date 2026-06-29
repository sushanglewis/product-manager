import { Box, Text } from 'ink'
import React from 'react'

export interface ReadyScreenProps {
  sessionId: string
  topic: string
  designId: string
  branch: string
}

export function ReadyScreen({ sessionId, topic, designId, branch }: ReadyScreenProps) {
  return (
    <Box flexDirection="column" borderStyle="round" borderColor="gray" padding={1}>
      <Box flexDirection="row" justifyContent="space-between" alignItems="center">
        <Box gap={1}>
          <Text color="red">●</Text>
          <Text color="yellow">●</Text>
          <Text color="green">●</Text>
        </Box>
        <Text bold color="white">Lincoln Recorder</Text>
      </Box>

      <Box flexDirection="column" paddingY={1}>
        <Text color="gray">Session: {sessionId}</Text>
        {topic ? <Text color="gray">Topic: {topic}</Text> : null}
        {designId ? <Text color="gray">Design: {designId}</Text> : null}
        {branch ? <Text color="gray">Branch: {branch}</Text> : null}
      </Box>

      <Box flexDirection="column" alignItems="center" paddingY={1} gap={1}>
        <Text bold color="green">[ Enter ] 开始录音</Text>
        <Text color="gray" dimColor>[ Q ] 退出</Text>
      </Box>
    </Box>
  )
}
