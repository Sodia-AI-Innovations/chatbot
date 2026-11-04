from sqlalchemy.orm import Session
import logging
from app.models.usage import UsageLog

logger = logging.getLogger(__name__)

def log_usage(db: Session, tenant_id, user_id, kind, prompt=0, completion=0):
    try:
        db.add(UsageLog(
            tenant_id=tenant_id, user_id=user_id, kind=kind,
            prompt_tokens=prompt, completion_tokens=completion,
            total_tokens=prompt + completion,
        ))
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Usage logging failed")
