import { callApi } from "../api.server";

export async function action({ request }) {
  if (request.method !== "POST") {
    return Response.json({ ok: false, error: "Method not allowed." }, { status: 405 });
  }

  let payload;
  try {
    payload = await request.json();
  } catch {
    return Response.json({ ok: false, error: "Invalid request." }, { status: 400 });
  }

  const ids = Array.isArray(payload.document_ids) && payload.document_ids.length
    ? payload.document_ids
    : null;

  const result = await callApi("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question: payload.question, document_ids: ids }),
  });

  if (!result.ok) {
    return Response.json({ ok: false, error: result.error }, { status: result.status });
  }
  return Response.json({ ok: true, ...result.data });
}
