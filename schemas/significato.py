from typing import List, Optional

from pydantic import BaseModel, Field

from schemas.esempio import EsempioRead

class SignificatoBase(BaseModel):
    lettera: Optional[str] = None
    numero: int
    numero_punto: int
    nome_parola: str
    categoria_parola: str
    testo: str


class SignificatoCreate(SignificatoBase):
    pass


class SignificatoRead(SignificatoBase):
    esempi: List["EsempioRead"] = Field(default_factory=list)

    class Config:
        from_attributes = True