from sqlalchemy import func

from database.tables import Taccuino, Parola


class TaccuinoDAO:
    def __init__(self, session):
        self.session = session

    def count_nomi_associati(
            self,
            username: str,
            nomi_parole: list[str]
    ) -> int:
        nomi_unici = set(nomi_parole)

        if not nomi_unici:
            return 0

        return (
                self.session.query(func.count(Taccuino.nome_parola))
                .filter(
                    Taccuino.username_persona == username,
                    Taccuino.nome_parola.in_(nomi_unici)
                )
                .scalar()
                or 0
        )

    def get_parole_utente(
            self,
            username: str,
            nome_parola: str
    ) -> list[Parola]:
        return (
            self.session.query(Parola)
            .join(Taccuino, Taccuino.nome_parola == Parola.nome)
            .filter(
                Taccuino.username_persona == username,
                Parola.nome.startswith(nome_parola)
            )
            .all()
        )


    def add_associazioni(
            self,
            username: str,
            nomi_parole: list[str]
    ) -> None:
        associazioni = [
            Taccuino(username_persona=username, nome_parola=nome)
            for nome in nomi_parole
        ]
        self.session.add_all(associazioni)