import { getAccessToken } from './supabase'

export class ApiError extends Error {
  constructor(message, { status, code } = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

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

async function fetchApi(path, { auth = true, headers, ...init } = {}) {
  const nextHeaders = new Headers(headers || {})

  if (auth) {
    const accessToken = await getAccessToken()
    if (!accessToken) {
      throw new ApiError('Authentication is required.', {
        status: 401,
        code: 'missing_token',
      })
    }
    nextHeaders.set('Authorization', `Bearer ${accessToken}`)
  }

  const response = await fetch(path, {
    ...init,
    headers: nextHeaders,
  })
  const payload = await response.json().catch(() => null)

  if (!response.ok) {
    throw new ApiError(
      payload?.error?.message || 'The request failed.',
      {
        status: response.status,
        code: payload?.error?.code,
      },
    )
  }

  return payload
}

export async function uploadVideo(file) {
  const formData = new FormData()
  const durationSeconds = await getVideoDurationSeconds(file)

  formData.append('video', file)
  formData.append('duration_seconds', String(durationSeconds))

  return fetchApi('/api/upload', {
    method: 'POST',
    body: formData,
  })
}

export async function getJobStatus(jobId) {
  return fetchApi(`/api/jobs/${jobId}`)
}

export async function getProfile() {
  return fetchApi('/api/profile')
}

export async function getMatches() {
  return fetchApi('/api/matches')
}
