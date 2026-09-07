import { useEffect, useRef } from 'react'
import { openStream } from '../api/client'

export function useStream(onResult) {
  const onResultRef = useRef(onResult)

  useEffect(() => {
    onResultRef.current = onResult
  }, [onResult])

  useEffect(() => {
    const source = openStream()

    source.onopen = () => onResultRef.current?.({ type: 'connected' })
    source.onerror = () => onResultRef.current?.({ type: 'sse-error' })

    source.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data)
        if (data.type === 'connected') return
        if (data.type !== 'result') return
        onResultRef.current?.({ type: 'result', data })
      } catch {
        /* ignore malformed frames */
      }
    }

    return () => source.close()
  }, [])

  return null
}