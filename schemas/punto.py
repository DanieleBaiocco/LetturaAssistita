from pydantic import BaseModel, Field
from typing import List, Optional
from schemas.significato import SignificatoRead

class PuntoBase(BaseModel):
    numero: int
    nome_parola: str
    categoria_parola: str
    descrizione: Optional[str] = None


class PuntoCreate(PuntoBase):
    pass


class PuntoRead(PuntoBase):
    significati: List["SignificatoRead"] = Field(default_factory=list)

    class Config:
        from_attributes = True
