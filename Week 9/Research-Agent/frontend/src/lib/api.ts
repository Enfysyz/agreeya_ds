import type { LogEntry, ResearchResult } from '@/types'

export async function streamResearch(
  topic: string,
  onLog: (log: LogEntry) => void,
  onComplete: (result: ResearchResult) => void,
  onError: (error: string) => void
): Promise<void> {
  try {
    const response = await fetch('/api/research', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic }),
    })

    if (!response.ok) {
      onError(`Server error: ${response.status} ${response.statusText}`)
      return
    }

    const reader = response.body?.getReader()
    if (!reader) {
      onError('Failed to initialize stream reader.')
      return
    }

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      // Keep the last incomplete line in the buffer
      buffer = lines.pop() || ''

      for (const line of lines) {
        const trimmed = line.trim()
        if (!trimmed.startsWith('data: ')) continue

        try {
          const jsonStr = trimmed.slice(6) // Remove 'data: ' prefix
          const event = JSON.parse(jsonStr)

          if (event.type === 'log') {
            onLog({
              type: 'log',
              message: event.message,
              url: event.url,
              timestamp: new Date(),
            })
          } else if (event.type === 'complete') {
            onComplete({
              type: 'complete',
              result: event.result,
            })
          }
        } catch {
          // Skip malformed JSON
        }
      }
    }
  } catch (err) {
    onError(err instanceof Error ? err.message : 'An unexpected error occurred.')
  }
}
