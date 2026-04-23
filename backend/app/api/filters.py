from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import SavedFilter
from app.schemas import SavedFilterIn, SavedFilterOut

router = APIRouter(prefix="/api/filters", tags=["filters"])


@router.get("", response_model=list[SavedFilterOut])
async def list_filters(client_id: str | None = None, session: AsyncSession = Depends(get_session)):
    q = select(SavedFilter)
    if client_id:
        q = q.where(SavedFilter.client_id == client_id)
    q = q.order_by(SavedFilter.created_at.desc())
    rows = (await session.execute(q)).scalars().all()
    return [SavedFilterOut(id=r.id, name=r.name, payload=r.payload, client_id=r.client_id, created_at=r.created_at) for r in rows]


@router.post("", response_model=SavedFilterOut)
async def create_filter(body: SavedFilterIn, session: AsyncSession = Depends(get_session)):
    row = SavedFilter(name=body.name, payload=body.payload, client_id=body.client_id)
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return SavedFilterOut(id=row.id, name=row.name, payload=row.payload, client_id=row.client_id, created_at=row.created_at)


@router.delete("/{filter_id}")
async def delete_filter(filter_id: int, session: AsyncSession = Depends(get_session)):
    row = await session.get(SavedFilter, filter_id)
    if not row:
        raise HTTPException(404, "filter not found")
    await session.delete(row)
    await session.commit()
    return {"ok": True}
