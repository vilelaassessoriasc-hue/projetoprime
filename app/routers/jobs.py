from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db
from ..dependencies import get_current_user
from ..models import User

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=schemas.JobDetail, status_code=201)
def create_job(
    job_in: schemas.JobCreate,
    empresa_id: int = Query(..., description="ID da empresa que está cadastrando o job"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.JobDetail:
    if empresa_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="operation not permitted for this company")

    job = crud.create_job(db, empresa_id, job_in)
    # Reload with relationships for the response
    return schemas.JobDetail.model_validate(crud.get_job(db, job.id))


@router.get("/{job_id}", response_model=schemas.JobDetail)
def read_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.JobDetail:
    job = crud.get_job(db, job_id)
    if job.company_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="operation not permitted for this company")
    return schemas.JobDetail.model_validate(job)


@router.get("/{job_id}/matches", response_model=List[schemas.JobMatch])
def read_job_matches(
    job_id: int,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[schemas.JobMatch]:
    job = crud.get_job(db, job_id)
    if job.company_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="operation not permitted for this company")
    return crud.list_job_matches(db, job, limit=limit, offset=offset)
