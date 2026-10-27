from app.loaders.registry import get_loader
from app.utils.file_validation import validate_file
from app.utils.text_cleaner import clean_text
import os
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import get_embedding_service
import math
from app.services.vector_store import get_vector_store
path = r"..\tests\data\handbook.txt"
ext = validate_file(os.path.basename(path), os.path.getsize(path))
pages = get_loader(ext).load(path)

for p in pages:
    print(p.page_number, len(p.text), "->", len(clean_text(p.text)))

raw = pages[0].text
cleaned = clean_text(raw)
print(repr(raw[:300]))
print(repr(cleaned[:300]))    

chunks = ChunkingService().chunk_pages(pages, document_id="doc1", filename=os.path.basename(path))

print()
print("total chunks:", len(chunks))
print("lengths:", [len(c.text) for c in chunks[:10]])
print()
print(chunks[0])
print()
print("--- end of chunk 0 ---")
print(chunks[0].text[-150:])
print("--- start of chunk 1 ---")
print(chunks[1].text[:150])


emd = get_embedding_service()
print()
print("dimension:", emd.dimension)

vectors = emd.embed_documents([c.text for c in chunks])
store = get_vector_store()
store.delete_document("doc1", tenant_id="default")
store.add_chunks(chunks, vectors, tenant_id="default")
print("embedded: ", len(vectors), "chunks")

def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (math.sqrt(sum(x* x for x in a)) * math.sqrt(sum(y* y for y in b)))

question = "How are tenent workspaces and user riles handled?"
q = emd.embed_query(question)
ranked = sorted(zip(chunks, vectors), key=lambda cv: cosine(q, cv[1]), reverse=True)

print("\nQuestion:", question)
for c, v in ranked[:3]:
    print(f"{cosine(q, v): .3f} {c.chunk_id} {c.text[:90]!r}")

print("\n from the database:")
for r in store.search(q, top_k=3, tenant_id="default"):
    print(f"{r.score:.3f} {r.chunk.chunk_id} {r.chunk.text[:90]!r}")
print("\n Other tenant sees:", len(store.search(q, top_k=3, tenant_id="someone-else")), "results")
print("Deleted", store.delete_document("doc1", tenant_id="default"), "chunks")        


