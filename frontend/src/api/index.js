// Use Vite env `VITE_API_BASE` if provided.
// In development (local), default to localhost:8000 to avoid ngrok timeouts/limits.
// In production, fallback to the ngrok URL or whatever is configured.
export const API_BASE = import.meta.env.VITE_API_BASE || (import.meta.env.DEV ? 'http://localhost:8000' : 'https://leisurely-pervertible-deonna.ngrok-free.dev')

async function handleJSONResponse(res) {
	const text = await res.text()
	try {
		return JSON.parse(text)
	} catch (e) {
		return text
	}
}

export async function getJson(path) {
	const res = await fetch(`${API_BASE}${path}`, {
		headers: {
			'ngrok-skip-browser-warning': 'true'
		}
	})
	if (!res.ok) throw new Error(`HTTP ${res.status} ${res.statusText}`)
	return handleJSONResponse(res)
}

export async function postForm(path, formData) {
	const res = await fetch(`${API_BASE}${path}`, {
		method: 'POST',
		headers: {
			'ngrok-skip-browser-warning': 'true'
		},
		body: formData,
	})
	if (!res.ok) throw new Error(`HTTP ${res.status} ${res.statusText}`)
	return handleJSONResponse(res)
}

export async function postFormBlob(path, formData) {
	const res = await fetch(`${API_BASE}${path}`, {
		method: 'POST',
		headers: {
			'ngrok-skip-browser-warning': 'true'
		},
		body: formData,
	})
	if (!res.ok) throw new Error(`HTTP ${res.status} ${res.statusText}`)
	return res.blob()
}

export async function getBlob(path) {
	const res = await fetch(`${API_BASE}${path}`, {
		headers: {
			'ngrok-skip-browser-warning': 'true'
		}
	})
	if (!res.ok) throw new Error(`HTTP ${res.status} ${res.statusText}`)
	return res.blob()
}
