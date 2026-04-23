from sqlalchemy import func

from database.tables import Parola
from model.converter import parola_data_to_orm, parola_orm_to_data
from model.parola import ParolaData

from schemas.parola import ParolaRead


class ParolaDAO:
    def __init__(self, session):
        self.session = session

    def salva_parola(self, parola_data: ParolaData) -> Parola:
        parola_orm = parola_data_to_orm(parola_data)
        self.session.add(parola_orm)

        # flush serve a sincronizzare col DB senza fare commit
        self.session.flush()
        return parola_orm

    def conta(self, parole: list[str]) -> int:
        nomi = {parola for parola in parole}  # set per evitare duplicati

        if not nomi:
            return 0

        return (
                self.session.query(func.count(Parola.nome))
                .filter(Parola.nome.in_(nomi))
                .scalar()
                or 0
        )

    def get_omonimi(self, parola_base: str) -> list[Parola]:
        return (
            self.session.query(Parola)
            .filter(Parola.nome.startswith(parola_base))
            .all()
        )
    def get_parola_by_nome(self, nome: str) -> Parola | None:
        query = self.session.query(Parola).filter(Parola.nome == nome)
        return query.first()