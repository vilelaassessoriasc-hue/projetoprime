from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/{user_id}/address", response_model=schemas.AddressRead)
def upsert_address(
    user_id: int, address_in: schemas.AddressCreate, db: Session = Depends(get_db)
) -> schemas.AddressRead:
    return crud.create_or_update_address(db, user_id, address_in)


@router.post("/{user_id}/skills/{skill_id}", response_model=schemas.UserRead)
def attach_skill(
    user_id: int, skill_id: int, db: Session = Depends(get_db)
) -> schemas.UserRead:
    return crud.attach_skill_to_user(db, user_id, skill_id)
