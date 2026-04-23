from typing import Optional

from sqlalchemy import String, Integer, Text, ForeignKey, ForeignKeyConstraint, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Parola(Base):
    __tablename__ = "parola"

    nome: Mapped[str] = mapped_column(String(100), primary_key=True)
    categoria: Mapped[str] = mapped_column(String(50), default="undefined")
    nome_accento: Mapped[str] = mapped_column(String(150))
    origine: Mapped[str] = mapped_column(Text)
    coniugazione: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    punti: Mapped[list["Punto"]] = relationship(
        "Punto",
        back_populates="parola",
        cascade="all, delete-orphan"
    )

    occorrenze_salvate: Mapped[list["OccorrenzaSalvata"]] = relationship(
        "OccorrenzaSalvata",
        back_populates="parola",
        cascade="all, delete-orphan"
    )


class Punto(Base):
    __tablename__ = "punto"

    numero: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome_parola: Mapped[str] = mapped_column(
        ForeignKey("parola.nome", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True
    )
    descrizione: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    parola: Mapped["Parola"] = relationship("Parola", back_populates="punti")

    significati: Mapped[list["Significato"]] = relationship(
        "Significato",
        back_populates="punto",
        cascade="all, delete-orphan"
    )


class Significato(Base):
    __tablename__ = "significato"

    lettera: Mapped[str] = mapped_column(String(10), primary_key=True)
    numero: Mapped[int] = mapped_column(Integer, primary_key=True)

    numero_punto: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome_parola: Mapped[str] = mapped_column(String(100), primary_key=True)

    testo: Mapped[str] = mapped_column(Text)

    __table_args__ = (
        ForeignKeyConstraint(
            ["numero_punto", "nome_parola"],
            ["punto.numero", "punto.nome_parola"],
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
    )

    punto: Mapped["Punto"] = relationship("Punto", back_populates="significati")

    esempi: Mapped[list["Esempio"]] = relationship(
        "Esempio",
        back_populates="significato",
        cascade="all, delete-orphan"
    )


class Esempio(Base):
    __tablename__ = "esempio"

    numero_esempio: Mapped[int] = mapped_column(Integer, primary_key=True)

    lettera_significato: Mapped[str] = mapped_column(String(10), primary_key=True)
    numero_significato: Mapped[int] = mapped_column(Integer, primary_key=True)

    numero_punto: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome_parola: Mapped[str] = mapped_column(String(100), primary_key=True)

    testo: Mapped[str] = mapped_column(Text)

    __table_args__ = (
        ForeignKeyConstraint(
            [
                "lettera_significato",
                "numero_significato",
                "numero_punto",
                "nome_parola",
            ],
            [
                "significato.lettera",
                "significato.numero",
                "significato.numero_punto",
                "significato.nome_parola",
            ],
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
    )

    significato: Mapped["Significato"] = relationship(
        "Significato",
        back_populates="esempi"
    )


class Persona(Base):
    __tablename__ = "persona"

    username: Mapped[str] = mapped_column(String(100), primary_key=True)
    password: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100))

    occorrenze_salvate: Mapped[list["OccorrenzaSalvata"]] = relationship(
        "OccorrenzaSalvata",
        back_populates="persona",
        cascade="all, delete-orphan"
    )

class Libro(Base):
    __tablename__ = "libro"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    titolo: Mapped[str] = mapped_column(String(200))
    autore: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)

    occorrenze_salvate: Mapped[list["OccorrenzaSalvata"]] = relationship(
        "OccorrenzaSalvata",
        back_populates="libro",
        cascade="all, delete-orphan"
    )

class OccorrenzaSalvata(Base):
    __tablename__ = "occorrenza_salvata"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    username_persona: Mapped[str] = mapped_column(
        ForeignKey("persona.username", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False
    )

    nome_parola: Mapped[str] = mapped_column(
        ForeignKey("parola.nome", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False
    )

    libro_id: Mapped[int] = mapped_column(
        ForeignKey("libro.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False
    )

    frase_contesto: Mapped[str] = mapped_column(Text, nullable=False)

    persona: Mapped["Persona"] = relationship("Persona", back_populates="occorrenze_salvate")
    parola: Mapped["Parola"] = relationship("Parola", back_populates="occorrenze_salvate")
    libro: Mapped["Libro"] = relationship("Libro", back_populates="occorrenze_salvate")

    __table_args__ = (
        UniqueConstraint(
            "username_persona",
            "nome_parola",
            "libro_id",
            "frase_contesto",
            name="uq_occorrenza_esatta"
        ),
    )