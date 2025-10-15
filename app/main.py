from __future__ import annotations

from fastapi import FastAPI

from .database import Base, engine
from .routers import auth, jobs, skills, users

Base.metadata.create_all(bind=engine)

app = FastAPI(title="GeoObra Backend", version="2.0")

app.include_router(auth.router)
app.include_router(skills.router)
app.include_router(users.router)
app.include_router(jobs.router)


@app.get("/health", tags=["system"])
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
