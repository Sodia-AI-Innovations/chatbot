from sqlalchemy import Column, Integer, String, DateTime, func
from app.core.db import Base

class UsageLog(Base):
    __tablename__="usage_logs"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String, index=True, nullable=False)
    user_id =  Column(String, index=True, nullable=True)
    kind = Column(String, nullable=False)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)