from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.tables import Base

DATABASE_URL = "mysql+pymysql://root:sBrodoLinabella3567@localhost/vocabolario"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True
)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)