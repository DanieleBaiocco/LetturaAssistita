from typing import List

from sqlalchemy.orm import Session

from database.tables import Parola
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
        """
        Recupera tutti gli omonimi generali di una parola e indica, per ciascuno,
        se è già presente nel taccuino dell'utente.
        """

        omonimi_orm = self.parola_repo.get_omonimi(parola_utente)

        if len(omonimi_orm) == 0:
            omonimi = scrape_treccani_multiple(parola_utente)

            try:
                omonimi_orm = [
                    self.parola_repo.salva_parola(omonimo)
                    for omonimo in omonimi
                ]
                self.session.commit()

            except IntegrityError as e:
                self.session.rollback()
                raise RuntimeError("Violazione di integrità nel database") from e

            except SQLAlchemyError as e:
                self.session.rollback()
                raise RuntimeError("Errore durante l'accesso al database") from e

        omonimi_utente_orm = self.taccuino_repo.get_parole_utente(
            username=username,
            nome_parola=parola_utente
        )

        nomi_omonimi_utente = {
            omonimo_utente.nome
            for omonimo_utente in omonimi_utente_orm
        }

        return [
            ParolaReadWithDbStatus(
                **ParolaRead.model_validate(omonimo_orm).model_dump(),
                presente_in_db=omonimo_orm.nome in nomi_omonimi_utente
            )
            for omonimo_orm in omonimi_orm
        ]

    def add_associazione(self, username: str, parole: list[str]) -> None:
        if not parole:
            raise ValueError("Nessuna parola da associare.")
        nomi_parole = set(parole)
        try:

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