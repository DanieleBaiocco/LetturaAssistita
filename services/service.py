from typing import List

from sqlalchemy.orm import Session

from database.tables import Parola
from model.parola import ParolaData
from repositories.parola_dao import ParolaDAO
from repositories.taccuino_dao import TaccuinoDAO
from schemas.parola import ParolaRead, ParolaReadWithDbStatus
from services.scraper import scrape_treccani, scrape_treccani_multiple
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

class ParolaService:

    def __init__(self, session: Session):
        self.session = session
        self.parola_repo = ParolaDAO(session)
        self.taccuino_repo = TaccuinoDAO(session)

    def get_parola(self, username: str, parola_utente: str) -> list[ParolaReadWithDbStatus]:
        parole_orm = self.taccuino_repo.get_parole_utente(
            username=username,
            nome_parola=parola_utente
        )

        if len(parole_orm) == 0:
            omonimi = scrape_treccani_multiple(parola_utente)

            try:
                for omonimo in omonimi:
                    self.parola_repo.salva_parola(omonimo)
                self.session.commit()
            except Exception:
                self.session.rollback()
                raise

            return [
                ParolaReadWithDbStatus(
                    **omonimo.model_dump(),
                    presente_in_db=False
                )
                for omonimo in omonimi
            ]

        return [
            ParolaReadWithDbStatus(
                **ParolaRead.model_validate(parola_orm).model_dump(),
                presente_in_db=True
            )
            for parola_orm in parole_orm
        ]

    def create_parola(self, username: str, parole: list[str]) -> None:
        try:
            nomi_parole = set(parole)

            n_parole = self.parola_repo.conta(list(nomi_parole))
            if n_parole != len(nomi_parole):
                raise ValueError("Una delle parole non è presente nel DB, aggiungerla prima!")

            num_nomi_associati = self.taccuino_repo.count_nomi_associati(
                username=username,
                nomi_parole=list(nomi_parole)
            )

            if num_nomi_associati == len(nomi_parole):
                raise ValueError("Non c'è nulla da aggiungere: le parole sono già tutte associate.")
            if num_nomi_associati != 0:
                raise ValueError("Qualche parola e' associata, qualche altra no.")

            self.taccuino_repo.add_associazioni(
                username=username,
                nomi_parole=list(nomi_parole)
            )
            self.session.commit()

        except IntegrityError as e:
            self.session.rollback()
            raise RuntimeError("Violazione di integrità nel database") from e


        except SQLAlchemyError as e:
            self.session.rollback()
            raise RuntimeError("Errore durante l'accesso al database") from e