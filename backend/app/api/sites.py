import uuid
from urllib.parse import quote

from fastapi import APIRouter, Depends,File , UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_document_service, get_tenant_id
from app.core.config import get_settings
from app.core.db import get_db
from app.core.errors import InvalidTokenError, SiteNotFoundError
from app.models.bot_token import BotToken
from app.models.response import DocumentInfo
from app.services.document_service import DocumentService
from app.utils.domains import normalize_domain
from app.utils.tokens import generate_token


router = APIRouter(tags=["sites"])

PUBLIC_URL = "http://localhost:8000"

class SiteCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    domain: str

def build_snippet(token:str) -> str:
    src = f"{PUBLIC_URL}/widget.js?token={quote(token)}"
    return f'<script src="{src}" async></script>'

def site_out(bt: BotToken) -> dict:
    return {
        "id": str(bt.id),
        "name": bt.name,
        "domain": bt.domain,
        "token": bt.token,
        "snippet": build_snippet(bt.token),
        "is_active": bt.is_active,
        "created_at": bt.created_at.isoformat(),
    }

def get_owned_site(db: Session, tenat_id: str, site_id: uuid.UUID) -> BotToken:
    bt = db.query(BotToken).filter_by(id=site_id, owner_id=tenat_id).first()
    if not bt:
        raise SiteNotFoundError()
    return bt

@router.post("/sites")
def create_site(body: SiteCreate, tenant_id: str = Depends(get_tenant_id), db: Session = Depends(get_db)):
    domain = normalize_domain(body.domain)
    if not domain or ("." not in domain and domain != "localhost"):
        raise InvalidDomainError()

    bt = db.query(BotToken).filter_by(owner_id=tenant_id, domain=domain).first()
    if not bt:
        bt = BotToken(owner_id=tenant_id, name=body.name.strip(),domain=domain, token=generate_token())
        db.add(bt)
        db.commit()
        db.refresh(bt)
    return site_out(bt)

@router.get("/sites")
def list_sites(tenant_id: str = Depends(get_tenant_id), db:Session = Depends(get_db)):
    rows = db.query(BotToken).filter_by(owner_id=tenant_id).order_by(BotToken.created_at.desc()).all()
    return [site_out(bt) for bt in rows]

@router.get("/sites/{site_id}")
def get_site(site_id: uuid.UUID, tenant_id: str = Depends(get_tenant_id), db:Session = Depends(get_db)):
    return site_out(get_owned_site(db, tenant_id, site_id))

@router.post("/sites/{site_id}/rotate")
def rotate_site(site_id: uuid.UUID, tenant_id: str = Depends(get_tenant_id), db: Session = Depends(get_db)):
    bt = get_owned_site(db, tenant_id, site_id)
    bt.token = generate_token()
    db.commit()
    return site_out(bt)

@router.delete("/sites/{site_id}")
def delete_site(
    site_id: uuid.UUID,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
    service: DocumentService = Depends(get_document_service),
):
    bt = get_owned_site(db, tenant_id, site_id)
    scope = str(bt.id)
    for doc in service.list_documents(scope):
        service.delete_document(doc.document_id, scope)
    db.delete(bt)
    db.commit()
    return {"deleted": True}


@router.post("/sites/{site_id}/documents", response_model=DocumentInfo, status_code=201)
def upload_site_document(
    site_id: uuid.UUID,
    file: UploadFile = File(...),
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
    service: DocumentService = Depends (get_document_service),
):
    bt = get_owned_site(db, tenant_id, site_id)
    max_bytes = get_settings().max_file_size_mb * 1024 * 1024
    content = file.file.read(max_bytes + 1)
    return service.ingest(file.filename,content,str(bt.id))

@router.get("/sites/{site_id}/documents", response_model=list[DocumentInfo])
def list_site_documents(
    site_id: uuid.UUID,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
    service: DocumentService = Depends(get_document_service),
):
    bt = get_owned_site(db, tenant_id, site_id)
    return service.list_documents(str(bt.id))

@router.delete("/sites/{site_id}/documents/{document_id}")
def delete_site_documet(
    site_id: uuid.UUID,
    document_id: str,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
    service: DocumentService = Depends(get_document_service),
):
    bt = get_owned_site(db, tenant_id, site_id)
    service.delete_document(document_id, str(bt.id))
    return {"document_id" : document_id, "status": "deleted"}

