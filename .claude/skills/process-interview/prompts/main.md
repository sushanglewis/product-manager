# process-interview

You are executing the Lincoln workflow step `ingest`: process a stakeholder interview recording.

## Goal

Extract structured information from the audio file and write artifacts to `interviews/<session-id>/`.

## Input

- `recording_path`: path to the audio file (e.g., `recordings/2026-06-27-stakeholder.m4a`)

## Steps

1. Validate the file exists and is one of the supported formats: `.mp3`, `.m4a`, `.wav`, `.mp4`, `.mov`.
2. Derive `session_id` from the filename without extension (e.g., `2026-06-27-stakeholder`).
3. Create directory `interviews/<session-id>/`.
4. Extract audio track if input is video using `ffmpeg`.
5. Transcribe using Whisper (prefer local `faster-whisper`; fallback to OpenAI Whisper API if local fails).
6. Generate `transcript.md` with timestamped Speaker A/B segments.
7. Generate `summary.md` with:
   - `关键主题`
   - `决策`
   - `行动项`
   - `开放问题`
8. Generate `raw-insights.md` with Agent's preliminary observations about potential requirements.
9. Write `metadata.json` with:
   - sessionId
   - originalFile
   - duration
   - processedAt
   - transcriptModel
   - status

## Output Artifacts

- `interviews/<session-id>/metadata.json`
- `interviews/<session-id>/transcript.md`
- `interviews/<session-id>/summary.md`
- `interviews/<session-id>/raw-insights.md`

## Rules

- Do not modify the original recording file.
- If transcription fails, write a partial artifact and report the error clearly.
- Use Chinese for the summary and insights unless the interview is in English.
- After completion, tell the user the next command: `claude clarify-requirements <session-id>`.
