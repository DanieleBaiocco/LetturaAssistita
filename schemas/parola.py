from typing import List, Optional

from pydantic import BaseModel

from schemas.punto import PuntoRead


class ParolaBase(BaseModel):
    nome: str
    nome_accento: str
    categoria: Optional[str] = None
    origine: Optional[str] = None
    coniugazione: Optional[str] = None


class ParolaCreate(ParolaBase):
    pass


class ParolaRead(ParolaBase):
    punti: List["PuntoRead"] = []

    class Config:
        from_attributes = True


class ParolaReadWithDbStatus(ParolaRead):
    presente_in_db: bool