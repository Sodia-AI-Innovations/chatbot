const BASE = process.env.API_URL || "http://localhost:8000";

export async function callApi(path, options = {}) {
  let res;
  try {
    res = await fetch(`${BASE}${path}`, options);
  } catch {
    return { ok: false, status: 503, error: "Cannot reach the backend. Is it running?" };
  }

  let data = null;
  try {
    data = await res.json();
  } catch {
    // response had no JSON body
  }

  if (!res.ok) {
    let message = data?.message || data?.detail?.[0]?.msg || `Request failed (${res.status})`;
    if (res.status >= 500 && data?.request_id) {
      message += ` (ref: ${data.request_id})`;
    }
    return { ok: false, status: res.status, error: message };
  }
  return { ok: true, status: res.status, data };
}
