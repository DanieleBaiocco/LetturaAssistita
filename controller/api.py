from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from database.engine import SessionLocal
from repositories.parola_dao import ParolaDAO
from schemas.parola import ParolaRead
from services.service import ParolaService

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/parola/{parola}")
def create_termine(parola: str, username: str, db: Session = Depends(get_db)) -> ParolaRead:
    service = ParolaService(db)
    try:
        return service.create_parola(parola, username)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))