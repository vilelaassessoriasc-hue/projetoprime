
# GeoObra Backend v2 (FastAPI + SQLite)

## Rodar
```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# http://localhost:8000/docs
```

## Melhorias desta versão
- Login com **JWT** (simplificado) – `/auth/login`
- **Listagem de skills** – `GET /skills`
- **Validações de lat/lng**
- **Paginação** em `/jobs/{id}/matches?limit=&offset=`
- Checagens e mensagens de erro mais claras

## Endpoints principais
- `POST /auth/signup` | `POST /auth/login`
- `POST /skills` | `GET /skills`
- `POST /users/{id}/address`
- `POST /users/{id}/skills/{skill_id}`
- `POST /jobs?empresa_id=` | `GET /jobs/{id}`
- `GET /jobs/{id}/matches?limit=50&offset=0`
