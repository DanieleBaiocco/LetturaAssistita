from database.tables import Punto, Parola, Significato, Esempio
from schemas.parola import ParolaRead


def read_to_orm(parola_read: ParolaRead) -> Parola:
    parola = Parola(
        nome=parola_read.nome,
        categoria=parola_read.categoria or "undefined",
        nome_accento=parola_read.nome_accento,
        origine=parola_read.origine,
        coniugazione=parola_read.coniugazione,
    )

    for punto_read in parola_read.punti:
        punto = Punto(
            numero=punto_read.numero,
            nome_parola=parola.nome,
            categoria_parola=parola.categoria,
            descrizione=punto_read.descrizione,
        )

        for sig_read in punto_read.significati:
            significato = Significato(
                lettera=sig_read.lettera or "_",
                numero=sig_read.numero,
                numero_punto=punto.numero,
                nome_parola=parola.nome,
                categoria_parola=parola.categoria,
                testo=sig_read.testo,
            )

            for ex_read in sig_read.esempi:
                esempio = Esempio(
                    numero_esempio=ex_read.numero_esempio,
                    lettera_significato=significato.lettera,
                    numero_significato=significato.numero,
                    numero_punto=punto.numero,
                    nome_parola=parola.nome,
                    categoria_parola=parola.categoria,
                    testo=ex_read.testo,
                )
                significato.esempi.append(esempio)

            punto.significati.append(significato)

        parola.punti.append(punto)
    return parola


def parola_orm_to_read(parola_orm: Parola) -> ParolaRead:
    return ParolaRead.model_validate(parola_orm)