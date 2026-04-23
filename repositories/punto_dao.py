from database.tables import Punto

class PuntoDAO:

    def __init__(self, session):
        self.session = session

    def create(self, punto: Punto):
        self.session.add(punto)

    def get_by_termine(self, nome_parola: str):
        return self.session.query(Punto).filter(
            Punto.nome_parola == nome_parola
        ).all()

    def get_one(self, numero: int, nome_parola: str):
        return self.session.query(Punto).filter(
            Punto.numero == numero,
            Punto.nome_parola == nome_parola
        ).first()