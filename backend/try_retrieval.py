import os

from app.loaders.registry import get_loader
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import get_embedding_service
from app.services.retrieval_service import RetrievalService
from app.services.vector_store import get_vector_store

path = r"..\tests\data\handbook.txt"
pages = get_loader("txt").load(path)
chunks = ChunkingService().chunk_pages(pages, "doc1", os.path.basename(path))

emb = get_embedding_service()
store = get_vector_store()
store.delete_document("doc1", tenant_id="default")
store.add_chunks(chunks, emb.embed_documents([c.text for c in chunks]), tenant_id="default")

service = RetrievalService()

print("Threshold:", service.similarity_threshold, " top_k:", service.top_k)

print("\n1) In-document question")
for r in service.retrieve("What happens when a fund is archived?"):
    print(f"  {r.score:.3f}  {r.chunk.chunk_id}  {r.chunk.text[:80]!r}")

print("\n2) Off-topic question (expect no results)")
print(" ", service.retrieve("What is the capital of France?"))

print("\n3) Filter to a document that doesn't exist (expect no results)")
print(" ", service.retrieve("What happens when a fund is archived?", document_ids=["nope"]))

print("\n4) Wrong tenant (expect no results)")
print(" ", service.retrieve("What happens when a fund is archived?", tenant_id="someone-else"))

print("\n5) Empty question (expect an error)")
try:
    service.retrieve("   ")
except Exception as e:
    print(" ", type(e).__name__)

store.delete_document("doc1", tenant_id="default")