from __future__ import annotations

from math import asin, cos, radians, sin, sqrt
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from . import models, schemas
from .security import get_password_hash, verify_password


class NotFoundError(HTTPException):
    def __init__(self, detail: str = "Resource not found") -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def create_user(db: Session, user_in: schemas.UserCreate) -> models.User:
    user = models.User(
        name=user_in.name,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:  # pragma: no cover - defensive
        db.rollback()
        if "UNIQUE constraint failed" in str(exc.orig):
            raise HTTPException(status_code=400, detail="email already registered") from exc
        raise
    db.refresh(user)
    return user


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.execute(select(models.User).where(models.User.email == email)).scalar_one_or_none()


def authenticate_user(db: Session, email: str, password: str) -> Optional[models.User]:
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def create_skill(db: Session, skill_in: schemas.SkillCreate) -> models.Skill:
    skill = models.Skill(name=skill_in.name.strip())
    db.add(skill)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="skill already exists") from exc
    db.refresh(skill)
    return skill


def list_skills(db: Session) -> List[models.Skill]:
    result = db.scalars(select(models.Skill).order_by(models.Skill.name))
    return list(result)


def create_or_update_address(
    db: Session, user_id: int, address_in: schemas.AddressCreate
) -> models.Address:
    user = db.get(models.User, user_id)
    if not user:
        raise NotFoundError("user not found")

    address = user.address
    if address is None:
        address = models.Address(user_id=user_id)
        db.add(address)

    for field, value in address_in.model_dump().items():
        setattr(address, field, value)

    db.commit()
    db.refresh(address)
    return address


def attach_skill_to_user(db: Session, user_id: int, skill_id: int) -> models.User:
    user = db.get(models.User, user_id)
    if not user:
        raise NotFoundError("user not found")
    skill = db.get(models.Skill, skill_id)
    if not skill:
        raise NotFoundError("skill not found")

    if skill not in user.skills:
        user.skills.append(skill)
        db.commit()
        db.refresh(user)
    return user


def create_job(db: Session, company_id: int, job_in: schemas.JobCreate) -> models.Job:
    company = db.get(models.User, company_id)
    if not company:
        raise NotFoundError("company not found")

    job = models.Job(
        title=job_in.title,
        description=job_in.description,
        company_id=company_id,
        latitude=job_in.latitude,
        longitude=job_in.longitude,
    )
    db.add(job)
    db.flush()  # ensure job.id for relationship assignment

    if job_in.skill_ids:
        skills = list(
            db.scalars(select(models.Skill).where(models.Skill.id.in_(job_in.skill_ids)))
        )
        missing = set(job_in.skill_ids) - {skill.id for skill in skills}
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"skills not found: {sorted(missing)}",
            )
        job.skills = skills

    db.commit()
    db.refresh(job)
    return job


def get_job(db: Session, job_id: int) -> models.Job:
    job = db.execute(
        select(models.Job)
        .options(joinedload(models.Job.skills), joinedload(models.Job.company).joinedload(models.User.skills))
        .where(models.Job.id == job_id)
    ).scalar_one_or_none()
    if not job:
        raise NotFoundError("job not found")
    return job


def list_job_matches(
    db: Session, job: models.Job, limit: int = 50, offset: int = 0
) -> List[schemas.JobMatch]:
    required_ids = {skill.id for skill in job.skills}

    query = (
        select(models.User)
        .options(joinedload(models.User.skills), joinedload(models.User.address))
        .where(models.User.id != job.company_id)
        .order_by(models.User.created_at.desc())
    )
    if required_ids:
        query = (
            query.join(models.user_skills_table)
            .where(models.user_skills_table.c.skill_id.in_(required_ids))
            .distinct()
        )
    else:
        query = query.distinct()
    users = list(db.scalars(query.offset(offset).limit(limit)))

    matches: List[schemas.JobMatch] = []
    required_len = len(required_ids) or 1
    for user in users:
        user_skill_ids = {skill.id for skill in user.skills}
        matching = len(required_ids & user_skill_ids) if required_ids else len(user_skill_ids)
        distance = _calculate_distance(job, user)
        matches.append(
            schemas.JobMatch(
                user_id=user.id,
                user_name=user.name,
                matching_skills=matching,
                required_skills=required_len,
                distance_km=distance,
            )
        )
    matches.sort(key=lambda m: (-(m.matching_skills / required_len), m.distance_km or float("inf")))
    return matches


def _calculate_distance(job: models.Job, user: models.User) -> Optional[float]:
    if job.latitude is None or job.longitude is None:
        return None
    if not user.address:
        return None
    lat1, lon1 = job.latitude, job.longitude
    lat2, lon2 = user.address.latitude, user.address.longitude
    return _haversine(lat1, lon1, lat2, lon2)


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0  # Earth radius in kilometers
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(min(1, sqrt(a)))
    return round(r * c, 2)
