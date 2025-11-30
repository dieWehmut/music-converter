// Use Vite env `VITE_API_BASE` if provided, otherwise default to local backend for dev
export const API_BASE = (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_BASE) || 'http://127.0.0.1:8000'

async function handleJSONResponse(res) {
	const text = await res.text()
	try {
		return JSON.parse(text)
	} catch (e) {
		return text
	}
}

export async function getJson(path) {
	const res = await fetch(`${API_BASE}${path}`)
	if (!res.ok) throw new Error(`HTTP ${res.status} ${res.statusText}`)
	return handleJSONResponse(res)
}

export async function postForm(path, formData) {
	const res = await fetch(`${API_BASE}${path}`, {
		method: 'POST',
		body: formData,
	})
	if (!res.ok) throw new Error(`HTTP ${res.status} ${res.statusText}`)
	return handleJSONResponse(res)
}

export async function postFormBlob(path, formData) {
	const res = await fetch(`${API_BASE}${path}`, {
		method: 'POST',
		body: formData,
	})
	if (!res.ok) throw new Error(`HTTP ${res.status} ${res.statusText}`)
	return res.blob()
}
