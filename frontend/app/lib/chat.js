export async function askQuestion(question, documentIds) {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, document_ids: documentIds }),
  });

  let data = null;
  try {
    data = await res.json();
  } catch {
    // not JSON
  }
  if (!data || !data.ok) {
    throw new Error(data?.error || "Something went wrong.");
  }
  return data;
}
