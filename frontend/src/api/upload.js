import { postForm, getJson, getBlob } from './index'

/**
 * Send audio file and target style to backend. Backend returns a task_id.
 * We poll `/api/tasks/{task_id}` until status === 'success' then download
 * the generated audio at `/api/tasks/{task_id}/download` and return it as Blob.
 * @param {File} file
 * @param {string} style
 * @param {string} emotion
 * @param {object} options - optional { pollIntervalMs, timeoutMs }
 * @returns {Promise<Blob>}
 */
export async function convertAudio(file, style, emotion, options = {}) {
  const form = new FormData()
  form.append('file', file)
  if (style) form.append('style', style)
  if (emotion) form.append('emotion', emotion)

  // Defaults: poll every 2s, no timeout by default (set timeoutMs to a number to enable)
  const { pollIntervalMs = 2000, timeoutMs = null } = options

  // Start conversion - backend returns JSON { task_id, status }
  const res = await postForm('/api/convert', form)
  const taskId = res && (res.task_id || res.taskId)
  if (!taskId) throw new Error('No task_id returned from convert API')

  const start = Date.now()
  // Poll until success or failed or timeout
  while (true) {
    if (timeoutMs && Date.now() - start > timeoutMs) throw new Error('Conversion timed out')
    let statusResp
    try {
      statusResp = await getJson(`/api/tasks/${taskId}`)
    } catch (e) {
      // transient error: wait and retry
      await new Promise(r => setTimeout(r, pollIntervalMs))
      continue
    }

    if (!statusResp) {
      await new Promise(r => setTimeout(r, pollIntervalMs))
      continue
    }

    if (statusResp.status === 'success') {
      // download blob
      const blob = await getBlob(`/api/tasks/${taskId}/download`)
      return blob
    }

    if (statusResp.status === 'failed' || statusResp.status === 'error') {
      const errMsg = statusResp.error || statusResp.detail || 'Conversion failed on server'
      throw new Error(errMsg)
    }

    // still pending/processing, wait
    await new Promise(r => setTimeout(r, pollIntervalMs))
  }
}
