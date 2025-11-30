import { getJson, postForm } from './index'

export async function getStyles() {
  return getJson('/api/styles')
}

export async function extractFeatures(file) {
  const form = new FormData()
  form.append('file', file)
  return postForm('/api/features', form)
}
