import { postFormBlob } from './index'

/**
 * Send audio file and target style to backend and receive converted audio as Blob
 * @param {File} file
 * @param {string} style
 * @returns {Promise<Blob>}
 */
export async function convertAudio(file, style) {
  const form = new FormData()
  form.append('file', file)
  if (style) form.append('style', style)
  return postFormBlob('/api/convert', form)
}
