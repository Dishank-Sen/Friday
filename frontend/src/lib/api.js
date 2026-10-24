export const viewerUrl = import.meta.env.VITE_VIEWER_URL?.trim() ?? '';
export const backendUrl = import.meta.env.VITE_BACKEND_URL?.trim() ?? '';

export async function getBackendHealth({ signal } = {}) {
  if (!backendUrl) {
    return { available: false, reason: 'Configure VITE_BACKEND_URL in frontend/.env.local.' };
  }

  try {
    const response = await fetch('/api/health', {
      headers: { Accept: 'application/json' },
      signal,
    });
    if (!response.ok) {
      return { available: false, reason: `Health check returned HTTP ${response.status}.` };
    }
    const data = await response.json();
    if (data.status !== 'ok') {
      return { available: false, reason: 'The control service did not report healthy.' };
    }
    return { available: true, checkedAt: new Date() };
  } catch (error) {
    if (error.name === 'AbortError') throw error;
    return { available: false, reason: 'Cannot reach the desktop control service.' };
  }
}
