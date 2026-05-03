from fastapi import Depends, HTTPException, Response, status
from fastapi import FastAPI
from sqlalchemy.orm import Session

from database.engine import SessionLocal
from schemas.associazione import AddAssociazioneRequest
from schemas.parola import ParolaRead
from services.service import ParolaService

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

"""
    Vien fatta quando l'utente cerca una certa parola che ha visto durante la lettura.
    Vengono ritornati tutti gli omonimi flaggati a True se sono nel DB, a False altrimenti.
    Avviene una ricerca verso Treccani (con successivo salvataggio nel DB) se la parola 
    (con i suoi omonimi) non stava nel DB.
"""
@app.get("/parola/{parola}")
def get_parola(username: str, parola: str, db: Session = Depends(get_db)) -> list[ParolaRead]:
    service = ParolaService(db)
    try:
        return service.get_parola(username, parola)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

"""
    Vien fatta quando l'utente decide di aggiungere al proprio vocabolario personale
    gli omonimi di una parola. Questo metodo vien invocato dopo get_parola(); nella richiesta 
    ci sono gli omonimi in versione Treccani da aggiungere es. [palla1, palla2, palla3]  
"""
@app.post("/parole/associazioni", status_code=status.HTTP_204_NO_CONTENT)
def add_associazione(
    payload: AddAssociazioneRequest,
    db: Session = Depends(get_db)
):
    service = ParolaService(db)
    try:
        service.add_associazione(payload.username, payload.parole)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))