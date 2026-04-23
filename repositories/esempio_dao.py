from database.tables import Esempio

class EsempioDAO:

    def __init__(self, session):
        self.session = session

    def create(self, sig: Esempio):
        self.session.add(sig)

    def get_by_voce(self, lettera, numero_punto, nome_parola):
        return self.session.query(Esempio).filter(
            Esempio.lettera_significato == lettera,
            Esempio.numero_punto == numero_punto,
            Esempio.nome_parola == nome_parola
        ).all()