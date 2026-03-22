import { getAccessToken } from './supabase'

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

export class ApiError extends Error {
  constructor(message, status, code) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

async function authenticatedFetch(path, init = {}) {
  const accessToken = await getAccessToken()
  if (!accessToken) {
    throw new ApiError('Authentication is required.', 401, 'missing_token')
  }

  const headers = new Headers(init.headers || {})
  headers.set('Authorization', `Bearer ${accessToken}`)

  const response = await fetch(path, {
    ...init,
    headers,
  })
  const payload = await response.json().catch(() => null)

  if (!response.ok) {
    throw new ApiError(
      payload?.error?.message || 'Request failed.',
      response.status,
      payload?.error?.code,
    )
  }

  return payload
}

export async function getJobStatus(jobId) {
  return authenticatedFetch(`/api/jobs/${jobId}`)
}

export async function uploadVideo(file) {
  const formData = new FormData()
  const durationSeconds = await getVideoDurationSeconds(file)

  formData.append('video', file)
  formData.append('duration_seconds', String(durationSeconds))

  return authenticatedFetch('/api/upload', {
    method: 'POST',
    body: formData,
  })
}

export async function getProfile() {
  return authenticatedFetch('/api/profile')
}

export async function getMatches() {
  return authenticatedFetch('/api/matches')
}
