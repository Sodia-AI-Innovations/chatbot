import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.core.errors import SiteNotFoundError, UserExistsError, UserNotFoundError
from app.models.bot_token import BotToken
from app.models.usage import UsageLog
from app.models.user import User

def require_admin():
    """admin login and roles"""

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])

EMPTY = {"requests": 0, "input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "last_active": None}

def _usage_by_tenant(db: Session, tenant_ids: list[str] | None = None) -> dict[str, dict]:
    q = db.query(
        UsageLog.tenant_id,
        func.count(UsageLog.id),
        func.coalesce(func.sum(UsageLog.prompt_tokens), 0),
        func.coalesce(func.sum(UsageLog.completion_tokens), 0),
        func.coalesce(func.sum(UsageLog.total_tokens), 0),
        func.max(UsageLog.created_at),
    )
    if tenant_ids is not None:
        q = q.filter(UsageLog.tenant_id.in_(tenant_ids))
    return {
        r[0]: {
            "requests": r[1], "input_tokens": int(r[2]), "output_tokens": int(r[3]),
            "total_tokens": int(r[4]),
            "last_active": r[5].isoformat() if r[5] else None,
        }
        for r in q.group_by(UsageLog.tenant_id).all()
    }

def _cost(tokens: int) -> float:
    return round(tokens / 1000 * get_settings().price_per_1k_tokens, 4)

def _bot_row(bot: BotToken, usage: dict) -> dict:
    u = usage.get(str(bot.id), EMPTY)
    return{
        "id": str(bot.id), "name": bot.name, "domain": bot.domain,
        "created_at": bot.created_at.isoformat(), **u, "cost":_cost(u["total_tokens"]),
    }

def _daily(db: Session, days: int, tenant_id: str | None = None) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    day = func.date_trunc("day", UsageLog.created_at)
    q = db.query(day, func.coalesce(func.sum(UsageLog.total_tokens), 0)). filter(
        UsageLog.created_at >= since
    )
    if tenant_id:
        q = q.filter(UsageLog.tenant_id == tenant_id)
    return [{"day": d. date().isoformat(), "tokens": int(t)}
            for d, t in q.group_by(day).order_by(day).all()]

@router.get("/overview")
def overview(days: int = 30, db: Session = Depends(get_db)):
    total = sum(v["total_tokens"] for v in _usage_by_tenant(db).values())
    return {
        "users": db.query(func.count(User.id)).scalar(),
        "chatbots": db.query(func.count(BotToken.id)).scalar(),
        "total_tokens": total,
        "cost": _cost(total),
        "currency": get_settings().currency,
        "daily": _daily(db, days),
    }

@router.get("/users")
def list_users(db: Session = Depends(get_db)):
    usage = _usage_by_tenant(db)
    by_owner: dict[str, list[BotToken]] = {}
    for b in db.query(BotToken).all():
        by_owner.setdefault(b.owner_id, []).append(b)

    out = []
    for u in db.query(User).order_by(User.created_at.desc()).all():
        mine = by_owner.get(u.id, [])
        total = sum(usage.get(str(b.id), EMPTY)["total_tokens"] for b in mine)
        total += usage.get(u.id, EMPTY)["total_tokens"]
        out.append({
            "id": u.id, "name": u.name, "email": u.email, "role": u.role,
            "joined": u.created_at.isoformat(), "chatbots": len(mine),
            "tokal_tokens": total, "cost": _cost(total),
        })
    return out

class UserIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=200)

@router.post("/users", status_code=201)
def create_user(body: UserIn, db: Session = Depends(get_db)):
    """Temporary: lets you add test users until registration exists."""
    email = body.email.strip().lower()
    if db.query(User).filter_by(email=email).first():
        raise UserExistsError()
    user = User(id=uuid.uuid4().hex, name=body.name.strip(), email=email)
    db.add(user)
    db.commit()
    return {"id": user.id, "name": user.name, "email": user.email}

@router.get("/users/{user_id}")
def user_detail(user_id: str, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise UserNotFoundError()
    usage = _usage_by_tenant(db)
    bots = db.query(BotToken).filter_by(owner_id=user_id).order_by(BotToken.created_at.desc()).all()
    rows = [_bot_row(b, usage) for b in bots] 
    direct = usage.get(user_id, EMPTY)["total_tokens"]
    total = sum(r["total_tokens"] for r in rows) + direct
    return {
        "user": {"id": user.id, "name": user.name, "email": user.email,"role": user.role, "joined":user.created_at.isoformat()},
        "chatbots": rows,
        "direct_tokens": direct,
        "total_tokens": total,
        "cost": _cost(total),
        "currency": get_settings().currency,
    }
@router.get("/chatbots/{bot_id}")
def chatbot_detail(bot_id: uuid.UUID, days: int = 30, db: Session = Depends(get_db)):
    bot = db.get(BotToken, bot_id)
    if not bot:
        raise SiteNotFoundError()
    usage = _usage_by_tenant(db, [str(bot.id)])
    owner = db.get(User, bot.owner_id)
    return {
        "chatbot": _bot_row(bot, usage),
        "owner": {"id": bot.owner_id, "name": owner.name if owner else bot.owner_id},
        "currency": get_settings().currency,
        "daily": _daily(db, days, str(bot.id)),
    }
