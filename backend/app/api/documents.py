from fastapi import APIRouter, Depends, File, UploadFile
from pydantic import BaseModel, HttpUrl
from app.api.deps import get_document_service ,get_tenant_id
from app.core.config import get_settings
from app.models.response import DocumentInfo
from app.services.document_service import DocumentService
from pydantic import BaseModel, Field, HttpUrl

router = APIRouter(prefix="/documents", tags=["documents"])
class UrlIn(BaseModel):
    url: HttpUrl
    crawl: bool = False
    max_pages: int = Field(default=15, ge=1, le=50)

@router.post("/url", response_model=DocumentInfo, status_code=201)
def add_url(
    body: UrlIn,
    tenant_id: str = Depends(get_tenant_id),
    service: DocumentService = Depends(get_document_service),
):
    return service.ingest_url(str(body.url), tenant_id, body.crawl, body.max_pages)    

@router.post("/upload", response_model=DocumentInfo, status_code=201)
def upload_document(
    file: UploadFile = File(...),
    tenant_id: str = Depends(get_tenant_id),
    service: DocumentService = Depends(get_document_service),
):
    max_bytes = get_settings(). max_file_size_mb *1024 * 1024
    content = file.file.read(max_bytes + 1)
    return service.ingest(file.filename, content, tenant_id)

@router.get("", response_model=list[DocumentInfo])
def list_documents(
    tenant_id: str = Depends(get_tenant_id),
    service: DocumentService = Depends(get_document_service),
):
    return service.list_documents(tenant_id)

@router.delete("/{document_id}")
def delete_document(
    document_id: str,
    teneant_id: str = Depends(get_tenant_id),
    service: DocumentService = Depends(get_document_service),
):
    service.delete_document(document_id, teneant_id)
    return {"document_id": document_id, "status": "deleted"}
