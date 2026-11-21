const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function api(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, options);
  if (!response.ok) {
    let message = `Error ${response.status}`;
    try { const body = await response.json(); message = body.detail || message; } catch { /* response without JSON */ }
    throw new Error(message);
  }
  if (response.status === 204) return null;
  const type = response.headers.get('content-type') || '';
  return type.includes('application/json') ? response.json() : response.blob();
}

export const jsonRequest = (method, data) => ({ method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
