from database.tables import Significato

class SignificatoDAO:

    def __init__(self, session):
        self.session = session

    def create(self, significato: Significato):
        self.session.add(significato)

    def get_by_punto(self, numero: int, nome_parola: str):
        return self.session.query(Significato).filter(
            Significato.numero_punto == numero,
            Significato.nome_parola == nome_parola
        ).all()

    def get_one(self, lettera: str, numero_punto: int, nome_parola: str):
        return self.session.query(Significato).filter(
            Significato.lettera == lettera,
            Significato.numero_punto == numero_punto,
            Significato.nome_parola == nome_parola
        ).first()