export type Feature = { id: string; geometry: { coordinates: [number, number] }; properties: Record<string, unknown> };
export const apiUrl = import.meta.env.VITE_FIREWATCH_API_URL || '';
export async function getJson(path: string) { const response = await fetch(`${apiUrl}${path}`); if (!response.ok) throw new Error(`API ${response.status}`); return response.json(); }
export async function loadMapData() { const [metadata, incidents] = await Promise.all([getJson('/api/v1/metadata'), getJson('/api/v1/incidents?west=94&south=-12&east=142&north=8&from=2026-10-18T00:00:00Z&to=2026-10-19T23:59:59Z&limit=500')]); return { metadata, features: (incidents.features || []) as Feature[] }; }
