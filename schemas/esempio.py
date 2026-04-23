from typing import Optional

from pydantic import BaseModel



class EsempioBase(BaseModel):
    numero_esempio: int
    lettera_significato: Optional[str] = None
    numero_significato: int
    numero_punto: int
    nome_parola: str
    categoria_parola: str
    testo: str

class EsempioCreate(EsempioBase):
    pass

class EsempioRead(EsempioBase):
    class Config:
        from_attributes = True