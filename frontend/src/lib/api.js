function getVideoDurationSeconds(file) {
  return new Promise((resolve, reject) => {
    const video = document.createElement('video')
    const objectUrl = URL.createObjectURL(file)

    const cleanup = () => {
      URL.revokeObjectURL(objectUrl)
      video.removeAttribute('src')
      video.load()
    }

    video.preload = 'metadata'
    video.onloadedmetadata = () => {
      const durationSeconds = Number(video.duration)
      cleanup()

      if (!Number.isFinite(durationSeconds) || durationSeconds <= 0) {
        reject(new Error('Unable to determine the selected video duration.'))
        return
      }

      resolve(durationSeconds)
    }
    video.onerror = () => {
      cleanup()
      reject(new Error('Unable to read the selected video metadata.'))
    }
    video.src = objectUrl
  })
}

export async function summarizeVideo(file) {
  const formData = new FormData()
  const durationSeconds = await getVideoDurationSeconds(file)

  formData.append('video', file)
  formData.append('duration_seconds', String(durationSeconds))

  const response = await fetch('/api/summarize', {
    method: 'POST',
    body: formData,
  })

  const payload = await response.json().catch(() => null)

  if (!response.ok) {
    const message = payload?.error?.message || 'Unable to analyze this recording right now.'
    throw new Error(message)
  }

  return payload
}
