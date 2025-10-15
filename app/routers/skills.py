from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db

router = APIRouter(prefix="/skills", tags=["skills"])


@router.post("", response_model=schemas.SkillRead, status_code=201)
def create_skill(
    skill_in: schemas.SkillCreate, db: Session = Depends(get_db)
) -> schemas.SkillRead:
    return crud.create_skill(db, skill_in)


@router.get("", response_model=List[schemas.SkillRead])
def list_skills(db: Session = Depends(get_db)) -> List[schemas.SkillRead]:
    return crud.list_skills(db)
